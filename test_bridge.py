import sys
sys.path.insert(0, ".")

from swarm.drone import Drone
from integration.adapters import LocalizationBridge

ANCHORS = [
    {"id": "A", "position": [0.0, 0.0]},
    {"id": "B", "position": [500.0, 0.0]},
    {"id": "C", "position": [250.0, 500.0]},
    {"id": "D", "position": [0.0, 500.0]},
]

def run(ranging_on, steps=200):
    drones = []
    for i in range(6):
        d = Drone(drone_id=i, position=(100.0 + i * 20, 100.0))
        d.velocity = [1.5, 0.8]
        d.alive = True
        drones.append(d)

    bridge = LocalizationBridge(drones, ANCHORS, ranging_on=ranging_on)

    for _ in range(steps):
        for d in drones:
            d.position = [d.position[0] + d.velocity[0],
                          d.position[1] + d.velocity[1]]
        bridge.update()

    return bridge.mean_error()

def sweep(bias, walk, alpha, steps=200):
    def run(ranging_on):
        drones = []
        for i in range(6):
            d = Drone(drone_id=i, position=(100.0 + i * 20, 100.0))
            d.velocity = [1.5, 0.8]
            d.alive = True
            drones.append(d)
        bridge = LocalizationBridge(drones, ANCHORS, ranging_on=ranging_on,
                                    bias_std=bias, walk_std=walk, alpha=alpha)
        for _ in range(steps):
            for d in drones:
                d.position = [d.position[0] + d.velocity[0],
                              d.position[1] + d.velocity[1]]
            bridge.update()
        return bridge.mean_error()
    return run(False), run(True)


print(f"  {'bias':>6} {'walk':>6} {'alpha':>6} {'OFF':>9} {'ON':>8} {'ratio':>8}")
print("  " + "-" * 48)

for bias, walk, alpha in [
    (0.05, 0.25, 0.35),   # where you started
    (0.15, 0.75, 0.35),   # more drift, same alpha
    (0.15, 0.75, 0.10),   # more drift + trust ranging more
    (0.20, 1.00, 0.10),
    (0.25, 1.20, 0.08),
]:
    off, on = sweep(bias, walk, alpha)
    flag = "  <-- PASS" if off > 30 and on < 3 else ""
    print(f"  {bias:6.2f} {walk:6.2f} {alpha:6.2f} {off:8.2f}m {on:7.2f}m {off/on if on else 0:7.1f}x{flag}")