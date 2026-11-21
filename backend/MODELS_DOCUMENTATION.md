# Pench AI - 3 Integrated AI Models Documentation

## Overview

The Pench AI system integrates **3 sophisticated AI models** as "blackbox" services to automate forest management workflows. Each model uses cutting-edge APIs and is designed to work independently or as part of the integrated pipeline.

---

## Model 1: Blank Image Detector
**File:** `blank_image_detector.py`
**Primary AI Service:** Claude 3.5 Sonnet (Anthropic) with Vision Capabilities

### Purpose
Automatically classifies camera trap images as "blank" (false trigger) or containing subjects. This is critical since 80-90% of camera trap images are typically false triggers (moving grass, rain, insects, heat shimmer).

### How It Works
1. **Vision Analysis**: Uses Claude's multimodal Vision API to analyze images
2. **Classification**: Categorizes into: BLANK, NOISE, RAIN, SHIMMER, SUBJECT
3. **Confidence Scoring**: Provides 0-1 confidence metric
4. **Safe Deletion**: Only marks images for deletion with >95% confidence
5. **Reasoning**: Provides detailed explanation for every decision

### Key Features
- ✅ Handles corrupted/degraded images gracefully
- ✅ Conservative approach (defaults to SUBJECT if uncertain)
- ✅ Batch processing for entire camera trap folders
- ✅ Reports space and time savings
- ✅ Quarantine system for ambiguous images requiring human review

### Usage Example
```python
from blank_image_detector import BlankImageDetector

detector = BlankImageDetector(api_key="your_anthropic_key")

# Single image detection
result = detector.detect_blank("path/to/image.jpg")
print(result)
# {
#     "is_blank": False,
#     "category": "SUBJECT",
#     "confidence": 0.98,
#     "safe_to_delete": False,
#     "reasoning": "Contains clearly visible tiger..."
# }

# Batch processing
results = detector.batch_detect([
    "image1.jpg",
    "image2.jpg",
    "image3.jpg"
], delete_threshold=0.95)
print(f"Deleted: {len(results['safe_for_deletion'])}")
print(f"Review needed: {len(results['quarantined'])}")
```

### API Requirements
- **Service**: Anthropic Claude API
- **Model**: `claude-3-5-sonnet-20241022` (multimodal)
- **Cost**: ~$0.003 per image
- **Setup**: Get API key from https://console.anthropic.com

### Configuration
```python
# .env file
ANTHROPIC_API_KEY=sk-ant-...
BLANK_DELETE_THRESHOLD=0.95
```

---

## Model 2: Tiger Stripe Pattern Matcher
**File:** `tiger_stripe_matcher.py`
**Primary AI Service:** OpenAI Embeddings API

### Purpose
Identifies individual tigers by analyzing their unique stripe patterns. Creates a persistent database of known individuals and matches new sightings to build movement history.

### How It Works
1. **Feature Extraction**: Analyzes stripe density, edge complexity, and pattern characteristics
2. **Embedding Generation**: Converts stripe patterns to semantic embeddings via OpenAI API
3. **Database Storage**: Maintains SQLite database of known tiger patterns
4. **Similarity Matching**: Compares new images against known patterns using cosine similarity
5. **Confidence Thresholding**: Auto-matches if >85% confident, else flags for human review

### Key Features
- ✅ Persistent individual tiger database
- ✅ Automatic enrollment of new tigers
- ✅ High-confidence auto-matching
- ✅ Human review queue for ambiguous matches
- ✅ Tracks capture history and confidence levels
- ✅ Scalable to thousands of known individuals

### Usage Example
```python
from tiger_stripe_matcher import TigerStripePatternMatcher

matcher = TigerStripePatternMatcher(api_key="your_openai_key")

# Register new tiger
result = matcher.register_tiger(
    tiger_id="PENCH-TGR-001",
    image_path="tiger_photo.jpg",
    tiger_box=(100, 50, 400, 300)  # Optional bbox
)
# {"status": "registered", "tiger_id": "PENCH-TGR-001", "confidence": 0.95}

# Match image to known tiger
match = matcher.match_tiger(
    image_path="new_photo.jpg",
    threshold=0.85
)
# {
#     "matched_tiger_id": "PENCH-TGR-001",
#     "decision": "auto_match",
#     "confidence": 0.92,
#     "candidates": [...]
# }

# Get all known tigers
tigers = matcher.get_known_tigers()
for tiger in tigers:
    print(f"{tiger['tiger_id']}: {tiger['num_captures']} captures")
```

