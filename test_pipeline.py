"""
Comprehensive test suite for Textile Production Waste Prediction and Risk Classification System.
Verifies:
1. Exact formula calculation: Waste % = (Waste / Total Production) * 100
2. Edge Case: High Production + High Absolute Waste (5,000 kg prod, 100 kg waste = 2.0% -> NORMAL)
3. Edge Case: Low Production + Very High Waste % (100 kg prod, 30 kg waste = 30.0% -> HIGH RISK)
4. Edge Case: Zero Production (0 kg prod -> is_valid=False, no ZeroDivisionError)
5. Edge Case: Missing Humidity (Graceful imputation at 55.0%, marked in output)
6. Edge Case: New Machine (Fallback to baselines, reduced confidence)
7. Edge Case: Maintenance Overdue (Days calculated, overdue penalty applied)
8. Edge Case: Abnormally High Production Speed (Safety penalty applied)
9. Duplicate Batch handling
10. Multi-dimensional analytics calculation (Machine, Fabric, Shift, Operator, Maintenance)
"""

import sys
import os
import io
import pandas as pd
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.data_validator import validate_and_clean_batch, validate_batch_collection, calculate_maintenance_age
from backend.baseline_analyzer import BaselineAnalyzer
from backend.ml_engine import TextileRiskMLEngine
from backend.sample_data import generate_sample_batches


