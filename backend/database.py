"""
Database access and schema management for Textile Waste Prediction System.
Uses SQLite for robust, zero-configuration persistence.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textile_production.db")

DEFAULT_SETTINGS = {
    "risk_threshold_warning": 40.0,
    "risk_threshold_high": 70.0,
    "maintenance_interval_days": 60,
    "iqr_multiplier": 1.5,
    "z_score_threshold": 2.0,
    "duplicate_strategy": "keep_latest"
}


def get_db_connection() -> sqlite3.Connection:
    """Creates a database connection with dictionary-like row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and default settings if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Batches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE NOT NULL,
            machine_id TEXT NOT NULL,
            fabric_type TEXT NOT NULL,
            operator TEXT NOT NULL,
            shift TEXT NOT NULL,
            total_production REAL NOT NULL,
            production_speed REAL NOT NULL,
            waste_quantity REAL NOT NULL,
            waste_percentage REAL NOT NULL,
            machine_age REAL NOT NULL,
            last_maintenance_date TEXT,
            maintenance_age_days INTEGER,
            humidity REAL,
            humidity_imputed INTEGER DEFAULT 0,
            temperature REAL,
            risk_level TEXT NOT NULL,
            risk_score REAL NOT NULL,
            confidence_score REAL NOT NULL,
            is_abnormal INTEGER DEFAULT 0,
            reasons_json TEXT,
            actions_json TEXT,
            is_valid INTEGER DEFAULT 1,
            validation_error TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Audit Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT
        )
    """)

    # Insert default settings if not existing
    for key, val in DEFAULT_SETTINGS.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))

    # Create indices for fast querying and filtering
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_machine ON batches(machine_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_fabric ON batches(fabric_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_shift ON batches(shift)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_operator ON batches(operator)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_risk ON batches(risk_level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch_created ON batches(created_at)")

    conn.commit()
    conn.close()


def get_settings() -> Dict[str, Any]:
    """Retrieves all configuration settings parsed into appropriate types."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()

    settings = dict(DEFAULT_SETTINGS)
    for row in rows:
        key = row["key"]
        val_str = row["value"]
        if key in ["risk_threshold_warning", "risk_threshold_high", "iqr_multiplier", "z_score_threshold"]:
            try:
                settings[key] = float(val_str)
            except ValueError:
                pass
        elif key in ["maintenance_interval_days"]:
            try:
                settings[key] = int(val_str)
            except ValueError:
                pass
        else:
            settings[key] = val_str
    return settings


