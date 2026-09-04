"""
Wraps Tejaswini's perception module for the simulation loop.

Falls back to a proximity model when the real detector is unavailable, so
the simulation always runs. Swap by passing use_real=True once her
detect() function exists.
"""

import math
import random
from pathlib import Path


class PerceptionAdapter:
    def __init__(self, use_real=False, frames_dir="perception/frames",
                 detect_radius=40.0, seed=None):
        self.detect_radius = detect_radius
        self.frames_dir = Path(frames_dir)
        self.rng = random.Random(seed)
        self.cache = {}            # cell -> result, so YOLO never runs twice
        self.detector = None
        self.use_real = False

        if use_real:
            try:
                from perception.fusion import detect
                self.detector = detect
                self.use_real = True
                print("[perception] real YOLO detector loaded")
            except Exception as e:
                print(f"[perception] real detector unavailable, using mock: {e}")

    # ------------------------------------------------------------------
    def cell_for(self, position, cell_size=50.0):
        return (int(position[0] // cell_size), int(position[1] // cell_size))

    def frame_path(self, cell):
        return self.frames_dir / f"cell_{cell[0]:02d}_{cell[1]:02d}.jpg"

    # ------------------------------------------------------------------
    def scan(self, drone, survivors):
        """
        Look at whatever is beneath this drone.

        Returns None, or a detection dict:
            {"survivor_id", "location", "confidence", "frame", "boxes"}

        Uses drone.position (ground truth) for what is physically below the
        drone - a camera sees what it is actually over, not what the drone
        believes. The reported LOCATION is the drone's belief, because that
        is all a real system could report.
        """
        cell = self.cell_for(drone.position)

        if self.use_real:
            result = self._scan_real(cell)
            if not result or not result.get("alert"):
                return None
            near = self._nearest_survivor(drone, survivors)
            if near is None:
                return None
            return {
                "survivor_id": near["id"],
                "location": list(near["pos"]),
                "confidence": round(result.get("confidence", 0.0), 2),
                "frame": result.get("frame"),
                "boxes": result.get("boxes", []),
            }

        return self._scan_mock(drone, survivors)

    def _scan_real(self, cell):
        if cell in self.cache:
            return self.cache[cell]
        path = self.frame_path(cell)
        if not path.exists():
            self.cache[cell] = None
            return None
        try:
            result = self.detector(str(path))
        except Exception as e:
            print(f"[perception] detect() failed on {path.name}: {e}")
            result = None
        self.cache[cell] = result
        return result

    def _scan_mock(self, drone, survivors):
        near = self._nearest_survivor(drone, survivors)
        if near is None:
            return None
        return {
            "survivor_id": near["id"],
            "location": list(near["pos"]),
            "confidence": round(self.rng.uniform(0.72, 0.95), 2),
            "frame": None,
            "boxes": [],
        }

    def _nearest_survivor(self, drone, survivors):
        for s in survivors:
            if s["found"]:
                continue
            if math.dist(drone.position, s["pos"]) < self.detect_radius:
                return s
        return None