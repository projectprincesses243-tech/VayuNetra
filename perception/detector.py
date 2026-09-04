"""
VayuNetra perception - the real detector.

Runs three independent checks on one image and requires two to agree
before reporting a survivor.

  1. RGB   - trained YOLOv8 model looking for a person
  2. Heat  - a thermal-style view built from the same image
  3. Blob  - a shape and size check

The weights are 0.50 / 0.30 / 0.20 deliberately. Equal weights let a
near-zero blob score veto a confident camera detection - in the offline
dataset that rejected 646 of 866 valid detections.
"""

from pathlib import Path

import cv2
import numpy as np

# ---------------------------------------------------------------- weights
RGB_WEIGHT     = 0.50
THERMAL_WEIGHT = 0.30
BLOB_WEIGHT    = 0.20

RGB_THRESHOLD     = 0.35
THERMAL_THRESHOLD = 0.30
BLOB_THRESHOLD    = 0.25

SCORE_THRESHOLD   = 0.45      # fused score must clear this
RGB_REQUIRED      = True      # the trained model must agree, not just heuristics
VOTES_REQUIRED    = 2         # and at least this many checks must agree

# confidence bands for active perception
CONFIDENT_ABOVE   = 0.75
IGNORE_BELOW      = 0.35


class SurvivorDetector:
    def __init__(self, model_path=None, verbose=True):
        self.model = None
        self.cache = {}
        self.available = False

        candidates = []
        if model_path:
            candidates.append(Path(model_path))
        candidates += [
            Path("runs/detect/train/weights/best.pt"),
            Path("runs/detect/train2/weights/best.pt"),
            Path("best.pt"),
            Path("yolov8n.pt"),
        ]

        for path in candidates:
            if not path.exists():
                continue
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(path))
                self.available = True
                if verbose:
                    print(f"[perception] model loaded: {path}")
                break
            except Exception as e:
                if verbose:
                    print(f"[perception] could not load {path}: {e}")

        if not self.available:
            try:
                from ultralytics import YOLO
                self.model = YOLO("yolov8n.pt")     # downloads ~6 MB once
                self.available = True
                if verbose:
                    print("[perception] using stock yolov8n")
            except Exception as e:
                if verbose:
                    print(f"[perception] no model available: {e}")

    # ------------------------------------------------------------ signals
    def _rgb_confidence(self, image_path):
        """Highest confidence the model gives to a person in this image."""
        if not self.available:
            return 0.0, []
        try:
            result = self.model(str(image_path), verbose=False)[0]
        except Exception:
            return 0.0, []

        best = 0.0
        boxes = []
        for box in result.boxes:
            cls = int(box.cls)
            conf = float(box.conf)
            # class 0 is "person" in COCO; a custom single-class model
            # also uses 0, so this works either way
            if cls == 0:
                boxes.append([round(v, 1) for v in box.xyxy[0].tolist()])
                best = max(best, conf)
        return best, boxes

    def _thermal_confidence(self, image):
        """
        Build a heat-style view and measure how much of the frame is 'warm'.
        This is a derived channel, not a real thermal measurement.
        """
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        grey = cv2.GaussianBlur(grey, (5, 5), 0)
        hot = (grey > 190).astype(np.uint8)
        fraction = float(hot.sum()) / float(hot.size)
        # a person is a small warm patch, not the whole frame
        if fraction <= 0.0:
            return 0.0
        score = min(1.0, fraction / 0.06)
        if fraction > 0.45:              # whole frame bright = sunlight
            score *= 0.3
        return float(score)

    def _blob_confidence(self, image):
        """Look for a person-sized, person-shaped bright region."""
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        grey = cv2.GaussianBlur(grey, (5, 5), 0)
        _, mask = cv2.threshold(grey, 180, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        frame_area = image.shape[0] * image.shape[1]
        best = 0.0
        for c in contours:
            area = cv2.contourArea(c)
            ratio = area / frame_area
            if not (0.0008 < ratio < 0.06):     # person-sized from altitude
                continue
            x, y, w, h = cv2.boundingRect(c)
            if w == 0:
                continue
            aspect = h / float(w)
            if 0.6 < aspect < 4.0:              # roughly upright shape
                best = max(best, min(1.0, ratio / 0.02))
        return float(best)

    # ------------------------------------------------------------- fusion
    def detect(self, image_path):
        """
        Run all three checks on one image.

        Returns a dict:
            alert       True if we would tell a rescue team
            band        "confident" | "uncertain" | "empty"
            confidence  fused score, 0 to 1
            votes       how many of the three checks agreed
            rgb / thermal / blob   individual scores
            boxes       bounding boxes from the model
            frame       the image path
        """
        key = str(image_path)
        if key in self.cache:
            return self.cache[key]

        empty = {"alert": False, "band": "empty", "confidence": 0.0,
                 "votes": 0, "rgb": 0.0, "thermal": 0.0, "blob": 0.0,
                 "boxes": [], "frame": key}

        path = Path(image_path)
        if not path.exists():
            self.cache[key] = empty
            return empty

        image = cv2.imread(str(path))
        if image is None:
            self.cache[key] = empty
            return empty

        rgb, boxes = self._rgb_confidence(path)
        thermal = self._thermal_confidence(image)
        blob = self._blob_confidence(image)

        votes = ((rgb > RGB_THRESHOLD)
                 + (thermal > THERMAL_THRESHOLD)
                 + (blob > BLOB_THRESHOLD))

        score = (RGB_WEIGHT * rgb
                 + THERMAL_WEIGHT * thermal
                 + BLOB_WEIGHT * blob)

        # The two heuristics can both fire on bright rubble, sky or sunlit
        # concrete. Requiring the trained model to be one of the agreeing
        # votes stops image texture alone from dispatching a rescue team.
        alert = (votes >= VOTES_REQUIRED) and (score > SCORE_THRESHOLD)
        if RGB_REQUIRED and rgb <= RGB_THRESHOLD:
            alert = False

        if alert and score >= CONFIDENT_ABOVE:
            band = "confident"
        elif score >= IGNORE_BELOW:
            band = "uncertain"       # active perception - go look again
        else:
            band = "empty"

        result = {
            "alert": bool(alert),
            "band": band,
            "confidence": round(float(score), 3),
            "votes": int(votes),
            "rgb": round(float(rgb), 3),
            "thermal": round(float(thermal), 3),
            "blob": round(float(blob), 3),
            "boxes": boxes,
            "frame": key,
        }
        self.cache[key] = result
        return result


# one shared instance
_DETECTOR = None


def get_detector():
    global _DETECTOR
    if _DETECTOR is None:
        _DETECTOR = SurvivorDetector()
    return _DETECTOR


def detect(image_path):
    """The single entry point the simulation calls."""
    return get_detector().detect(image_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python -m perception.detector <image>")
        raise SystemExit
    from pprint import pprint
    pprint(detect(sys.argv[1]))