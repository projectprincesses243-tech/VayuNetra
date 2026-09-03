"""
Copy dataset images into perception/frames, named by grid cell.

Every cell the drones can fly over gets an image. Cells that contain a
survivor get an image from the 'people' folder; the rest get an image
from the 'empty' folder. That way the detector sees real photographs
and must genuinely decide.

usage:
    python tools/map_frames.py <folder_with_people> <folder_without_people>
"""

import random
import shutil
import sys
from pathlib import Path

MAP_SIZE = 500.0
CELL = 50.0
SEED = 42

# same survivor positions the simulation generates with seed 42
random.seed(SEED)
SURVIVORS = [(random.uniform(50, 450), random.uniform(50, 450))
             for _ in range(5)]


def images_in(folder):
    folder = Path(folder)
    out = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"):
        out += list(folder.rglob(ext))
    return out


def main(people_dir, empty_dir):
    people = images_in(people_dir)
    empty = images_in(empty_dir)

    if not people:
        print(f"no images found in {people_dir}")
        return
    if not empty:
        print(f"no images found in {empty_dir}, reusing people images")
        empty = people

    out = Path("perception/frames")
    out.mkdir(parents=True, exist_ok=True)

    survivor_cells = {(int(x // CELL), int(y // CELL)) for x, y in SURVIVORS}
    print(f"survivor cells: {sorted(survivor_cells)}")

    n = int(MAP_SIZE // CELL)
    rng = random.Random(SEED)
    written = 0

    for cx in range(n):
        for cy in range(n):
            if (cx, cy) in survivor_cells:
                src = rng.choice(people)
            else:
                src = rng.choice(empty)
            dst = out / f"cell_{cx:02d}_{cy:02d}.jpg"
            shutil.copy(src, dst)
            written += 1

    print(f"wrote {written} frames to {out}")
    print(f"{len(survivor_cells)} of them contain a person")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit
    main(sys.argv[1], sys.argv[2])