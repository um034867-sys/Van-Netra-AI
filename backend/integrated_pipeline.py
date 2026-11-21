"""
Integrated Pipeline for Pench AI System
Demonstrates how to use all 3 AI models together:
1. Blank Image Detector (Claude Vision)
2. Tiger Stripe Pattern Matcher (OpenAI Embeddings)
3. Movement Deviation Detector (Claude Analysis)

This file shows the complete workflow without modifying existing code.
Can be integrated into main.py and ingestion.py as needed.
"""

from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

# Import the 3 models
from blank_image_detector import BlankImageDetector
from tiger_stripe_matcher import TigerStripePatternMatcher
from movement_deviation_detector import MovementDeviationDetector


class PenchAIIntegratedPipeline:
    """
    Complete pipeline for camera trap image processing with all 3 AI models.
    """

    def __init__(
        self,
        db_path: str = "penchai.db",
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ):
        """Initialize all 3 models"""
        
        # Model 1: Blank Image Detector
        self.blank_detector = BlankImageDetector(
            api_key=anthropic_key
        )
        
        # Model 2: Tiger Stripe Pattern Matcher
        self.stripe_matcher = TigerStripePatternMatcher(
            api_key=openai_key,
            db_path=db_path
        )
        
        # Model 3: Movement Deviation Detector
        self.deviation_detector = MovementDeviationDetector(
            api_key=anthropic_key,
            db_path=db_path
        )
        
        self.db_path = db_path

    def process_image_folder(
        self,
        folder_path: str,
        max_images: Optional[int] = None,
        delete_blanks: bool = False
    ) -> Dict:
        """
        Process entire folder of camera trap images.
        
        Complete workflow:
        1. Detect and quarantine blank images
        2. Identify tigers in remaining images
        3. Match against known individuals
        4. Track movements
        5. Generate alerts
        
        Args:
            folder_path: Path to image folder
            max_images: Limit processing (for testing)
            delete_blanks: Actually delete blank images (careful!)
            
        Returns:
            Comprehensive processing report
        """
        
        folder = Path(folder_path)
        image_files = list(
            folder.glob("**/*.jpg")
        ) + list(folder.glob("**/*.jpeg"))
        
        if max_images:
            image_files = image_files[:max_images]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_images": len(image_files),
            "processing_stages": {}
        }
        
        # ====================================
        # STAGE 1: BLANK IMAGE DETECTION
        # ====================================
        
        print("\n" + "="*60)
        print("STAGE 1: Blank Image Detection")
        print("="*60)
        
        blank_detection_results = (
            self.blank_detector.batch_detect(
                [str(f) for f in image_files],
                delete_threshold=0.95
            )
        )
        
        report["processing_stages"]["blank_detection"] = {
            "total": blank_detection_results["total"],
            "blanks_found": blank_detection_results["blanks"],
            "subjects_found": blank_detection_results["subjects"],
            "safe_for_deletion": len(
                blank_detection_results["safe_for_deletion"]
            ),
            "quarantined": len(
                blank_detection_results["quarantined"]
            ),
            "space_saved_mb": len(
                blank_detection_results["safe_for_deletion"]
            ) * 3  # Approx 3MB per image
        }
        
        print(f"\nResults:")
        print(f"  Total images: {blank_detection_results['total']}")
        print(f"  Blanks: {blank_detection_results['blanks']}")
        print(f"  Subjects: {blank_detection_results['subjects']}")
        print(f"  Safe for deletion: {len(blank_detection_results['safe_for_deletion'])}")
        print(f"  Quarantined for review: {len(blank_detection_results['quarantined'])}")
        print(f"  Estimated space savings: {report['processing_stages']['blank_detection']['space_saved_mb']} MB")
        
        # Optional: Delete blank images
        if delete_blanks:
            for item in blank_detection_results["safe_for_deletion"]:
                try:
                    Path(item["path"]).unlink()
                    print(f"  Deleted: {item['path']}")
                except Exception as e:
                    print(f"  Error deleting {item['path']}: {e}")
        
        # Process remaining images (non-blank)
        subject_images = [
            img_path 
            for img_path in image_files 
            if not any(
                img_path == Path(r["image_path"]) 
                for r in blank_detection_results["results"] 
                if r.get("is_blank")
            )
        ]
        
        # ====================================
        # STAGE 2: TIGER IDENTIFICATION
        # ====================================
        
        print("\n" + "="*60)
        print("STAGE 2: Tiger Identification via Stripe Matching")
        print("="*60)
        
        tiger_matches = []
        new_tigers = []
        needs_review = []
        
        for image_path in subject_images:
            try:
                match_result = self.stripe_matcher.match_tiger(
                    str(image_path),
                    threshold=0.85
                )
                
                if match_result.get("matched_tiger_id"):
                    tiger_matches.append({
                        "image": image_path,
                        "tiger_id": match_result["matched_tiger_id"],
                        "confidence": match_result["confidence"]
                    })
                    print(f"  ✓ Matched: {image_path.name} -> {match_result['matched_tiger_id']} ({match_result['confidence']:.2%})")
                    
                elif match_result.get("requires_human_review"):
                    needs_review.append({
                        "image": image_path,
                        "candidates": match_result["candidates"]
                    })
                    print(f"  ? Review needed: {image_path.name}")
                    
            except Exception as e:
                needs_review.append({
                    "image": image_path,
                    "error": str(e)
                })
        
        report["processing_stages"]["tiger_identification"] = {
            "auto_matched": len(tiger_matches),
            "needs_human_review": len(needs_review),
            "matches": tiger_matches
        }
        
        print(f"\nResults:")
        print(f"  Auto-matched: {len(tiger_matches)}")
        print(f"  Needs human review: {len(needs_review)}")
        
        # ====================================
        # STAGE 3: MOVEMENT ANALYSIS
        # ====================================
        
        print("\n" + "="*60)
        print("STAGE 3: Movement Deviation Detection")
        print("="*60)
        
        # Get unique tigers and analyze deviations
        unique_tigers = set(m["tiger_id"] for m in tiger_matches)
        all_alerts = []
        
        for tiger_id in unique_tigers:
            tiger_images = [
                m for m in tiger_matches 
                if m["tiger_id"] == tiger_id
            ]
            
            # Prepare location data (simplified)
            locations = [
                {
                    "station": f"station_{i}",
                    "latitude": 21.78 + (i * 0.01),
                    "longitude": 78.31 + (i * 0.01)
                }
                for i in range(len(tiger_images))
            ]
            
            # Detect deviations
            alerts = self.deviation_detector.detect_deviations(
                tiger_id,
                locations
            )
            
            all_alerts.extend(alerts)
            
            if alerts:
                print(f"\n  Tiger {tiger_id}:")
                for alert in alerts:
                    severity_emoji = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(alert.get("severity"), "⚪")
                    
                    print(f"    {severity_emoji} {alert.get('type')}: "
                          f"{alert.get('description', '')}")
        
        report["processing_stages"]["movement_analysis"] = {
            "tigers_analyzed": len(unique_tigers),
            "alerts_generated": len(all_alerts),
            "high_severity_alerts": len([
                a for a in all_alerts 
                if a.get("severity") == "high"
            ]),
            "alerts": all_alerts
        }
        
        # ====================================
        # SUMMARY REPORT
        # ====================================
        
        print("\n" + "="*60)
        print("PROCESSING COMPLETE - SUMMARY")
        print("="*60)
        print(f"\nTimestamp: {report['timestamp']}")
        print(f"Total images: {report['total_images']}")
        print(f"Subjects identified: {len(subject_images)}")
        print(f"Tigers matched: {len(tiger_matches)}")
        print(f"Movement alerts: {len(all_alerts)}")
        print(f"High-severity alerts: {report['processing_stages']['movement_analysis']['high_severity_alerts']}")
        
        return report

    def register_new_tiger_with_image(
        self,
        image_path: str,
        station_code: str,
        latitude: float,
        longitude: float,
        tiger_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Register a new tiger individual identified by stripe pattern.
        
        Args:
            image_path: Path to image with tiger
            station_code: Camera trap station code
            latitude, longitude: GPS coordinates
            tiger_id: Optional custom tiger ID
            metadata: Additional metadata
            
        Returns:
            Registration confirmation
        """
        
        # Register with stripe matcher (generates tiger_id if needed)
        result = self.stripe_matcher.register_tiger(
            tiger_id=tiger_id or "NEW_TIGER",
            image_path=image_path,
            metadata=metadata
        )
        
        return {
            "registration": result,
            "station": station_code,
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_management_dashboard_data(self) -> Dict:
        """Get all data needed for management dashboard"""
        
        known_tigers = self.stripe_matcher.get_known_tigers()
        unacknowledged_alerts = (
            self.deviation_detector.get_unacknowledged_alerts()
        )
        
        return {
            "tigers": known_tigers,
            "total_tigers": len(known_tigers),
            "pending_alerts": unacknowledged_alerts,
            "high_severity_alerts": [
                a for a in unacknowledged_alerts 
                if a["severity"] == "high"
            ],
            "generated_at": datetime.now().isoformat()
        }


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    pipeline = PenchAIIntegratedPipeline(
        db_path="penchai.db",
        anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Process a folder of camera trap images
    # report = pipeline.process_image_folder(
    #     "path/to/camera/trap/images",
    #     delete_blanks=False  # Set to True only after manual review
    # )
    
    # Get management dashboard data
    # dashboard = pipeline.get_management_dashboard_data()
    # print(dashboard)
