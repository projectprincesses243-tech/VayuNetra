from pathlib import Path
import random
import shutil

# Original dataset
source = Path("Perception/dataset")

# YOLO dataset
destination = Path("Perception/yolo_dataset")

categories = [
    "collapsed_building",
    "Fire",
    "Flood",
    "Landslide",
    "Normal",
    "traffic_incident"
]

random.seed(42)

for category in categories:

    folder = source / category

    images = []
    images += list(folder.glob("*.jpg"))
    images += list(folder.glob("*.jpeg"))
    images += list(folder.glob("*.png"))

    random.shuffle(images)

    split_index = int(len(images) * 0.8)

    train_images = images[:split_index]
    val_images = images[split_index:]

    print(f"\n{category}")
    print(f"Train: {len(train_images)}")
    print(f"Val: {len(val_images)}")

    for image in train_images:

        label = image.with_suffix(".txt")

        shutil.copy2(
            image,
            destination / "images" / "train" / image.name
        )

        if label.exists():
            shutil.copy2(
                label,
                destination / "labels" / "train" / label.name
            )

    for image in val_images:

        label = image.with_suffix(".txt")

        shutil.copy2(
            image,
            destination / "images" / "val" / image.name
        )

        if label.exists():
            shutil.copy2(
                label,
                destination / "labels" / "val" / label.name
            )

print("\nDataset split completed!")