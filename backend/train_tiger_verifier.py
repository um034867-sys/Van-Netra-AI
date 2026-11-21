from pathlib import Path
import random
import shutil

from ultralytics import YOLO


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parent

TIGER_TRAIN = Path(
    r"E:\tiger dataset\archive\tigers\train"
)

TIGER_VAL = Path(
    r"E:\tiger dataset\archive\tigers\val"
)

NEGATIVE_ROOT = BASE / "background_data"

DATASET = BASE / "verifier_dataset"


# ============================================================
# SETTINGS
# ============================================================

MAX_TIGER_TRAIN = 180
MAX_TIGER_VAL = 27

MAX_HUMAN = 100
MAX_OTHER = 150

SEED = 42

random.seed(SEED)


# ============================================================
# IMAGE EXTENSIONS
# ============================================================

EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp"
}


def image_files(folder):

    if not folder.exists():
        return []

    return [
        p for p in folder.rglob("*")
        if p.is_file()
        and p.suffix.lower() in EXTENSIONS
    ]


def copy_images(files, output):

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    copied = 0

    for index, source in enumerate(files):

        extension = source.suffix.lower()

        destination = (
            output /
            f"img_{index:05d}{extension}"
        )

        shutil.copy2(
            source,
            destination
        )

        copied += 1

    return copied


# ============================================================
# PREPARE DATASET
# ============================================================

def prepare_dataset():

    if DATASET.exists():

        print(
            "Removing previous verifier dataset..."
        )

        shutil.rmtree(DATASET)

    train_tiger = (
        DATASET /
        "train" /
        "tiger"
    )

    train_not_tiger = (
        DATASET /
        "train" /
        "not_tiger"
    )

    val_tiger = (
        DATASET /
        "val" /
        "tiger"
    )

    val_not_tiger = (
        DATASET /
        "val" /
        "not_tiger"
    )

    # --------------------------------------------------------
    # TIGERS
    # --------------------------------------------------------

    tigers_train = image_files(
        TIGER_TRAIN
    )

    tigers_val = image_files(
        TIGER_VAL
    )

    random.shuffle(tigers_train)
    random.shuffle(tigers_val)

    tigers_train = tigers_train[
        :MAX_TIGER_TRAIN
    ]

    tigers_val = tigers_val[
        :MAX_TIGER_VAL
    ]

    # --------------------------------------------------------
    # HUMANS
    # --------------------------------------------------------

    humans = image_files(
        NEGATIVE_ROOT / "humans"
    )

    random.shuffle(humans)

    humans = humans[
        :MAX_HUMAN
    ]

    # --------------------------------------------------------
    # OTHER ANIMALS
    # --------------------------------------------------------

    other = image_files(
        NEGATIVE_ROOT / "other"
    )

    random.shuffle(other)

    other = other[
        :MAX_OTHER
    ]

    # --------------------------------------------------------
    # SPLIT NEGATIVES
    # --------------------------------------------------------

    negatives = humans + other

    random.shuffle(negatives)

    val_negative_count = max(
        1,
        int(len(negatives) * 0.20)
    )

    val_negatives = negatives[
        :val_negative_count
    ]

    train_negatives = negatives[
        val_negative_count:
    ]

    print()
    print("=" * 60)
    print("TIGER VERIFIER DATASET")
    print("=" * 60)

    print(
        f"Tiger train : {len(tigers_train)}"
    )

    print(
        f"Tiger val   : {len(tigers_val)}"
    )

    print(
        f"Negative train : {len(train_negatives)}"
    )

    print(
        f"Negative val   : {len(val_negatives)}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # COPY
    # --------------------------------------------------------

    copy_images(
        tigers_train,
        train_tiger
    )

    copy_images(
        train_negatives,
        train_not_tiger
    )

    copy_images(
        tigers_val,
        val_tiger
    )

    copy_images(
        val_negatives,
        val_not_tiger
    )

    print()
    print(
        f"Dataset created at:"
    )

    print(
        DATASET
    )


# ============================================================
# TRAIN
# ============================================================

def train():

    yaml_path = DATASET / "data.yaml"

    yaml_path.write_text(
        f"""path: {DATASET.as_posix()}
train: train
val: val

names:
  0: tiger
  1: not_tiger
""",
        encoding="utf-8"
    )

    print()
    print("=" * 60)
    print("TRAINING TIGER VERIFIER")
    print("=" * 60)

    # Small classification model.
    # CPU-friendly.
    model = YOLO(
        "yolo11n-cls.pt"
    )

    model.train(

        data=str(DATASET),

        epochs=15,

        imgsz=224,

        batch=16,

        device="cpu",

        workers=0,

        patience=5,

        project=str(
            BASE / "runs" / "classify"
        ),

        name="tiger_verifier",

        exist_ok=True,

        verbose=True
    )

    print()
    print("=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    print(
        "Best model:"
    )

    print(
        BASE /
        "runs" /
        "classify" /
        "tiger_verifier" /
        "weights" /
        "best.pt"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    prepare_dataset()

    train()
