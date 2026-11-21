from pathlib import Path
from ultralytics import YOLO
import cv2

BASE = Path(__file__).resolve().parent

MODEL = BASE / "runs" / "detect" / "tiger_detector" / "weights" / "best.pt"

TIGER_DIR = Path(r"E:\tiger dataset\archive\tigers\val")

NEGATIVE_DIRS = [
    BASE / "background_data" / "humans",
    BASE / "background_data" / "other",
]

model = YOLO(str(MODEL))

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

thresholds = [
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.85,
    0.90,
]


def images(folder):
    if not folder.exists():
        return []

    return [
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in EXTS
    ]


tiger_images = images(TIGER_DIR)

negative_images = []

for folder in NEGATIVE_DIRS:
    negative_images.extend(images(folder))


print()
print("=" * 70)
print("PENCH AI — FALSE POSITIVE THRESHOLD TEST")
print("=" * 70)

print("Tiger images:", len(tiger_images))
print("Negative images:", len(negative_images))
print()


def has_tiger(path, conf):

    results = model.predict(
        source=str(path),
        conf=conf,
        imgsz=640,
        device="cpu",
        verbose=False
    )

    for result in results:

        if result.boxes is not None and len(result.boxes) > 0:
            return True

    return False


for threshold in thresholds:

    print(f"Testing confidence = {threshold:.2f}")

    tp = 0
    fn = 0
    fp = 0
    tn = 0

    for image in tiger_images:

        if has_tiger(image, threshold):
            tp += 1
        else:
            fn += 1

    for image in negative_images:

        if has_tiger(image, threshold):
            fp += 1
        else:
            tn += 1

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0
    )

    accuracy = (
        (tp + tn) /
        (tp + tn + fp + fn)
    )

    print(
        f"  TP={tp} "
        f"FN={fn} "
        f"FP={fp} "
        f"TN={tn}"
    )

    print(
        f"  Precision={precision:.3f} "
        f"Recall={recall:.3f} "
        f"Accuracy={accuracy:.3f}"
    )

    print()