### API Requirements
- **Service**: OpenAI Embeddings API
- **Model**: `text-embedding-3-small` (efficient & accurate)
- **Cost**: ~$0.001-0.002 per image
- **Setup**: Get API key from https://platform.openai.com/api-keys

### Database Schema
```sql
-- Stored in SQLite (penchai.db)
tiger_patterns:
  - tiger_id (unique)
  - pattern_features (JSON)
  - embedding (binary vector)
  - first_captured, last_updated
  - num_captures, confidence

pattern_matches:
  - query_image
  - matched_tiger_id
  - confidence
  - human_verified (for QA)
```

### Configuration
```python
# .env file
OPENAI_API_KEY=sk-...
TIGER_MATCH_THRESHOLD=0.85
```

---

## Model 3: Movement Deviation & Anomaly Detector
**File:** `movement_deviation_detector.py`
**Primary AI Service:** Claude 3.5 Sonnet (Anthropic) with Multi-Agent Analysis

### Purpose
Detects meaningful behavioral deviations and generates actionable alerts for forest managers. Distinguishes genuine wildlife movements from survey artifacts.

### How It Works
1. **Data Collection**: Gathers historical movement data (180+ days)
2. **Range Calculation**: Computes centroid and home range for each tiger
3. **Pattern Analysis**: Feeds complex contextual data to Claude
4. **Intelligent Classification**: Claude identifies genuine deviations vs. artifacts
5. **Alert Generation**: Creates structured alerts with evidence and recommendations
6. **Manager Interface**: Provides unacknowledged alert queue for human review

### Detection Types
- **Range Shift**: Centroid movement >20km (core) or >5km (buffer)
- **New Territory**: First appearance at previously unvisited station
- **Prolonged Absence**: Tiger missing >14 days after regular appearances
- **Conflict Risk**: Movement toward villages or human settlements
- **Territorial Overlap**: Interaction with other known tigers

### Key Features
- ✅ Temporal pattern analysis (90/180 day windows)
- ✅ Geospatial reasoning (coordinates → km calculations)
- ✅ Artifact filtering (ignores survey effort biases)
- ✅ Severity classification (LOW/MEDIUM/HIGH)
- ✅ Actionable recommendations for managers
- ✅ Evidence-based justifications
- ✅ Manager acknowledgment tracking

### Usage Example
```python
from movement_deviation_detector import MovementDeviationDetector

detector = MovementDeviationDetector(api_key="your_anthropic_key")

# Get alerts for specific tiger
alerts = detector.detect_deviations(
    tiger_id="PENCH-TGR-001",
    current_locations=[
        {"station": "ST-001", "latitude": 21.78, "longitude": 78.31},
        {"station": "ST-007", "latitude": 21.82, "longitude": 78.35},
    ]
)

for alert in alerts:
    print(f"[{alert['severity']}] {alert['type']}")
    print(f"  Description: {alert['description']}")
    print(f"  Evidence: {alert['evidence']}")
    print(f"  Recommended action: {alert['recommended_action']}")

# Analyze territorial interactions
overlap = detector.compare_territories([
    "PENCH-TGR-001",
    "PENCH-TGR-002",
    "PENCH-TGR-003"
])
print(overlap["analysis"])

# Manager review workflow
pending_alerts = detector.get_unacknowledged_alerts(
    severity_filter="HIGH"
)
for alert in pending_alerts:
    print(f"Alert #{alert['id']}: {alert['description']}")
    # After review...
    detector.acknowledge_alert(
        alert_id=alert['id'],
        manager_notes="Tracked dispersal pattern, no action needed"
    )
```

### Alert Severity Levels
- **🔴 HIGH**: Immediate management action recommended (dispersal, conflict)
- **🟡 MEDIUM**: Requires monitoring and documentation (range expansion)
- **🟢 LOW**: Informational (typical seasonal movement)

### API Requirements
- **Service**: Anthropic Claude API
- **Model**: `claude-3-5-sonnet-20241022` (reasoning + analysis)
- **Cost**: ~$0.005-0.01 per analysis
- **Setup**: Same as Model 1

### Database Schema
```sql
movement_alerts:
  - tiger_id, alert_type, severity
  - confidence, description, evidence
  - recommended_action, created_at
  - acknowledged, manager_notes

tiger_movement_history:
  - tiger_id, station_code
  - latitude, longitude, timestamp
  - images_count, avg_confidence
```

### Configuration
```python
# .env file
ANTHROPIC_API_KEY=sk-ant-...
CORE_RANGE_SHIFT_THRESHOLD_KM=20
BUFFER_RANGE_SHIFT_THRESHOLD_KM=5
```

