import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "penchai.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.executescript("""
    
    CREATE TABLE IF NOT EXISTS tigers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tiger_code TEXT UNIQUE NOT NULL,
        first_seen TEXT,
        last_seen TEXT,
        status TEXT DEFAULT 'active'
    );

    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tiger_id INTEGER,
        image_path TEXT,
        station_id TEXT,
        timestamp TEXT,
        latitude REAL,
        longitude REAL,
        confidence REAL,
        FOREIGN KEY(tiger_id) REFERENCES tigers(id)
    );

    CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_code TEXT UNIQUE,
        latitude REAL,
        longitude REAL,
        deployment_start TEXT,
        deployment_end TEXT
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        detection_id INTEGER,
        ai_prediction TEXT,
        reviewer_decision TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tiger_id INTEGER,
        alert_type TEXT,
        message TEXT,
        evidence TEXT,
        confidence REAL,
        created_at TEXT,
        FOREIGN KEY(tiger_id) REFERENCES tigers(id)
    );

    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":

    init_db()

    print("PenchAI database initialized.")
    print("Database:", DB_PATH.absolute())