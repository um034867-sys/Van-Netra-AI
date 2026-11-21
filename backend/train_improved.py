from ultralytics import YOLO


MODEL = "yolo11n.pt"
DATA = "improved_data.yaml"


model = YOLO(MODEL)


results = model.train(
    data=DATA,

    # Training
    epochs=40,
    imgsz=640,
    batch=8,

    # Hardware
    device="cpu",
    workers=2,

    # Augmentation
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,

    degrees=8,
    translate=0.1,
    scale=0.5,
    shear=2.0,

    fliplr=0.5,

    mosaic=1.0,
    mixup=0.1,

    # Slight robustness to camera blur/noise
    close_mosaic=10,

    # Output
    project="runs/detect",
    name="tiger_detector_v2",

    exist_ok=True
)


print("\n================================")
print("TRAINING COMPLETE")
print("================================")
print(
    "Best model:"
    "\nruns/detect/tiger_detector_v2/weights/best.pt"
)