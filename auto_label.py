from ultralytics import YOLO
from pathlib import Path

# Load pretrained YOLO model
model = YOLO("yolo11n.pt")

# Dataset folders
dataset_path = Path("Perception/dataset")

# Disaster categories
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

    folder = dataset_path / category

    print(f"\nProcessing: {category}")

    # Find images
    images = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))

    for image in images:

        # Run YOLO
        results = model(image, verbose=False)

        # Create label file
        label_file = image.with_suffix(".txt")

        with open(label_file, "w") as f:

            for result in results:

                for box in result.boxes:

                    # YOLO class ID
                    class_id = int(box.cls[0])

                    # 0 = person in COCO dataset
                    if class_id == 0:

                        x_center, y_center, width, height = box.xywhn[0]

                        f.write(
                            f"0 {x_center:.6f} {y_center:.6f} "
                            f"{width:.6f} {height:.6f}\n"
                        )

    print(f"Finished: {category}")

print("\nAll categories processed!")