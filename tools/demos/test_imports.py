import sys
sys.path.insert(0, ".")

print("Checking imports...\n")

try:
    from swarm.drone import Drone
    d = Drone(drone_id=1, position=(100, 200))
    print(f"  [ok]   Eashanvi's Drone      -> position {d.position}, battery {d.battery}")
except Exception as e:
    print(f"  [FAIL] Eashanvi's Drone      -> {type(e).__name__}: {e}")

try:
    from localize.localizer import Localizer
    loc = Localizer()
    print(f"  [ok]   Vaishnavi's Localizer -> ranging_on={loc.ranging_on}, alpha={loc.alpha}")
except Exception as e:
    print(f"  [FAIL] Vaishnavi's Localizer -> {type(e).__name__}: {e}")

try:
    from world.environment import Environment
    print("  [ok]   Environment")
except Exception as e:
    print(f"  [FAIL] Environment           -> {type(e).__name__}: {e}")

try:
    from planning.astar import *
    print("  [ok]   A* planner")
except Exception as e:
    print(f"  [FAIL] A* planner            -> {type(e).__name__}: {e}")