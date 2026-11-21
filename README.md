# Van Netra AI
### AI-Powered Wildlife Monitoring and Intelligence Platform

Van Netra AI is an AI-powered wildlife monitoring platform designed to support tiger detection, camera-trap monitoring, wildlife records, alerts, and visual analytics.

## Features
- AI-based tiger detection using YOLO
- General object and human detection
- Wildlife dashboard and detection statistics
- Tiger database and profile management
- Camera station monitoring
- Human review workflow
- Detection alerts
- Model performance visualizations
- Interactive movement map

## Technology Stack

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Leaflet, Recharts.

**Backend:** Python 3.12, FastAPI, Ultralytics YOLO, OpenCV, SQLite.

## Requirements
- Windows 10/11
- Python 3.12
- Node.js 20.19+ (Node.js 24 recommended)
- npm

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/um034867-sys/Van-Netra-AI.git
cd Van-Netra-AI
```

### 2. Set up Python

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

### 3. Install frontend dependencies

```powershell
npm ci
```

### 4. Configure model weights

The trained tiger model is not included in this repository.

Place your compatible trained model at:

`backend/runs/detect/van_netra_v2/weights/best.pt`

Place the general YOLO model at:

`backend/yolo11n.pt`

Both files are required for complete AI detection functionality. Obtain model files only from sources whose usage terms permit your intended use.

### 5. Start Van Netra

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start_penchai.ps1
```

The startup script initializes demo data and starts the backend and frontend in separate terminal windows.

## Application URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:5174 |
| Backend | http://127.0.0.1:8001 |
| API Documentation | http://127.0.0.1:8001/docs |
| Health Check | http://127.0.0.1:8001/health |

Keep both terminal windows open while using the application.

## Project Structure

```text
Van-Netra-AI/
├── backend/
│   ├── main.py
│   ├── detector.py
│   ├── database.py
│   ├── seed_demo_data.py
│   ├── requirements.txt
│   └── static/
│       └── evaluation/
├── public/
├── src/
├── package.json
├── package-lock.json
└── start_penchai.ps1
```

## Important Notes
- Model weights and training datasets are not included.
- Compatible model files are required for AI detection.
- Demo records are initialized locally.
- SQLite databases are generated locally.
- Evaluation images are included in `backend/static/evaluation/`.

## Development

Build frontend:

```powershell
npm run build
```

Run frontend independently:

```powershell
npm run dev -- --port 5174 --strictPort
```

Run backend independently from the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

## Repository

https://github.com/um034867-sys/Van-Netra-AI