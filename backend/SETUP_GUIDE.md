# Pench AI - Quick Setup Guide for 3 Models

## What Was Added

I've added **3 advanced AI models** to your Pench AI system without modifying any existing code. These integrate seamlessly as optional services.

### 📦 Files Created

1. **requirements.txt** - Complete dependency list with all necessary packages
2. **blank_image_detector.py** - Model 1: Blank image detection (Claude Vision)
3. **tiger_stripe_matcher.py** - Model 2: Tiger identification (OpenAI Embeddings)
4. **movement_deviation_detector.py** - Model 3: Movement analysis (Claude Analysis)
5. **integrated_pipeline.py** - Complete end-to-end pipeline combining all 3 models
6. **.env.example** - Environment configuration template
7. **MODELS_DOCUMENTATION.md** - Detailed documentation for each model

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
cd C:\Users\Lenovo\pench-ai\backend

# Install all packages
pip install -r requirements.txt
```

### Step 2: Get API Keys
You'll need 2 free API keys:

#### A. Anthropic Claude (for Models 1 & 3)
- Visit: https://console.anthropic.com
- Sign up (free tier available)
- Create API key
- Copy key to .env file

#### B. OpenAI Embeddings (for Model 2)
- Visit: https://platform.openai.com/api-keys
- Sign up or login
- Create API key
- Copy key to .env file

### Step 3: Configure Environment
```bash
# Copy template
copy .env.example .env

# Edit .env with your API keys
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxx
```

### Step 4: Test Installation
```bash
# Test all models
python -c "
from blank_image_detector import BlankImageDetector
from tiger_stripe_matcher import TigerStripePatternMatcher
from movement_deviation_detector import MovementDeviationDetector

print('✅ All models imported successfully!')
"
```

---

## 📊 The 3 Models Explained

### Model 1: Blank Image Detector ✅
**What it does:** Automatically removes false triggers (80-90% of images)
- Uses Claude's Vision AI
- Identifies: blanks, noise, rain, heat shimmer, subjects
- Conservative approach (only deletes >95% confident blanks)
- Safe & reversible (quarantine system)

**Cost:** ~$0.003 per image

**Usage:**
```python
from blank_image_detector import BlankImageDetector
detector = BlankImageDetector()
result = detector.detect_blank("image.jpg")
```

---

### Model 2: Tiger Stripe Pattern Matcher 🐅
**What it does:** Identifies individual tigers by stripe patterns
- Uses OpenAI Embeddings
- Builds persistent database of known tigers
- Auto-matches high-confidence (>85%) sightings
- Flags ambiguous matches for human review

**Cost:** ~$0.002 per image

**Usage:**
```python
from tiger_stripe_matcher import TigerStripePatternMatcher
matcher = TigerStripePatternMatcher()
matcher.register_tiger("PENCH-TGR-001", "image.jpg")
result = matcher.match_tiger("new_image.jpg")
```

---

### Model 3: Movement Deviation Detector 🗺️
**What it does:** Detects behavioral changes & generates management alerts
- Uses Claude's reasoning capabilities
- Analyzes 90/180-day movement patterns
- Identifies: range shifts, new territories, prolonged absence, conflict risks
- Distinguishes real changes from survey artifacts
- Provides severity levels and recommendations

**Cost:** ~$0.005-0.01 per analysis

**Usage:**
```python
from movement_deviation_detector import MovementDeviationDetector
detector = MovementDeviationDetector()
alerts = detector.detect_deviations("PENCH-TGR-001", locations)
```

---

## 🔗 Complete Integration (One Command)

Process entire image folder with all 3 models:

```python
from integrated_pipeline import PenchAIIntegratedPipeline

pipeline = PenchAIIntegratedPipeline()

report = pipeline.process_image_folder(
    "C:/path/to/camera/trap/images",
    delete_blanks=False  # Set True after review
)

