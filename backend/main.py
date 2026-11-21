import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .detector import TigerDetector
from .database import get_connection, DB_PATH, init_db
import sys, os
sys.path.append(os.path.dirname(__file__))

# ============================================================
# APP
# ============================================================
app = FastAPI(
    title="Van Netra â€“ Wildlife Intelligence Backend",
    description="Computer vision backend for Pench Tiger Reserve",
    version="0.3.0",
)

# Serve evaluation PNGs at /static/evaluation/<filename>
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVALUATION_DIR = PROJECT_ROOT / "backend" / "static" / "evaluation"
if not EVALUATION_DIR.is_dir():
    raise RuntimeError(f"Evaluation directory not found: {EVALUATION_DIR}")
app.mount(
    "/static/evaluation",
    StaticFiles(directory=str(EVALUATION_DIR), html=False),
    name="evaluation",
)

# ============================================================
# STARTUP
# ============================================================
@app.on_event("startup")
def on_startup():
    """Ensure the database schema exists on every cold start."""
    init_db()

# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# AI DETECTOR (lazy-loaded)
# ============================================================
_detector: Optional[TigerDetector] = None

def get_detector() -> TigerDetector:
    global _detector
    if _detector is None:
        _detector = TigerDetector()
    return _detector

# ============================================================
# DATABASE HELPER
# ============================================================
def db_connection():
    return get_connection()

