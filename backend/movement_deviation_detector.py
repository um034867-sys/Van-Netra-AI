"""
Model 3: Movement Deviation & Anomaly Detector
Uses Claude AI API as a blackbox service for intelligent pattern analysis.
Detects meaningful behavioral deviations, territorial shifts, and anomalies.
"""

import anthropic
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path


class MovementDeviationDetector:
    """
    Intelligent movement pattern analysis for tiger population management.
    Uses Claude as a blackbox to identify meaningful behavioral changes.
    """

    def __init__(self, api_key: Optional[str] = None, db_path: str = "penchai.db"):
        """Initialize with Anthropic API key"""
        if api_key is None:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("ANTHROPIC_API_KEY")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.db_path = db_path
        self._init_alert_db()

    def _init_alert_db(self):
        """Initialize alert tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movement_alerts (
                id INTEGER PRIMARY KEY,
                tiger_id TEXT,
                alert_type TEXT,
                severity TEXT,
                confidence REAL,
                description TEXT,
                evidence TEXT,
                recommended_action TEXT,
                created_at TEXT,
                acknowledged INTEGER DEFAULT 0,
                manager_notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tiger_movement_history (
                id INTEGER PRIMARY KEY,
                tiger_id TEXT,
                station_code TEXT,
                latitude REAL,
                longitude REAL,
                timestamp TEXT,
                images_count INTEGER,
                avg_confidence REAL
            )
        """)
        
        conn.commit()
        conn.close()

    def _get_tiger_history(
        self,
        tiger_id: str,
        days: int = 90
    ) -> List[Dict]:
        """Retrieve tiger movement history"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (
            datetime.now() - timedelta(days=days)
        ).isoformat()
        
        cursor.execute("""
            SELECT station_code, latitude, longitude, timestamp, 
                   images_count, avg_confidence
            FROM tiger_movement_history
            WHERE tiger_id = ? AND timestamp > ?
            ORDER BY timestamp DESC
        """, (tiger_id, cutoff_date))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "station": row[0],
                "latitude": row[1],
                "longitude": row[2],
                "timestamp": row[3],
                "image_count": row[4],
                "confidence": row[5]
            })
        
        conn.close()
        return history

    def _calculate_range_centroid(
        self,
        locations: List[Dict]
    ) -> Dict:
        """Calculate centroid of tiger's movement range"""
        
        if not locations:
            return {"error": "No locations"}
        
        lats = [loc["latitude"] for loc in locations]
        lons = [loc["longitude"] for loc in locations]
        
        centroid_lat = sum(lats) / len(lats)
        centroid_lon = sum(lons) / len(lons)
        
        # Calculate area (approximate)
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Rough calculation: ~111 km per degree at equator
        lat_km = (max_lat - min_lat) * 111
        lon_km = (max_lon - min_lon) * 111 * 0.65  # Adjusted for latitude
        
        area_sq_km = lat_km * lon_km
        
        return {
            "centroid_lat": centroid_lat,
            "centroid_lon": centroid_lon,
            "area_sq_km": area_sq_km,
            "num_locations": len(set(loc["station"] for loc in locations))
        }

    def detect_deviations(
        self,
        tiger_id: str,
        current_locations: List[Dict],
        buffer_zone_info: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Detect meaningful movement deviations using Claude AI.
        
        Args:
            tiger_id: Tiger identifier
            current_locations: Recent sightings (last 30 days)
            buffer_zone_info: Info about buffer/village zones
            
        Returns:
            List of alerts with severity and recommended actions
        """
        
        # Get historical data
        historical = self._get_tiger_history(tiger_id, days=180)
        
        # Calculate ranges
        current_range = self._calculate_range_centroid(current_locations)
        historical_range = self._calculate_range_centroid(historical)
        
        # Prepare analysis for Claude
        analysis_prompt = f"""
Analyze tiger movement patterns for forest management alert system.

TIGER: {tiger_id}
ANALYSIS DATE: {datetime.now().isoformat()}

CURRENT MOVEMENT (Last 30 days):
- Stations visited: {len(set(loc['station'] for loc in current_locations))}
- New stations: {len([loc for loc in current_locations if not any(h['station'] == loc['station'] for h in historical)])}
- Activity range: {current_range.get('area_sq_km', 0):.1f} sq km
- Centroid: ({current_range.get('centroid_lat', 0):.4f}, {current_range.get('centroid_lon', 0):.4f})
- Stations: {', '.join(set(loc['station'] for loc in current_locations))}

HISTORICAL BASELINE (Last 180 days):
- Average range: {historical_range.get('area_sq_km', 0):.1f} sq km
- Historical centroid: ({historical_range.get('centroid_lat', 0):.4f}, {historical_range.get('centroid_lon', 0):.4f})
- Known stations: {len(set(loc['station'] for loc in historical))}

DETECTION CRITERIA:
- Range centroid shift >20 km = significant deviation (core area)
- Range centroid shift >5 km = notable deviation (buffer area)
- First appearance at new station = new territory use
- Absence >14 days after regular appearance = possible dispersal/death
- Movement toward villages = human conflict risk
- Overlap with known territories of other tigers = competitive interaction

Identify:
1. Any genuine behavioral deviations (not survey artifacts)
2. Severity (low/medium/high)
3. Confidence (0-1)
4. Recommended management action
5. Supporting evidence

Output as JSON array of alerts. Each alert: {{
    "type": "range_shift|new_territory|prolonged_absence|conflict_risk|territorial_overlap",
    "severity": "low|medium|high",
    "confidence": 0-1,
    "description": "what changed",
    "evidence": "supporting data",
    "recommended_action": "what manager should do"
}}

Be conservative - only flag genuine behavioral change, not artifacts of uneven survey effort."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ]
        )
        
        # Parse Claude response
        response_text = message.content[0].text
        
        # Extract JSON arrays
        alerts = []
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(
                r'\[.*?\]',
                response_text,
                re.DOTALL
            )
            if json_match:
                alerts_data = json.loads(json_match.group())
                alerts = alerts_data if isinstance(
                    alerts_data,
                    list
                ) else []
        except (json.JSONDecodeError, re.error):
            # If parsing fails, return raw analysis
            alerts = [{
                "type": "analysis_summary",
                "description": response_text,
                "severity": "info",
                "confidence": 0.5
            }]
        
        # Store alerts in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute("""
                INSERT INTO movement_alerts
                (tiger_id, alert_type, severity, confidence,
                 description, evidence, recommended_action, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tiger_id,
                alert.get("type", "unknown"),
                alert.get("severity", "medium"),
                alert.get("confidence", 0.5),
                alert.get("description", ""),
                alert.get("evidence", ""),
                alert.get("recommended_action", ""),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        return alerts

    def compare_territories(
        self,
        tiger_ids: List[str]
    ) -> Dict:
        """
        Analyze territorial overlap between tigers.
        
        Args:
            tiger_ids: List of tiger IDs to compare
            
        Returns:
            Overlap analysis with conflict risk assessment
        """
        
        tiger_ranges = {}
        
        for tiger_id in tiger_ids:
            history = self._get_tiger_history(tiger_id, days=90)
            tiger_ranges[tiger_id] = self._calculate_range_centroid(history)
        
        # Use Claude to analyze overlaps
        overlap_prompt = f"""
Analyze territorial patterns and potential conflicts.

Tiger movements (last 90 days):
{json.dumps(tiger_ranges, indent=2)}

Identify:
1. Overlapping ranges (which tigers share territory)
2. Conflict risk level (low/medium/high)
3. Behavioral patterns (resident/transient/dispersing)
4. Management recommendations

Output as JSON."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": overlap_prompt
                }
            ]
        )
        
        analysis_text = message.content[0].text
        
        return {
            "tiger_count": len(tiger_ids),
            "analysis": analysis_text,
            "ranges": tiger_ranges
        }

    def get_unacknowledged_alerts(
        self,
        tiger_id: Optional[str] = None,
        severity_filter: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve unacknowledged alerts for manager review"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM movement_alerts WHERE acknowledged = 0"
        params = []
        
        if tiger_id:
            query += " AND tiger_id = ?"
            params.append(tiger_id)
        
        if severity_filter:
            query += " AND severity = ?"
            params.append(severity_filter)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                "id": row[0],
                "tiger_id": row[1],
                "alert_type": row[2],
                "severity": row[3],
                "confidence": row[4],
                "description": row[5],
                "evidence": row[6],
                "recommended_action": row[7],
                "created_at": row[8]
            })
        
        conn.close()
        return alerts

    def acknowledge_alert(
        self,
        alert_id: int,
        manager_notes: str = ""
    ) -> bool:
        """Mark alert as reviewed by manager"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE movement_alerts
            SET acknowledged = 1, manager_notes = ?
            WHERE id = ?
        """, (manager_notes, alert_id))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0


if __name__ == "__main__":
    # Test example
    detector = MovementDeviationDetector()
    # alerts = detector.detect_deviations("PENCH-TGR-001", [])
