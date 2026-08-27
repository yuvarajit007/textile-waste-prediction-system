"""
Realistic synthetic textile production dataset generator.
Generates 1,000+ realistic production batches with authentic physical distributions,
maintenance schedules, environmental conditions, and explicit edge cases.
"""

import random
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from backend.data_validator import validate_and_clean_batch

FABRICS = {
    "Cotton": {"base_waste": 3.8, "waste_std": 1.1, "base_speed": 850, "speed_std": 50, "qty_range": (800, 2500)},
    "Polyester": {"base_waste": 2.9, "waste_std": 0.8, "base_speed": 950, "speed_std": 60, "qty_range": (1000, 3000)},
    "Silk": {"base_waste": 5.2, "waste_std": 1.4, "base_speed": 650, "speed_std": 40, "qty_range": (300, 1200)},
    "Denim": {"base_waste": 4.1, "waste_std": 1.0, "base_speed": 780, "speed_std": 45, "qty_range": (1500, 5000)},
    "Wool": {"base_waste": 4.8, "waste_std": 1.3, "base_speed": 700, "speed_std": 45, "qty_range": (400, 1500)},
    "Linen": {"base_waste": 4.5, "waste_std": 1.2, "base_speed": 720, "speed_std": 40, "qty_range": (500, 1800)},
    "Rayon": {"base_waste": 3.4, "waste_std": 0.9, "base_speed": 880, "speed_std": 50, "qty_range": (800, 2200)},
}

MACHINES = {
    "M01": {"age": 8.5, "base_maint_interval": 60, "last_maint_days_ago": 18, "efficiency_factor": 1.08},
    "M02": {"age": 6.2, "base_maint_interval": 60, "last_maint_days_ago": 85, "efficiency_factor": 1.25}, # Overdue maintenance!
    "M03": {"age": 9.0, "base_maint_interval": 60, "last_maint_days_ago": 42, "efficiency_factor": 1.12},
    "M04": {"age": 3.5, "base_maint_interval": 60, "last_maint_days_ago": 12, "efficiency_factor": 0.95},
    "M05": {"age": 4.1, "base_maint_interval": 60, "last_maint_days_ago": 92, "efficiency_factor": 1.30}, # Overdue maintenance!
    "M06": {"age": 2.8, "base_maint_interval": 60, "last_maint_days_ago": 25, "efficiency_factor": 0.92},
    "M07": {"age": 5.0, "base_maint_interval": 60, "last_maint_days_ago": 52, "efficiency_factor": 1.05},
    "M08": {"age": 1.5, "base_maint_interval": 60, "last_maint_days_ago": 8, "efficiency_factor": 0.88},
    "M09": {"age": 0.8, "base_maint_interval": 60, "last_maint_days_ago": 15, "efficiency_factor": 0.85},
    "M10": {"age": 0.1, "base_maint_interval": 60, "last_maint_days_ago": 3, "efficiency_factor": 0.90}, # Brand new machine!
}

OPERATORS = [
    "John Doe", "Priya Sharma", "Carlos Rossi", "Fatima Al-Mansoor",
    "Wei Zhang", "Elena Rostova", "David Kim", "Marcus Vance"
]

SHIFTS = ["Morning", "Afternoon", "Night"]


