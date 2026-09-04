import sys
sys.path.insert(0, ".")

from swarm.drone import Drone
from core.contracts import make_task
from core.bus import BUS
from mission.auction import ContractNet
from mission.fsm import MissionFSM


def make_swarm():
    drones = []
    for i, (x, y) in enumerate([(100, 100), (300, 120), (150, 400), (450, 450)]):
        d = Drone(drone_id=i, position=(x, y))
        d.belief_pos = [float(x), float(y)]
        d.alive = True
        d.state = "SEARCHING"
        d.assigned_task = None
        drones.append(d)
    drones[1].battery = 55.0        # closest, but weaker battery
    return drones


drones = make_swarm()
fsm = MissionFSM(drones)
net = ContractNet(settle_ticks=1)
task = make_task("T001", 250, 150)

print("survivor at [250, 150]\n")
print("  bids:")
for d in drones:
    print(f"    drone {d.drone_id} at {d.belief_pos}  battery {d.battery:5.1f}"
          f"  ->  {net.compute_bid(d, task):8.1f}")

net.issue_cfp(task)
net.collect_bids(drones)
awarded = net.resolve()
winner_id = awarded[0][1]
print(f"\n  awarded to drone {winner_id} at cost {awarded[0][2]:.1f}")

drones[winner_id].assigned_task = "T001"
fsm.transition(drones[winner_id], "ENROUTE", "won auction")

print(f"\n  killing drone {winner_id} mid-task...")
released = fsm.kill(winner_id)
print(f"  released task: {released}")

net.issue_cfp(task)
net.collect_bids(drones)
awarded2 = net.resolve()
print(f"  re-auctioned to drone {awarded2[0][1]} at cost {awarded2[0][2]:.1f}")

print(f"\n  blocked transition test:")
fsm.transition(drones[winner_id], "SEARCHING", "should be impossible")

print(f"\n  events on bus: {len(BUS.log)}")
for e in BUS.log:
    print(f"    {e['event']}")