def run_all_tests():
    print("=" * 70)
    print("STARTING TEXTILE WASTE PREDICTION SYSTEM VALIDATION TESTS")
    print("=" * 70)

    today = date.today()

    # ----------------------------------------------------
    # TEST 1: Formula Calculation Verification
    # ----------------------------------------------------
    print("\n[TEST 1] Verifying Core Waste Percentage Formula...")
    sample_1 = {
        "batch_id": "T1-FORMULA",
        "machine_id": "M01",
        "fabric_type": "Cotton",
        "total_production": 1000.0,
        "waste_quantity": 50.0,
        "production_speed": 800.0
    }
    clean_1 = validate_and_clean_batch(sample_1)
    assert clean_1["waste_percentage"] == 5.0, f"Expected 5.0%, got {clean_1['waste_percentage']}%"
    print(f"  [PASS] Formula check: 50 kg / 1000 kg * 100 = {clean_1['waste_percentage']}%")

    # ----------------------------------------------------
    # TEST 2: Edge Case: Zero Production (Division by Zero Guard)
    # ----------------------------------------------------
    print("\n[TEST 2] Verifying Zero Production Edge Case...")
    sample_zero = {
        "batch_id": "T2-ZERO",
        "machine_id": "M01",
        "fabric_type": "Cotton",
        "total_production": 0.0,
        "waste_quantity": 10.0,
        "production_speed": 0.0
    }
    clean_zero = validate_and_clean_batch(sample_zero)
    assert clean_zero["is_valid"] is False, "Zero production should be marked is_valid = False"
    assert clean_zero["waste_percentage"] == 0.0, "Zero production should not raise ZeroDivisionError"
    print(f"  [PASS] Zero production caught cleanly: is_valid={clean_zero['is_valid']}, error='{clean_zero['validation_error']}'")

    # ----------------------------------------------------
    # TEST 3: Edge Case: Missing Humidity Handling
    # ----------------------------------------------------
    print("\n[TEST 3] Verifying Missing Humidity Imputation...")
    sample_no_hum = {
        "batch_id": "T3-NO-HUM",
        "machine_id": "M04",
        "fabric_type": "Polyester",
        "total_production": 1200.0,
        "waste_quantity": 36.0,
        "humidity": None
    }
    clean_no_hum = validate_and_clean_batch(sample_no_hum)
    assert clean_no_hum["humidity"] == 55.0, f"Expected default humidity 55.0%, got {clean_no_hum['humidity']}"
    assert clean_no_hum["humidity_imputed"] is True, "Expected humidity_imputed = True"
    print(f"  [PASS] Missing humidity imputed to {clean_no_hum['humidity']}% with imputed flag = {clean_no_hum['humidity_imputed']}")

    # ----------------------------------------------------
    # TEST 4: Maintenance Age Calculation
    # ----------------------------------------------------
    print("\n[TEST 4] Verifying Maintenance Age Calculation...")
    past_date = today - timedelta(days=75)
    days_ago, fmt_date = calculate_maintenance_age(past_date.strftime("%Y-%m-%d"), reference_date=today)
    assert days_ago == 75, f"Expected 75 days, got {days_ago}"
    print(f"  [PASS] Maintenance age correctly computed: {days_ago} days since {fmt_date}")

    # ----------------------------------------------------
    # TEST 5: Baseline Analyzer & Multi-Dimensional Analytics
    # ----------------------------------------------------
    print("\n[TEST 5] Generating Sample Batches & Verifying Baseline Analytics...")
    samples = generate_sample_batches(total_count=500)
    df_samples = pd.DataFrame(samples)
    
    analyzer = BaselineAnalyzer(df_samples)
    assert analyzer.factory_stats["total_batches"] > 0, "Factory baseline must have total_batches > 0"
    print(f"  [PASS] Factory Baseline: Mean Waste = {analyzer.factory_stats['mean_waste_pct']:.2f}%, IQR Upper = {analyzer.factory_stats['iqr_upper_bound']:.2f}%")

    machine_analytics = analyzer.get_machine_analysis(maintenance_interval_days=60)
    assert len(machine_analytics["machines"]) > 0, "Machine analytics list must not be empty"
    print(f"  [PASS] Machine Analytics: {len(machine_analytics['machines'])} machines tracked.")
    print(f"    - Highest Waste Machine: {machine_analytics['highest_waste_machine']['machine_id']} ({machine_analytics['highest_waste_machine']['average_waste_pct']}%)")
    print(f"    - Lowest Waste Machine: {machine_analytics['lowest_waste_machine']['machine_id']} ({machine_analytics['lowest_waste_machine']['average_waste_pct']}%)")
    print(f"    - Age vs Waste Correlation: {machine_analytics['age_waste_correlation']}")

    fabric_analytics = analyzer.get_fabric_analysis()
    assert len(fabric_analytics["fabrics"]) > 0, "Fabric analytics list must not be empty"
    print(f"  [PASS] Fabric Analytics: {len(fabric_analytics['fabrics'])} fabrics tracked. High-Risk fabrics: {[f['fabric_type'] for f in fabric_analytics['high_risk_fabrics']]}")

    shift_analytics = analyzer.get_shift_analysis()
    assert len(shift_analytics["shifts"]) == 3, f"Expected 3 shifts, got {len(shift_analytics['shifts'])}"
    print(f"  [PASS] Shift Analytics: {', '.join(s['shift'] for s in shift_analytics['shifts'])}")

    op_analytics = analyzer.get_operator_analysis()
    assert len(op_analytics["operators"]) > 0, "Operator analytics list must not be empty"
    print(f"  [PASS] Operator Analytics: {len(op_analytics['operators'])} operators tracked with constructive condition stats.")

    maint_analytics = analyzer.get_maintenance_analysis(maintenance_interval_days=60)
    print(f"  [PASS] Maintenance Matrix: {len(maint_analytics['recently_maintained'])} Good, {len(maint_analytics['approaching'])} Approaching, {len(maint_analytics['overdue'])} Overdue.")

    # ----------------------------------------------------
    # TEST 6: ML Model Training & Hybrid Risk Engine
    # ----------------------------------------------------
    print("\n[TEST 6] Training ML Engine & Evaluating Predictions...")
    ml_engine = TextileRiskMLEngine(analyzer)
    ml_engine.train(df_samples, maintenance_interval_days=60)
    assert ml_engine.is_trained is True, "ML engine should be successfully trained"
    print("  [PASS] Random Forest Classifier and Isolation Forest Anomaly Detector successfully trained.")

    # ----------------------------------------------------
    # TEST 7: Hidden Edge Case 1: High Production + High Absolute Waste (2.0% -> NORMAL)
    # ----------------------------------------------------
    print("\n[TEST 7] Testing Edge Case: High Production + High Absolute Waste...")
    edge_1 = {
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
        "temperature": 24.5
    }
    clean_edge_1 = validate_and_clean_batch(edge_1)
    pred_1 = ml_engine.predict_batch(clean_edge_1)
    print(f"  Input: 5,000 kg Prod, 100 kg Waste -> Waste %: {clean_edge_1['waste_percentage']}%")
    print(f"  Prediction: {pred_1['risk_level']} (Risk Score: {pred_1['risk_score']}/100)")
    assert pred_1["risk_level"] == "NORMAL", f"Expected NORMAL risk for 2.0% waste, got {pred_1['risk_level']}"
    print("  [PASS] Correctly classified as NORMAL despite high absolute waste (100 kg).")

    # ----------------------------------------------------
    # TEST 8: Hidden Edge Case 2: Low Production + Very High Waste % (30.0% -> HIGH RISK)
    # ----------------------------------------------------
    print("\n[TEST 8] Testing Edge Case: Low Production + High Waste %...")
    edge_2 = {
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
        "temperature": 29.0
    }
    clean_edge_2 = validate_and_clean_batch(edge_2)
    pred_2 = ml_engine.predict_batch(clean_edge_2)
    print(f"  Input: 100 kg Prod, 30 kg Waste -> Waste %: {clean_edge_2['waste_percentage']}%")
    print(f"  Prediction: {pred_2['risk_level']} (Risk Score: {pred_2['risk_score']}/100, Abnormal: {pred_2['is_abnormal']})")
    assert pred_2["risk_level"] == "HIGH RISK", f"Expected HIGH RISK for 30.0% waste, got {pred_2['risk_level']}"
    print("  [PASS] Correctly classified as HIGH RISK for 30.0% waste.")

    # ----------------------------------------------------
    # TEST 9: Edge Case: New Machine (M10 with no historical batches)
    # ----------------------------------------------------
    print("\n[TEST 9] Testing Edge Case: New Machine (Limited History)...")
    edge_new_machine = {
        "batch_id": "TEST-NEW-MACHINE",
        "machine_id": "M99-BRAND-NEW",
        "fabric_type": "Cotton",
        "operator": "Wei Zhang",
        "shift": "Morning",
        "total_production": 1000.0,
        "production_speed": 850.0,
        "waste_quantity": 40.0,
        "machine_age": 0.1,
        "last_maintenance_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
        "humidity": 55.0,
        "temperature": 25.0
    }
    clean_new_m = validate_and_clean_batch(edge_new_machine)
    pred_new_m = ml_engine.predict_batch(clean_new_m)
    print(f"  Machine: {clean_new_m['machine_id']}")
    print(f"  Prediction: {pred_new_m['risk_level']} (Confidence: {pred_new_m['confidence_score']}%, New Machine Tag: {pred_new_m['is_new_machine']})")
    assert pred_new_m["is_new_machine"] is True, "Expected is_new_machine = True"
    assert pred_new_m["confidence_score"] < 90.0, "Expected lower confidence score for new machine"
    print(f"  Explanation Note: {pred_new_m['reasons'][0]}")
    print("  [PASS] Correctly applied fallback baseline and lowered confidence score.")

    # ----------------------------------------------------
    # TEST 10: Edge Case: Maintenance Overdue Risk Escalation
    # ----------------------------------------------------
    print("\n[TEST 10] Testing Edge Case: Maintenance Overdue Escalation...")
    edge_overdue = {
        "batch_id": "TEST-OVERDUE-MAINT",
        "machine_id": "M02",
        "fabric_type": "Wool",
        "operator": "Elena Rostova",
        "shift": "Night",
        "total_production": 1000.0,
        "production_speed": 720.0,
        "waste_quantity": 90.0,
        "machine_age": 6.2,
        "last_maintenance_date": (today - timedelta(days=95)).strftime("%Y-%m-%d"),
        "humidity": 52.0,
        "temperature": 26.0
    }
    clean_overdue = validate_and_clean_batch(edge_overdue)
    pred_overdue = ml_engine.predict_batch(clean_overdue)
    print(f"  Days since maintenance: {clean_overdue['maintenance_age_days']} days (Threshold: 60)")
    print(f"  Risk Score: {pred_overdue['risk_score']}/100 ({pred_overdue['risk_level']})")
    assert any("overdue" in r.lower() for r in pred_overdue["reasons"]), "Expected overdue maintenance in reasons"
    print(f"  Overdue Reason: {[r for r in pred_overdue['reasons'] if 'overdue' in r.lower()][0]}")
    print("  [PASS] Correctly identified overdue maintenance and included action recommendations.")

    # ----------------------------------------------------
    # TEST 11: Duplicate Batch Collection Handling
    # ----------------------------------------------------
    print("\n[TEST 11] Testing Duplicate Batch Collection Validation...")
    records_with_dup = [
        {"batch_id": "DUP-001", "machine_id": "M01", "fabric_type": "Cotton", "total_production": 1000.0, "waste_quantity": 40.0},
        {"batch_id": "DUP-001", "machine_id": "M01", "fabric_type": "Cotton", "total_production": 1000.0, "waste_quantity": 45.0},
        {"batch_id": "DUP-002", "machine_id": "M02", "fabric_type": "Silk", "total_production": 800.0, "waste_quantity": 30.0},
    ]
    cleaned_col, summary_col = validate_batch_collection(records_with_dup)
    assert summary_col["duplicate_ids_found"] == 1, f"Expected 1 duplicate, got {summary_col['duplicate_ids_found']}"
    print(f"  [PASS] Duplicate detection check passed: {summary_col['duplicate_ids_found']} duplicates identified.")

    # ----------------------------------------------------
    # TEST 12: Root-Cause AI Multi-Factor Attribution & Primary Cause
    # ----------------------------------------------------
    print("\n[TEST 12] Testing Root-Cause AI Multi-Factor Attribution & Playbook...")
    from backend.root_cause_ai import RootCauseAIEngine
    rc_engine = RootCauseAIEngine()

    high_speed_batch = {
        "batch_id": "TEST-RCA-SPEED",
        "machine_id": "M01",
        "fabric_type": "Silk",
        "operator": "Priya Sharma",
        "shift": "Morning",
        "total_production": 1000.0,
        "production_speed": 980.0,  # Far above silk safe speed (~650 RPM)
        "waste_quantity": 85.0,
        "waste_percentage": 8.5,
        "machine_age": 2.0,
        "maintenance_age_days": 20,
        "humidity": 55.0,
        "temperature": 24.0,
        "is_valid": True
    }
    diag = rc_engine.diagnose_batch(high_speed_batch, analyzer)
    assert diag["status"] == "SUCCESS", "Expected diagnostic status SUCCESS"
    assert diag["primary_cause"]["factor_key"] == "operational_speed", f"Expected speed primary cause, got {diag['primary_cause']['factor_key']}"
    assert len(diag["prescriptive_playbook"]) > 0, "Expected prescriptive playbook steps"
    print(f"  Primary Root Cause: {diag['primary_cause']['title']} (Attribution: {diag['primary_cause']['attribution_pct']}%)")
    print(f"  Playbook Action: {diag['prescriptive_playbook'][0]['action']} (Est Savings: {diag['prescriptive_playbook'][0]['estimated_waste_reduction_pct']}%)")
    print("  [PASS] Root-Cause AI successfully attributed speed stress as primary driver and produced actionable playbook.")

    # ----------------------------------------------------
    # TEST 13: Root-Cause AI Counterfactual "What-If" Simulation
    # ----------------------------------------------------
    print("\n[TEST 13] Testing Root-Cause AI Counterfactual 'What-If' Simulation...")
    sim_res = rc_engine.simulate_counterfactual(
        batch=high_speed_batch,
        modified_params={
            "production_speed": 660.0,  # Safe speed for silk
            "humidity": 60.0,
            "maintenance_age_days": 10,
            "temperature": 24.0
        },
        baseline_analyzer=analyzer
    )
    assert sim_res["simulated_risk_score"] < diag["current_risk_score"], "Simulated risk score should decrease"
    assert sim_res["waste_reduction_pct"] > 0, "Waste reduction % should be positive"
    assert sim_res["estimated_kg_saved"] > 0, "Estimated kg saved should be positive"
    print(f"  Initial Risk: {sim_res['initial_risk_score']:.1f} -> Simulated Risk: {sim_res['simulated_risk_score']:.1f}")
    print(f"  Initial Waste: {sim_res['initial_waste_percentage']:.2f}% -> Simulated Waste: {sim_res['simulated_waste_percentage']:.2f}%")
    print(f"  Estimated Savings: {sim_res['waste_reduction_pct']:.2f}% ({sim_res['estimated_kg_saved']} kg)")
    print("  [PASS] Counterfactual simulation correctly modeled risk reduction and estimated savings.")

    # ----------------------------------------------------
    # TEST 14: Plant-Wide Root-Cause Pareto & Aggregations
    # ----------------------------------------------------
    print("\n[TEST 14] Testing Plant-Wide Root-Cause Pareto & Category Analysis...")
    plant_rca = rc_engine.generate_plant_root_cause_analysis(df_samples, analyzer)
    assert plant_rca["total_batches_analyzed"] > 0, "Expected non-zero analyzed batches"
    assert len(plant_rca["pareto_causes"]) > 0, "Expected pareto causes"
    assert len(plant_rca["category_distribution"]) > 0, "Expected category distributions"
    print(f"  Top Failure Mode: {plant_rca['pareto_causes'][0]['title']} ({plant_rca['pareto_causes'][0]['count']} occurrences, {plant_rca['pareto_causes'][0]['percentage_of_failures']}%)")
    print(f"  Total Potential Waste Saved across plant: {plant_rca['total_potential_waste_kg_saved']} kg")
    print("  [PASS] Plant-Wide Pareto and strategic recommendation engine verified.")

    # ----------------------------------------------------
    # TEST 15: Evidence-Based Reason Cards Verification
    # ----------------------------------------------------
    print("\n[TEST 15] Verifying Evidence-Based Reason Cards Generation...")
    high_waste_stress_batch = {
        "batch_id": "T15-HIGH-STRESS",
        "machine_id": "M02",
        "fabric_type": "Silk",
        "shift": "Night",
        "operator": "Priya Sharma",
        "total_production": 800.0,
        "waste_quantity": 72.0,  # 9.0% waste
        "production_speed": 940.0,  # Benchmark is ~650 rpm
        "machine_age": 6.5,
        "last_maintenance_date": (today - timedelta(days=55)).strftime("%Y-%m-%d"),  # 55 days
        "humidity": 38.0,  # Dry
        "temperature": 31.0
    }
    clean_15 = validate_and_clean_batch(high_waste_stress_batch)
    pred_15 = ml_engine.predict_batch(clean_15)
    reason_cards = pred_15.get("reason_cards", [])
    assert len(reason_cards) >= 3, f"Expected at least 3 reason cards for multi-factor batch, got {len(reason_cards)}"
    
    # Verify card structure
    for card in reason_cards:
        assert "id" in card and "title" in card and "severity" in card
        assert "observed" in card and "benchmark" in card and "impact" in card
        assert "icon" in card and "badge_color" in card
    
    speed_card = next((c for c in reason_cards if c["id"] == "production_speed"), None)
    assert speed_card is not None, f"Expected production_speed reason card, got {[c['id'] for c in reason_cards]}"
    assert "940" in speed_card["observed"], f"Observed speed should be in card: {speed_card['observed']}"
    assert "RPM" in speed_card["benchmark"] and "Silk" in speed_card["benchmark"], f"Benchmark speed should be in card: {speed_card['benchmark']}"
    print(f"  [PASS] Speed Card generated: Observed='{speed_card['observed']}' vs Benchmark='{speed_card['benchmark']}' | Severity='{speed_card['severity']}'")

    # ----------------------------------------------------
    # TEST 16: 1-to-1 Preventive Solutions Mapping
    # ----------------------------------------------------
    print("\n[TEST 16] Verifying 1-to-1 Reason -> Solution Preventive Mapping...")
    solutions = pred_15.get("preventive_solutions", [])
    assert len(solutions) >= 3, f"Expected at least 3 solutions, got {len(solutions)}"
    for sol in solutions:
        assert "reason_id" in sol and "title" in sol and "solution" in sol and "priority" in sol
    
    speed_sol = next((s for s in solutions if s["reason_id"] == "production_speed"), None)
    assert speed_sol is not None, "Expected production_speed preventive solution"
    assert "Reduce production speed" in speed_sol["solution"] or "RPM" in speed_sol["solution"]
    print(f"  [PASS] Solution mapped: '{speed_sol['title']}' -> '{speed_sol['solution']}' (Priority: {speed_sol['priority']})")

    # ----------------------------------------------------
    # TEST 17: Tailored Recommended Action Plan (Inspect -> Adjust -> Maintain -> Monitor)
    # ----------------------------------------------------
    print("\n[TEST 17] Verifying Recommended Action Plan Protocol...")
    action_plan = pred_15.get("recommended_action_plan", {})
    assert "summary" in action_plan and "protocol" in action_plan and "steps" in action_plan
    assert action_plan["protocol"] == "Inspect -> Adjust -> Maintain -> Monitor"
    assert len(action_plan["steps"]) >= 4, f"Expected at least 4 action steps, got {len(action_plan['steps'])}"
    print(f"  Protocol: {action_plan['protocol']}")
    print(f"  Summary: {action_plan['summary']}")
    for idx, st in enumerate(action_plan["steps"], 1):
        print(f"    Step {idx}: {st}")
    print("  [PASS] Recommended Action Plan fully conforms to Inspect -> Adjust -> Maintain -> Monitor protocol.")

    # ----------------------------------------------------
    # TEST 18: Missing Humidity Reason Card (No False Alarm)
    # ----------------------------------------------------
    print("\n[TEST 18] Verifying Missing Humidity Reason Card...")
    missing_hum_batch = {
        "batch_id": "T18-MISSING-HUM",
        "machine_id": "M01",
        "fabric_type": "Cotton",
        "shift": "Morning",
        "operator": "David Kim",
        "total_production": 1200.0,
        "waste_quantity": 40.0,
        "production_speed": 820.0,
        "machine_age": 2.0,
        "last_maintenance_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
        "humidity": None,  # Missing!
        "temperature": 24.0
    }
    clean_18 = validate_and_clean_batch(missing_hum_batch)
    pred_18 = ml_engine.predict_batch(clean_18)
    hum_card = next((c for c in pred_18.get("reason_cards", []) if c["id"] == "missing_humidity"), None)
    assert hum_card is not None, "Expected missing_humidity card"
    assert "unavailable" in hum_card["impact"].lower() or "missing" in hum_card["observed"].lower()
    print(f"  [PASS] Missing humidity handled with transparent explainability: {hum_card['impact']}")

    # ----------------------------------------------------
    # TEST 19: Waste Causes and Prevention Summary Table
    # ----------------------------------------------------
    print("\n[TEST 19] Verifying Waste Causes and Prevention Overview Summary Aggregator...")
    from backend.root_cause_ai import get_waste_causes_prevention_summary
    from backend.database import get_settings
    
    settings = get_settings()
    summary_rows = get_waste_causes_prevention_summary(df_samples, analyzer, settings)
    assert isinstance(summary_rows, list) and len(summary_rows) > 0, f"Expected non-empty list of summary causes, got {summary_rows}"
    top_cause = summary_rows[0]
    assert "cause_name" in top_cause and "category" in top_cause and "affected_batches" in top_cause
    assert "avg_waste_pct" in top_cause and "preventive_action" in top_cause and "risk_level" in top_cause
    print(f"  Top Aggregated Cause: {top_cause['cause_name']} | Category: {top_cause['category']} | Affected Batches: {top_cause['affected_batches']} | Avg Waste: {top_cause['avg_waste_pct']}%")
    print(f"  Preventive Remedy: {top_cause['preventive_action']}")
    print("  [PASS] Waste causes and prevention summary aggregator validated.")

    # ----------------------------------------------------
    # TEST 22: Continuous Regression Model Training & Metrics
    # ----------------------------------------------------
    print("\n[TEST 22] Verifying Continuous Regression Model Training & Evaluation Metrics...")
    metrics = ml_engine.regression_metrics
    print(f"  Regressor Metrics: MAE={metrics.get('mae')}, RMSE={metrics.get('rmse')}, R2={metrics.get('r2')}, Samples={metrics.get('sample_count')}")
    assert ml_engine.regressor is not None, "Regression model is None"
    assert "mae" in metrics and "rmse" in metrics and "r2" in metrics, "Missing regression metrics"
    print("  [PASS] Continuous RandomForestRegressor trained with valid MAE, RMSE, and R2 metrics.")

    # ----------------------------------------------------
    # TEST 23: Pre-Production Expected Waste Forecast (No actual waste required)
    # ----------------------------------------------------
    print("\n[TEST 23] Verifying Pre-Production Expected Waste Forecast (KG & Good Production)...")
    pre_prod_batch = {
        "batch_id": "T23-EXP-PREPROD",
        "machine_id": "M03",
        "fabric_type": "Cotton",
        "shift": "Night",
        "operator": "Marcus Vance",
        "total_production": 1000.0,
        "production_speed": 880.0,
        "machine_age": 8.0,
        "last_maintenance_date": (today - timedelta(days=200)).strftime("%Y-%m-%d"),
        "humidity": 75.0,
        "temperature": 34.0
    }
    clean_23 = validate_and_clean_batch(pre_prod_batch)
    exp_23 = ml_engine.predict_expected_waste(clean_23)
    
    assert exp_23["is_valid"] is True
    assert exp_23["expected_waste_percentage"] is not None
    assert exp_23["expected_waste_kg"] is not None
    assert exp_23["expected_good_production_kg"] is not None
    
    # Formula check: Expected Waste (kg) = Production Quantity * Expected Waste % / 100
    expected_calc_kg = round(1000.0 * (exp_23["expected_waste_percentage"] / 100.0), 2)
    assert abs(exp_23["expected_waste_kg"] - expected_calc_kg) < 0.05, f"Expected {expected_calc_kg}, got {exp_23['expected_waste_kg']}"
    
    # Formula check: Expected Good Production = Total Production - Expected Waste
    good_calc_kg = round(1000.0 - exp_23["expected_waste_kg"], 2)
    assert abs(exp_23["expected_good_production_kg"] - good_calc_kg) < 0.05, f"Expected {good_calc_kg}, got {exp_23['expected_good_production_kg']}"
    
    print(f"  Expected Waste %: {exp_23['expected_waste_percentage']:.2f}%")
    print(f"  Expected Waste: {exp_23['expected_waste_kg']:.1f} kg")
    print(f"  Expected Good Production: {exp_23['expected_good_production_kg']:.1f} kg")
    print(f"  Risk Level: {exp_23['risk_level']}")
    print("  [PASS] Expected waste and good production formulas validated strictly.")

    # ----------------------------------------------------
    # TEST 24: Prediction Uncertainty Range (Likely Range % and kg)
    # ----------------------------------------------------
    print("\n[TEST 24] Verifying Prediction Uncertainty Range (Likely Range % and kg)...")
    pct_range = exp_23["likely_range_pct"]
    kg_range = exp_23["likely_range_kg"]
    assert pct_range["min"] < exp_23["expected_waste_percentage"] <= pct_range["max"]
    assert kg_range["min"] < exp_23["expected_waste_kg"] <= kg_range["max"]
    print(f"  Likely Range %: {pct_range['display']}")
    print(f"  Likely Range kg: {kg_range['display']}")
    print("  [PASS] Prediction uncertainty ranges estimated and formatted properly.")

    # ----------------------------------------------------
    # TEST 25: Multi-Level Historical Comparison Matrix
    # ----------------------------------------------------
    print("\n[TEST 25] Verifying Multi-Level Historical Comparison Matrix...")
    comp_25 = exp_23["historical_comparison"]
    assert "factory_average_pct" in comp_25
    assert "machine_average_pct" in comp_25
    assert "fabric_average_pct" in comp_25
    assert "machine_fabric_combination_avg_pct" in comp_25
    assert "shift_average_pct" in comp_25
    assert "comparison_summary" in comp_25
    print(f"  Comparison Summary: {comp_25['comparison_summary']}")
    print(f"  Factory Avg: {comp_25['factory_average_pct']}%, Machine Avg: {comp_25['machine_average_pct']}%, Fabric Avg: {comp_25['fabric_average_pct']}%, Combo: {comp_25['machine_fabric_combination_avg_pct']}%, Shift: {comp_25['shift_average_pct']}%")
    print("  [PASS] Multi-level historical comparison matrix validated.")

    # ----------------------------------------------------
    # TEST 26: Expected vs Actual Waste Comparison (Completed batch)
    # ----------------------------------------------------
    print("\n[TEST 26] Verifying Expected vs Actual Waste Comparison...")
    completed_batch = dict(pre_prod_batch)
    completed_batch["waste_quantity"] = 82.0  # Actual waste entered
    clean_26 = validate_and_clean_batch(completed_batch)
    exp_26 = ml_engine.predict_expected_waste(clean_26)
    eva = exp_26["expected_vs_actual"]
    assert eva is not None, "Expected vs actual dictionary is None"
    assert eva["actual_waste_kg"] == 82.0
    assert abs(eva["difference_kg"] - (82.0 - exp_26["expected_waste_kg"])) < 0.05
    assert abs(eva["absolute_error_kg"] - abs(82.0 - exp_26["expected_waste_kg"])) < 0.05
    assert 0.0 <= eva["prediction_accuracy_pct"] <= 100.0
    print(f"  Expected: {eva['expected_waste_kg']} kg ({eva['expected_waste_pct']}%)")
    print(f"  Actual: {eva['actual_waste_kg']} kg ({eva['actual_waste_pct']}%)")
    print(f"  Difference: {eva['difference_sign']} | Abs Error: {eva['absolute_error_kg']} kg | Accuracy: {eva['prediction_accuracy_pct']}%")
    print("  [PASS] Expected vs Actual comparison metrics validated.")

    # ----------------------------------------------------
    # TEST 27: Edge Cases (Zero Production, Missing Humidity, New Machine)
    # ----------------------------------------------------
    print("\n[TEST 27] Verifying Expected Waste Edge Cases...")
    # Zero production
    zero_batch = dict(pre_prod_batch)
    zero_batch["total_production"] = 0.0
    clean_zero = validate_and_clean_batch(zero_batch)
    exp_zero = ml_engine.predict_expected_waste(clean_zero)
    assert exp_zero["is_valid"] is False
    assert exp_zero["validation_error"] == "Production quantity must be greater than 0 kg."
    assert exp_zero["expected_waste_kg"] is None
    print("  [PASS] Zero production guard returned: 'Production quantity must be greater than 0 kg.' without division error.")

    # Missing humidity
    missing_hum_batch = dict(pre_prod_batch)
    missing_hum_batch["humidity"] = None
    clean_hum = validate_and_clean_batch(missing_hum_batch)
    exp_hum = ml_engine.predict_expected_waste(clean_hum)
    assert any("Humidity unavailable" in r for r in exp_hum["reasons"])
    print("  [PASS] Missing humidity reported: 'Humidity unavailable. Prediction is based on the remaining available parameters.'")

    # New Machine
    new_m_batch = dict(pre_prod_batch)
    new_m_batch["machine_id"] = "M99_NEW"
    clean_new_m = validate_and_clean_batch(new_m_batch)
    exp_new_m = ml_engine.predict_expected_waste(clean_new_m)
    assert exp_new_m["is_new_machine"] is True
    assert any("Limited historical data available" in r for r in exp_new_m["reasons"])
    print("  [PASS] New machine fallback reported: 'Limited historical data available for this machine. Prediction is based on similar machines and overall historical patterns.'")

    # ----------------------------------------------------
    # TEST 28: CSV / Excel Upload Validation & Ingestion
    # ----------------------------------------------------
    print("\n[TEST 28] Verifying CSV / Excel File Upload & Ingestion Pipeline...")
    from backend.database import save_batches_bulk

    csv_data = """Batch ID,Machine ID,Fabric Type,Operator,Shift,Total Production Quantity,Production Speed,Waste Quantity,Machine Age,Last Maintenance Date,Humidity,Temperature
BATCH-UP-01,M01,Cotton,David Kim,Morning,1000,820,40,4.0,2026-06-01,55,24
BATCH-UP-02,M02,Silk,Priya Sharma,Night,800,920,,6.0,2026-04-01,,30
BATCH-UP-03,M03,Denim,Carlos Rossi,Afternoon,0,750,0,2.0,2026-07-01,60,25
"""
    df_up = pd.read_csv(io.StringIO(csv_data))
    col_mapping = {col: str(col).strip().lower().replace(" ", "_").replace("-", "_") for col in df_up.columns}
    df_up = df_up.rename(columns=col_mapping)
    raw_recs = df_up.to_dict(orient="records")
    cleaned_recs, val_summary = validate_batch_collection(raw_recs)
    
    assert val_summary["total_records"] == 3
    assert val_summary["valid_records"] == 2
    assert val_summary["zero_or_negative_production_count"] == 1
    assert val_summary["imputed_humidity_count"] == 1

    proc_list = []
    for item in cleaned_recs:
        pred_item = ml_engine.predict_batch(item, settings)
        item.update(pred_item)
        proc_list.append(item)

    saved_up = save_batches_bulk(proc_list, duplicate_strategy="keep_latest")
    assert saved_up == 3
    print(f"  Validation Summary: Total={val_summary['total_records']}, Valid={val_summary['valid_records']}, Missing Hum={val_summary['imputed_humidity_count']}, Zero Prod={val_summary['zero_or_negative_production_count']}")
    print(f"  [PASS] CSV file parsing, batch validation, predictive scoring, and database ingestion passed successfully.")

    print("\n" + "=" * 70)
    print("ALL 28 TESTS (DATA VALIDATION, ML, EXPECTED WASTE, RCA, REASONS, CSV UPLOAD) PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()


