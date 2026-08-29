import cv2
from pathlib import Path
from ultralytics import YOLO

# Load trained person detector
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

for category in categories:

    rgb_folder = dataset_path / category
    thermal_folder = thermal_path / category

    images = (
        list(rgb_folder.glob("*.jpg")) +
        list(rgb_folder.glob("*.jpeg")) +
        list(rgb_folder.glob("*.png"))
    )

    print(f"\n===== {category} =====")
    print(f"Images: {len(images)}")

    for rgb_path in images:

        thermal_image_path = thermal_folder / rgb_path.name

        rgb = cv2.imread(str(rgb_path))
        thermal = cv2.imread(str(thermal_image_path))

        if rgb is None or thermal is None:
            continue

        # Detect people
        results = model(rgb, verbose=False)

        person_found = False

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])

                # Class 0 = person
                if class_id == 0:

                    person_found = True

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Keep coordinates inside image
                    x1 = max(0, x1)
                    y1 = max(0, y1)
                    x2 = min(thermal.shape[1], x2)
                    y2 = min(thermal.shape[0], y2)

                    # Crop person's region
                    crop = thermal[y1:y2, x1:x2]

                    if crop.size == 0:
                        continue

                    # Convert to grayscale
                    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

                    # Threshold bright regions
                    _, binary = cv2.threshold(
                        gray,
                        180,
                        255,
                        cv2.THRESH_BINARY
                    )

                    # Find blobs
                    num_labels, labels, stats, centroids = (
                        cv2.connectedComponentsWithStats(
                            binary,
                            connectivity=8
                        )
                    )

                    crop_area = crop.shape[0] * crop.shape[1]

                    largest_blob = 0

                    for i in range(1, num_labels):

                        area = stats[i, cv2.CC_STAT_AREA]

                        if area > largest_blob:
                            largest_blob = area

                    # Calculate blob confidence
                    if crop_area > 0:
                        blob_conf = largest_blob / crop_area
                    else:
                        blob_conf = 0

                    blob_conf = min(blob_conf, 1.0)

                    if blob_conf > 0.25:
                        status = "PASS"
                    else:
                        status = "FAIL"

                    print(
                        f"{rgb_path.name} → "
                        f"blob_conf = {blob_conf:.3f} → "
                        f"{status}"
                    )

                    break

            if person_found:
                break

        if not person_found:
            print(
                f"{rgb_path.name} → "
                f"No person → blob_conf = 0.000 → FAIL"
            )

print("\nAll blob detection completed!")