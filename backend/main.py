"""
FastAPI Application Entrypoint for AI-Based Textile Production Waste Prediction & Risk Classification System.
Provides REST API endpoints for analytics, real-time prediction, file uploads, settings, and serves the web UI.
"""

import os
import io
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from backend.database import (
    init_db, get_settings, update_settings, save_batch, save_batches_bulk,
    fetch_all_batches, fetch_valid_batches_df, clear_all_batches
)
from backend.data_validator import validate_and_clean_batch, validate_batch_collection
from backend.baseline_analyzer import BaselineAnalyzer
from backend.ml_engine import TextileRiskMLEngine
from backend.root_cause_ai import RootCauseAIEngine
from backend.sample_data import generate_sample_batches

app = FastAPI(
    title="Textile Production Waste Prediction & Risk Classification API",
    description="Intelligent AI system predicting textile waste risks and abnormal batches.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instances
baseline_analyzer = BaselineAnalyzer()
root_cause_engine = RootCauseAIEngine()
ml_engine = TextileRiskMLEngine(baseline_analyzer)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


def refresh_system_state():
    """Fetches valid records from database, refreshes baseline statistics, and retrains ML models."""
    df = fetch_valid_batches_df()
    settings = get_settings()
    baseline_analyzer.set_data(df)
    ml_engine.train(df, maintenance_interval_days=settings.get("maintenance_interval_days", 60))


@app.on_event("startup")
def startup_event():
    """Initializes DB and populates sample data if empty."""
    init_db()
    df = fetch_valid_batches_df()
    if df.empty:
        print("[Startup] Database empty. Populating realistic sample textile batches...")
        raw_samples = generate_sample_batches(total_count=1000)
        settings = get_settings()
        
        # Calculate baseline from samples first
        temp_df = pd.DataFrame(raw_samples)
        baseline_analyzer.set_data(temp_df)
        ml_engine.train(temp_df, maintenance_interval_days=settings.get("maintenance_interval_days", 60))

        # Predict each sample to populate risk scores and explanations
        processed = []
        for item in raw_samples:
            pred = ml_engine.predict_batch(item, settings)
            item.update(pred)
            processed.append(item)

        save_batches_bulk(processed, duplicate_strategy="keep_latest")
        print(f"[Startup] Successfully seeded {len(processed)} production batches.")

    refresh_system_state()


# ----------------------------------------------------
# 1. Overview & Dashboard Summary KPIs
# ----------------------------------------------------
@app.get("/api/overview")
def get_overview():
    """Returns top-level KPIs and summary counts for the dashboard header."""
    batches = fetch_all_batches(limit=10000)
    settings = get_settings()

    total_count = len(batches)
    valid_batches = [b for b in batches if b.get("is_valid", 1) == 1]
    invalid_batches = [b for b in batches if b.get("is_valid", 1) == 0]

    normal_count = sum(1 for b in valid_batches if b.get("risk_level") == "NORMAL")
    warning_count = sum(1 for b in valid_batches if b.get("risk_level") == "WARNING")
    high_risk_count = sum(1 for b in valid_batches if b.get("risk_level") == "HIGH RISK")
    abnormal_count = sum(1 for b in valid_batches if b.get("is_abnormal", 0) == 1)

    avg_waste_pct = round(sum(b.get("waste_percentage", 0) for b in valid_batches) / max(1, len(valid_batches)), 2)
    total_prod = round(sum(b.get("total_production", 0) for b in valid_batches), 1)
    total_waste = round(sum(b.get("waste_quantity", 0) for b in valid_batches), 1)

    # Machine waste summary
    machine_analysis = baseline_analyzer.get_machine_analysis(settings.get("maintenance_interval_days", 60))
    fabric_analysis = baseline_analyzer.get_fabric_analysis()

    # Recent high-risk batches for alert banner
    recent_high_risks = [b for b in valid_batches if b.get("risk_level") == "HIGH RISK"][:5]

    return {
        "kpis": {
            "total_batches": total_count,
            "valid_batches": len(valid_batches),
            "invalid_batches": len(invalid_batches),
            "average_waste_percentage": avg_waste_pct,
            "total_production_kg": total_prod,
            "total_waste_kg": total_waste,
            "normal_count": normal_count,
            "warning_count": warning_count,
            "high_risk_count": high_risk_count,
            "abnormal_count": abnormal_count
        },
        "recent_high_risk_alerts": recent_high_risks,
        "highest_waste_machine": machine_analysis.get("highest_waste_machine"),
        "lowest_waste_machine": machine_analysis.get("lowest_waste_machine"),
        "high_risk_fabrics": fabric_analysis.get("high_risk_fabrics", [])
    }


# ----------------------------------------------------
# 2. Batch Explorer & Filterable Data Table
# ----------------------------------------------------
@app.get("/api/batches")
def get_batches(
    machine: Optional[str] = Query("ALL"),
    fabric: Optional[str] = Query("ALL"),
    shift: Optional[str] = Query("ALL"),
    operator: Optional[str] = Query("ALL"),
    risk: Optional[str] = Query("ALL"),
    search: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """Retrieves paginated and filtered batch records."""
    batches = fetch_all_batches(
        machine=machine,
        fabric=fabric,
        shift=shift,
        operator=operator,
        risk=risk,
        search=search,
        limit=limit,
        offset=offset
    )
    # Total matching count for pagination
    all_filtered = fetch_all_batches(
        machine=machine,
        fabric=fabric,
        shift=shift,
        operator=operator,
        risk=risk,
        search=search,
        limit=100000,
        offset=0
    )
    return {
        "batches": batches,
        "total_count": len(all_filtered),
        "limit": limit,
        "offset": offset
    }


# ----------------------------------------------------
# 3. Real-Time Single Batch Predictor & Simulator
# ----------------------------------------------------
@app.post("/api/predict")
def predict_single_batch(batch_data: Dict[str, Any], save: bool = Query(False)):
    """
    Evaluates a production batch, calculates waste percentage, calculates maintenance age,
    runs hybrid ML and adaptive baseline checks, and returns explainability reasons and actions.
    """
    cleaned = validate_and_clean_batch(batch_data)
    settings = get_settings()
    prediction = ml_engine.predict_batch(cleaned, settings)
    result = {**cleaned, **prediction}

    if save:
        dup_strategy = settings.get("duplicate_strategy", "keep_latest")
        save_batch(result, duplicate_strategy=dup_strategy)
        refresh_system_state()

    return result


# ----------------------------------------------------
# 4. File Upload (CSV & Excel)
# ----------------------------------------------------
@app.post("/api/upload")
async def upload_production_file(file: UploadFile = File(...)):
    """
    Processes uploaded CSV or Excel production files, runs full data validation,
    predicts risk levels and reasons for all records, saves to DB, and returns validation summary.
    """
    filename = file.filename.lower()
    content = await file.read()

    try:
        if filename.endswith(".csv"):
            df_raw = pd.read_csv(io.BytesIO(content))
        elif filename.endswith((".xlsx", ".xls")):
            df_raw = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a CSV or Excel (.xlsx) file.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    if df_raw.empty:
        raise HTTPException(status_code=400, detail="Uploaded file contains no data.")

    # Normalize column names
    col_mapping = {}
    for col in df_raw.columns:
        c_clean = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        col_mapping[col] = c_clean
    df_raw = df_raw.rename(columns=col_mapping)

    raw_records = df_raw.to_dict(orient="records")
    cleaned_records, validation_summary = validate_batch_collection(raw_records)

    settings = get_settings()
    processed_batches = []
    for item in cleaned_records:
        pred = ml_engine.predict_batch(item, settings)
        item.update(pred)
        processed_batches.append(item)

    dup_strategy = settings.get("duplicate_strategy", "keep_latest")
    saved_count = save_batches_bulk(processed_batches, duplicate_strategy=dup_strategy)
    refresh_system_state()

    return {
        "message": f"Successfully processed and imported {saved_count} batches from {file.filename}.",
        "validation_summary": validation_summary,
        "sample_preview": processed_batches[:5]
    }


# ----------------------------------------------------
# 5. Multi-Dimensional Analytics Endpoints
# ----------------------------------------------------
@app.get("/api/analytics/machines")
def get_machine_analytics():
    """Returns machine-wise metrics, age correlation, and maintenance status."""
    settings = get_settings()
    return baseline_analyzer.get_machine_analysis(settings.get("maintenance_interval_days", 60))


@app.get("/api/analytics/fabrics")
def get_fabric_analytics():
    """Returns fabric-wise metrics and high-risk fabric flags."""
    return baseline_analyzer.get_fabric_analysis()


@app.get("/api/analytics/shifts")
def get_shift_analytics():
    """Returns shift-wise comparisons."""
    return baseline_analyzer.get_shift_analysis()


@app.get("/api/analytics/operators")
def get_operator_analytics():
    """Returns objective, condition-oriented operator metrics."""
    return baseline_analyzer.get_operator_analysis()


@app.get("/api/analytics/maintenance")
def get_maintenance_analytics():
    """Returns maintenance matrix and degradation bins curve."""
    settings = get_settings()
    return baseline_analyzer.get_maintenance_analysis(settings.get("maintenance_interval_days", 60))


@app.get("/api/analytics/correlations")
def get_correlations_analytics():
    """Returns correlation coefficients with waste percentage."""
    return baseline_analyzer.get_correlations()


# ----------------------------------------------------
# 5.5 Root-Cause AI & Explainability Endpoints
# ----------------------------------------------------
@app.get("/api/root-cause/plant-analysis")
def get_plant_root_cause_analysis():
    """
    Returns plant-wide Root-Cause Pareto analysis, failure category distribution,
    machine-level failure modes, prioritized recommendations, and waste causes summary.
    """
    df = fetch_valid_batches_df()
    settings = get_settings()
    return root_cause_engine.generate_plant_root_cause_analysis(df, baseline_analyzer, settings)


@app.get("/api/analytics/waste-causes-prevention")
def get_waste_causes_prevention():
    """
    Returns aggregated table of top waste causes, affected batch counts,
    average waste percentages, preventive actions, and risk tiers.
    """
    df = fetch_valid_batches_df()
    settings = get_settings()
    summary = root_cause_engine.get_waste_causes_prevention_summary(df, baseline_analyzer, settings)
    return {"summary": summary}


@app.post("/api/root-cause/diagnose")
def diagnose_root_cause_single(batch_data: Dict[str, Any]):
    """
    Performs deep-dive Root-Cause AI diagnosis for a given batch payload.
    Returns multi-factor attribution, primary & secondary root causes, severity,
    prescriptive remediation playbook with estimated savings, and counterfactual targets.
    """
    cleaned = validate_and_clean_batch(batch_data)
    settings = get_settings()
    if "risk_score" not in cleaned or "risk_level" not in cleaned:
        pred = ml_engine.predict_batch(cleaned, settings)
        cleaned.update(pred)
    diag = root_cause_engine.diagnose_batch(cleaned, baseline_analyzer, settings)
    return diag


@app.post("/api/root-cause/simulate")
def simulate_counterfactual_scenario(payload: Dict[str, Any]):
    """
    Performs interactive 'What-If' counterfactual simulation for parameter adjustments.
    Payload: { "batch": {...}, "modified_params": { "production_speed": ..., "humidity": ..., "maintenance_age_days": ..., "temperature": ... } }
    """
    batch = payload.get("batch", {})
    modified_params = payload.get("modified_params", {})
    cleaned = validate_and_clean_batch(batch)
    settings = get_settings()
    if "risk_score" not in cleaned or "risk_level" not in cleaned:
        pred = ml_engine.predict_batch(cleaned, settings)
        cleaned.update(pred)
    res = root_cause_engine.simulate_counterfactual(
        batch=cleaned,
        modified_params=modified_params,
        baseline_analyzer=baseline_analyzer,
        settings=settings
    )
    return res


@app.get("/api/root-cause/batch/{batch_id}")
def get_batch_root_cause(batch_id: str):
    """
    Retrieves stored batch by ID and computes complete Root-Cause AI diagnosis.
    """
    batches = fetch_all_batches(search=batch_id, limit=1)
    if not batches:
        raise HTTPException(status_code=404, detail=f"Batch '{batch_id}' not found.")
    b = batches[0]
    settings = get_settings()
    diag = root_cause_engine.diagnose_batch(b, baseline_analyzer, settings)
    return {
        "batch": b,
        "diagnosis": diag
    }


# ----------------------------------------------------
# 6. Configuration & Threshold Settings
# ----------------------------------------------------
@app.get("/api/config")
def get_config():
    """Returns current system configuration thresholds."""
    return get_settings()


@app.post("/api/config")
def update_config(new_settings: Dict[str, Any]):
    """Updates system configuration thresholds and recalculates states."""
    update_settings(new_settings)
    refresh_system_state()
    return {"message": "Configuration updated successfully.", "settings": get_settings()}


# ----------------------------------------------------
# 7. Dataset Reset & Re-Seed
# ----------------------------------------------------
@app.post("/api/reset-data")
def reset_sample_data(count: int = Query(1000)):
    """Clears and re-populates the database with fresh realistic sample batches."""
    clear_all_batches()
    raw_samples = generate_sample_batches(total_count=count)
    settings = get_settings()

    # Pre-train baseline
    temp_df = pd.DataFrame(raw_samples)
    baseline_analyzer.set_data(temp_df)
    ml_engine.train(temp_df, maintenance_interval_days=settings.get("maintenance_interval_days", 60))

    processed = []
    for item in raw_samples:
        pred = ml_engine.predict_batch(item, settings)
        item.update(pred)
        processed.append(item)

    save_batches_bulk(processed, duplicate_strategy="keep_latest")
    refresh_system_state()

    return {"message": f"Database successfully reset and re-seeded with {len(processed)} batches."}


# ----------------------------------------------------
# 8. CSV Data Export & Finalized Reports
# ----------------------------------------------------
@app.get("/api/export")
def export_batches_csv():
    """Exports all stored batches as a downloadable CSV file."""
    batches = fetch_all_batches(limit=100000)
    if not batches:
        raise HTTPException(status_code=404, detail="No batches available for export.")

    df = pd.DataFrame(batches)
    cols_to_export = [
        "batch_id", "machine_id", "fabric_type", "operator", "shift",
        "total_production", "production_speed", "waste_quantity", "waste_percentage",
        "machine_age", "last_maintenance_date", "maintenance_age_days",
        "humidity", "temperature", "risk_level", "risk_score", "confidence_score",
        "is_abnormal", "is_valid", "created_at"
    ]
    available_cols = [c for c in cols_to_export if c in df.columns]
    csv_buffer = io.StringIO()
    df[available_cols].to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=textile_production_batches.csv"}
    )


@app.get("/api/report/batch/{batch_id}")
def get_batch_finalized_report(batch_id: str):
    """
    Generates a formal, finalized Quality & Risk Audit Report for a specific production batch.
    Includes full telemetry, baseline comparison, AI risk score, Root-Cause AI diagnostic trace,
    and formal supervisor action protocols.
    """
    batches = fetch_all_batches(search=batch_id, limit=1)
    if not batches:
        raise HTTPException(status_code=404, detail=f"Batch '{batch_id}' not found.")

    b = batches[0]
    m_id = b.get("machine_id", "M01")
    f_type = b.get("fabric_type", "Cotton")

    m_thresh = baseline_analyzer.get_machine_thresholds(m_id)
    f_thresh = baseline_analyzer.get_fabric_thresholds(f_type)
    factory = baseline_analyzer.factory_stats or {"mean_waste_pct": 4.0}
    settings = get_settings()

    waste_pct = float(b.get("waste_percentage", 0.0))
    prod_qty = float(b.get("total_production", 0.0))
    waste_qty = float(b.get("waste_quantity", 0.0))
    risk_level = b.get("risk_level", "NORMAL")
    risk_score = float(b.get("risk_score", 0.0))
    conf_score = float(b.get("confidence_score", 95.0))

    # Executive Evaluation Summary
    if risk_level == "HIGH RISK":
        status_statement = "CRITICAL DEFECT RISK: Significant abnormal waste or multi-factor operating stress identified. Immediate mitigation and machine inspection required."
    elif risk_level == "WARNING":
        status_statement = "CAUTION ADVISED: Moderate variance from historical baselines or maintenance limit approached. Supervisory monitoring recommended."
    else:
        status_statement = "QUALITY CERTIFIED: Batch telemetry and waste metrics operate within nominal manufacturing tolerances."

    # Compute Root-Cause AI deep-dive for report
    root_cause_diag = root_cause_engine.diagnose_batch(b, baseline_analyzer, settings)

    report = {
        "report_id": f"REP-TX-{b.get('id', 1):05d}",
        "timestamp": b.get("created_at", "N/A"),
        "plant_facility": "TexPulse Manufacturing Plant - Weaving & Finishing Unit 1",
        "compliance_standard": "ISO 9001:2015 / ISO 14001 Textile Waste Minimization Protocol",
        "batch_telemetry": {
            "batch_id": b.get("batch_id"),
            "machine_id": m_id,
            "fabric_type": f_type,
            "operator": b.get("operator"),
            "shift": b.get("shift"),
            "total_production_kg": prod_qty,
            "waste_quantity_kg": waste_qty,
            "waste_percentage": waste_pct,
            "production_speed_rpm": float(b.get("production_speed", 0.0)),
            "machine_age_years": float(b.get("machine_age", 0.0)),
            "last_maintenance_date": b.get("last_maintenance_date") or "N/A",
            "maintenance_age_days": int(b.get("maintenance_age_days", 0)),
            "humidity_rh": b.get("humidity"),
            "humidity_imputed": bool(b.get("humidity_imputed", False)),
            "temperature_c": float(b.get("temperature", 25.0))
        },
        "risk_assessment": {
            "classification": risk_level,
            "risk_score": risk_score,
            "confidence_score": conf_score,
            "is_abnormal_anomaly": bool(b.get("is_abnormal", False)),
            "status_statement": status_statement
        },
        "baseline_comparison": {
            "machine_historical_avg_waste_pct": round(m_thresh["mean"], 2),
            "fabric_historical_avg_waste_pct": round(f_thresh["mean"], 2),
            "factory_benchmark_avg_waste_pct": round(factory.get("mean_waste_pct", 4.0), 2),
            "waste_variance_from_machine_baseline_pct": round(waste_pct - m_thresh["mean"], 2),
            "speed_variance_from_safe_fabric_rpm": round(float(b.get("production_speed", 800)) - f_thresh.get("mean_speed", 800), 1)
        },
        "explainability_reasons": b.get("reasons", []),
        "actionable_recommendations": b.get("actions", []),
        "reason_cards": root_cause_diag.get("reason_cards", []),
        "preventive_solutions": root_cause_diag.get("preventive_solutions", []),
        "recommended_action_plan": root_cause_diag.get("recommended_action_plan", {}),
        "root_cause_analysis": root_cause_diag,
        "audit_signoff": {
            "audited_by": "TexPulse AI Intelligent Production Engine v1.0",
            "supervisor_approval": "Pending Plant Supervisor Review",
            "maintenance_lead_sign": "Pending Maintenance Lead Sign-off"
        }
    }
    return report


@app.get("/api/report/plant-summary")
def get_plant_executive_report():
    """Generates an executive plant-wide summary audit report."""
    batches = fetch_all_batches(limit=100000)
    settings = get_settings()

    valid_batches = [b for b in batches if b.get("is_valid", 1) == 1]
    total_count = len(valid_batches)
    normal_count = sum(1 for b in valid_batches if b.get("risk_level") == "NORMAL")
    warning_count = sum(1 for b in valid_batches if b.get("risk_level") == "WARNING")
    high_risk_count = sum(1 for b in valid_batches if b.get("risk_level") == "HIGH RISK")
    abnormal_count = sum(1 for b in valid_batches if b.get("is_abnormal", 0) == 1)

    total_prod = sum(b.get("total_production", 0) for b in valid_batches)
    total_waste = sum(b.get("waste_quantity", 0) for b in valid_batches)
    avg_waste = (total_waste / max(1, total_prod)) * 100.0 if total_prod > 0 else 0.0

    machine_analysis = baseline_analyzer.get_machine_analysis(settings.get("maintenance_interval_days", 60))
    fabric_analysis = baseline_analyzer.get_fabric_analysis()
    maint_analysis = baseline_analyzer.get_maintenance_analysis(settings.get("maintenance_interval_days", 60))
    
    # Generate plant-wide root-cause insights
    df = fetch_valid_batches_df()
    rca = root_cause_engine.generate_plant_root_cause_analysis(df, baseline_analyzer, settings)

    return {
        "report_title": "TexPulse Plant-Wide Production Waste & Risk Audit Report",
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_production_volume_kg": round(total_prod, 1),
        "total_waste_generated_kg": round(total_waste, 1),
        "plant_wide_waste_percentage": round(avg_waste, 2),
        "total_batches_audited": total_count,
        "normal_batches_count": normal_count,
        "warning_batches_count": warning_count,
        "high_risk_batches_count": high_risk_count,
        "abnormal_anomaly_count": abnormal_count,
        "overdue_machines_count": len(maint_analysis.get("overdue", [])),
        "overdue_machines": maint_analysis.get("overdue", []),
        "high_risk_fabrics": fabric_analysis.get("high_risk_fabrics", []),
        "highest_waste_machine": machine_analysis.get("highest_waste_machine"),
        "lowest_waste_machine": machine_analysis.get("lowest_waste_machine"),
        "plant_root_cause_analysis": rca
    }


# ----------------------------------------------------
# 9. Serve Static Frontend Files
# ----------------------------------------------------
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    """Serves the main frontend dashboard index.html."""
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>Textile Production Waste Prediction System</h1><p>Frontend files are being assembled.</p>")
