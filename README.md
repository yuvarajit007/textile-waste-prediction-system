---
title: TexPulse AI Textile Waste Prediction
emoji: 🧵
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# 🧵 TexPulse AI — Textile Production Waste Prediction & Risk Classification System


An enterprise-grade, AI-powered industrial intelligence dashboard designed to predict textile production waste, classify batch risks in real-time, detect production anomalies, and identify root causes behind textile manufacturing inefficiencies.

---

## 🌟 Key Features

- **⚡ Real-Time Waste Prediction & Risk Scoring**: Calculates exact waste percentages and categorizes batches into *Low*, *Medium*, or *High Risk* with normalized Risk Scores (0–100).
- **🤖 Hybrid ML & Anomaly Detection Engine**: Combines Random Forest classification, Isolation Forest unsupervised anomaly detection, and dynamic statistical baselines.
- **🔍 Root-Cause AI Diagnostics**: Automatically identifies key drivers behind excessive waste (e.g., maintenance overdue, machine age wear, humidity fluctuations, speed anomalies, operator variance) with actionable corrective recommendations.
- **📊 Multi-Dimensional Analytics**: Breakdown analysis across Machines, Fabric Types (Cotton, Polyester, Silk, Denim, Wool, Linen, Rayon, Nylon), Production Shifts (Morning, Afternoon, Night), and Operators.
- **📁 Drag-and-Drop Batch File Ingestion**: Supports batch processing of CSV and Excel (`.xlsx`) datasets with instant validation and risk classification.
- **🛡️ Robust Data Validation & Imputation**: Handles edge cases including 0-production divisions, missing environmental readings (humidity/temperature imputation), overdue maintenance calculations, and duplicate batch tracking.
- **🎨 Glassmorphic Executive Dashboard**: Responsive, dark-themed UI built with modern CSS glassmorphism, interactive Chart.js visualizations, and live metric cards.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **Machine Learning & Data**: [Scikit-Learn](https://scikit-learn.org/), [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **Database**: SQLite3 (persistent lightweight batch storage)
- **Frontend**: Modern Vanilla HTML5 / CSS3 (Glassmorphism & Flex/Grid), Vanilla JavaScript (ES6+), [Chart.js](https://www.chartjs.org/)

---

## 🚀 Quick Start Guide

### 1. Clone or Extract the Project
```bash
git clone <repository-url>
cd "textiles project"
```

### 2. Create and Activate a Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Application
```bash
python run.py
```
Or start via Uvicorn directly:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Access the Web Dashboard
Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

Interactive API documentation (Swagger UI) is available at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🧪 Testing & Sample Data

- **Run Automated Verification Suite**:
  ```bash
  python test_pipeline.py
  ```
  Runs 10+ edge-case test scenarios verifying baseline calculations, overdue maintenance penalties, zero-division resilience, and anomaly classification.

- **Generate Sample Excel/CSV Upload Files**:
  ```bash
  python generate_test_files.py
  ```
  Generates `sample_test_batches.csv` and `sample_test_batches.xlsx` for drag-and-drop batch testing in the UI.

---

## 📂 Project Structure

```
├── backend/
│   ├── __init__.py
│   ├── baseline_analyzer.py   # Statistical baseline & threshold calculator
│   ├── data_validator.py      # Input sanitation, date parsing, & edge-case guards
│   ├── database.py            # SQLite schema, batch CRUD, & persistence
│   ├── main.py                # FastAPI REST routes, static file serving, & CORS
│   ├── ml_engine.py           # Hybrid Random Forest + Isolation Forest model
│   ├── root_cause_ai.py       # AI rule engine for anomaly explainability
│   └── sample_data.py         # Realistic synthetic dataset generator
├── frontend/
│   ├── app.js                 # Frontend application state, API calls, & Chart.js
│   ├── index.html             # Glassmorphic dashboard markup & modals
│   └── styles.css             # Dark theme design system & animations
├── generate_test_files.py     # Helper to export sample CSV/XLSX test datasets
├── test_pipeline.py           # Comprehensive integration & edge-case test suite
├── run.py                     # Entrypoint launcher script
├── requirements.txt           # Python package requirements
├── .gitignore                 # Excluded environments, caches, and temp files
└── README.md                  # Documentation and setup instructions
```

---

## 📄 License
This project is licensed under the MIT License.
