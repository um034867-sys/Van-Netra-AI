import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

import cv2
from ultralytics import YOLO


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

# General YOLO model.
# It is used only to determine whether a frame contains a recognizable subject.
GENERAL_MODEL_PATH = r"C:\Users\Lenovo\pench-ai\backend\yolo11n.pt"

# Your custom tiger detector.
TIGER_MODEL_PATH = (
    r"C:\Users\Lenovo\pench-ai\backend"
    r"\runs\detect\tiger_detector\weights\best.pt"
)


class CameraTrapProcessor:

    def __init__(self):

        self.general_model = YOLO(GENERAL_MODEL_PATH)
        self.tiger_model = YOLO(TIGER_MODEL_PATH)

    def file_hash(self, path):

        sha256 = hashlib.sha256()

        with open(path, "rb") as f:

            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def analyze_image(self, image_path):

        image = cv2.imread(str(image_path))

        if image is None:
            return {
                "status": "invalid",
                "subject": False,
                "tiger": False,
                "reason": "Unreadable image",
            }

        height, width = image.shape[:2]

        if width == 0 or height == 0:
            return {
                "status": "invalid",
                "subject": False,
                "tiger": False,
                "reason": "Invalid dimensions",
            }

        # ---------------------------------------
        # GENERAL SUBJECT DETECTION
        # ---------------------------------------

        general_results = self.general_model(
            image,
            conf=0.35,
            verbose=False,
        )

        general_count = 0

        for result in general_results:

            if result.boxes is not None:
                general_count += len(result.boxes)

        # ---------------------------------------
        # TIGER DETECTION
        # ---------------------------------------

        tiger_results = self.tiger_model(
            image,
            conf=0.45,
            verbose=False,
        )

        tiger_count = 0
        tiger_confidence = 0.0

        for result in tiger_results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                tiger_count += 1

                confidence = float(box.conf[0])

                tiger_confidence = max(
                    tiger_confidence,
                    confidence,
                )

        # ---------------------------------------
        # DECISION
        # ---------------------------------------

        if tiger_count > 0:

            return {
                "status": "subject",
                "subject": True,
                "tiger": True,
                "confidence": round(tiger_confidence, 3),
                "general_objects": general_count,
                "reason": "Tiger detected",
            }

        if general_count > 0:

            return {
                "status": "subject",
                "subject": True,
                "tiger": False,
                "confidence": None,
                "general_objects": general_count,
                "reason": "Non-tiger subject detected",
            }

        return {
            "status": "blank",
            "subject": False,
            "tiger": False,
            "confidence": None,
            "general_objects": 0,
            "reason": "No recognizable subject detected",
        }

    def process_folder(self, input_folder):

        input_folder = Path(input_folder)

        if not input_folder.exists():
            raise FileNotFoundError(
                f"Folder does not exist: {input_folder}"
            )

        working_folder = input_folder / "_penchai"

        retained_folder = working_folder / "retained"
        quarantine_folder = working_folder / "quarantine"
        invalid_folder = working_folder / "invalid"

        retained_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        quarantine_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        invalid_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        images = [
            p
            for p in input_folder.rglob("*")
            if p.suffix.lower() in IMAGE_EXTENSIONS
            and "_penchai" not in p.parts
        ]

        results = []

        total_original_size = 0
        quarantine_size = 0

        start_time = datetime.now()

        for index, image_path in enumerate(images, start=1):

            print(
                f"[{index}/{len(images)}] "
                f"Processing {image_path.name}"
            )

            try:

                file_size = image_path.stat().st_size

                total_original_size += file_size

                analysis = self.analyze_image(image_path)

                file_hash = self.file_hash(image_path)

                result = {
                    "filename": image_path.name,
                    "path": str(image_path),
                    "hash": file_hash,
                    "size_bytes": file_size,
                    **analysis,
                }

                # ---------------------------------------
                # RETAIN SUBJECT IMAGES
                # ---------------------------------------

                if analysis["status"] == "subject":

                    destination = (
                        retained_folder / image_path.name
                    )

                    shutil.copy2(
                        image_path,
                        destination,
                    )

                # ---------------------------------------
                # QUARANTINE BLANK IMAGES
                # ---------------------------------------

                elif analysis["status"] == "blank":

                    destination = (
                        quarantine_folder / image_path.name
                    )

                    shutil.copy2(
                        image_path,
                        destination,
                    )

                    quarantine_size += file_size

                # ---------------------------------------
                # INVALID IMAGES
                # ---------------------------------------

                else:

                    destination = (
                        invalid_folder / image_path.name
                    )

                    shutil.copy2(
                        image_path,
                        destination,
                    )

                results.append(result)

            except Exception as e:

                results.append({
                    "filename": image_path.name,
                    "path": str(image_path),
                    "status": "error",
                    "error": str(e),
                })

        elapsed = (
            datetime.now() - start_time
        ).total_seconds()

        total = len(results)

        blank_count = sum(
            1
            for r in results
            if r.get("status") == "blank"
        )

        subject_count = sum(
            1
            for r in results
            if r.get("status") == "subject"
        )

        tiger_count = sum(
            1
            for r in results
            if r.get("tiger") is True
        )

        report = {
            "processed": total,
            "subjects": subject_count,
            "blank": blank_count,
            "tigers": tiger_count,
            "errors": sum(
                1
                for r in results
                if r.get("status") == "error"
            ),
            "quarantine_bytes": quarantine_size,
            "elapsed_seconds": round(elapsed, 2),
            "images_per_second": round(
                total / elapsed,
                2
            ) if elapsed > 0 else 0,
            "results": results,
        }

        return report