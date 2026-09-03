import cv2
import json
from pathlib import Path
from ultralytics import YOLO

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

# Thresholds from the project workflow
RGB_THRESHOLD = 0.35
THERMAL_THRESHOLD = 0.30
BLOB_THRESHOLD = 0.25

# Equal weights because no specific weights were provided
RGB_WEIGHT = 1 / 3
THERMAL_WEIGHT = 1 / 3
BLOB_WEIGHT = 1 / 3

all_results=[]

for category in categories:

    rgb_folder = dataset_path / category
    thermal_folder = thermal_path / category

    images = (
        list(rgb_folder.glob("*.jpg")) +
        list(rgb_folder.glob("*.jpeg")) +
        list(rgb_folder.glob("*.png"))
    )

    print(f"\n===== {category} =====")

    for rgb_path in images:

        thermal_image_path = thermal_folder / rgb_path.name

        rgb = cv2.imread(str(rgb_path))
        thermal = cv2.imread(str(thermal_image_path))

        if rgb is None or thermal is None:
            continue

        results = model(rgb, verbose=False)

        rgb_conf = 0.0
        thermal_conf = 0.0
        blob_conf = 0.0

        person_found = False

        # ---------------- RGB / YOLO ----------------

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])

                if class_id == 0:

                    person_found = True

                    rgb_conf = float(box.conf[0])

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

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

        # Weighted fusion score
        fusion_score = (
            RGB_WEIGHT * rgb_conf +
            THERMAL_WEIGHT * thermal_conf +
            BLOB_WEIGHT * blob_conf
        )

        # Final decision
        if passed_methods >= 2:

            if fusion_score > 0.60:
                final_decision = "ALERT"
            else:
                final_decision = "NO ALERT"

        else:
            final_decision = "NO ALERT"

        print(
            f"{rgb_path.name} | "
            f"RGB={rgb_conf:.3f} | "
            f"Thermal={thermal_conf:.3f} | "
            f"Blob={blob_conf:.3f} | "
            f"Passed={passed_methods}/3 | "
            f"Score={fusion_score:.3f} | "
            f"{final_decision}"
        )
        all_results.append({
            "image": rgb_path.name,
            "category": category,
            "rgb_conf": round(rgb_conf, 3),
            "thermal_conf": round(thermal_conf, 3),
            "blob_conf": round(blob_conf, 3),
            "methods_passed":int(passed_methods),
            "fusion_score": round(fusion_score, 3),
            "decision": final_decision
        })

print("\n===== FUSION COMPLETED =====")

with open("perception_results.json", "w") as file:
    json.dump(all_results, file, indent=4)

print("Results saved to perception_results.json")