import cv2
from pathlib import Path

# Original dataset
dataset_path = Path("Perception/dataset")

# Where pseudo-thermal images will be saved
output_path = Path("Perception/pseudo_thermal")

categories = [
    "collapsed_building",
    "Fire",
    "Flood",
    "Landslide",
    "Normal",
    "traffic_incident"
]

# Create output folders
for category in categories:

    input_folder = dataset_path / category
    output_folder = output_path / category

    output_folder.mkdir(parents=True, exist_ok=True)

    images = (
        list(input_folder.glob("*.jpg")) +
        list(input_folder.glob("*.jpeg")) +
        list(input_folder.glob("*.png"))
    )

    print(f"\nProcessing {category}: {len(images)} images")

    for image_path in images:

        image = cv2.imread(str(image_path))

        if image is None:
            continue

        # Convert RGB image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Create pseudo-thermal image
        thermal = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

        # Save with same filename
        output_file = output_folder / image_path.name

        cv2.imwrite(str(output_file), thermal)

print("\nAll pseudo-thermal images created!")