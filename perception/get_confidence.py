from ultralytics import YOLO
from pathlib import Path

# Load our trained model
model = YOLO("runs/detect/train/weights/best.pt")

# Test images
dataset = Path("Perception/dataset")

categories = [
    "collapsed_building",
    "Fire",
    "Flood",
    "Landslide",
    "Normal",
    "traffic_incident"
]

for category in categories:

    folder = dataset / category

    print(f"\n===== {category} =====")

    images = (
        list(folder.glob("*.jpg")) +
        list(folder.glob("*.jpeg")) +
        list(folder.glob("*.png"))
    )

    # Check first 5 images only for now
    for image in images[:5]:

        results = model(image, verbose=False)

        person_confidences = []

        for result in results:
            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # Class 0 = person
                if class_id == 0:
                    person_confidences.append(confidence)

        if person_confidences:
            rgb_conf = max(person_confidences)
            print(f"{image.name} → rgb_conf = {rgb_conf:.3f}")
        else:
            print(f"{image.name} → No person detected")