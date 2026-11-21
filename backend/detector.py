from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path


class TigerDetector:

    def __init__(self):

        # --------------------------------------------------
        # YOUR TRAINED TIGER DETECTOR
        # --------------------------------------------------

        backend_dir = Path(__file__).parent

        candidate_model_paths = sorted(
            backend_dir.glob("runs/detect/**/weights/best.pt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if candidate_model_paths:
            tiger_model_path = candidate_model_paths[0]
        else:
            tiger_model_path = backend_dir / "runs/detect/tiger_detector/weights/best.pt"

        general_model_path = backend_dir / "yolo11n.pt"

        self.tiger_model = YOLO(str(tiger_model_path))

        # --------------------------------------------------
        # COCO MODEL
        #
        # Used mainly for human / common animal detection.
        # --------------------------------------------------

        self.general_model = YOLO(str(general_model_path))

    # ======================================================
    # IMAGE DECODING
    # ======================================================

    def decode_image(self, image_bytes):

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if image is None:
            raise ValueError(
                "Invalid image"
            )

        return image

    # ======================================================
    # GENERAL OBJECT DETECTION
    # ======================================================

    def detect_general(self, image):

        results = self.general_model.predict(
            source=image,
            conf=0.35,
            verbose=False
        )

        detections = []

        human_boxes = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )

                class_name = result.names[
                    class_id
                ]

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                detection = {
                    "class": class_name,
                    "confidence": round(
                        confidence,
                        3
                    ),
                    "box": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2
                    }
                }

                detections.append(
                    detection
                )

                if class_name == "person":

                    human_boxes.append(
                        detection
                    )

        return detections, human_boxes

    # ======================================================
    # TIGER DETECTION
    # ======================================================

    def detect_tiger(self, image):

        results = self.tiger_model.predict(
            source=image,
            conf=0.30,
            verbose=False
        )

        detections = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                confidence = float(
                    box.conf[0]
                )

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                detections.append({

                    "class": "tiger",

                    "confidence": round(
                        confidence,
                        3
                    ),

                    "box": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2
                    }

                })

        return detections

    # ======================================================
    # BOX OVERLAP
    # ======================================================

    @staticmethod
    def calculate_iou(box_a, box_b):

        ax1 = box_a["x1"]
        ay1 = box_a["y1"]
        ax2 = box_a["x2"]
        ay2 = box_a["y2"]

        bx1 = box_b["x1"]
        by1 = box_b["y1"]
        bx2 = box_b["x2"]
        by2 = box_b["y2"]

        intersection_x1 = max(
            ax1,
            bx1
        )

        intersection_y1 = max(
            ay1,
            by1
        )

        intersection_x2 = min(
            ax2,
            bx2
        )

        intersection_y2 = min(
            ay2,
            by2
        )

        width = max(
            0,
            intersection_x2 -
            intersection_x1
        )

        height = max(
            0,
            intersection_y2 -
            intersection_y1
        )

        intersection = (
            width * height
        )

        area_a = (
            max(0, ax2 - ax1) *
            max(0, ay2 - ay1)
        )

        area_b = (
            max(0, bx2 - bx1) *
            max(0, by2 - by1)
        )

        union = (
            area_a +
            area_b -
            intersection
        )

        if union <= 0:
            return 0.0

        return intersection / union

    # ======================================================
    # FINAL DECISION
    # ======================================================

    def classify_scene(
        self,
        tiger_detections,
        general_detections,
        human_boxes
    ):

        final_detections = []

        # --------------------------------------------------
        # HUMAN OVERRIDE
        #
        # If a strong person detection overlaps the tiger
        # detection, reject the tiger prediction.
        # --------------------------------------------------

        for tiger in tiger_detections:

            human_overlap = False

            for human in human_boxes:

                iou = self.calculate_iou(
                    tiger["box"],
                    human["box"]
                )

                if (
                    human["confidence"] >= 0.70
                    and iou >= 0.15
                ):

                    human_overlap = True

                    break

            if human_overlap:

                continue

            # ------------------------------------------------
            # TIGER CONFIDENCE RULE
            # ------------------------------------------------

            confidence = tiger[
                "confidence"
            ]

            # Use a realistic tiger gate. The general model can still
            # detect similar animal classes in the same scene, but that
            # should not override a valid tiger detection.
            if confidence >= 0.55:

                final_detections.append(
                    tiger
                )

        # --------------------------------------------------
        # ADD HUMAN DETECTIONS
        # --------------------------------------------------

        for human in human_boxes:

            final_detections.append({

                "class": "human",

                "confidence":
                    human["confidence"],

                "box":
                    human["box"]

            })

        # --------------------------------------------------
        # NO TIGER / NO HUMAN
        # --------------------------------------------------

        if not final_detections:

            return {
                "scene": "blank",
                "detections": []
            }

        has_tiger = any(
            d["class"] == "tiger"
            for d in final_detections
        )

        has_human = any(
            d["class"] == "human"
            for d in final_detections
        )

        if has_tiger:

            scene = "tiger"

        elif has_human:

            scene = "human"

        else:

            scene = "other"

        return {
            "scene": scene,
            "detections": final_detections
        }

    # ======================================================
    # PUBLIC API
    # ======================================================

    def detect(
        self,
        image_bytes: bytes
    ):

        image = self.decode_image(
            image_bytes
        )

        # ----------------------------------------------
        # RUN BOTH MODELS
        # ----------------------------------------------

        tiger_detections = (
            self.detect_tiger(image)
        )

        general_detections, human_boxes = (
            self.detect_general(image)
        )

        # ----------------------------------------------
        # FINAL DECISION
        # ----------------------------------------------

        result = self.classify_scene(
            tiger_detections,
            general_detections,
            human_boxes
        )

        return {

            "scene":
                result["scene"],

            "detections":
                result["detections"],

            "tiger_candidates":
                tiger_detections,

            "general_detections":
                general_detections,

            "image_width":
                image.shape[1],

            "image_height":
                image.shape[0]

        }