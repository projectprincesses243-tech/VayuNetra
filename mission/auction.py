"""
Contract Net Protocol. Decentralized task allocation.

There is no allocator in this file. Each drone computes its own bid, and
every drone independently arrives at the same winner.
"""

import math
from core.bus import BUS


class ContractNet:
    def __init__(self, settle_ticks=4):
        self.open_calls = {}
        self.settle_ticks = settle_ticks

    def compute_bid(self, drone, task):
        """
        Run by each drone ON ITSELF. Lower cost wins.

        Uses belief_pos, not position - a real drone has no access to ground
        truth. This is what keeps the GPS-denied claim honest: when
        localization is poor, bids are poor, exactly as in reality.
        """
        if not getattr(drone, "alive", True) or drone.state == "DEAD":
            return float("inf")
        if drone.battery < 20:
            return float("inf")

        bx, by = drone.belief_pos
        tx, ty = task["location"]
        distance = math.hypot(bx - tx, by - ty)

        battery_penalty = (100.0 - drone.battery) * 0.5
        busy_penalty = 40.0 if drone.state in ("ENROUTE", "RESCUING") else 0.0

        return distance + battery_penalty + busy_penalty

    def issue_cfp(self, task):
        """A drone announces it needs help with a task."""
        self.open_calls[task["id"]] = {"task": task, "bids": {}, "age": 0}
        BUS.publish("CFP_ISSUED", {"task_id": task["id"],
                                   "location": task["location"]})

    def collect_bids(self, drones):
        """Each tick, drones that haven't bid yet compute and broadcast a bid."""
        for call in self.open_calls.values():
            for drone in drones:
                if drone.drone_id in call["bids"]:
                    continue
                cost = self.compute_bid(drone, call["task"])
                call["bids"][drone.drone_id] = cost
                if cost < float("inf"):
                    BUS.publish("BID_PLACED", {
                        "task_id": call["task"]["id"],
                        "drone_id": drone.drone_id,
                        "cost": round(cost, 1),
                    })

    def resolve(self):
        """
        Called each tick. Awards any call that has settled.

        The tie-break on (cost, drone_id) is the correctness guarantee: every
        drone computing this independently reaches the same answer, so no
        final coordinating step is needed.
        """
        awarded = []
        for task_id, call in list(self.open_calls.items()):
            call["age"] += 1
            if call["age"] < self.settle_ticks:
                continue

            valid = {d: c for d, c in call["bids"].items() if c < float("inf")}
            if valid:
                winner = min(valid.items(), key=lambda kv: (kv[1], kv[0]))[0]
                awarded.append((task_id, winner, valid[winner]))
                BUS.publish("TASK_AWARDED", {
                    "task_id": task_id,
                    "winner": winner,
                    "cost": round(valid[winner], 1),
                    "bidders": len(valid),
                })
            del self.open_calls[task_id]
        return awarded