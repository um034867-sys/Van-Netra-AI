import random
import shutil
from pathlib import Path

from PIL import Image


# ============================================================
# SETTINGS
# ============================================================

OUTPUT_ROOT = Path(
    r"C:\Users\Lenovo\pench-ai\backend\background_data"
)

MAX_PER_CATEGORY = {
    "humans": 100,
    "other": 150,
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}

random.seed(42)


# ============================================================
# SOURCE DATASETS
# ============================================================

SOURCES = {
    "humans": Path(
        r"E:\tiger dataset\archive (1)"
    ),

    "other_animal": Path(
        r"E:\tiger dataset\other animal"
    ),

    "small_animal": Path(
        r"E:\tiger dataset\small animal"
    ),

    "wild_animal": Path(
        r"E:\tiger dataset\wild animal"
    ),
}


# ============================================================
# FIND IMAGES
# ============================================================

def find_images(folder):

    images = []

    if not folder.exists():

        print(f"WARNING: Folder not found: {folder}")

        return images

    for file in folder.rglob("*"):

        if (
            file.is_file()
            and file.suffix.lower() in IMAGE_EXTENSIONS
        ):

            images.append(file)

    return images


# ============================================================
# VALIDATE IMAGE
# ============================================================

def valid_image(path):

    try:

        with Image.open(path) as img:
            img.verify()

        return True

    except Exception:

        return False


# ============================================================
# COPY IMAGE
# ============================================================

def copy_image(
    source,
    destination_folder,
    prefix,
    index
):

    extension = source.suffix.lower()

    destination = (
        destination_folder
        / f"{prefix}_{index:04d}{extension}"
    )

    shutil.copy2(
        source,
        destination
    )

    return destination


# ============================================================
# PREPARE HUMANS
# ============================================================

def prepare_humans():

    print("\nPreparing HUMAN images...")

    source_images = find_images(
        SOURCES["humans"]
    )

    print(
        f"Found {len(source_images)} images"
    )

    random.shuffle(source_images)

    output = (
        OUTPUT_ROOT / "humans"
    )

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    count = 0

    for image in source_images:

        if count >= MAX_PER_CATEGORY["humans"]:
            break

        if not valid_image(image):
            continue

        copy_image(
            image,
            output,
            "human",
            count
        )

        count += 1

    print(
        f"Copied {count} human images"
    )


# ============================================================
# PREPARE OTHER ANIMALS
# ============================================================

def prepare_other():

    print("\nPreparing OTHER ANIMAL images...")

    all_images = []

    # ----------------------------------------
    # Collect images
    # ----------------------------------------

    for source_name in [
        "other_animal",
        "small_animal",
        "wild_animal",
    ]:

        folder = SOURCES[source_name]

        images = find_images(folder)

        print(
            f"{source_name}: {len(images)} images"
        )

        all_images.extend(images)

    # ----------------------------------------
    # Remove actual tiger-class images
    # ----------------------------------------
    #
    # IMPORTANT:
    # We check the path RELATIVE to each
    # dataset, not the complete E:\tiger dataset
    # path. Otherwise every image would contain
    # the word "tiger".
    # ----------------------------------------

    filtered = []

    for image in all_images:

        is_tiger = False

        for source_name in [
            "other_animal",
            "small_animal",
            "wild_animal",
        ]:

            source_root = SOURCES[source_name]

            try:

                relative_path = image.relative_to(
                    source_root
                )

                parts = [
                    part.lower()
                    for part in relative_path.parts
                ]

                if any(
                    part in {
                        "tiger",
                        "tigers"
                    }
                    for part in parts
                ):

                    is_tiger = True

                break

            except ValueError:

                continue

        if not is_tiger:

            filtered.append(image)

    print(
        f"After tiger exclusion: "
        f"{len(filtered)} images"
    )

    random.shuffle(filtered)

    output = (
        OUTPUT_ROOT / "other"
    )

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    count = 0

    for image in filtered:

        if count >= MAX_PER_CATEGORY["other"]:
            break

        if not valid_image(image):
            continue

        copy_image(
            image,
            output,
            "other",
            count
        )

        count += 1

    print(
        f"Copied {count} non-tiger animal images"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "PENCHAI BACKGROUND DATA PREPARATION"
    )

    print("=" * 60)

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )

    prepare_humans()

    prepare_other()

    print("\nFinished.")

    print(
        f"\nOutput directory:\n{OUTPUT_ROOT}"
    )