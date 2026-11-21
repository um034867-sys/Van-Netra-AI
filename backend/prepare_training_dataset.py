import random
import shutil
from pathlib import Path

from PIL import Image


# ============================================================
# PATHS
# ============================================================

TIGER_DATASET = Path(
    r"E:\tiger dataset\yolo_dataset"
)

BACKGROUND_DATA = Path(
    r"C:\Users\Lenovo\pench-ai\backend\background_data"
)

OUTPUT = Path(
    r"C:\Users\Lenovo\pench-ai\backend\improved_dataset"
)


# ============================================================
# SETTINGS
# ============================================================

TIGER_TRAIN = 182
TIGER_VAL = 26

HUMAN_TOTAL = 100
OTHER_TOTAL = 150

random.seed(42)


# ============================================================
# IMAGE VALIDATION
# ============================================================

def valid_image(path):

    try:

        with Image.open(path) as img:
            img.verify()

        return True

    except Exception:

        return False


# ============================================================
# CREATE DIRECTORIES
# ============================================================

for split in ["train", "val"]:

    (
        OUTPUT / "images" / split
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    (
        OUTPUT / "labels" / split
    ).mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# COPY TIGER DATA
# ============================================================

def copy_tigers():

    print("\nCopying tiger dataset...")

    train_images = list(
        (
            TIGER_DATASET
            / "images"
            / "train"
        ).glob("*")
    )

    val_images = list(
        (
            TIGER_DATASET
            / "images"
            / "val"
        ).glob("*")
    )

    count_train = 0

    for image in train_images:

        if not valid_image(image):
            continue

        label = (
            TIGER_DATASET
            / "labels"
            / "train"
            / f"{image.stem}.txt"
        )

        if not label.exists():
            continue

        new_name = f"tiger_{count_train:04d}{image.suffix.lower()}"

        shutil.copy2(
            image,
            OUTPUT / "images" / "train" / new_name
        )

        shutil.copy2(
            label,
            OUTPUT / "labels" / "train" /
            f"tiger_{count_train:04d}.txt"
        )

        count_train += 1

    count_val = 0

    for image in val_images:

        if not valid_image(image):
            continue

        label = (
            TIGER_DATASET
            / "labels"
            / "val"
            / f"{image.stem}.txt"
        )

        if not label.exists():
            continue

        new_name = f"tiger_{count_val:04d}{image.suffix.lower()}"

        shutil.copy2(
            image,
            OUTPUT / "images" / "val" / new_name
        )

        shutil.copy2(
            label,
            OUTPUT / "labels" / "val" /
            f"tiger_{count_val:04d}.txt"
        )

        count_val += 1

    print(
        f"Tiger train: {count_train}"
    )

    print(
        f"Tiger val: {count_val}"
    )


# ============================================================
# COPY NEGATIVE IMAGES
# ============================================================

def copy_negatives():

    print("\nCopying negative images...")

    negatives = []

    for category in [
        "humans",
        "other",
    ]:

        folder = (
            BACKGROUND_DATA / category
        )

        if not folder.exists():
            continue

        for image in folder.iterdir():

            if (
                image.is_file()
                and valid_image(image)
            ):

                negatives.append(image)

    random.shuffle(negatives)

    # 80/20 split
    split_index = int(
        len(negatives) * 0.8
    )

    train_negatives = negatives[
        :split_index
    ]

    val_negatives = negatives[
        split_index:
    ]

    # ----------------------------------------
    # TRAIN NEGATIVES
    # ----------------------------------------

    for index, image in enumerate(
        train_negatives
    ):

        new_name = (
            f"negative_{index:04d}"
            f"{image.suffix.lower()}"
        )

        destination = (
            OUTPUT
            / "images"
            / "train"
            / new_name
        )

        shutil.copy2(
            image,
            destination
        )

        # EMPTY YOLO LABEL
        (
            OUTPUT
            / "labels"
            / "train"
            / f"negative_{index:04d}.txt"
        ).touch()

    # ----------------------------------------
    # VALIDATION NEGATIVES
    # ----------------------------------------

    for index, image in enumerate(
        val_negatives
    ):

        new_name = (
            f"negative_{index:04d}"
            f"{image.suffix.lower()}"
        )

        destination = (
            OUTPUT
            / "images"
            / "val"
            / new_name
        )

        shutil.copy2(
            image,
            destination
        )

        # EMPTY YOLO LABEL
        (
            OUTPUT
            / "labels"
            / "val"
            / f"negative_{index:04d}.txt"
        ).touch()

    print(
        f"Negative train: "
        f"{len(train_negatives)}"
    )

    print(
        f"Negative val: "
        f"{len(val_negatives)}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("PENCHAI IMPROVED DATASET BUILDER")
    print("=" * 60)

    copy_tigers()

    copy_negatives()

    print("\nDataset preparation complete!")

    print(
        f"\nDataset location:\n{OUTPUT}"
    )