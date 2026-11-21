from pathlib import Path
import random
import shutil

random.seed(123)

OUT = Path(r"D:\VanNetraDataset")

SOURCES = [
    Path(r"D:\Users\HP\Downloads\Animal dataset\dataset"),
    Path(r"D:\Users\HP\Downloads\Animals Detection Images Dataset\train"),
    Path(r"D:\Users\HP\Downloads\WildVision47\animals\animals"),
]

CLASSES = [
    "Leopard", "leopard",
    "Lion", "lion",
    "Cheetah", "cheetah",
    "Jaguar", "jaguar",
    "Lynx", "lynx",
    "Bear", "bear",
    "Brown bear",
    "Polar bear",
    "Deer", "deer",
    "Boar", "boar",
    "Wolf", "wolf",
    "Hyena", "hyena",
    "Zebra", "zebra",
    "Horse", "horse",
    "Fox", "fox",
    "Coyote", "coyote",
]

EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Keep evaluation relatively compact.
VAL_PER_CLASS = 20
TEST_PER_CLASS = 20

used = set()


def collect_images():
    found = []

    for source in SOURCES:
        if not source.exists():
            continue

        for cls in CLASSES:
            folder = source / cls

            if not folder.exists():
                continue

            for p in folder.rglob("*"):
                if p.is_file() and p.suffix.lower() in EXTS:
                    found.append((p, cls))

    return found


def copy_negative(img, split, cls, number):
    safe_cls = cls.lower().replace(" ", "_")
    name = f"negative_{safe_cls}_{number}{img.suffix.lower()}"

    # Avoid collisions
    base = Path(name).stem
    ext = img.suffix.lower()

    i = 1
    while name.lower() in used:
        name = f"{base}_{i}{ext}"
        i += 1

    used.add(name.lower())

    target_img = OUT / "images" / split / name
    target_label = OUT / "labels" / split / f"{Path(name).stem}.txt"

    shutil.copy2(img, target_img)

    # Empty label = background / no tiger
    target_label.touch()


def main():
    candidates = collect_images()

    if not candidates:
        raise RuntimeError("No negative images found.")

    grouped = {}

    for img, cls in candidates:
        grouped.setdefault(cls.lower(), []).append((img, cls))

    total_val = 0
    total_test = 0

    for key, items in grouped.items():
        random.shuffle(items)

        val_items = items[:VAL_PER_CLASS]
        test_items = items[VAL_PER_CLASS:VAL_PER_CLASS + TEST_PER_CLASS]

        for i, (img, cls) in enumerate(val_items):
            copy_negative(img, "val", cls, i)
            total_val += 1

        for i, (img, cls) in enumerate(test_items):
            copy_negative(img, "test", cls, i)
            total_test += 1

    print("======================================")
    print("NEGATIVE EVALUATION SET READY")
    print("======================================")
    print(f"Validation negatives: {total_val}")
    print(f"Test negatives:       {total_test}")
    print(f"Dataset:              {OUT}")


if __name__ == "__main__":
    main()