# Results:
print(f"Processed: {report['total_images']} images")
print(f"Blanks found: {report['processing_stages']['blank_detection']['blanks_found']}")
print(f"Tigers identified: {report['processing_stages']['tiger_identification']['auto_matched']}")
print(f"Alerts generated: {report['processing_stages']['movement_analysis']['alerts_generated']}")
```

---

## 💾 Key Changes Summary

### ✅ What Was Added
- 4 new Python modules (800+ lines of code)
- Complete requirements.txt with all dependencies
- Environment configuration system
- Comprehensive documentation

### ✅ What Stayed the Same
- All existing code untouched
- detector.py, ingestion.py, main.py, database.py - NO CHANGES
- Your trained YOLO models still work
- Existing database schema compatible

### ✅ Backward Compatible
- These models are completely optional
- Existing code continues to work as-is
- New models integrate as additional services

---

## 📋 Required Packages (Key Additions)

```
NEW PACKAGES ADDED:
- anthropic==0.7.0          # Claude API
- openai==1.3.0             # OpenAI Embeddings
- pydantic==2.5.0           # Data validation
- scikit-learn==1.3.2       # ML utilities
- geopandas==0.14.0         # Geospatial analysis
- shapely==2.0.2            # Geometry operations
- folium==0.14.0            # Map visualization
```

All packages are open-source or use free APIs where available.

---

## 🧪 Testing the Models

### Test Model 1 (Blank Detector)
```bash
python blank_image_detector.py
# Edit: result = detector.detect_blank("path/to/test/image.jpg")
# Run and check output
```

### Test Model 2 (Stripe Matcher)
```bash
python tiger_stripe_matcher.py
# Register a tiger first, then test matching
```

### Test Model 3 (Movement Detector)
```bash
python movement_deviation_detector.py
# Analyze tiger movement patterns
```

### Test Integrated Pipeline
```bash
python integrated_pipeline.py
# Edit example paths and run
```

---

## 📚 Documentation

**Comprehensive guide:** See `MODELS_DOCUMENTATION.md` for:
- Detailed model descriptions
- API requirements & costs
- Complete usage examples
- Database schemas
- Troubleshooting guide
- Best practices

---

## 🔑 Environment Variables

```env
# Required - Claude Vision & Analysis
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx

# Required - OpenAI Embeddings
OPENAI_API_KEY=sk-xxxxxxxx

# Optional - Processing settings
BLANK_DELETE_THRESHOLD=0.95          # 0-1, default 0.95
TIGER_MATCH_THRESHOLD=0.85           # 0-1, default 0.85
DATABASE_URL=sqlite:///./penchai.db
SERVER_PORT=8000
```

---

## 💰 Cost Estimates

Processing 10,000 camera trap images per month:

| Model | Cost | Details |
|-------|------|---------|
| Blank Detection | $30 | ~$0.003/image |
| Tiger Matching | $20 | ~$0.002/image |
| Movement Analysis | $50 | ~$0.005/analysis |
| **TOTAL** | **~$100/month** | Scales with usage |

*Actual costs may vary; includes free tier usage*

---

## ⚠️ Important Notes

1. **API Keys**: Keep .env file secure - don't commit to git
2. **Rate Limits**: Monitor API usage to stay within tier limits
3. **Batch Processing**: Process images in batches for efficiency
4. **Database Backups**: Regular backups before bulk operations
5. **Human Review**: Always review HIGH severity alerts manually

---

## 🐛 Troubleshooting

### Module Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### API Key Issues
```bash
# Check .env file exists
ls -la .env

# Validate key format
# Should start with: sk-ant-... or sk-...
```

### Database Errors
```bash
# Check file permissions
ls -la penchai.db

# Reset database (careful!)
rm penchai.db
# Database will be recreated on first run
```

---

## 📞 Support

Refer to `MODELS_DOCUMENTATION.md` for detailed troubleshooting and examples.

---

## ✨ What's Next?

1. ✅ Install requirements.txt
2. ✅ Set up .env with API keys
3. ✅ Test individual models
4. ✅ Integrate with existing pipeline
5. ✅ Process camera trap images
6. ✅ Review alerts and refine thresholds

---

**Ready to process your Pench Tiger Reserve camera trap data!** 🐅

For questions, refer to MODELS_DOCUMENTATION.md or the inline code comments.
