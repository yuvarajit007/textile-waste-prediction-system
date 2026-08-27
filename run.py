"""
Application Launcher for Textile Production Waste Prediction and Risk Classification System.
Starts the Uvicorn web server and serves the dashboard on http://localhost:8000
"""

import uvicorn
import os
import sys

if __name__ == "__main__":
    print("=" * 70)
    print("STARTING TEXPULSE AI - TEXTILE PRODUCTION WASTE PREDICTION SYSTEM")
    print("Dashboard available at: http://localhost:8000")
    print("=" * 70)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
