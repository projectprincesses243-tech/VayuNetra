import sys, inspect
sys.path.insert(0, ".")
import numpy as np

from localize.ranging import get_ranges
from localize.trilateration import trilaterate

print("SIGNATURES")
print("  get_ranges ", inspect.signature(get_ranges))
print("  trilaterate", inspect.signature(trilaterate))
print()

drone = {"id": 0, "position": [150.0, 150.0], "velocity": [1.5, 0.8],
         "belief_pos": [150.0, 150.0], "uncertainty": 0.0}

anchors_dict = [{"id": "A", "position": [0.0, 0.0]},
                {"id": "B", "position": [500.0, 0.0]},
                {"id": "C", "position": [250.0, 500.0]},
                {"id": "D", "position": [0.0, 500.0]}]

anchors_array = np.array([[0.0, 0.0], [500.0, 0.0], [250.0, 500.0], [0.0, 500.0]])

for label, anchors in (("DICTS", anchors_dict), ("ARRAY", anchors_array)):
    print(f"--- anchors as {label} ---")
    try:
        ranges = get_ranges(drone, [drone], anchors)
        print("  get_ranges ->", np.round(np.asarray(ranges, dtype=float), 2))
    except Exception as e:
        print(f"  get_ranges FAILED -> {type(e).__name__}: {e}")
        print()
        continue

    try:
        fix = trilaterate(anchors, ranges, [150.0, 150.0])
        print("  trilaterate ->", np.round(fix, 2), " (true position is [150. 150.])")
    except Exception as e:
        print(f"  trilaterate FAILED -> {type(e).__name__}: {e}")
    print()