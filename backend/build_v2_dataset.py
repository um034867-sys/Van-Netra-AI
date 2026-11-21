from pathlib import Path
import shutil
import random
import csv

# ============================================================
# VAN NETRA V2 DATASET BUILDER
# ============================================================

random.seed(42)

BASE = Path(r"D:\Users\HP\Downloads")
OUT = Path(r"D:\VanNetraDataset")

TIGER_DETECTION = BASE / "Tiger detection dataset" / "final_data" / "dataset"
TIGER_CSV = BASE / "Tiger dataset" / "tigers"
ANIMAL = BASE / "Animal dataset" / "dataset"
WILD = BASE / "WildVision47" / "animals" / "animals"
ANIMALS_DETECTION = BASE / "Animals Detection Images Dataset"

# Hard-negative classes: visually relevant to tiger detection
NEGATIVE_CLASSES = [
    "Leopard", "Lion", "Cheetah", "Jaguar", "Lynx",
    "Bear", "Brown bear", "Polar bear",
    "Deer", "Fox", "Wolf", "Boar",
    "Zebra", "Horse", "Cow", "Dog", "Cat",
]

WILD_NEGATIVE_CLASSES = [
    "leopard", "lion", "cheetah", "jaguar", "lynx",
    "bear", "deer", "wolf", "boar", "hyena",
    "zebra", "horse", "fox", "coyote", "bison",
    "bull", "antelope", "okapi", "donkey",
]

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ------------------------------------------------------------
# Clean output
# ------------------------------------------------------------

if OUT.exists():
    print(f"Removing old dataset: {OUT}")
    shutil.rmtree(OUT)

for split in ["train", "val", "test"]:
    (OUT / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUT / "labels" / split).mkdir(parents=True, exist_ok=True)

used_names = set()


def unique_name(path: Path, prefix: str):
    stem = path.stem
    suffix = path.suffix.lower()

    name = f"{prefix}_{stem}{suffix}"

    if name in used_names:
        i = 2
        while f"{prefix}_{stem}_{i}{suffix}" in used_names:
            i += 1
        name = f"{prefix}_{stem}_{i}{suffix}"

    used_names.add(name)
    return name


def copy_detection_dataset(split, limit=None):
    image_dir = TIGER_DETECTION / "images" / split
    label_dir = TIGER_DETECTION / "labels" / split

    if not image_dir.exists():
        print(f"WARNING: missing {image_dir}")
        return 0

    images = [
        p for p in image_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]

    if limit:
        images = images[:limit]

    copied = 0

    for img in images:
        label = label_dir / f"{img.stem}.txt"

        if not label.exists():
            continue

        new_name = unique_name(img, f"det_{split}")
        shutil.copy2(img, OUT / "images" / split / new_name)
        shutil.copy2(
            label,
            OUT / "labels" / split / f"{Path(new_name).stem}.txt"
        )

        copied += 1

    print(f"Tiger detection {split}: {copied}")
    return copied


# ------------------------------------------------------------
# Convert Tiger CSV annotations to YOLO
# ------------------------------------------------------------

def convert_csv_split(split):
    image_dir = TIGER_CSV / split
    csv_path = image_dir / f"{split}_annotations.csv"

    if not csv_path.exists():
        # test is named test_annotations.csv
        print(f"WARNING: no CSV found: {csv_path}")
        return 0

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Group rows by image
    grouped = {}
    for row in rows:
        grouped.setdefault(row["image_name"], []).append(row)

    copied = 0

    for image_name, annotations in grouped.items():
        img = image_dir / image_name

        if not img.exists():
            continue

        # Keep this dataset's original split
        target_split = split

        # Get image dimensions
        try:
            from PIL import Image
            with Image.open(img) as im:
                width, height = im.size
        except Exception:
            continue

        label_lines = []

        for row in annotations:
            x1 = float(row["x1"])
            y1 = float(row["y1"])
            x2 = float(row["x2"])
            y2 = float(row["y2"])

            xc = ((x1 + x2) / 2) / width
            yc = ((y1 + y2) / 2) / height
            w = (x2 - x1) / width
            h = (y2 - y1) / height

            label_lines.append(
                f"0 {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}"
            )

        new_name = unique_name(img, f"csv_{split}")

        shutil.copy2(
            img,
            OUT / "images" / target_split / new_name
        )

        with open(
            OUT / "labels" / target_split /
            f"{Path(new_name).stem}.txt",
            "w",
            encoding="utf-8"
        ) as f:
            f.write("\n".join(label_lines))

        copied += 1

    print(f"Tiger CSV {split}: {copied}")
    return copied