# ============================================================
# BASIC ROUTES
# ============================================================
@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Van Netra â€“ Wildlife Intelligence Backend",
        "version": "0.3.0",
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# -----------------------------------------------------------
# DETECTION ENDPOINT
# -----------------------------------------------------------
@app.post("/detect")
async def detect_tiger(
    file: UploadFile = File(...),
    station_id: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):
    image_bytes = await file.read()
    detector = get_detector()
    result = detector.detect(image_bytes)
    # Simplified detection handling â€“ persist if tiger detected
    if result.get("scene") and any(d["class"] == "tiger" for d in result.get("detections", [])):
        conn = db_connection()
        try:
            # Ensure an "UNASSIGNED" tiger placeholder exists
            row = conn.execute("SELECT id FROM tigers WHERE tiger_code = 'UNASSIGNED' LIMIT 1").fetchone()
            if row:
                tiger_id = row["id"]
            else:
                now_iso = datetime.now().isoformat()
                cur = conn.execute(
                    "INSERT INTO tigers (tiger_code, first_seen, last_seen, status) VALUES (?, ?, ?, ?)",
                    ("UNASSIGNED", now_iso, now_iso, "active"),
                )
                tiger_id = cur.lastrowid
            # Save detection record
            ts = datetime.now().isoformat()
            best_conf = max((d["confidence"] for d in result.get("detections", []) if d["class"] == "tiger"), default=0)
            conn.execute(
                "INSERT INTO detections (tiger_id, image_path, station_id, timestamp, latitude, longitude, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    tiger_id,
                    f"[UPLOAD] {file.filename}",
                    station_id or "MANUAL_UPLOAD",
                    ts,
                    latitude,
                    longitude,
                    best_conf,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    return {"filename": file.filename, **result}

# -----------------------------------------------------------
# DASHBOARD SUMMARY
# -----------------------------------------------------------
@app.get("/api/dashboard")
def dashboard():
    conn = db_connection()
    cursor = conn.cursor()
    tigers = cursor.execute("SELECT COUNT(*) AS count FROM tigers").fetchone()["count"]
    detections = cursor.execute("SELECT COUNT(*) AS count FROM detections").fetchone()["count"]
    stations = cursor.execute("SELECT COUNT(*) AS count FROM stations").fetchone()["count"]
    alerts = cursor.execute("SELECT COUNT(*) AS count FROM alerts").fetchone()["count"]
    pending_reviews = cursor.execute("SELECT COUNT(*) AS count FROM reviews WHERE reviewer_decision IS NULL").fetchone()["count"]
    conn.close()
    return {
        "tigers": tigers,
        "detections": detections,
        "stations": stations,
        "alerts": alerts,
        "pending_reviews": pending_reviews,
    }

# -----------------------------------------------------------
# TIGERS ENDPOINTS
# -----------------------------------------------------------
@app.get("/api/tigers")
def get_tigers():
    conn = db_connection()
    rows = conn.execute(
        """
        SELECT t.id, t.tiger_code, t.first_seen, t.last_seen, t.status, COUNT(d.id) AS detection_count
        FROM tigers t
        LEFT JOIN detections d ON d.tiger_id = t.id
        GROUP BY t.id
        ORDER BY t.tiger_code
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/tigers/{tiger_id}")
def get_tiger(tiger_id: str):
    conn = db_connection()
    if tiger_id.isdigit():
        row = conn.execute(
            "SELECT id, tiger_code, first_seen, last_seen, status FROM tigers WHERE id = ?",
            (int(tiger_id),),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id, tiger_code, first_seen, last_seen, status FROM tigers WHERE tiger_code = ?",
            (tiger_id,),
        ).fetchone()
    conn.close()
    if row:
        return dict(row)
    raise HTTPException(status_code=404, detail="Tiger not found")

# -----------------------------------------------------------
# STATIONS ENDPOINT
# -----------------------------------------------------------
@app.get("/api/stations")
def get_stations():
    conn = db_connection()
    rows = conn.execute("SELECT * FROM stations").fetchall()
    conn.close()
    return [dict(row) for row in rows]

# -----------------------------------------------------------
# DETECTIONS ENDPOINT
# -----------------------------------------------------------
@app.get("/api/detections")
def get_detections():
    conn = db_connection()
    rows = conn.execute("SELECT * FROM detections").fetchall()
    conn.close()
    return [dict(row) for row in rows]



# -----------------------------------------------------------
# REVIEWS ENDPOINTS
# -----------------------------------------------------------

from pydantic import BaseModel

class ReviewUpdate(BaseModel):
    decision: str

@app.get("/api/reviews")
def get_reviews():
    conn = db_connection()
    rows = conn.execute("SELECT * FROM reviews").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.patch("/api/reviews/{review_id}")
def patch_review(review_id: int, payload: ReviewUpdate):
    conn = db_connection()
    cur = conn.execute(
        "UPDATE reviews SET reviewer_decision = ? WHERE id = ?",
        (payload.decision, review_id)
    )
    conn.commit()
    # Return the updated record
    row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    raise HTTPException(status_code=404, detail="Review not found")

# -----------------------------------------------------------
# MODEL PERFORMANCE ENDPOINT
# -----------------------------------------------------------

@app.get("/api/model-performance")
def model_performance():
    # Static evaluation results â€“ files are served via /static/evaluation
    graphs = [
        "BoxF1_curve.png",
        "BoxPR_curve.png",
        "BoxP_curve.png",
        "BoxR_curve.png",
        "confusion_matrix.png",
        "confusion_matrix_normalized.png",
        "val_batch0_labels.jpg",
        "val_batch0_pred.jpg",
        "val_batch1_labels.jpg",
        "val_batch1_pred.jpg",
        "val_batch2_labels.jpg",
        "val_batch2_pred.jpg",
    ]
    return {
        "model_name": "van_netra_v2",
        "model_file": "model.pt",
        "base_architecture": "YOLOv8",
        "dataset_class": "VanNetraDataset",
        "test_images": 2032,
        "annotated_instances": 3670,
        "metrics": {
            "precision": 0.9266,
            "recall": 0.8632,
            "map50": 0.9189,
            "map50_95": 0.5530,
        },
        "evaluation_dir": str(EVALUATION_DIR),
        "graphs": graphs,
        "note": "Evaluation metrics for Van Netra V2 test set.",
    }


