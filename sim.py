"""VayuNetra integrated simulation. Everything running in one loop."""

import sys, math, random, argparse
sys.path.insert(0, ".")

from swarm.drone import Drone
from core.bus import BUS
from core.contracts import make_task
from mission.fsm import MissionFSM
from mission.auction import ContractNet
from integration.adapters import LocalizationBridge
from integration.perception_adapter import PerceptionAdapter

ANCHORS = [[0.0, 0.0], [500.0, 0.0], [250.0, 500.0], [0.0, 500.0]]
SIZE = 500.0
CELL = 50.0                      # search cell size in metres
DETECT_RADIUS = 40.0
RESCUE_RADIUS = 20.0


class Mission:
    def __init__(self, n_drones=6, n_survivors=5, seed=42, ranging_on=True):
        random.seed(seed)
        self.drones = []
        for i in range(n_drones):
            d = Drone(drone_id=i, position=(random.uniform(50, 450),
                                            random.uniform(50, 450)))
            d.belief_pos = list(d.position)
            d.velocity = [0.0, 0.0]
            d.alive = True
            d.state = "SEARCHING"
            d.assigned_task = None
            d.uncertainty = 0.0
            d.search_target = None
            self.drones.append(d)

        self.survivors = [{"id": i,
                           "pos": [random.uniform(50, 450), random.uniform(50, 450)],
                           "found": False, "rescued": False}
                          for i in range(n_survivors)]

        self.bridge = LocalizationBridge(self.drones, ANCHORS, ranging_on=ranging_on)
        self.fsm = MissionFSM(self.drones)
        self.net = ContractNet(settle_ticks=4)
        self.perception = PerceptionAdapter(use_real=False, seed=seed)
        self.tasks = {}
        self.complete = False

        # ---- distributed search state ----
        # Every cell centre that still needs sweeping.
        n_cells = int(SIZE // CELL)
        self.unsearched = {(cx, cy)
                           for cx in range(n_cells)
                           for cy in range(n_cells)}
        self.total_cells = len(self.unsearched)
        self.claimed = {}            # cell -> drone_id

        BUS.subscribe("SURVIVOR_DETECTED", self.on_detection)

    # ------------------------------------------------------------------
    def on_detection(self, p):
        tid = f"T{p['survivor_id']:03d}"
        if tid in self.tasks:
            return
        task = make_task(tid, p["location"][0], p["location"][1], p["confidence"])
        self.tasks[tid] = task
        self.net.issue_cfp(task)

    def cell_centre(self, cell):
        return [cell[0] * CELL + CELL / 2, cell[1] * CELL + CELL / 2]

    def claim_cell(self, drone):
        """
        Each drone picks its own next search cell, using its own belief
        position and skipping cells another drone has already claimed.
        No allocator - this is the same local-decision principle as the auction.
        """
        available = [c for c in self.unsearched if c not in self.claimed]
        if not available:
            self.claimed = {k: v for k, v in self.claimed.items()
                            if v == drone.drone_id}
            available = [c for c in self.unsearched if c not in self.claimed]
            if not available:
                return None
        bx, by = drone.belief_pos
        best = min(available, key=lambda c: math.dist(self.cell_centre(c), (bx, by)))
        self.claimed[best] = drone.drone_id
        return best

    def release_claims(self, drone_id):
        self.claimed = {k: v for k, v in self.claimed.items() if v != drone_id}

    # ------------------------------------------------------------------
    def move(self, d):
        """Fly to an assigned survivor, otherwise sweep the next search cell."""
        if d.assigned_task and d.assigned_task in self.tasks:
            target = self.tasks[d.assigned_task]["location"]
        else:
            if d.search_target is None or d.search_target not in self.unsearched:
                d.search_target = self.claim_cell(d)
            target = self.cell_centre(d.search_target) if d.search_target else None

        if target is None:
            d.velocity = [0.0, 0.0]
            return

        # navigate using BELIEF, not truth - this is the honest bit
        bx, by = d.belief_pos
        dx, dy = target[0] - bx, target[1] - by
        dist = math.hypot(dx, dy) or 1.0
        speed = min(3.0, dist)
        d.velocity = [dx / dist * speed, dy / dist * speed]

        d.position = [max(0, min(SIZE, d.position[0] + d.velocity[0])),
                      max(0, min(SIZE, d.position[1] + d.velocity[1]))]
        d.battery -= 0.08

        # A cell counts as searched when the drone believes it has arrived.
        # Belief, not truth - so bad localization means cells get "searched"
        # that were never actually visited.
        if d.search_target and math.dist((bx, by), target) < CELL / 2:
            self.unsearched.discard(d.search_target)
            self.claimed.pop(d.search_target, None)
            d.search_target = None

    def perceive(self, d):
        """Perception via adapter. Mock today, real YOLO tomorrow."""
        hit = self.perception.scan(d, self.survivors)
        if hit is None:
            return
        self.survivors[hit["survivor_id"]]["found"] = True
        BUS.publish("SURVIVOR_DETECTED", {
            "drone_id": d.drone_id,
            "survivor_id": hit["survivor_id"],
            "location": hit["location"],
            "confidence": hit["confidence"],
            "frame": hit["frame"],
            "boxes": hit["boxes"],
        })
    def coverage(self):
        return 100.0 * (self.total_cells - len(self.unsearched)) / self.total_cells

    # ------------------------------------------------------------------
    def step(self, tick, kill_at=None, kill_id=None):
        BUS.tick = tick

        if kill_at and tick == kill_at:
            if kill_id is None:
                busy = [d for d in self.drones
                        if d.alive and d.assigned_task and d.state == "ENROUTE"]
                if busy:
                    kill_id = busy[0].drone_id
            if kill_id is not None:
                released = self.fsm.kill(kill_id)
                self.release_claims(kill_id)
                print(f"  [t{tick}] drone {kill_id} lost, released {released}")
                if released:
                    self.net.issue_cfp(self.tasks[released])

        for d in self.drones:
            if not d.alive:
                continue
            self.move(d)
            self.perceive(d)
            self.fsm.check_battery(d)

        self.bridge.update()

        alive = [d for d in self.drones if d.alive]
        self.net.collect_bids(alive)
        for task_id, winner, cost in self.net.resolve():
            w = next(d for d in self.drones if d.drone_id == winner)
            w.assigned_task = task_id
            self.tasks[task_id]["status"] = "ASSIGNED"
            self.fsm.transition(w, "ENROUTE", "won auction")
            print(f"  [t{tick}] {task_id} -> drone {winner} (cost {cost:.0f})")

        for d in self.drones:
            if d.state == "ENROUTE" and d.assigned_task:
                if math.dist(d.position, self.tasks[d.assigned_task]["location"]) < RESCUE_RADIUS:
                    sid = int(d.assigned_task[1:])
                    self.survivors[sid]["rescued"] = True
                    self.tasks[d.assigned_task]["status"] = "DONE"
                    BUS.publish("TASK_COMPLETED", {"task_id": d.assigned_task})
                    print(f"  [t{tick}] {d.assigned_task} rescued by drone {d.drone_id}")
                    d.assigned_task = None
                    self.fsm.transition(d, "SEARCHING", "rescue complete")

        if all(s["rescued"] for s in self.survivors):
            self.complete = True

        return kill_id

    def run(self, ticks=400, kill_at=None, kill_id=None):
        BUS.publish("MISSION_STARTED", {})
        for tick in range(ticks):
            kill_id = self.step(tick, kill_at, kill_id)
            if kill_at and tick == kill_at:
                kill_at = None
            if self.complete:
                BUS.publish("MISSION_COMPLETE", {"tick": tick})
                print(f"\n  MISSION COMPLETE at tick {tick}")
                break
        return self.results()

    def results(self):
        return {
            "ticks": BUS.tick,
            "coverage": round(self.coverage(), 1),
            "rescued": sum(s["rescued"] for s in self.survivors),
            "detected": sum(s["found"] for s in self.survivors),
            "total": len(self.survivors),
            "mean_error": round(self.bridge.mean_error(), 2),
            "auctions": BUS.count("TASK_AWARDED"),
            "bids": BUS.count("BID_PLACED"),
            "lost": BUS.count("DRONE_DIED"),
        }

    def snapshot(self):
        """Complete system state as JSON for the dashboard. Read-only."""
        return {
            "tick": BUS.tick,
            "complete": self.complete,
            "world": {"size": SIZE, "anchors": ANCHORS, "cell": CELL},
            "ranging_on": self.bridge.localizers[self.drones[0].drone_id].ranging_on,
            "searched_cells": [self.cell_centre(c)
                               for c in ({(x, y)
                                          for x in range(int(SIZE // CELL))
                                          for y in range(int(SIZE // CELL))}
                                         - self.unsearched)],
            "drones": [{
                "id": d.drone_id,
                "true_pos": [round(d.position[0], 1), round(d.position[1], 1)],
                "belief_pos": [round(d.belief_pos[0], 1), round(d.belief_pos[1], 1)],
                "error": round(self.bridge.error(d), 2),
                "uncertainty": round(d.uncertainty, 2),
                "battery": round(d.battery, 1),
                "state": d.state,
                "alive": d.alive,
                "assigned_task": d.assigned_task,
                "search_target": self.cell_centre(d.search_target) if d.search_target else None,
            } for d in self.drones],
            "survivors": [{
                "id": s["id"],
                "pos": [round(s["pos"][0], 1), round(s["pos"][1], 1)],
                "found": s["found"],
                "rescued": s["rescued"],
            } for s in self.survivors],
            "tasks": list(self.tasks.values()),
            "open_auctions": [{
                "task_id": tid,
                "age": c["age"],
                "bids": [{"drone_id": k, "cost": round(v, 1)}
                         for k, v in sorted(c["bids"].items(), key=lambda kv: kv[1])
                         if v != float("inf")],
            } for tid, c in self.net.open_calls.items()],
            "metrics": self.results(),
            "events": BUS.recent(25),
        }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kill-at", type=int, default=None)
    ap.add_argument("--kill-id", type=int, default=None)
    ap.add_argument("--no-ranging", action="store_true")
    ap.add_argument("--drones", type=int, default=6)
    ap.add_argument("--ticks", type=int, default=400)
    a = ap.parse_args()

    m = Mission(n_drones=a.drones, ranging_on=not a.no_ranging)
    r = m.run(ticks=a.ticks, kill_at=a.kill_at, kill_id=a.kill_id)
    print("\n  " + "-" * 40)
    for k, v in r.items():
        print(f"  {k:12} {v}")