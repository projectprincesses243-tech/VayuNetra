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

# Process every category
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

        # Detect people using YOLO
        results = model(rgb, verbose=False)

        person_found = False

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])

                # Class 0 = person
                if class_id == 0:

                    person_found = True

                    # Person bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Make sure coordinates stay inside image
                    x1 = max(0, x1)
                    y1 = max(0, y1)
                    x2 = min(thermal.shape[1], x2)
                    y2 = min(thermal.shape[0], y2)

                    # Crop corresponding thermal region
                    thermal_crop = thermal[y1:y2, x1:x2]

                    if thermal_crop.size == 0:
                        continue

                    # Convert to grayscale
                    gray = cv2.cvtColor(
                        thermal_crop,
                        cv2.COLOR_BGR2GRAY
                    )

                    # Calculate average intensity
                    mean_intensity = gray.mean()

                    # Convert to 0–1 confidence
                    thermal_conf = mean_intensity / 255.0

                    if thermal_conf > 0.30:
                        result_status = "PASS"
                    else:
                        result_status = "FAIL"

                    print(
                        f"{rgb_path.name} → "
                        f"rgb person detected → "
                        f"thermal_conf = {thermal_conf:.3f} → "
                        f"{result_status}"
                    )

                    break

            if person_found:
                break

        if not person_found:
            print(
                f"{rgb_path.name} → "
                f"No person detected → "
                f"thermal_conf = 0.000 → FAIL"
            )

print("\nAll thermal detection completed!")