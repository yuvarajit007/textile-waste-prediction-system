"""
Data validation and preprocessing module for Textile Production Waste Prediction.
Handles all critical edge cases:
- Division-by-zero prevention (Zero Production)
- Missing humidity imputation and tagging
- Maintenance age calculation from last maintenance date
- Data type conversion, range sanity checks, and duplicate detection
"""

import math
from datetime import datetime, date
from typing import Dict, Any, Tuple, Optional, List

DEFAULT_AMBIENT_HUMIDITY = 55.0  # Industry standard standard relative humidity for spinning/weaving
DEFAULT_AMBIENT_TEMP = 26.0

def parse_date(date_str: Any) -> Optional[date]:
    """Tries multiple date formats to parse last maintenance date."""
    if not date_str or str(date_str).strip() == "" or str(date_str).lower() in ["none", "nan", "null"]:
        return None
    date_str = str(date_str).strip()
    # Try ISO YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    return None


def calculate_maintenance_age(last_maintenance: Any, reference_date: Optional[date] = None) -> Tuple[int, Optional[str]]:
    """
    Calculates maintenance age in days: (reference_date - last_maintenance_date).
    If date is missing, returns a default heuristic based on typical maintenance cycle (e.g. 45 days).
    """
    if reference_date is None:
        reference_date = date.today()
        
    parsed = parse_date(last_maintenance)
    if parsed:
        diff_days = max(0, (reference_date - parsed).days)
        return diff_days, parsed.strftime("%Y-%m-%d")
    else:
        return 45, None  # Default average baseline when unrecorded


