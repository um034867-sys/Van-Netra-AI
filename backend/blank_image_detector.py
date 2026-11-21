"""
Model 1: Blank Image Detector
Uses Claude Vision API as a blackbox service for intelligent blank frame detection.
Integrates with existing ingestion pipeline without modifying base code.
"""

import anthropic
import base64
from pathlib import Path
from typing import Optional


class BlankImageDetector:
    """
    Intelligent blank image detector using Claude Vision API.
    Detects: blank frames, noise, rain, heat shimmer, false triggers.
    Returns confidence and detailed reasoning.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Anthropic API key"""
        if api_key is None:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("ANTHROPIC_API_KEY")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API"""
        with open(image_path, "rb") as image_file:
            return base64.standard_b64encode(
                image_file.read()
            ).decode("utf-8")

    def detect_blank(self, image_path: str) -> dict:
        """
        Analyze image for blankness.
        
        Returns:
        {
            "is_blank": bool,
            "confidence": float (0-1),
            "category": str (blank/noise/rain/shimmer/subject),
            "reasoning": str,
            "safe_to_delete": bool
        }
        """
        
        image_data = self.encode_image(image_path)
        
        # Determine media type
        path_obj = Path(image_path)
        suffix = path_obj.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif"
        }
        media_type = media_type_map.get(
            suffix,
            "image/jpeg"
        )
        
        prompt = """Analyze this camera trap image for the Pench Tiger Reserve.
        
Determine if this frame is a "blank" (false trigger) or contains a subject.

Categories:
- BLANK: Empty/featureless frame
- NOISE: Random pixel noise, corruption
- RAIN: Water droplets, rain interference
- SHIMMER: Heat shimmer, light distortion
- SUBJECT: Contains animal/human/clear subject

Provide:
1. Category
2. Confidence (0-1) that it's blank/false trigger
3. Brief reasoning
4. Safe to delete? (Only YES if >95% confident it's blank)

Be conservative - if uncertain, mark as SUBJECT."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )
        
        response_text = message.content[0].text.lower()
        
        # Parse response
        result = {
            "image_path": image_path,
            "is_blank": any(
                x in response_text 
                for x in ["blank", "false trigger", "empty"]
            ),
            "category": self._extract_category(response_text),
            "confidence": self._extract_confidence(response_text),
            "reasoning": message.content[0].text,
            "safe_to_delete": "yes" in response_text 
                              and "safe to delete" in response_text
        }
        
        return result

    @staticmethod
    def _extract_category(text: str) -> str:
        """Extract category from response"""
        categories = ["blank", "noise", "rain", "shimmer", "subject"]
        for cat in categories:
            if cat in text:
                return cat.upper()
        return "UNKNOWN"

    @staticmethod
    def _extract_confidence(text: str) -> float:
        """Extract confidence score from response"""
        import re
        # Look for patterns like "0.95", "95%", "confidence: 0.95"
        patterns = [
            r"confidence[:\s]+(\d+\.?\d*)",
            r"(\d+\.?\d*)%",
            r"(\d+\.?\d*)\s*(?:confidence|blank|likely)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                val = float(match.group(1))
                return min(val, 1.0) if val > 1 else val
        return 0.5  # Default

    def batch_detect(
        self,
        image_paths: list,
        delete_threshold: float = 0.95
    ) -> dict:
        """
        Process multiple images.
        
        Returns:
        {
            "total": int,
            "blanks": int,
            "subjects": int,
            "safe_for_deletion": list,
            "quarantined": list,
            "results": list[dict]
        }
        """
        
        results = []
        blanks = 0
        subjects = 0
        safe_for_deletion = []
        quarantined = []
        
        for img_path in image_paths:
            try:
                result = self.detect_blank(img_path)
                results.append(result)
                
                if result["is_blank"]:
                    blanks += 1
                    if result["confidence"] >= delete_threshold:
                        safe_for_deletion.append({
                            "path": img_path,
                            "confidence": result["confidence"]
                        })
                    else:
                        quarantined.append({
                            "path": img_path,
                            "confidence": result["confidence"],
                            "reason": "Below delete threshold"
                        })
                else:
                    subjects += 1
                    
            except Exception as e:
                quarantined.append({
                    "path": img_path,
                    "error": str(e),
                    "reason": "Processing error"
                })
        
        return {
            "total": len(image_paths),
            "blanks": blanks,
            "subjects": subjects,
            "safe_for_deletion": safe_for_deletion,
            "quarantined": quarantined,
            "results": results
        }


if __name__ == "__main__":
    # Test example
    detector = BlankImageDetector()
    # result = detector.detect_blank("path/to/test/image.jpg")
    # print(result)
