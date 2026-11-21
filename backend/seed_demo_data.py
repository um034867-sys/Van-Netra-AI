"""
seed_demo_data.py
=================
Populates the Van Netra SQLite database with clearly-labelled DEMO data.

Rules:
- All synthetic records carry the prefix [DEMO] in relevant text fields.
- Coordinates are real camera-trap-style locations inside Pench Tiger Reserve.
- NO individual tiger identification is claimed – tigers are labelled by arbitrary code.
- Script is IDEMPOTENT: running it multiple times is safe (uses INSERT OR IGNORE).
- Nothing here represents actual observed tiger movements.
"""

import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# Allow running directly from project root or backend/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from database import get_connection, init_db

random.seed(42)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

# Real-ish camera-trap positions inside Pench Tiger Reserve area
# (approximate, representative – NOT claimed as exact field data)
DEMO_STATIONS = [
    ("PCH-01", 21.6980, 79.2440, "South Core Zone – Rukhad Gate"),
    ("PCH-02", 21.7110, 79.2560, "Central Zone – Turia"),
    ("PCH-03", 21.7250, 79.2680, "Central Zone – Jamtara"),
    ("PCH-04", 21.7380, 79.2800, "North Zone – Karmajhiri"),
    ("PCH-05", 21.7050, 79.2720, "East Buffer – Bodanala"),
    ("PCH-06", 21.7180, 79.2900, "East Zone – Raiyakasa"),
    ("PCH-07", 21.7310, 79.2620, "North Buffer – Khursapar"),
    ("PCH-08", 21.6900, 79.2580, "South Buffer – Sillari"),
]

# Demo tiger codes – arbitrary identifiers, no real individual ID claimed
DEMO_TIGERS = [
    ("PENCH-TGR-001",),
    ("PENCH-TGR-002",),
    ("PENCH-TGR-003",),
]


def already_seeded(conn) -> bool:
    """Return True if demo data is already present."""
    n = conn.execute("SELECT COUNT(*) FROM stations WHERE station_code LIKE 'PCH-%'").fetchone()[0]
    return n > 0


def seed():
    init_db()
    conn = get_connection()

    if already_seeded(conn):
        print("[seed_demo_data] Demo data already present – skipping seed.")
        conn.close()
        return

    print("[seed_demo_data] Seeding DEMO data into Van Netra database…")

    # -----------------------------------------------------------------------
    # Stations
    # -----------------------------------------------------------------------
    for code, lat, lon, description in DEMO_STATIONS:
        conn.execute(
            """
            INSERT OR IGNORE INTO stations
            (station_code, latitude, longitude, deployment_start)
            VALUES (?, ?, ?, ?)
            """,
            (code, lat, lon, "2026-01-15T00:00:00"),
        )
    conn.commit()
    print(f"  → {len(DEMO_STATIONS)} camera stations inserted.")

    # -----------------------------------------------------------------------
    # Tigers
    # -----------------------------------------------------------------------
    now_iso = datetime.now().isoformat()
    for (code,) in DEMO_TIGERS:
        conn.execute(
            """
            INSERT OR IGNORE INTO tigers
            (tiger_code, first_seen, last_seen, status)
            VALUES (?, ?, ?, ?)
            """,
            (code, now_iso, now_iso, "active"),
        )
    conn.commit()

    # Fetch inserted tiger IDs
    rows = conn.execute("SELECT id, tiger_code FROM tigers WHERE tiger_code LIKE 'PENCH-TGR-%'").fetchall()
    tigers = [(r[0], r[1]) for r in rows]
    print(f"  → {len(tigers)} tiger records inserted.")

    # -----------------------------------------------------------------------
    # Detections (spread across the last 60 days)
    # -----------------------------------------------------------------------
    start_date = datetime.now() - timedelta(days=60)
    stations_list = [(r[0], r[1], r[2]) for r in conn.execute(
        "SELECT station_code, latitude, longitude FROM stations"
    ).fetchall()]

    detection_count = 0
    tiger_last_seen: dict[int, str] = {}
    tiger_first_seen: dict[int, str] = {}

    for tiger_id, tiger_code in tigers:
        # 10 detections per tiger = 30 total demo detections
        for i in range(10):
            station_code, lat, lon = random.choice(stations_list)
            days_offset = random.uniform(0, 60)
            ts = (start_date + timedelta(days=days_offset)).isoformat()

            conn.execute(
                """
                INSERT INTO detections
                (tiger_id, image_path, station_id, timestamp, latitude, longitude, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tiger_id,
                    f"[DEMO] demo/sample_{tiger_code}_{i}.jpg",
                    station_code,
                    ts,
                    lat + random.uniform(-0.0020, 0.0020),  # slight scatter
                    lon + random.uniform(-0.0020, 0.0020),
                    round(random.uniform(0.78, 0.97), 3),
                ),
            )
            detection_count += 1

            if tiger_id not in tiger_first_seen or ts < tiger_first_seen[tiger_id]:
                tiger_first_seen[tiger_id] = ts
            if tiger_id not in tiger_last_seen or ts > tiger_last_seen[tiger_id]:
                tiger_last_seen[tiger_id] = ts

    conn.commit()

    # Update first_seen / last_seen on tigers table
    for tiger_id, tiger_code in tigers:
        conn.execute(
            "UPDATE tigers SET first_seen = ?, last_seen = ? WHERE id = ?",
            (tiger_first_seen[tiger_id], tiger_last_seen[tiger_id], tiger_id),
        )
    conn.commit()
    print(f"  → {detection_count} detection records inserted.")

    # -----------------------------------------------------------------------
    # Alerts (sample scenario alerts – clearly labelled DEMO)
    # -----------------------------------------------------------------------
    alert_tiger_id = tigers[0][0]
    sample_alerts = [
        (
            alert_tiger_id,
            "BUFFER ZONE BREACH",
            "[DEMO] PENCH-TGR-001 detected near reserve boundary at station PCH-08. Buffer zone monitoring recommended.",
            "PCH-08",
            0.91,
        ),
        (
            alert_tiger_id,
            "RANGE SHIFT",
            "[DEMO] PENCH-TGR-001 showed unusual northward movement over 15-day window. Possible territory shift.",
            "PCH-04",
            0.84,
        ),
        (
            tigers[1][0],
            "ABSENCE WARNING",
            "[DEMO] PENCH-TGR-002 not detected on any station for 12 days. Camera trap check recommended.",
            None,
            0.76,
        ),
    ]

    for t_id, a_type, message, evidence, conf in sample_alerts:
        conn.execute(
            """
            INSERT INTO alerts
            (tiger_id, alert_type, message, evidence, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                t_id,
                a_type,
                message,
                evidence,
                conf,
                (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
            ),
        )
    conn.commit()
    print(f"  → {len(sample_alerts)} demo alerts inserted.")

    # -----------------------------------------------------------------------
    # Reviews (sample pending review items)
    # -----------------------------------------------------------------------
    detection_ids = [r[0] for r in conn.execute(
        "SELECT id FROM detections ORDER BY id LIMIT 4"
    ).fetchall()]

    for det_id in detection_ids:
        conn.execute(
            """
            INSERT INTO reviews
            (detection_id, ai_prediction, reviewer_decision, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                det_id,
                "[DEMO] tiger – confidence marginal, human review required",
                None,  # pending
                (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            ),
        )
    conn.commit()
    print(f"  → {len(detection_ids)} pending review items inserted.")

    conn.close()
    print("[seed_demo_data] Done. All records are clearly labelled [DEMO].")


if __name__ == "__main__":
    seed()
