"""
Model 2: Tiger Stripe Pattern Matcher
Uses OpenAI embeddings as a blackbox service for stripe pattern matching.
Identifies individual tigers by comparing flank stripe patterns.
Builds and maintains a persistent pattern database.
"""

import sqlite3
import json
from typing import Optional, List, Tuple
from pathlib import Path
from datetime import datetime

import openai
import cv2
import numpy as np
from PIL import Image


class TigerStripePatternMatcher:
    """
    Tiger individual identification system using stripe pattern embeddings.
    Uses OpenAI embeddings API as blackbox for pattern similarity.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        db_path: str = "penchai.db"
    ):
        """Initialize with OpenAI API key and database path"""
        if api_key is None:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
        
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.db_path = db_path
        self.model = "text-embedding-3-small"
        
        self._init_pattern_db()

    def _init_pattern_db(self):
        """Initialize pattern database if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tiger_patterns (
                id INTEGER PRIMARY KEY,
                tiger_id TEXT UNIQUE,
                pattern_features TEXT,
                embedding BLOB,
                first_captured TEXT,
                last_updated TEXT,
                num_captures INTEGER DEFAULT 1,
                confidence REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_matches (
                id INTEGER PRIMARY KEY,
                query_image TEXT,
                matched_tiger_id TEXT,
                confidence REAL,
                match_timestamp TEXT,
                human_verified INTEGER DEFAULT 0,
                verified_as_tiger TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    def extract_stripe_features(
        self,
        image_path: str,
        tiger_box: Optional[Tuple[int, int, int, int]] = None
    ) -> dict:
        """
        Extract stripe pattern features from tiger image.
        
        Args:
            image_path: Path to image
            tiger_box: Optional (x1, y1, x2, y2) bbox for tiger
            
        Returns:
            Dictionary with pattern features and description
        """
        
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Could not read image"}
        
        # If bbox provided, crop to tiger region
        if tiger_box:
            x1, y1, x2, y2 = tiger_box
            tiger_region = image[y1:y2, x1:x2]
        else:
            tiger_region = image
        
        # Convert to grayscale for stripe analysis
        gray = cv2.cvtColor(tiger_region, cv2.COLOR_BGR2GRAY)
        
        # Extract edge features (stripes appear as edges)
        edges = cv2.Canny(gray, 50, 150)
        
        # Calculate features
        stripe_density = np.sum(edges > 0) / edges.size
        stripe_hist = cv2.calcHist(
            [gray],
            [0],
            None,
            [256],
            [0, 256]
        )
        
        # Create pattern description for embedding
        description = f"""Tiger stripe pattern analysis:
- Stripe density: {stripe_density:.3f}
- Image region: {tiger_region.shape}
- Edge complexity: {np.mean(edges[edges > 0]) if np.any(edges) else 0:.1f}
- Pattern characteristics: {'high contrast' if stripe_density > 0.3 else 'low contrast'}
- Dominant values: {np.argmax(stripe_hist)}
"""
        
        features = {
            "stripe_density": float(stripe_density),
            "edge_complexity": float(
                np.mean(edges[edges > 0]) 
                if np.any(edges) else 0
            ),
            "region_shape": tiger_region.shape,
            "histogram_peak": int(np.argmax(stripe_hist)),
            "description": description,
            "image_path": image_path
        }
        
        return features

    def get_pattern_embedding(self, features: dict) -> list:
        """Get embedding from OpenAI for pattern features"""
        
        # Use description text for embedding
        description = features.get(
            "description",
            str(features)
        )
        
        embedding = self.client.embeddings.create(
            model=self.model,
            input=description
        ).data[0].embedding
        
        return embedding

    def register_tiger(
        self,
        tiger_id: str,
        image_path: str,
        tiger_box: Optional[Tuple[int, int, int, int]] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Register new tiger with stripe pattern.
        
        Args:
            tiger_id: Unique tiger identifier
            image_path: Path to first image
            tiger_box: Optional bbox
            metadata: Additional metadata
            
        Returns:
            Registration result
        """
        
        # Extract features
        features = self.extract_stripe_features(
            image_path,
            tiger_box
        )
        if "error" in features:
            return features
        
        # Get embedding
        embedding = self.get_pattern_embedding(features)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO tiger_patterns
                (tiger_id, pattern_features, embedding, 
                 first_captured, last_updated, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tiger_id,
                json.dumps(features),
                bytes(np.array(embedding).tobytes()),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                0.95  # High confidence for new tiger
            ))
            
            conn.commit()
            
            return {
                "status": "registered",
                "tiger_id": tiger_id,
                "confidence": 0.95,
                "features_stored": True
            }
            
        except sqlite3.IntegrityError:
            return {
                "status": "error",
                "message": f"Tiger {tiger_id} already registered"
            }
        finally:
            conn.close()

    def match_tiger(
        self,
        image_path: str,
        tiger_box: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.75
    ) -> dict:
        """
        Match image to known tiger using stripe patterns.
        
        Args:
            image_path: Path to query image
            tiger_box: Optional bbox
            threshold: Confidence threshold for auto-match
            
        Returns:
            Match result with confidence and candidates
        """
        
        # Extract query features
        query_features = self.extract_stripe_features(
            image_path,
            tiger_box
        )
        if "error" in query_features:
            return query_features
        
        query_embedding = np.array(
            self.get_pattern_embedding(query_features)
        )
        
        # Retrieve all known patterns
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tiger_id, embedding, confidence 
            FROM tiger_patterns
        """)
        
        known_patterns = cursor.fetchall()
        conn.close()
        
        matches = []
        
        for tiger_id, emb_bytes, stored_confidence in known_patterns:
            # Deserialize embedding
            stored_embedding = np.frombuffer(
                emb_bytes,
                dtype=np.float32
            )
            
            # Calculate cosine similarity
            similarity = float(
                np.dot(query_embedding, stored_embedding) /
                (np.linalg.norm(query_embedding) *
                 np.linalg.norm(stored_embedding))
            )
            
            # Normalize to 0-1 range
            normalized_score = (similarity + 1) / 2
            
            matches.append({
                "tiger_id": tiger_id,
                "confidence": min(normalized_score, 1.0),
                "stored_confidence": stored_confidence
            })
        
        # Sort by confidence
        matches.sort(
            key=lambda x: x["confidence"],
            reverse=True
        )
        
        # Determine if auto-match or needs human review
        if matches and matches[0]["confidence"] >= threshold:
            decision = "auto_match"
            matched_tiger = matches[0]["tiger_id"]
            confidence = matches[0]["confidence"]
        else:
            decision = "needs_review"
            matched_tiger = None
            confidence = matches[0]["confidence"] if matches else 0.0
        
        return {
            "image_path": image_path,
            "decision": decision,
            "matched_tiger_id": matched_tiger,
            "confidence": confidence,
            "candidates": matches[:5],  # Top 5 candidates
            "requires_human_review": decision == "needs_review"
        }

    def get_known_tigers(self) -> List[dict]:
        """Get list of all registered tigers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tiger_id, first_captured, last_updated, 
                   num_captures, confidence
            FROM tiger_patterns
            ORDER BY last_updated DESC
        """)
        
        tigers = []
        for row in cursor.fetchall():
            tigers.append({
                "tiger_id": row[0],
                "first_captured": row[1],
                "last_updated": row[2],
                "num_captures": row[3],
                "confidence": row[4]
            })
        
        conn.close()
        return tigers


if __name__ == "__main__":
    # Test example
    matcher = TigerStripePatternMatcher()
    # result = matcher.register_tiger("PENCH-TGR-001", "path/to/image.jpg")
    # match = matcher.match_tiger("path/to/test/image.jpg")