---

## Integrated Pipeline

**File:** `integrated_pipeline.py`

Combines all 3 models into a complete end-to-end workflow:

```
Raw Image Folder
    ↓
[Model 1] Blank Detection → Remove false triggers
    ↓
Subject Images Only
    ↓
[Model 2] Tiger Identification → Match to individuals
    ↓
Identified Tigers
    ↓
[Model 3] Movement Analysis → Generate alerts
    ↓
Manager Dashboard
```

### Complete Processing Example
```python
from integrated_pipeline import PenchAIIntegratedPipeline

# Initialize with all 3 models
pipeline = PenchAIIntegratedPipeline()

# Process entire folder (single command!)
report = pipeline.process_image_folder(
    folder_path="/path/to/camera/trap/images",
    delete_blanks=False  # Set True after manual review
)

# Results include:
# - Blank detection stats and space savings
# - Tiger identification results
# - Movement deviation alerts
# - Management recommendations

print(f"Total images: {report['total_images']}")
print(f"Subjects: {report['processing_stages']['tiger_identification']['auto_matched']}")
print(f"Alerts: {len(report['processing_stages']['movement_analysis']['alerts'])}")
```

---

## Setup Instructions

### Prerequisites
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get API keys
# - Anthropic: https://console.anthropic.com
# - OpenAI: https://platform.openai.com/api-keys

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///penchai.db
BLANK_DELETE_THRESHOLD=0.95
TIGER_MATCH_THRESHOLD=0.85
```

### First Run
```python
# Test Model 1: Blank Detector
from blank_image_detector import BlankImageDetector
detector = BlankImageDetector()
result = detector.detect_blank("sample_image.jpg")

# Test Model 2: Stripe Matcher
from tiger_stripe_matcher import TigerStripePatternMatcher
matcher = TigerStripePatternMatcher()
tiger = matcher.register_tiger("TEST-001", "tiger_image.jpg")

# Test Model 3: Movement Detector
from movement_deviation_detector import MovementDeviationDetector
detector = MovementDeviationDetector()
alerts = detector.detect_deviations("TEST-001", [])
```

---

## Cost Estimates

| Model | Avg Cost/Image | Monthly (10K images) |
|-------|----------------|---------------------|
| Blank Detector | $0.003 | $30 |
| Stripe Matcher | $0.002 | $20 |
| Movement Analysis | $0.005* | $50* |
| **Total** | **$0.01** | **~$100** |

*Movement analysis: per tiger analysis, not per image

---

## Troubleshooting

### Model 1: Blank Detector Issues
```
Error: API key invalid
→ Check ANTHROPIC_API_KEY in .env

Error: Image too large
→ Claude Vision has size limits; compress images <10MB

Error: Always returning SUBJECT
→ Adjust prompt in blank_image_detector.py
```

### Model 2: Stripe Matcher Issues
```
Error: No matches found
→ Database empty; register tigers first
→ Confidence threshold too high; lower TIGER_MATCH_THRESHOLD

Error: Database locked
→ Close other processes; check file permissions
```

### Model 3: Movement Detector Issues
```
Error: Not enough historical data
→ Need 30+ days of sightings for meaningful analysis
→ System learns over time

Error: Too many false alerts
→ Claude is conservative; adjust detection criteria in code
```

---

## Best Practices

1. **Batch Processing**: Process images in batches (1000s at a time)
2. **Human Review**: Always review high-severity alerts manually
3. **Database Backups**: Regular SQLite backups before batch operations
4. **API Rate Limits**: Monitor usage to stay within API tier limits
5. **Iterative Refinement**: Feedback loop improves accuracy over time

---

## Integration Points with Existing Code

These 3 models integrate seamlessly:

- **blank_detector** → Works with `ingestion.py` for raw image processing
- **stripe_matcher** → Feeds into `tiger_intelligence.py` for individual tracking
- **deviation_detector** → Generates alerts for `main.py` API endpoints
- **integrated_pipeline** → Optional high-level orchestration

No modifications needed to existing code; these are additive features.

---

## References

- [Anthropic Claude Documentation](https://docs.anthropic.com)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [SQLite Database Documentation](https://www.sqlite.org/docs.html)
- [Geospatial Calculations](https://en.wikipedia.org/wiki/Great-circle_distance)

---

**Last Updated:** 2026-08-17
**Status:** Ready for Integration
**Models Validated:** ✅ Claude Vision | ✅ OpenAI Embeddings | ✅ Claude Analysis
