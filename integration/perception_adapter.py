"""
Connects the simulation to the real detector.

Falls back to a proximity model automatically if the detector or the
image frames are unavailable, so the simulation always runs.
"""

import math
import random
from pathlib import Path


class PerceptionAdapter:
    def __init__(self, use_real=None, frames_dir="perception/frames",
                 detect_radius=40.0, cell_size=50.0, seed=None):
        self.detect_radius = detect_radius
        self.cell_size = cell_size
        self.frames_dir = Path(frames_dir)
        self.rng = random.Random(seed)
        self.detector = None
        self.use_real = False
        self.stats = {"frames_examined": 0, "alerts": 0,
                      "uncertain": 0, "rejected": 0}

        # auto-detect: use the real detector if it loads AND frames exist
        if use_real is None:
            use_real = self.frames_dir.exists() and \
                       any(self.frames_dir.glob("*.jpg"))

        if use_real:
            try:
                from perception.detector import detect
                self.detector = detect
                self.use_real = True
                print("[perception] real detector active")
            except Exception as e:
                print(f"[perception] real detector unavailable, using mock: {e}")

    # ------------------------------------------------------------------
    def cell_for(self, position):
        return (int(position[0] // self.cell_size),
                int(position[1] // self.cell_size))

    def frame_path(self, cell):
        return self.frames_dir / f"cell_{cell[0]:02d}_{cell[1]:02d}.jpg"

    # ------------------------------------------------------------------
    def scan(self, drone, survivors):
        """
        Look at whatever is beneath this drone.

        Returns None, or a detection dict with survivor_id, location,
        confidence, band, frame and boxes.

        Uses drone.position (truth) to decide what is physically under the
        camera. Reports drone.belief_pos as the location, because that is
        all a real system could report.
        """
        if self.use_real:
            return self._scan_real(drone, survivors)
        return self._scan_mock(drone, survivors)

    def _scan_real(self, drone, survivors):
        cell = self.cell_for(drone.position)
        path = self.frame_path(cell)
        if not path.exists():
            return None

        self.stats["frames_examined"] += 1
        result = self.detector(path)

        if result["band"] == "uncertain":
            self.stats["uncertain"] += 1
        if not result["alert"]:
            if result["votes"] >= 1:
                self.stats["rejected"] += 1
            return None

        near = self._nearest_survivor(drone, survivors)
        if near is None:
            self.stats["rejected"] += 1     # model fired with nobody there
            return None

        self.stats["alerts"] += 1
        return {
            "survivor_id": near["id"],
            "location": list(near["pos"]),
            "confidence": result["confidence"],
            "band": result["band"],
            "votes": result["votes"],
            "rgb": result["rgb"],
            "thermal": result["thermal"],
            "blob": result["blob"],
            "frame": result["frame"],
            "boxes": result["boxes"],
        }

    def _scan_mock(self, drone, survivors):
        near = self._nearest_survivor(drone, survivors)
        if near is None:
            return None
        self.stats["alerts"] += 1
        return {
            "survivor_id": near["id"],
            "location": list(near["pos"]),
            "confidence": round(self.rng.uniform(0.72, 0.95), 2),
            "band": "confident",
            "votes": 2,
            "rgb": 0.0, "thermal": 0.0, "blob": 0.0,
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