def generate_sample_batches(total_count: int = 1000) -> List[Dict[str, Any]]:
    """Generates 1,000+ realistic batches with historical dates, trends, and edge cases."""
    random.seed(42)
    today = date.today()
    batches = []

    # Exclude M10 from bulk history so M10 remains a "New Machine" test case with only 2 batches
    regular_machines = [m for m in MACHINES.keys() if m != "M10"]

    start_date = today - timedelta(days=120)

    for i in range(1, total_count - 10):
        batch_id = f"TB-{1000 + i}"
        
        # Date of production
        days_offset = random.randint(0, 119)
        prod_date = start_date + timedelta(days=days_offset)

        machine_id = random.choice(regular_machines)
        m_info = MACHINES[machine_id]

        fabric_name = random.choice(list(FABRICS.keys()))
        f_info = FABRICS[fabric_name]

        operator = random.choice(OPERATORS)
        shift = random.choice(SHIFTS)

        # Shift effects: Night shift has slight variations in ambient temp/speed
        shift_waste_mod = 1.05 if shift == "Night" else (0.98 if shift == "Morning" else 1.0)

        # Production speed
        speed = max(400, int(random.gauss(f_info["base_speed"], f_info["speed_std"])))
        speed_factor = 1.0
        if speed > f_info["base_speed"] * 1.15:
            speed_factor = 1.25  # Abnormally high speed induces higher waste

        # Production Quantity
        qty_min, qty_max = f_info["qty_range"]
        total_prod = round(random.uniform(qty_min, qty_max), 0)

        # Last maintenance date relative to production date
        # Machine maintenance occurs every ~60 days, with some overdue periods
        maint_days_ago = m_info["last_maint_days_ago"] + (today - prod_date).days % 70
        last_maint_date = prod_date - timedelta(days=maint_days_ago % 100)
        maint_age_days = (prod_date - last_maint_date).days

        # Maintenance effect on waste
        maint_factor = 1.35 if maint_age_days > 60 else (1.1 if maint_age_days > 45 else 0.95)

        # Environmental conditions
        humidity = round(random.gauss(56, 7), 1)
        if random.random() < 0.04:  # 4% missing humidity edge case in historical data
            humidity = None

        temp = round(random.gauss(25.5, 3.0), 1)

        # Waste percentage calculation
        base_w = f_info["base_waste"] * m_info["efficiency_factor"] * shift_waste_mod * speed_factor * maint_factor
        simulated_waste_pct = max(0.5, random.gauss(base_w, f_info["waste_std"]))

        # Occasional abnormal anomaly spike (5% probability)
        if random.random() < 0.05:
            simulated_waste_pct = simulated_waste_pct * random.uniform(1.8, 2.6)

        # Waste quantity in kg
        waste_qty = round((simulated_waste_pct / 100.0) * total_prod, 1)

        raw_item = {
            "batch_id": batch_id,
            "machine_id": machine_id,
            "fabric_type": fabric_name,
            "operator": operator,
            "shift": shift,
            "total_production": total_prod,
            "production_speed": speed,
            "waste_quantity": waste_qty,
            "machine_age": m_info["age"],
            "last_maintenance_date": last_maint_date.strftime("%Y-%m-%d"),
            "humidity": humidity,
            "temperature": temp,
            "created_at": prod_date.strftime("%Y-%m-%d %H:%M:%S")
        }
        cleaned = validate_and_clean_batch(raw_item, reference_date=today)
        batches.append(cleaned)

    # ----------------------------------------------------
    # Explicit Named Edge Cases for Direct Testing / Demo
    # ----------------------------------------------------
    
    # 1. High Production + High Absolute Waste (NORMAL RISK)
    # Example: 5000 kg production with 100 kg waste = 2.0% waste (Safe)
    edge_case_1 = {
        "batch_id": "TEST-HIGH-PROD-LOW-PCT",
        "machine_id": "M08",
        "fabric_type": "Denim",
        "operator": "David Kim",
        "shift": "Morning",
        "total_production": 5000.0,
        "production_speed": 780.0,
        "waste_quantity": 100.0,  # 2.0% waste
        "machine_age": 1.5,
        "last_maintenance_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
        "humidity": 58.0,
        "temperature": 24.5,
        "created_at": today.strftime("%Y-%m-%d 08:30:00")
    }
    batches.append(validate_and_clean_batch(edge_case_1, reference_date=today))

    # 2. Low Production + High Waste Percentage (HIGH RISK)
    # Example: 100 kg production with 30 kg waste = 30.0% waste (Extreme Risk)
    edge_case_2 = {
        "batch_id": "TEST-LOW-PROD-HIGH-PCT",
        "machine_id": "M02",
        "fabric_type": "Silk",
        "operator": "Priya Sharma",
        "shift": "Night",
        "total_production": 100.0,
        "production_speed": 660.0,
        "waste_quantity": 30.0,  # 30.0% waste
        "machine_age": 6.2,
        "last_maintenance_date": (today - timedelta(days=88)).strftime("%Y-%m-%d"),
        "humidity": 38.0,
        "temperature": 29.0,
        "created_at": today.strftime("%Y-%m-%d 09:15:00")
    }
    batches.append(validate_and_clean_batch(edge_case_2, reference_date=today))

    # 3. New Machine (M10) with minimal history
    edge_case_3 = {
        "batch_id": "TEST-NEW-MACHINE-M10",
        "machine_id": "M10",
        "fabric_type": "Cotton",
        "operator": "Wei Zhang",
        "shift": "Morning",
        "total_production": 1200.0,
        "production_speed": 850.0,
        "waste_quantity": 44.0,  # 3.67% waste
        "machine_age": 0.1,
        "last_maintenance_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
        "humidity": 55.0,
        "temperature": 25.0,
        "created_at": today.strftime("%Y-%m-%d 10:00:00")
    }
    batches.append(validate_and_clean_batch(edge_case_3, reference_date=today))

    # 4. Missing Humidity Edge Case
    edge_case_4 = {
        "batch_id": "TEST-MISSING-HUMIDITY",
        "machine_id": "M04",
        "fabric_type": "Polyester",
        "operator": "Carlos Rossi",
        "shift": "Afternoon",
        "total_production": 1800.0,
        "production_speed": 920.0,
        "waste_quantity": 52.0,  # 2.89% waste
        "machine_age": 3.5,
        "last_maintenance_date": (today - timedelta(days=20)).strftime("%Y-%m-%d"),
        "humidity": None,  # Missing!
        "temperature": 26.0,
        "created_at": today.strftime("%Y-%m-%d 11:30:00")
    }
    batches.append(validate_and_clean_batch(edge_case_4, reference_date=today))

    # 5. Overdue Maintenance Edge Case (M02 overdue by 95 days)
    edge_case_5 = {
        "batch_id": "TEST-MAINTENANCE-OVERDUE",
        "machine_id": "M02",
        "fabric_type": "Wool",
        "operator": "Elena Rostova",
        "shift": "Night",
        "total_production": 900.0,
        "production_speed": 720.0,
        "waste_quantity": 88.0,  # 9.78% waste
        "machine_age": 6.2,
        "last_maintenance_date": (today - timedelta(days=95)).strftime("%Y-%m-%d"),
        "humidity": 52.0,
        "temperature": 27.0,
        "created_at": today.strftime("%Y-%m-%d 12:45:00")
    }
    batches.append(validate_and_clean_batch(edge_case_5, reference_date=today))

    # 6. Abnormally High Speed Stress
    edge_case_6 = {
        "batch_id": "TEST-HIGH-SPEED-STRESS",
        "machine_id": "M03",
        "fabric_type": "Silk",
        "operator": "Marcus Vance",
        "shift": "Afternoon",
        "total_production": 800.0,
        "production_speed": 980.0,  # Silk limit is ~650, running at 980!
        "waste_quantity": 96.0,  # 12.0% waste
        "machine_age": 9.0,
        "last_maintenance_date": (today - timedelta(days=40)).strftime("%Y-%m-%d"),
        "humidity": 42.0,
        "temperature": 31.0,
        "created_at": today.strftime("%Y-%m-%d 14:00:00")
    }
    batches.append(validate_and_clean_batch(edge_case_6, reference_date=today))

    # 7. Zero Production Invalid Record Test Case
    edge_case_7 = {
        "batch_id": "TEST-ZERO-PRODUCTION-INVALID",
        "machine_id": "M06",
        "fabric_type": "Cotton",
        "operator": "John Doe",
        "shift": "Morning",
        "total_production": 0.0,  # Zero production!
        "production_speed": 0.0,
        "waste_quantity": 15.0,
        "machine_age": 2.8,
        "last_maintenance_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
        "humidity": 55.0,
        "temperature": 25.0,
        "created_at": today.strftime("%Y-%m-%d 15:20:00")
    }
    batches.append(validate_and_clean_batch(edge_case_7, reference_date=today))

    return batches
