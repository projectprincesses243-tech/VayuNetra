import cv2
import json
from pathlib import Path
from ultralytics import YOLO


# ---------------- CONFIGURATION ----------------

# Load trained YOLO person detector
model = YOLO("runs/detect/train/weights/best.pt")

dataset_path = Path("Perception/dataset")
thermal_path = Path("Perception/pseudo_thermal")

categories = [
    "collapsed_building",
    "Fire",
    "Flood",
    "Landslide",
    "Normal",
    "traffic_incident"
]

# Detection thresholds
RGB_THRESHOLD = 0.35
THERMAL_THRESHOLD = 0.30
BLOB_THRESHOLD = 0.25

# Updated fusion weights
RGB_WEIGHT = 0.50
THERMAL_WEIGHT = 0.30
BLOB_WEIGHT = 0.20

FUSION_THRESHOLD = 0.60


# ---------------- SINGLE IMAGE DETECTION ----------------

def detect(image_path):
    """
    Detect a possible survivor in one image.

    Returns:
        {
            "alert": bool,
            "confidence": float,
            "boxes": [...],
            "frame": image_path
        }
    """

    image_path = Path(image_path)

    # Find the corresponding pseudo-thermal image
    # Find the corresponding pseudo-thermal image
    relative_path = image_path.relative_to(dataset_path)
    thermal_image_path = thermal_path / relative_path

    rgb = cv2.imread(str(image_path))
    thermal = cv2.imread(str(thermal_image_path))

    if rgb is None:
        raise FileNotFoundError(
            f"RGB image not found: {image_path}"
        )

    if thermal is None:
        raise FileNotFoundError(
            f"Pseudo-thermal image not found: {thermal_image_path}"
        )

    results = model(rgb, verbose=False)

    rgb_conf = 0.0
    thermal_conf = 0.0
    blob_conf = 0.0

    person_found = False
    boxes = []

    # ---------------- RGB / YOLO ----------------

    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])

            if class_id == 0:

                person_found = True

                rgb_conf = float(box.conf[0])

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                boxes.append({
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "confidence": round(rgb_conf, 3)
                })

                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(thermal.shape[1], x2)
                y2 = min(thermal.shape[0], y2)

                crop = thermal[y1:y2, x1:x2]

                if crop.size > 0:

                    # ---------------- THERMAL ----------------

                    gray = cv2.cvtColor(
                        crop,
                        cv2.COLOR_BGR2GRAY
                    )

                    mean_intensity = gray.mean()

                    thermal_conf = mean_intensity / 255.0

                    # ---------------- BLOB ----------------

                    _, binary = cv2.threshold(
                        gray,
                        180,
                        255,
                        cv2.THRESH_BINARY
                    )

                    num_labels, labels, stats, centroids = (
                        cv2.connectedComponentsWithStats(
                            binary,
                            connectivity=8
                        )
                    )

                    crop_area = crop.shape[0] * crop.shape[1]

                    largest_blob = 0

                    for i in range(1, num_labels):

                        area = stats[
                            i,
                            cv2.CC_STAT_AREA
                        ]

                        if area > largest_blob:
                            largest_blob = area

                    if crop_area > 0:
                        blob_conf = (
                            largest_blob / crop_area
                        )

                    blob_conf = min(blob_conf, 1.0)

                break

        if person_found:
            break

    # ---------------- DECISION ----------------

    rgb_pass = rgb_conf > RGB_THRESHOLD
    thermal_pass = thermal_conf > THERMAL_THRESHOLD
    blob_pass = blob_conf > BLOB_THRESHOLD

    passed_methods = sum([
        rgb_pass,
        thermal_pass,
        blob_pass
    ])

    # Updated weighted fusion
    fusion_score = (
        RGB_WEIGHT * rgb_conf +
        THERMAL_WEIGHT * thermal_conf +
        BLOB_WEIGHT * blob_conf
    )

    if passed_methods >= 2 and fusion_score > FUSION_THRESHOLD:
        final_decision = "ALERT"
    else:
        final_decision = "NO ALERT"

    # ---------------- RETURN RESULT ----------------

    return {
        "alert": final_decision == "ALERT",
        "confidence": float(round(fusion_score, 3)),
        "boxes": boxes,
        "frame": str(image_path),

        # Detailed outputs
        "rgb_conf": round(rgb_conf, 3),
        "thermal_conf": round(thermal_conf, 3),
        "blob_conf": round(blob_conf, 3),
        "rgb_pass": rgb_pass,
        "thermal_pass": thermal_pass,
        "blob_pass": blob_pass,
        "passed_methods": passed_methods,
        "fusion_score": float(round(fusion_score, 3)),
        "decision": final_decision

}
    


# ---------------- DATASET SCAN ----------------

if __name__ == "__main__":

    all_results = []

    for category in categories:

        rgb_folder = dataset_path / category

        images = (
            list(rgb_folder.glob("*.jpg")) +
            list(rgb_folder.glob("*.jpeg")) +
            list(rgb_folder.glob("*.png"))
        )

        print(f"\n===== {category} =====")

        for rgb_path in images:

            try:
                result = detect(rgb_path)

            except FileNotFoundError:
                continue

            print(
                f"{rgb_path.name} | "
                f"Score={result['confidence']:.3f} | "
                f"{'ALERT' if result['alert'] else 'NO ALERT'}"
            )

            all_results.append({
                "image": rgb_path.name,
                "category": category,
                "fusion_score": result["confidence"],
                "decision": (
                    "ALERT"
                    if result["alert"]
                    else "NO ALERT"
                ),
                "boxes": result["boxes"]
            })

    print("\n===== FUSION COMPLETED =====")

    with open("perception_results.json", "w") as file:
        json.dump(all_results, file, indent=4)

    print("Results saved to perception_results.json")