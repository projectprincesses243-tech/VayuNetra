"""VayuNetra integrated simulation. Everything running in one loop."""

import sys, math, random, argparse
sys.path.insert(0, ".")

from swarm.drone import Drone
from core.bus import BUS
from core.contracts import make_task
from mission.fsm import MissionFSM
from mission.auction import ContractNet
from integration.adapters import LocalizationBridge

ANCHORS = [[0.0, 0.0], [500.0, 0.0], [250.0, 500.0], [0.0, 500.0]]
SIZE = 500.0


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
            self.drones.append(d)

        self.survivors = [{"id": i,
                           "pos": [random.uniform(50, 450), random.uniform(50, 450)],
                           "found": False, "rescued": False}
                          for i in range(n_survivors)]

        self.bridge = LocalizationBridge(self.drones, ANCHORS, ranging_on=ranging_on)
        self.fsm = MissionFSM(self.drones)
        self.net = ContractNet(settle_ticks=4)
        self.tasks = {}
        self.visited = set()
        self.complete = False

        BUS.subscribe("SURVIVOR_DETECTED", self.on_detection)

    def on_detection(self, p):
        tid = f"T{p['survivor_id']:03d}"
        if tid in self.tasks:
            return
        task = make_task(tid, p["location"][0], p["location"][1], p["confidence"])
        self.tasks[tid] = task
        self.net.issue_cfp(task)

    def move(self, d):
        """Fly toward target if assigned, else wander."""
        if d.assigned_task and d.assigned_task in self.tasks:
            tx, ty = self.tasks[d.assigned_task]["location"]
        else:
            tx = ty = None

        if tx is None:
            if random.random() < 0.1 or d.velocity == [0.0, 0.0]:
                a = random.uniform(0, 6.283)
                d.velocity = [math.cos(a) * 3.0, math.sin(a) * 3.0]
        else:
            # navigate using BELIEF, not truth - this is the honest bit
            bx, by = d.belief_pos
            dx, dy = tx - bx, ty - by
            dist = math.hypot(dx, dy) or 1.0
            speed = min(3.0, dist)
            d.velocity = [dx / dist * speed, dy / dist * speed]

        d.position = [max(0, min(SIZE, d.position[0] + d.velocity[0])),
                      max(0, min(SIZE, d.position[1] + d.velocity[1]))]
        d.battery -= 0.08
        self.visited.add((int(d.position[0]) // 25, int(d.position[1]) // 25))

    def perceive(self, d):
        """MOCK perception. Replaced by Tejaswini's YOLO at the hackathon."""
        for s in self.survivors:
            if s["found"]:
                continue
            if math.dist(d.position, s["pos"]) < 40:
                s["found"] = True
                BUS.publish("SURVIVOR_DETECTED", {
                    "drone_id": d.drone_id, "survivor_id": s["id"],
                    "location": list(s["pos"]),
                    "confidence": round(random.uniform(0.72, 0.95), 2)})

    def coverage(self):
        return 100.0 * len(self.visited) / ((SIZE // 25) ** 2)

    def step(self, tick, kill_at=None, kill_id=None):
        """One simulation tick. Returns the kill_id used, so callers can track it."""
        BUS.tick = tick

        # ----- scheduled drone failure -----
        if kill_at and tick == kill_at:
            if kill_id is None:
                busy = [d for d in self.drones
                        if d.alive and d.assigned_task and d.state == "ENROUTE"]
                if busy:
                    kill_id = busy[0].drone_id
            if kill_id is not None:
                released = self.fsm.kill(kill_id)
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
                if math.dist(d.position, self.tasks[d.assigned_task]["location"]) < 15:
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
            "world": {"size": SIZE, "anchors": ANCHORS},
            "ranging_on": self.bridge.localizers[self.drones[0].drone_id].ranging_on,
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
    a = ap.parse_args()

    m = Mission(ranging_on=not a.no_ranging)
    r = m.run(kill_at=a.kill_at, kill_id=a.kill_id)
    print("\n  " + "-" * 40)
    for k, v in r.items():
        print(f"  {k:12} {v}")