def validate_and_clean_batch(raw: Dict[str, Any], reference_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Validates a single batch input, calculates derived metrics (Waste %, Maintenance Age),
    and flags edge cases (zero production, missing humidity, range warnings).
    """
    cleaned: Dict[str, Any] = {}
    
    # Helper to look up key from multiple aliases case-insensitively
    def get_val(*keys):
        for k in keys:
            if k in raw and raw[k] is not None:
                return raw[k]
            k_lower = k.lower()
            for rk in raw:
                if rk.lower() == k_lower and raw[rk] is not None:
                    return raw[rk]
        return None

    # 1. Batch ID
    batch_id = str(get_val("batch_id", "Batch ID", "batchId", "batch", "Batch") or "").strip()
    if not batch_id:
        batch_id = f"BATCH-{int(datetime.now().timestamp() * 1000)}"
    cleaned["batch_id"] = batch_id

    # 2. Machine ID
    machine_id = str(get_val("machine_id", "Machine ID", "machineId", "machine", "Machine") or "M01").strip().upper()
    cleaned["machine_id"] = machine_id

    # 3. Fabric Type
    fabric = str(get_val("fabric_type", "Fabric Type", "fabricType", "fabric", "Fabric") or "Cotton").strip()
    cleaned["fabric_type"] = fabric.title()

    # 4. Operator
    operator = str(get_val("operator", "Operator", "operator_name", "Worker") or "Operator A").strip().title()
    cleaned["operator"] = operator

    # 5. Shift
    shift = str(get_val("shift", "Shift", "shift_type") or "Morning").strip().title()
    if shift not in ["Morning", "Afternoon", "Night"]:
        shift = "Morning"
    cleaned["shift"] = shift

    # 6. Total Production Quantity
    prod_raw = get_val("total_production", "Total Production Quantity", "total_production_quantity", "production_quantity", "totalProduction", "production", "Production", "total_prod")
    try:
        prod_val = float(prod_raw if prod_raw is not None and str(prod_raw).strip() != "" else 0)
    except (ValueError, TypeError):
        prod_val = 0.0
    cleaned["total_production"] = prod_val

    # 7. Waste Quantity (Optional for pre-production expected waste predictions)
    waste_raw = get_val("waste_quantity", "Waste Quantity", "waste_qty", "wasteQuantity", "waste", "Waste")
    has_actual_waste = False
    waste_val = None
    if waste_raw is not None and str(waste_raw).strip() != "" and str(waste_raw).lower() not in ["none", "nan", "null"]:
        try:
            waste_val = max(0.0, float(waste_raw))
            has_actual_waste = True
        except (ValueError, TypeError):
            waste_val = None
            has_actual_waste = False

    cleaned["has_actual_waste"] = has_actual_waste
    cleaned["waste_quantity"] = waste_val if has_actual_waste else 0.0

    # 8. Edge Case: Zero or Negative Production Quantity
    if prod_val <= 0:
        cleaned["is_valid"] = False
        cleaned["validation_error"] = "Production quantity must be greater than 0 kg."
        cleaned["waste_percentage"] = 0.0
    else:
        cleaned["is_valid"] = True
        cleaned["validation_error"] = None
        if has_actual_waste and waste_val is not None:
            # Strict formula requirement: (Waste Quantity / Total Production Quantity) * 100
            cleaned["waste_percentage"] = round((waste_val / prod_val) * 100.0, 2)
        else:
            cleaned["waste_percentage"] = None

    # 9. Production Speed
    speed_raw = get_val("production_speed", "Production Speed", "productionSpeed", "speed", "Speed", "rpm")
    try:
        speed_val = float(speed_raw if speed_raw is not None else 800)
    except (ValueError, TypeError):
        speed_val = 800.0
    cleaned["production_speed"] = max(0.0, speed_val)

    # 10. Machine Age
    age_raw = get_val("machine_age", "Machine Age", "machineAge", "age", "Age")
    try:
        age_val = float(age_raw if age_raw is not None else 3.0)
    except (ValueError, TypeError):
        age_val = 3.0
    cleaned["machine_age"] = max(0.0, age_val)

    # 11. Last Maintenance Date & Maintenance Age Calculation
    raw_maint_date = get_val("last_maintenance_date", "Last Maintenance Date", "lastMaintenanceDate", "maintenance_date", "last_maintenance")
    maint_age_days, formatted_maint_date = calculate_maintenance_age(raw_maint_date, reference_date)
    cleaned["last_maintenance_date"] = formatted_maint_date
    cleaned["maintenance_age_days"] = maint_age_days

    # 12. Humidity (Edge Case: Missing Humidity)
    raw_hum = get_val("humidity", "Humidity", "rh", "relative_humidity")
    if raw_hum is None or str(raw_hum).strip() == "" or str(raw_hum).lower() in ["none", "nan", "null"]:
        cleaned["humidity"] = DEFAULT_AMBIENT_HUMIDITY
        cleaned["humidity_imputed"] = True
    else:
        try:
            h_val = float(raw_hum)
            if math.isnan(h_val) or h_val < 0 or h_val > 100:
                cleaned["humidity"] = DEFAULT_AMBIENT_HUMIDITY
                cleaned["humidity_imputed"] = True
            else:
                cleaned["humidity"] = round(h_val, 1)
                cleaned["humidity_imputed"] = False
        except (ValueError, TypeError):
            cleaned["humidity"] = DEFAULT_AMBIENT_HUMIDITY
            cleaned["humidity_imputed"] = True

    # 13. Temperature
    raw_temp = get_val("temperature", "Temperature", "temp", "Temp")
    try:
        t_val = float(raw_temp) if raw_temp is not None else DEFAULT_AMBIENT_TEMP
        if math.isnan(t_val) or t_val < -10 or t_val > 60:
            t_val = DEFAULT_AMBIENT_TEMP
    except (ValueError, TypeError):
        t_val = DEFAULT_AMBIENT_TEMP
    cleaned["temperature"] = round(t_val, 1)

    return cleaned


def validate_batch_collection(raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Validates a list of batch records, tracks duplicates, zero production rows, and missing values.
    Returns (cleaned_records, validation_summary).
    """
    cleaned_list = []
    seen_ids = set()
    duplicate_count = 0
    invalid_prod_count = 0
    imputed_humidity_count = 0

    for item in raw_records:
        cleaned = validate_and_clean_batch(item)
        bid = cleaned["batch_id"]

        if bid in seen_ids:
            duplicate_count += 1
        seen_ids.add(bid)

        if not cleaned["is_valid"]:
            invalid_prod_count += 1
        if cleaned["humidity_imputed"]:
            imputed_humidity_count += 1

        cleaned_list.append(cleaned)

    summary = {
        "total_records": len(raw_records),
        "valid_records": len(raw_records) - invalid_prod_count,
        "duplicate_ids_found": duplicate_count,
        "zero_or_negative_production_count": invalid_prod_count,
        "imputed_humidity_count": imputed_humidity_count
    }
    return cleaned_list, summary
