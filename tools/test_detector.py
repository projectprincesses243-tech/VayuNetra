"""
Run the detector across a folder of images and print a comparison table.

usage:
    python tools/test_detector.py                    # tests both folders
    python tools/test_detector.py some/folder        # tests one folder
"""

import sys
from pathlib import Path

# This script lives in tools/, so add the project root to Python's search
# path before importing anything from the project.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from perception.detector import detect


def run(folder):
    folder = Path(folder)
    if not folder.exists():
        print(f"  (no folder {folder})")
        return

    files = []
    seen = set()
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        for p in folder.glob(ext):
            if p.resolve() not in seen:
                seen.add(p.resolve())
                files.append(p)

    if not files:
        print(f"  (no images in {folder})")
        return

    print(f"\n  {folder}")
    print(f"  {'file':<26} {'alert':>6} {'conf':>6} {'rgb':>6} "
          f"{'therm':>6} {'blob':>6} {'votes':>6} {'boxes':>6}")
    print("  " + "-" * 78)

    for f in sorted(files):
        r = detect(f)
        print(f"  {f.name:<26} {str(r['alert']):>6} {r['confidence']:>6.3f} "
              f"{r['rgb']:>6.3f} {r['thermal']:>6.3f} {r['blob']:>6.3f} "
              f"{r['votes']:>6} {len(r['boxes']):>6}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        run("perception/samples")
        run("Frontend/src/assets/demoperceptionimages")
    print()