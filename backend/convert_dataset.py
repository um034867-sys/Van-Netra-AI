import os
import csv
import shutil
from PIL import Image

# Your dataset
DATASET_ROOT = r"E:\tiger dataset\archive\tigers"

# Output YOLO dataset
OUTPUT = r"E:\tiger dataset\yolo_dataset"

# Dataset splits
SPLITS = ["train", "val", "test"]

# YOLO class
CLASS_ID = 0  # tiger


def convert_split(split):
    source_dir = os.path.join(DATASET_ROOT, split)
    csv_file = os.path.join(source_dir, f"{split}_annotations.csv")

    image_output = os.path.join(OUTPUT, "images", split)
    label_output = os.path.join(OUTPUT, "labels", split)

    os.makedirs(image_output, exist_ok=True)
    os.makedirs(label_output, exist_ok=True)

    print(f"\nProcessing {split}...")

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        count = 0

        for row in reader:
            image_name = row["image_name"]

            x1 = float(row["x1"])
            y1 = float(row["y1"])
            x2 = float(row["x2"])
            y2 = float(row["y2"])

            image_path = os.path.join(source_dir, image_name)

            if not os.path.exists(image_path):
                print(f"WARNING: Missing image: {image_path}")
                continue

            # Get image dimensions
            with Image.open(image_path) as img:
                width, height = img.size

            # YOLO format
            x_center = ((x1 + x2) / 2) / width
            y_center = ((y1 + y2) / 2) / height

            box_width = (x2 - x1) / width
            box_height = (y2 - y1) / height

            # Copy image
            shutil.copy2(
                image_path,
                os.path.join(image_output, image_name)
            )

            # Create label
            label_name = os.path.splitext(image_name)[0] + ".txt"
            label_path = os.path.join(label_output, label_name)

            with open(label_path, "w") as label_file:
                label_file.write(
                    f"{CLASS_ID} "
                    f"{x_center:.6f} "
                    f"{y_center:.6f} "
                    f"{box_width:.6f} "
                    f"{box_height:.6f}\n"
                )

            count += 1

    print(f"{split}: converted {count} images")


for split in SPLITS:
    convert_split(split)

print("\nDataset conversion complete!")
print(f"YOLO dataset created at:")
print(OUTPUT)