def update_settings(new_settings: Dict[str, Any]):
    """Updates one or more configuration settings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for key, val in new_settings.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))
    conn.commit()
    conn.close()


def save_batch(batch_data: Dict[str, Any], duplicate_strategy: str = "keep_latest") -> bool:
    """
    Saves a single batch record into the database.
    Handles duplicate strategy: 'keep_latest' replaces or updates; 'reject' ignores.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    reasons_str = json.dumps(batch_data.get("reasons", []))
    actions_str = json.dumps(batch_data.get("actions", []))
    created_at = batch_data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    tot_prod = float(batch_data.get("total_production") or 0.0)
    prod_spd = float(batch_data.get("production_speed") or 0.0)
    w_qty = float(batch_data.get("waste_quantity") if batch_data.get("waste_quantity") is not None else (batch_data.get("expected_waste_kg") or 0.0))
    w_pct = float(batch_data.get("waste_percentage") if batch_data.get("waste_percentage") is not None else (batch_data.get("expected_waste_percentage") or 0.0))
    m_age = float(batch_data.get("machine_age") or 0.0)
    maint_d = int(batch_data.get("maintenance_age_days") or 0)
    temp_val = float(batch_data.get("temperature") if batch_data.get("temperature") is not None else 25.0)
    r_score = float(batch_data.get("risk_score") if batch_data.get("risk_score") is not None else 0.0)
    c_score = float(batch_data.get("confidence_score") if batch_data.get("confidence_score") is not None else 100.0)

    record_params = (
        batch_data["batch_id"],
        batch_data["machine_id"],
        batch_data["fabric_type"],
        batch_data["operator"],
        batch_data["shift"],
        tot_prod,
        prod_spd,
        w_qty,
        w_pct,
        m_age,
        batch_data.get("last_maintenance_date"),
        maint_d,
        batch_data.get("humidity"),
        1 if batch_data.get("humidity_imputed") else 0,
        temp_val,
        batch_data.get("risk_level", "NORMAL"),
        r_score,
        c_score,
        1 if batch_data.get("is_abnormal") else 0,
        reasons_str,
        actions_str,
        1 if batch_data.get("is_valid", True) else 0,
        batch_data.get("validation_error"),
        created_at
    )

    if duplicate_strategy == "keep_latest":
        cursor.execute("""
            INSERT OR REPLACE INTO batches (
                batch_id, machine_id, fabric_type, operator, shift,
                total_production, production_speed, waste_quantity, waste_percentage,
                machine_age, last_maintenance_date, maintenance_age_days,
                humidity, humidity_imputed, temperature,
                risk_level, risk_score, confidence_score, is_abnormal,
                reasons_json, actions_json, is_valid, validation_error, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, record_params)
    else:  # reject
        cursor.execute("""
            INSERT OR IGNORE INTO batches (
                batch_id, machine_id, fabric_type, operator, shift,
                total_production, production_speed, waste_quantity, waste_percentage,
                machine_age, last_maintenance_date, maintenance_age_days,
                humidity, humidity_imputed, temperature,
                risk_level, risk_score, confidence_score, is_abnormal,
                reasons_json, actions_json, is_valid, validation_error, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, record_params)

    conn.commit()
    conn.close()
    return True


def save_batches_bulk(batches_list: List[Dict[str, Any]], duplicate_strategy: str = "keep_latest") -> int:
    """Saves multiple batches in a single transaction."""
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0

    verb = "INSERT OR REPLACE" if duplicate_strategy == "keep_latest" else "INSERT OR IGNORE"

    for b in batches_list:
        reasons_str = json.dumps(b.get("reasons", []))
        actions_str = json.dumps(b.get("actions", []))
        created_at = b.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        tot_prod = float(b.get("total_production") or 0.0)
        prod_spd = float(b.get("production_speed") or 0.0)
        w_qty = float(b.get("waste_quantity") if b.get("waste_quantity") is not None else (b.get("expected_waste_kg") or 0.0))
        w_pct = float(b.get("waste_percentage") if b.get("waste_percentage") is not None else (b.get("expected_waste_percentage") or 0.0))
        m_age = float(b.get("machine_age") or 0.0)
        maint_d = int(b.get("maintenance_age_days") or 0)
        temp_val = float(b.get("temperature") if b.get("temperature") is not None else 25.0)
        r_score = float(b.get("risk_score") if b.get("risk_score") is not None else 0.0)
        c_score = float(b.get("confidence_score") if b.get("confidence_score") is not None else 100.0)

        record_params = (
            b["batch_id"],
            b["machine_id"],
            b["fabric_type"],
            b["operator"],
            b["shift"],
            tot_prod,
            prod_spd,
            w_qty,
            w_pct,
            m_age,
            b.get("last_maintenance_date"),
            maint_d,
            b.get("humidity"),
            1 if b.get("humidity_imputed") else 0,
            temp_val,
            b.get("risk_level", "NORMAL"),
            r_score,
            c_score,
            1 if b.get("is_abnormal") else 0,
            reasons_str,
            actions_str,
            1 if b.get("is_valid", True) else 0,
            b.get("validation_error"),
            created_at
        )

        cursor.execute(f"""
            {verb} INTO batches (
                batch_id, machine_id, fabric_type, operator, shift,
                total_production, production_speed, waste_quantity, waste_percentage,
                machine_age, last_maintenance_date, maintenance_age_days,
                humidity, humidity_imputed, temperature,
                risk_level, risk_score, confidence_score, is_abnormal,
                reasons_json, actions_json, is_valid, validation_error, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, record_params)
        count += 1

    conn.commit()
    conn.close()
    return count


def rescore_batches_in_db(scored_batches: List[Dict[str, Any]]) -> int:
    """Updates risk_level, risk_score, confidence_score, is_abnormal, reasons, and actions for existing batches in DB."""
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    for b in scored_batches:
        reasons_str = json.dumps(b.get("reasons", []))
        actions_str = json.dumps(b.get("actions", []))
        cursor.execute("""
            UPDATE batches
            SET risk_level = ?,
                risk_score = ?,
                confidence_score = ?,
                is_abnormal = ?,
                reasons_json = ?,
                actions_json = ?
            WHERE batch_id = ?
        """, (
            b.get("risk_level", "NORMAL"),
            float(b.get("risk_score", 0.0)),
            float(b.get("confidence_score", 100.0)),
            1 if b.get("is_abnormal") else 0,
            reasons_str,
            actions_str,
            b["batch_id"]
        ))
        count += 1
    conn.commit()
    conn.close()
    return count


def fetch_all_batches(
    machine: Optional[str] = None,
    fabric: Optional[str] = None,
    shift: Optional[str] = None,
    operator: Optional[str] = None,
    risk: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 5000,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Fetches batches with flexible filtering options."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM batches WHERE 1=1"
    params = []

    if machine and machine != "ALL":
        query += " AND machine_id = ?"
        params.append(machine)
    if fabric and fabric != "ALL":
        query += " AND fabric_type = ?"
        params.append(fabric)
    if shift and shift != "ALL":
        query += " AND shift = ?"
        params.append(shift)
    if operator and operator != "ALL":
        query += " AND operator = ?"
        params.append(operator)
    if risk and risk != "ALL":
        query += " AND UPPER(risk_level) = UPPER(?)"
        params.append(risk)
    if search:
        query += " AND (batch_id LIKE ? OR machine_id LIKE ? OR fabric_type LIKE ? OR operator LIKE ?)"
        s_param = f"%{search}%"
        params.extend([s_param, s_param, s_param, s_param])

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        try:
            d["reasons"] = json.loads(d.get("reasons_json") or "[]")
        except Exception:
            d["reasons"] = []
        try:
            d["actions"] = json.loads(d.get("actions_json") or "[]")
        except Exception:
            d["actions"] = []
        results.append(d)
    return results


def fetch_valid_batches_df():
    """Returns a pandas DataFrame of all valid production batches for analytics and modeling."""
    import pandas as pd
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM batches WHERE is_valid = 1", conn)
    conn.close()
    return df


def clear_all_batches():
    """Clears all batch records and resets auto-increment."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batches")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='batches'")
    conn.commit()
    conn.close()
