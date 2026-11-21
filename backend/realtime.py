import cv2
from ultralytics import YOLO

# Your trained tiger detector
TIGER_MODEL = r"C:\Users\Lenovo\pench-ai\backend\runs\detect\tiger_detector\weights\best.pt"

# Pretrained YOLO model - detects people
PERSON_MODEL = r"C:\Users\Lenovo\pench-ai\backend\yolo11n.pt"

tiger_model = YOLO(TIGER_MODEL)
person_model = YOLO(PERSON_MODEL)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam")
    exit()

print("PenchAI real-time detection started.")
print("Press Q to quit.")


def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union between two boxes.
    Boxes: [x1, y1, x2, y2]
    """

    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_width = max(0, x2 - x1)
    intersection_height = max(0, y2 - y1)

    intersection = intersection_width * intersection_height

    area1 = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
    area2 = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])

    union = area1 + area2 - intersection

    if union == 0:
        return 0

    return intersection / union


while True:

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read frame")
        break

    # --------------------------------------------------
    # 1. Detect HUMAN using pretrained YOLO
    # --------------------------------------------------

    person_results = person_model(
        frame,
        conf=0.40,
        verbose=False
    )

    person_boxes = []

    for result in person_results:

        for box in result.boxes:

            class_id = int(box.cls[0])

            # COCO class 0 = person
            if class_id == 0:

                confidence = float(box.conf[0])

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                person_boxes.append(
                    (x1, y1, x2, y2, confidence)
                )

    # --------------------------------------------------
    # 2. Detect TIGER using your custom model
    # --------------------------------------------------

    tiger_results = tiger_model(
        frame,
        conf=0.50,
        verbose=False
    )

    tiger_boxes = []

    for result in tiger_results:

        for box in result.boxes:

            confidence = float(box.conf[0])

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            tiger_box = (x1, y1, x2, y2)

            # Check whether this tiger detection
            # overlaps a human detection
            overlaps_person = False

            for person in person_boxes:

                person_box = person[:4]

                iou = calculate_iou(
                    tiger_box,
                    person_box
                )

                if iou > 0.20:
                    overlaps_person = True
                    break

            # Ignore suspicious tiger detections
            if not overlaps_person:

                tiger_boxes.append(
                    (x1, y1, x2, y2, confidence)
                )

    # --------------------------------------------------
    # 3. Draw HUMAN detections
    # --------------------------------------------------

    for x1, y1, x2, y2, confidence in person_boxes:

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (255, 180, 0),
            2
        )

        label = f"HUMAN {confidence * 100:.1f}%"

        cv2.putText(
            frame,
            label,
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 180, 0),
            2
        )

    # --------------------------------------------------
    # 4. Draw TIGER detections
    # --------------------------------------------------

    for x1, y1, x2, y2, confidence in tiger_boxes:

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 165, 255),
            3
        )

        label = f"TIGER {confidence * 100:.1f}%"

        cv2.putText(
            frame,
            label,
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),
            2
        )

    # --------------------------------------------------
    # 5. System title
    # --------------------------------------------------

    cv2.putText(
        frame,
        "PenchAI - Real-Time Wildlife Detection",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "PenchAI - Tiger + Human Detection",
        frame
    )

    # Q = quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()