import sqlite3
from datetime import datetime
from pathlib import Path

from database import get_connection


def get_or_create_tiger(
    tiger_code=None
):

    conn = get_connection()

    cursor = conn.cursor()

    if tiger_code:

        cursor.execute(
            """
            SELECT id, tiger_code
            FROM tigers
            WHERE tiger_code = ?
            """,
            (tiger_code,)
        )

        result = cursor.fetchone()

        if result:

            conn.close()

            return result[0], result[1]

    # Create new tiger

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tigers
        """
    )

    count = cursor.fetchone()[0] + 1

    new_code = (
        f"PENCH-TGR-{count:03d}"
    )

    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO tigers
        (tiger_code, first_seen, last_seen)
        VALUES (?, ?, ?)
        """,
        (
            new_code,
            now,
            now
        )
    )

    tiger_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return tiger_id, new_code


def add_detection(
    tiger_id,
    image_path,
    station_id,
    timestamp,
    latitude,
    longitude,
    confidence
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO detections
        (
            tiger_id,
            image_path,
            station_id,
            timestamp,
            latitude,
            longitude,
            confidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tiger_id,
            image_path,
            station_id,
            timestamp,
            latitude,
            longitude,
            confidence
        )
    )

    cursor.execute(
        """
        UPDATE tigers
        SET last_seen = ?
        WHERE id = ?
        """,
        (
            timestamp,
            tiger_id
        )
    )

    conn.commit()
    conn.close()