"""
Build perception/frames - one image per grid cell.

Cells containing a survivor get an image where the detector CAN find a
person. All other cells get disaster imagery with no visible people.
The drone must then genuinely decide, image by image.

Survivor positions are read from the simulation itself, so the frames
always line up with the world the drones actually fly in.

usage:  python tools/map_frames.py
"""

import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MAP_SIZE = 500.0
CELL = 50.0
SEED = 42
N_DRONES = 6
N_SURVIVORS = 5

# images where the detector finds a person
SURVIVOR_IMAGES = [
    "Frontend/src/assets/demoperceptionimages/flood2.png",
    "perception/samples/people_01.jpg",
    "perception/samples/people_02.jpg",
]

# disaster imagery with no visible people
EMPTY_IMAGES = [
    "Frontend/src/assets/demoperceptionimages/buildingcollapse.png",
    "Frontend/src/assets/demoperceptionimages/earthquake.png",
    "Frontend/src/assets/demoperceptionimages/flood1.png",
    "Frontend/src/assets/demoperceptionimages/landslide.png",
]


def load(paths):
    """Read the images once, resized down so inference stays fast."""
    out = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"  missing, skipping: {p}")
            continue
        img = cv2.imread(str(path))
        if img is None:
            print(f"  unreadable, skipping: {p}")
            continue
        h, w = img.shape[:2]
        if w > 960:
            scale = 960.0 / w
            img = cv2.resize(img, (960, int(h * scale)))
        out.append((path.name, img))
    return out


def survivor_cells():
    """Ask the simulation where the survivors actually are."""
    from sim import Mission
    m = Mission(n_drones=N_DRONES, n_survivors=N_SURVIVORS, seed=SEED)
    cells = set()
    for s in m.survivors:
        cells.add((int(s["pos"][0] // CELL), int(s["pos"][1] // CELL)))
    return cells, [s["pos"] for s in m.survivors]


def main():
    people = load(SURVIVOR_IMAGES)
    empty = load(EMPTY_IMAGES)

    if not people:
        print("no survivor images available - stopping")
        return
    if not empty:
        print("no empty images available, reusing survivor images")
        empty = people

    cells, positions = survivor_cells()
    print(f"\n  survivors at: {[(round(x), round(y)) for x, y in positions]}")
    print(f"  survivor cells: {sorted(cells)}\n")

    out = Path("perception/frames")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.jpg"):
        old.unlink()

    n = int(MAP_SIZE // CELL)
    written = 0
    for cx in range(n):
        for cy in range(n):
            if (cx, cy) in cells:
                name, img = people[written % len(people)]
            else:
                name, img = empty[written % len(empty)]
            cv2.imwrite(str(out / f"cell_{cx:02d}_{cy:02d}.jpg"), img)
            written += 1

    print(f"  wrote {written} frames")
    print(f"  {len(cells)} contain a person, {written - len(cells)} do not")


if __name__ == "__main__":
    main()