# ------------------------------------------------------------
# Add classification images as NEGATIVE/background images
# ------------------------------------------------------------

def add_negative_folder(
    folder,
    split,
    prefix,
    limit
):
    if not folder.exists():
        return 0

    images = [
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]

    random.shuffle(images)
    images = images[:limit]

    copied = 0

    for img in images:
        new_name = unique_name(img, prefix)

        shutil.copy2(
            img,
            OUT / "images" / split / new_name
        )

        # Empty label file = background / no object
        label_path = (
            OUT / "labels" / split /
            f"{Path(new_name).stem}.txt"
        )

        label_path.touch()

        copied += 1

    return copied


# ------------------------------------------------------------
# MAIN DATASET
# ------------------------------------------------------------

print("\n=== TIGER DETECTION DATASET ===")

# Existing YOLO dataset
copy_detection_dataset("train")
copy_detection_dataset("val")

# IMPORTANT:
# Do NOT use the 1651-image original test set for training.
# Instead, copy it into our final test set untouched.
copy_detection_dataset("test")


print("\n=== TIGER CSV DATASET ===")

convert_csv_split("train")
convert_csv_split("val")
convert_csv_split("test")


# ------------------------------------------------------------
# NEGATIVES
# ------------------------------------------------------------

print("\n=== HARD NEGATIVES ===")

# 70/15/15-ish distribution for negatives
for cls in NEGATIVE_CLASSES:
    folder = ANIMAL / cls

    if folder.exists():
        n = add_negative_folder(
            folder,
            "train",
            f"animal_{cls.lower().replace(' ', '_')}",
            100
        )

        print(f"Animal/{cls}: {n}")


# Animals Detection Dataset has train/<class>
for cls in NEGATIVE_CLASSES:
    folder = ANIMALS_DETECTION / "train" / cls

    if folder.exists():
        n = add_negative_folder(
            folder,
            "train",
            f"ad_{cls.lower().replace(' ', '_')}",
            100
        )

        print(f"Detection/{cls}: {n}")


# WildVision47
for cls in WILD_NEGATIVE_CLASSES:
    folder = WILD / cls

    if folder.exists():
        n = add_negative_folder(
            folder,
            "train",
            f"wild_{cls}",
            60
        )

        print(f"Wild/{cls}: {n}")


# ------------------------------------------------------------
# EXTRA TIGER CLASSIFICATION IMAGES
# ------------------------------------------------------------

# These are useful as tiger positives only if used with
# classification-level image labels. Since YOLO needs boxes,
# we DO NOT blindly label them as full-image tiger boxes.
#
# They are intentionally NOT added here.
#
# We will use the properly annotated tiger datasets first.
# ------------------------------------------------------------


# ------------------------------------------------------------
# DATA.YAML
# ------------------------------------------------------------

yaml = f"""path: {OUT.as_posix()}
train: images/train
val: images/val
test: images/test

names:
  0: tiger
"""

(OUT / "data.yaml").write_text(yaml, encoding="utf-8")

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print("\n======================================")
print("VAN NETRA V2 DATASET READY")
print("======================================")

for split in ["train", "val", "test"]:
    imgs = list((OUT / "images" / split).glob("*"))
    labels = list((OUT / "labels" / split).glob("*.txt"))

    print(
        f"{split:5s}: "
        f"{len(imgs):5d} images | "
        f"{len(labels):5d} labels"
    )

print(f"\nDataset: {OUT}")
print(f"YAML:    {OUT / 'data.yaml'}")