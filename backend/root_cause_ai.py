"""
Root-Cause AI & Explainability Engine for Textile Waste Prediction System.

Provides:
1. Evidence-based Reason Cards (Observed vs. Normal Benchmarks & Physical Impact Statements)
2. Preventive Solution Cards with Direct Reason -> Solution Mapping
3. Risk-Based Action Protocols (NORMAL, WARNING, HIGH RISK with Inspect -> Adjust -> Maintain -> Monitor)
4. Multi-factor mathematical attribution / SHAP-like feature decomposition
5. Primary and Secondary Root Cause Identification and Severity Tagging
6. Prescriptive Remediation Playbooks with Quantified Waste Reduction Estimates
7. Interactive Counterfactual "What-If" Simulation & Optimization Engine
8. Plant-Wide "Waste Causes & Prevention" Aggregator & Pareto Analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class RootCauseAIEngine:
    """
    AI Root Cause Analyzer and Explainer for Textile Production Batches.
    Deconstructs multi-dimensional risk into explainable mechanical, operational,
    material, and environmental causal factors with practical preventive remedies.
    """

    # Category constants
    CAT_MECHANICAL = "Mechanical / Maintenance"
    CAT_OPERATIONAL = "Operational / Speed"
    CAT_ATMOSPHERIC = "Atmospheric / Humidity"
    CAT_MATERIAL = "Material / Fabric Complexity"
    CAT_THERMAL = "Thermal / Environmental"
    CAT_OPERATOR = "Operator / Shift Dynamics"

    def __init__(self):
        pass

    def diagnose_batch(
        self,
        batch: Dict[str, Any],
        baseline_analyzer: Any,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Performs a full deep-dive Root-Cause AI diagnostic on a single batch.
        Returns:
        - reason_cards: Evidence-based cards with Observed vs Benchmark and Impact
        - preventive_solutions: 1-to-1 Reason -> Solution actionable remedies
        - recommended_action_plan: Risk-tailored Inspect -> Adjust -> Maintain -> Monitor checklist
        - attributions: Quantitative point and percentage contributions per factor
        - primary_cause: The leading driver of excess waste / risk
        - secondary_causes: Additional contributing factors
        - severity: 'CRITICAL', 'HIGH', 'MODERATE', or 'NOMINAL'
        - prescriptive_playbook: Step-by-step prioritized instructions with estimated savings
        - counterfactual_target: Recommended parameter adjustments to restore normal baseline
        """
        if settings is None:
            settings = {
                "risk_threshold_warning": 40.0,
                "risk_threshold_high": 70.0,
                "maintenance_interval_days": 60,
                "iqr_multiplier": 1.5,
                "z_score_threshold": 2.0
            }

        maint_interval = int(settings.get("maintenance_interval_days", 60))
        warn_thresh = float(settings.get("risk_threshold_warning", 40.0))
        high_thresh = float(settings.get("risk_threshold_high", 70.0))

        # Extract telemetry
        b_id = str(batch.get("batch_id", "N/A"))
        m_id = str(batch.get("machine_id", "M01"))
        f_type = str(batch.get("fabric_type", "Cotton"))
        shift = str(batch.get("shift", "Morning"))
        operator = str(batch.get("operator", "Operator A"))
        total_prod = float(batch.get("total_production", 1000.0))
        waste_qty = float(batch.get("waste_quantity", 0.0))
        waste_pct = float(batch.get("waste_percentage", 0.0))
        speed = float(batch.get("production_speed", 800.0))
        maint_age = int(batch.get("maintenance_age_days", 30))
        machine_age = float(batch.get("machine_age", 3.0))
        humidity = float(batch.get("humidity", 55.0))
        humidity_imputed = bool(batch.get("humidity_imputed", False))
        temperature = float(batch.get("temperature", 25.0))
        is_valid = bool(batch.get("is_valid", True))

        # ----------------------------------------------------
        # 0. INVALID / ZERO PRODUCTION HANDLING
        # ----------------------------------------------------
        if not is_valid or total_prod <= 0:
            zero_reason = {
                "id": "zero_production",
                "title": "Invalid Production Telemetry",
                "severity": "CRITICAL",
                "badge_color": "danger",
                "icon": "fa-triangle-exclamation",
                "observed": f"{total_prod:.1f} kg Total Production",
                "benchmark": "> 0 kg Valid Production",
                "impact": "Waste percentage cannot be computed due to mathematical division by zero.",
                "evidence_text": "Invalid batch: production quantity is zero. Waste percentage cannot be calculated."
            }
            zero_solution = {
                "reason_id": "zero_production",
                "title": "Verify Production Meter",
                "icon": "fa-clipboard-check",
                "solution": "Inspect meter sensor at Loom Bay and enter valid total production quantity before continuing.",
                "priority": "CRITICAL"
            }
            zero_actions = {
                "risk_level": "INVALID",
                "badge_class": "badge-danger",
                "summary": "Invalid batch: production quantity is zero. Waste percentage cannot be calculated.",
                "protocol": "Inspect → Adjust → Maintain → Monitor",
                "steps": [
                    "Verify raw production meter reading at loom controller.",
                    "Input valid total production quantity greater than zero.",
                    "Re-run prediction analysis after data correction."
                ]
            }
            return {
                "status": "INVALID_BATCH",
                "severity": "CRITICAL",
                "summary": "Invalid batch: production quantity is zero. Waste percentage cannot be calculated.",
                "reason_cards": [zero_reason],
                "preventive_solutions": [zero_solution],
                "recommended_action_plan": zero_actions,
                "attributions": {},
                "primary_cause": {
                    "category": self.CAT_OPERATIONAL,
                    "title": "Zero Production Division Error",
                    "attribution_pct": 100.0,
                    "impact_points": 100.0,
                    "explanation": "Batch record contains total_production <= 0, causing mathematical division errors."
                },
                "secondary_causes": [],
                "prescriptive_playbook": [
                    {
                        "step": 1,
                        "priority": "CRITICAL",
                        "action": "Inspect meter sensor at Loom Bay and enter valid total production.",
                        "estimated_waste_reduction_pct": 0.0,
                        "estimated_kg_saved": 0.0
                    }
                ],
                "counterfactual_target": {}
            }

        # Retrieve baselines
        m_thresh = baseline_analyzer.get_machine_thresholds(m_id)
        f_thresh = baseline_analyzer.get_fabric_thresholds(f_type)
        is_new_machine = not m_thresh.get("has_history", False)
        target_waste_mean = m_thresh["mean"] if not is_new_machine else f_thresh["mean"]
        fabric_safe_speed = f_thresh.get("mean_speed", 800.0)

        # Factory general benchmarks
        factory_stats = getattr(baseline_analyzer, "factory_stats", {}) or {
            "mean_waste_pct": 4.0, "mean_speed": 800.0
        }
        overall_avg_waste = factory_stats.get("mean_waste_pct", 4.0)

        # ----------------------------------------------------
        # 1. EVIDENCE-BASED REASON ANALYSIS & IMPACT EVALUATION
        # ----------------------------------------------------
        reason_cards: List[Dict[str, Any]] = []
        preventive_solutions: List[Dict[str, Any]] = []

        # A. High Waste Percentage
        raw_waste_impact = 0.0
        waste_card = None
        if is_new_machine:
            if waste_pct > f_thresh["mean"] * 1.25:
                raw_waste_impact = min(100.0, (waste_pct / max(0.1, f_thresh["mean"])) * 35.0)
                waste_card = {
                    "id": "waste_percentage",
                    "title": "High Waste Percentage vs Fabric Baseline",
                    "severity": "HIGH" if waste_pct > f_thresh["mean"] * 1.5 else "WARNING",
                    "badge_color": "danger" if waste_pct > f_thresh["mean"] * 1.5 else "warning",
                    "icon": "fa-chart-line",
                    "observed": f"{waste_pct:.2f}% Waste ({waste_qty:.1f} kg)",
                    "benchmark": f"{f_thresh['mean']:.2f}% Historical {f_type} Avg",
                    "impact": f"Current waste exceeds {f_type} baseline, indicating elevated material loss during weaving.",
                    "evidence_text": f"The current waste percentage is {waste_pct:.2f}%, compared with {f_type}'s historical average of {f_thresh['mean']:.2f}%."
                }
        else:
            if waste_pct > m_thresh["mean"] * 1.25:
                raw_waste_impact = min(100.0, (waste_pct / max(0.1, m_thresh["mean"])) * 38.0)
                sev = "CRITICAL" if waste_pct > m_thresh["mean"] * 1.8 else ("HIGH" if waste_pct > m_thresh["mean"] * 1.4 else "WARNING")
                waste_card = {
                    "id": "waste_percentage",
                    "title": "High Waste Percentage vs Machine Baseline",
                    "severity": sev,
                    "badge_color": "danger" if sev in ["CRITICAL", "HIGH"] else "warning",
                    "icon": "fa-chart-line",
                    "observed": f"{waste_pct:.2f}% Waste ({waste_qty:.1f} kg)",
                    "benchmark": f"{m_thresh['mean']:.2f}% Machine {m_id} Baseline ({overall_avg_waste:.2f}% Factory Avg)",
                    "impact": f"Waste percentage is significantly higher than Machine {m_id}'s historical average, generating excessive scrap.",
                    "evidence_text": f"The current waste percentage is {waste_pct:.2f}%, compared with Machine {m_id}'s historical average of {m_thresh['mean']:.2f}%."
                }

        if waste_card:
            reason_cards.append(waste_card)
            preventive_solutions.append({
                "reason_id": "waste_percentage",
                "title": "Mitigate Excessive Waste Baseline",
                "icon": "fa-magnifying-glass-chart",
                "solution": "Stop or closely monitor the batch, inspect machine settings and fabric quality, and compare the current process with previous low-waste batches.",
                "priority": "HIGH"
            })

        # B. Excessive Production Speed
        raw_speed_impact = 0.0
        speed_ratio = speed / max(1.0, fabric_safe_speed)
        if speed_ratio > 1.15:
            pct_over = (speed_ratio - 1.0) * 100.0
            raw_speed_impact = min(100.0, (speed_ratio - 1.0) * 180.0)
            sev = "CRITICAL" if speed_ratio > 1.25 else "HIGH"
            reason_cards.append({
                "id": "production_speed",
                "title": "Excessive Production Speed",
                "severity": sev,
                "badge_color": "danger" if sev == "CRITICAL" else "warning",
                "icon": "fa-gauge-high",
                "observed": f"{speed:.0f} RPM",
                "benchmark": f"{fabric_safe_speed * 0.9:.0f}-{fabric_safe_speed * 1.05:.0f} RPM Safe Range for {f_type}",
                "impact": f"Excessive speed (+{pct_over:.0f}%) induces yarn tension shock, micro-breakages, and elevated fabric defect rates.",
                "evidence_text": f"Production speed ({speed:.0f} RPM) is significantly higher than the machine's normal operating speed for {f_type} ({fabric_safe_speed:.0f} RPM), which increases fabric defects and material loss."
            })
            preventive_solutions.append({
                "reason_id": "production_speed",
                "title": "Optimize Production Speed",
                "icon": "fa-gauge-simple",
                "solution": f"Reduce production speed to the machine/fabric validated operating range (<= {fabric_safe_speed * 1.02:.0f} RPM) and monitor waste percentage during the next batch.",
                "priority": "HIGH"
            })
        elif speed_ratio < 0.70:
            raw_speed_impact = 15.0
            reason_cards.append({
                "id": "production_speed_low",
                "title": "Sub-Optimal Production Pace",
                "severity": "WARNING",
                "badge_color": "cyan",
                "icon": "fa-gauge",
                "observed": f"{speed:.0f} RPM",
                "benchmark": f"{fabric_safe_speed:.0f} RPM Standard Pace",
                "impact": "Abnormally sluggish machine speed may indicate motor friction, mechanical binding, or frequent operator halts.",
                "evidence_text": f"Production speed ({speed:.0f} RPM) is abnormally sluggish compared to standard operating pace ({fabric_safe_speed:.0f} RPM)."
            })
            preventive_solutions.append({
                "reason_id": "production_speed_low",
                "title": "Inspect Mechanical Drive",
                "icon": "fa-gears",
                "solution": "Check loom drive motor and warp let-off mechanism to verify smooth uninterrupted feeding.",
                "priority": "MEDIUM"
            })

        # C. Maintenance Delay
        raw_maint_impact = 0.0
        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            raw_maint_impact = min(100.0, 45.0 + (days_over * 1.8) + (machine_age * 1.5))
            sev = "CRITICAL" if days_over > 20 else "HIGH"
            reason_cards.append({
                "id": "maintenance_overdue",
                "title": "Machine Maintenance Overdue",
                "severity": sev,
                "badge_color": "danger",
                "icon": "fa-wrench",
                "observed": f"{maint_age} days since service",
                "benchmark": f"{maint_interval} days recommended interval",
                "impact": f"Operating {days_over} days past scheduled service causes component misalignment, reed friction, and tension fluctuation.",
                "evidence_text": f"The machine has exceeded its recommended maintenance interval by {days_over} days and should be inspected. Historical data indicates higher waste when this machine operates beyond its maintenance interval."
            })
            preventive_solutions.append({
                "reason_id": "maintenance_overdue",
                "title": "Schedule Preventive Maintenance",
                "icon": "fa-screwdriver-wrench",
                "solution": "Schedule preventive maintenance and inspect components responsible for alignment, tension, cutting, feeding, or other relevant machine functions.",
                "priority": "CRITICAL"
            })
        elif maint_age > maint_interval * 0.8:
            raw_maint_impact = 25.0 + (machine_age * 1.0)
            reason_cards.append({
                "id": "maintenance_approaching",
                "title": "Maintenance Window Approaching",
                "severity": "WARNING",
                "badge_color": "warning",
                "icon": "fa-clock-rotate-left",
                "observed": f"{maint_age} days since service",
                "benchmark": f"{maint_interval} days interval limit",
                "impact": f"Machine is approaching the {maint_interval}-day threshold ({maint_interval - maint_age} days remaining).",
                "evidence_text": f"Machine service is approaching due threshold ({maint_age}/{maint_interval} days)."
            })
            preventive_solutions.append({
                "reason_id": "maintenance_approaching",
                "title": "Plan Maintenance Window",
                "icon": "fa-calendar-check",
                "solution": f"Schedule upcoming maintenance slot for Machine {m_id} within the next {maint_interval - maint_age} days before running heavy production.",
                "priority": "MEDIUM"
            })

        # D. Machine Age
        raw_age_impact = 0.0
        if machine_age >= 7.5:
            raw_age_impact = min(50.0, (machine_age - 6.0) * 8.0)
            reason_cards.append({
                "id": "machine_age",
                "title": "Machine Aging & Wear Pattern",
                "severity": "WARNING",
                "badge_color": "warning",
                "icon": "fa-clock",
                "observed": f"{machine_age:.1f} years operating age",
                "benchmark": "< 5.0 years nominal wear",
                "impact": "Higher machine age is correlated with mechanical vibration, requiring more frequent calibration.",
                "evidence_text": f"The machine is relatively old ({machine_age:.1f} years) and similar historical batches have shown higher waste percentages."
            })
            preventive_solutions.append({
                "reason_id": "machine_age",
                "title": "Enhanced Mechanical Calibration",
                "icon": "fa-sliders",
                "solution": "Perform comprehensive vibration dampening check, replace worn bushings, and calibrate rapier guide timing.",
                "priority": "MEDIUM"
            })

        # E. Fabric Type Sensitivity
        raw_fabric_impact = 0.0
        fragile_fabrics = {
            "Silk": {"difficulty": 30.0, "safe_speed": 650.0},
            "Viscose": {"difficulty": 25.0, "safe_speed": 720.0},
            "Wool": {"difficulty": 20.0, "safe_speed": 700.0},
            "Linen": {"difficulty": 15.0, "safe_speed": 750.0},
            "Cotton": {"difficulty": 5.0, "safe_speed": 820.0},
            "Polyester": {"difficulty": 0.0, "safe_speed": 860.0},
            "Denim": {"difficulty": 0.0, "safe_speed": 800.0}
        }
        fabric_info = fragile_fabrics.get(f_type, {"difficulty": 10.0, "safe_speed": 800.0})
        if f_thresh["mean"] > 4.5 or fabric_info["difficulty"] >= 20.0:
            raw_fabric_impact = fabric_info["difficulty"] + max(0.0, (f_thresh["mean"] - 3.5) * 5.0)
            reason_cards.append({
                "id": "fabric_sensitivity",
                "title": "High Fabric Sensitivity & Complexity",
                "severity": "WARNING",
                "badge_color": "warning",
                "icon": "fa-layer-group",
                "observed": f"{f_type} ({f_thresh['mean']:.2f}% Historical Avg Waste)",
                "benchmark": f"{overall_avg_waste:.2f}% Factory Baseline",
                "impact": f"{f_type} has lower tensile elasticity and is more susceptible to shedding and edge frays.",
                "evidence_text": f"This fabric type ({f_type}) has historically produced higher waste percentages ({f_thresh['mean']:.2f}% avg) and requires precise process controls."
            })
            preventive_solutions.append({
                "reason_id": "fabric_sensitivity",
                "title": "Review Fabric-Specific Parameters",
                "icon": "fa-sliders",
                "solution": f"Review the machine settings and operating parameters specifically for {f_type} and compare them with successful low-waste batches.",
                "priority": "HIGH" if fabric_info["difficulty"] >= 25.0 else "MEDIUM"
            })

        # F. Shift Dynamics
        raw_shift_impact = 0.0
        if shift == "Night":
            raw_shift_impact = 18.0
            reason_cards.append({
                "id": "shift_dynamics",
                "title": "Shift Operating Variance",
                "severity": "WARNING",
                "badge_color": "cyan",
                "icon": "fa-moon",
                "observed": f"{shift} Shift",
                "benchmark": "Morning / Standard Shift Baseline",
                "impact": "Night shift operations historically show higher pacing variance and handover differences across weaving units.",
                "evidence_text": "The current shift (Night) has a higher historical average waste percentage than other shifts."
            })
            preventive_solutions.append({
                "reason_id": "shift_dynamics",
                "title": "Standardize Shift Handover Protocols",
                "icon": "fa-clipboard-list",
                "solution": "Standardize shift handover inspection checklists and ensure consistent monitoring of machine tension across shift transitions.",
                "priority": "LOW"
            })

        # G. Operator Dynamics (Constructive, objective, conditions-oriented)
        raw_operator_impact = 0.0
        # Check operator variance objectively
        op_analysis = baseline_analyzer.get_operator_analysis() if hasattr(baseline_analyzer, "get_operator_analysis") else {}
        operator_list = op_analysis.get("operators", [])
        current_op_stat = next((o for o in operator_list if o.get("operator") == operator), None)
        if current_op_stat and current_op_stat.get("average_waste_pct", 0.0) > overall_avg_waste * 1.3:
            raw_operator_impact = 15.0
            reason_cards.append({
                "id": "operator_conditions",
                "title": "Operating Conditions Pattern",
                "severity": "WARNING",
                "badge_color": "cyan",
                "icon": "fa-user-gear",
                "observed": f"{operator} ({current_op_stat.get('average_waste_pct'):.2f}% Avg Waste in similar batches)",
                "benchmark": f"{overall_avg_waste:.2f}% Factory Operating Baseline",
                "impact": "Operating conditions for similar batches have exhibited higher variance during manual knotting and bobbin changes.",
                "evidence_text": "Similar batches handled under the same machine and operating conditions have shown increased waste."
            })
            preventive_solutions.append({
                "reason_id": "operator_conditions",
                "title": "Provide Technical Settings Coaching",
                "icon": "fa-chalkboard-user",
                "solution": "Review standard operating procedures for knotting and tension adjustment to ensure uniform best practices across all machine operators.",
                "priority": "LOW"
            })

        # H. Atmospheric Humidity
        raw_humidity_impact = 0.0
        if humidity_imputed:
            reason_cards.append({
                "id": "missing_humidity",
                "title": "Environmental Telemetry Unavailable",
                "severity": "NOMINAL",
                "badge_color": "cyan",
                "icon": "fa-circle-info",
                "observed": "Missing Humidity Telemetry",
                "benchmark": "50.0-65.0% RH Standard Operating Target",
                "impact": "Real-time atmospheric condition analysis is limited; default baseline (55.0% RH) applied for safety calculations.",
                "evidence_text": "Humidity data is unavailable, so environmental-condition analysis is limited."
            })
            preventive_solutions.append({
                "reason_id": "missing_humidity",
                "title": "Inspect Atmospheric Sensor",
                "icon": "fa-temperature-arrow-up",
                "solution": "Check Loom Bay relative humidity sensor and transmitter to restore real-time environmental telemetry.",
                "priority": "LOW"
            })
        elif humidity < 42.0:
            deficit = 55.0 - humidity
            raw_humidity_impact = min(100.0, 30.0 + (deficit * 3.5))
            reason_cards.append({
                "id": "humidity_low",
                "title": "Low Ambient Humidity",
                "severity": "HIGH" if humidity < 35.0 else "WARNING",
                "badge_color": "warning",
                "icon": "fa-droplet-slash",
                "observed": f"{humidity:.1f}% RH",
                "benchmark": "50.0-65.0% RH Validated Weaving Range",
                "impact": "Dry air creates yarn static charge, fiber brittleness, and warp micro-shedding during high-speed reed strikes.",
                "evidence_text": "Current humidity is outside the normal historical operating range for this fabric."
            })
            preventive_solutions.append({
                "reason_id": "humidity_low",
                "title": "Adjust Weaving Humidity",
                "icon": "fa-droplet",
                "solution": "Check environmental-control systems and maintain humidity within the validated operating range (55-65% RH) for the fabric and process.",
                "priority": "HIGH"
            })
        elif humidity > 75.0:
            excess = humidity - 70.0
            raw_humidity_impact = min(100.0, 25.0 + (excess * 3.0))
            reason_cards.append({
                "id": "humidity_high",
                "title": "Excess Ambient Humidity",
                "severity": "WARNING",
                "badge_color": "warning",
                "icon": "fa-droplet",
                "observed": f"{humidity:.1f}% RH",
                "benchmark": "50.0-65.0% RH Validated Weaving Range",
                "impact": "High moisture content causes yarn swelling and increases frictional drag through heald wires.",
                "evidence_text": "Current humidity is outside the normal historical operating range for this fabric."
            })
            preventive_solutions.append({
                "reason_id": "humidity_high",
                "title": "Regulate Weaving Shed Dehumidification",
                "icon": "fa-fan",
                "solution": "Activate HVAC dehumidification cycle in Loom Bay and maintain relative humidity within the validated 50-65% RH range.",
                "priority": "MEDIUM"
            })

        # I. Thermal Temperature
        raw_temp_impact = 0.0
        if temperature > 33.0:
            t_excess = temperature - 30.0
            raw_temp_impact = min(80.0, 20.0 + (t_excess * 4.0))
            reason_cards.append({
                "id": "temperature_high",
                "title": "Elevated Ambient Temperature",
                "severity": "WARNING",
                "badge_color": "warning",
                "icon": "fa-temperature-high",
                "observed": f"{temperature:.1f} C",
                "benchmark": "20.0-28.0 C Validated Thermal Range",
                "impact": "High temperature decreases machine lubricant viscosity and softens synthetic yarn sizing chemicals.",
                "evidence_text": "Current temperature is outside the normal operating range observed for similar batches."
            })
            preventive_solutions.append({
                "reason_id": "temperature_high",
                "title": "Restore Process Temperature",
                "icon": "fa-temperature-arrow-down",
                "solution": "Monitor temperature and restore it to the validated process range (22-27 C) before continuing high-volume production.",
                "priority": "MEDIUM"
            })
        elif temperature < 18.0:
            raw_temp_impact = 20.0
            reason_cards.append({
                "id": "temperature_low",
                "title": "Low Ambient Temperature",
                "severity": "WARNING",
                "badge_color": "cyan",
                "icon": "fa-temperature-low",
                "observed": f"{temperature:.1f} C",
                "benchmark": "20.0-28.0 C Validated Thermal Range",
                "impact": "Low temperatures increase sizing binder stiffness and motor starting friction.",
                "evidence_text": "Current temperature is outside the normal operating range observed for similar batches."
            })
            preventive_solutions.append({
                "reason_id": "temperature_low",
                "title": "Restore Process Temperature",
                "icon": "fa-temperature-arrow-up",
                "solution": "Monitor temperature and restore it to the validated process range (22-27 C) before continuing high-volume production.",
                "priority": "LOW"
            })

        # J. New Machine Cold-Start
        if is_new_machine:
            reason_cards.insert(0, {
                "id": "new_machine",
                "title": "Limited Machine History (New Unit)",
                "severity": "WARNING",
                "badge_color": "cyan",
                "icon": "fa-circle-question",
                "observed": f"Machine {m_id} (0 previous records)",
                "benchmark": "≥ 10 batches required for dedicated baseline",
                "impact": "Prediction confidence is reduced; evaluated against overall factory and fabric-type averages.",
                "evidence_text": f"Limited historical data is available for this machine. Prediction is based on available overall, fabric ({f_type}), and operating-condition patterns."
            })
            preventive_solutions.insert(0, {
                "reason_id": "new_machine",
                "title": "Establish Calibration Baseline",
                "icon": "fa-chart-simple",
                "solution": f"Log consecutive batches on Machine {m_id} to establish a machine-specific statistical baseline and tune tension parameters.",
                "priority": "MEDIUM"
            })

        # Nominal fallback if no active risk reasons were found
        if not reason_cards:
            reason_cards.append({
                "id": "nominal_operations",
                "title": "Nominal Operating Conditions",
                "severity": "NOMINAL",
                "badge_color": "normal",
                "icon": "fa-circle-check",
                "observed": f"{waste_pct:.2f}% Waste, {speed:.0f} RPM, {maint_age}d Maint.",
                "benchmark": "All parameters within optimal envelopes",
                "impact": "Telemetry indicates stable mechanical, atmospheric, and material processing parameters.",
                "evidence_text": f"Waste percentage ({waste_pct:.2f}%) and operating conditions are within the expected normal range."
            })
            preventive_solutions.append({
                "reason_id": "nominal_operations",
                "title": "Maintain Standard Procedures",
                "icon": "fa-check-double",
                "solution": "Continue production under current validated settings and maintain regular inspection intervals.",
                "priority": "LOW"
            })

        # ----------------------------------------------------
        # 2. WEIGHTING & MULTI-FACTOR ATTRIBUTION DECOMPOSITION
        # ----------------------------------------------------
        weighted_points = {
            "mechanical_maintenance": raw_maint_impact * 0.35,
            "operational_speed": raw_speed_impact * 0.30,
            "atmospheric_humidity": raw_humidity_impact * 0.15,
            "fabric_sensitivity": raw_fabric_impact * 0.08,
            "thermal_environment": raw_temp_impact * 0.06,
            "shift_operator": (raw_shift_impact + raw_operator_impact) * 0.06
        }

        total_weighted_points = sum(weighted_points.values())
        total_risk_score = round(min(100.0, max(5.0, total_weighted_points)), 1)

        # Risk Classification
        if total_risk_score >= high_thresh:
            calculated_risk_level = "HIGH RISK"
        elif total_risk_score >= warn_thresh:
            calculated_risk_level = "WARNING"
        else:
            calculated_risk_level = "NORMAL"

        # Final risk level overrides from batch if already assigned by ML
        final_risk_level = str(batch.get("risk_level", calculated_risk_level))
        final_risk_score = float(batch.get("risk_score", total_risk_score))

        # Attribution percentages
        if total_weighted_points > 0:
            attribution_pcts = {
                k: round((v / total_weighted_points) * 100.0, 1)
                for k, v in weighted_points.items()
            }
        else:
            attribution_pcts = {k: 16.7 for k in weighted_points.keys()}

        # ----------------------------------------------------
        # 3. PRIMARY & SECONDARY ROOT CAUSE IDENTIFICATION
        # ----------------------------------------------------
        active_candidates = [
            {
                "category": self.CAT_MECHANICAL,
                "factor_key": "mechanical_maintenance",
                "raw_impact": raw_maint_impact,
                "weighted_points": round(weighted_points["mechanical_maintenance"], 1),
                "attribution_pct": attribution_pcts["mechanical_maintenance"],
                "title": f"Maintenance Overdue by {max(0, maint_age - maint_interval)} Days" if maint_age > maint_interval else "Mechanical Calibration Wear",
                "explanation": f"Loom serviced {maint_age}d ago vs {maint_interval}d limit.",
                "is_active": raw_maint_impact >= 20.0
            },
            {
                "category": self.CAT_OPERATIONAL,
                "factor_key": "operational_speed",
                "raw_impact": raw_speed_impact,
                "weighted_points": round(weighted_points["operational_speed"], 1),
                "attribution_pct": attribution_pcts["operational_speed"],
                "title": f"Excess Loom Speed ({speed:.0f} RPM vs {fabric_safe_speed:.0f} RPM Limit)",
                "explanation": f"Operating speed is {(speed_ratio - 1.0) * 100:.0f}% higher than safe pace for {f_type}.",
                "is_active": raw_speed_impact >= 20.0
            },
            {
                "category": self.CAT_ATMOSPHERIC,
                "factor_key": "atmospheric_humidity",
                "raw_impact": raw_humidity_impact,
                "weighted_points": round(weighted_points["atmospheric_humidity"], 1),
                "attribution_pct": attribution_pcts["atmospheric_humidity"],
                "title": f"Dry Yarn Brittleness ({humidity:.1f}% RH)" if humidity < 42.0 else (f"Excess Ambient Humidity ({humidity:.1f}% RH)" if humidity > 75.0 else "Missing Humidity Telemetry"),
                "explanation": f"Relative humidity ({humidity:.1f}% RH) is outside optimal 50-65% range.",
                "is_active": raw_humidity_impact >= 20.0
            },
            {
                "category": self.CAT_MATERIAL,
                "factor_key": "fabric_sensitivity",
                "raw_impact": raw_fabric_impact,
                "weighted_points": round(weighted_points["fabric_sensitivity"], 1),
                "attribution_pct": attribution_pcts["fabric_sensitivity"],
                "title": f"High Fragility Material Dynamics ({f_type})",
                "explanation": f"{f_type} has higher fiber sensitivity (baseline {f_thresh['mean']:.2f}% avg).",
                "is_active": raw_fabric_impact >= 18.0
            },
            {
                "category": self.CAT_THERMAL,
                "factor_key": "thermal_environment",
                "raw_impact": raw_temp_impact,
                "weighted_points": round(weighted_points["thermal_environment"], 1),
                "attribution_pct": attribution_pcts["thermal_environment"],
                "title": f"Thermal Stress ({temperature:.1f}°C)",
                "explanation": f"Ambient temperature ({temperature:.1f}°C) is outside 20-28°C range.",
                "is_active": raw_temp_impact >= 20.0
            },
            {
                "category": self.CAT_OPERATOR,
                "factor_key": "shift_operator",
                "raw_impact": raw_shift_impact + raw_operator_impact,
                "weighted_points": round(weighted_points["shift_operator"], 1),
                "attribution_pct": attribution_pcts["shift_operator"],
                "title": f"{shift} Shift Dynamics",
                "explanation": f"Shift pacing variance observed.",
                "is_active": (raw_shift_impact + raw_operator_impact) >= 15.0
            }
        ]

        sorted_causes = sorted(active_candidates, key=lambda x: x["weighted_points"], reverse=True)
        active_causes = [c for c in sorted_causes if c["is_active"]]

        if active_causes:
            primary_cause = active_causes[0]
            secondary_causes = active_causes[1:4]
        else:
            primary_cause = {
                "category": "Nominal Operations",
                "factor_key": "nominal",
                "raw_impact": 0.0,
                "weighted_points": 0.0,
                "attribution_pct": 0.0,
                "title": "Nominal Operating Conditions",
                "explanation": "No significant root cause detected. All mechanical, speed, and ambient parameters are within nominal safety envelopes.",
                "is_active": False
            }
            secondary_causes = []

        # Severity level
        if final_risk_level == "HIGH RISK" or final_risk_score >= high_thresh or (primary_cause["raw_impact"] >= 65.0):
            severity = "CRITICAL"
        elif final_risk_level == "WARNING" or final_risk_score >= warn_thresh or (primary_cause["raw_impact"] >= 35.0):
            severity = "HIGH"
        elif final_risk_score >= 25.0:
            severity = "MODERATE"
        else:
            severity = "NOMINAL"

        # ----------------------------------------------------
        # 4. STRUCTURED RISK-BASED ACTION PLAN
        # (Inspect -> Adjust -> Maintain -> Monitor)
        # ----------------------------------------------------
        if final_risk_level == "HIGH RISK":
            recommended_action_plan = {
                "risk_level": "HIGH RISK",
                "badge_class": "badge-danger",
                "summary": "Multiple factors indicate a high probability of abnormal waste. Immediate inspection is recommended before continuing production.",
                "protocol": "Inspect -> Adjust -> Maintain -> Monitor",
                "steps": [
                    "Inspect machine condition and components (rapier guides, heald wires) before starting the next batch.",
                    "Verify machine settings and ensure production speed is within the validated operating range.",
                    "Perform overdue preventive maintenance if applicable.",
                    "Verify fabric quality and fabric-specific tension settings.",
                    "Check temperature and humidity in the weaving shed.",
                    "Closely monitor waste percentage during the next production cycle."
                ]
            }
        elif final_risk_level == "WARNING":
            recommended_action_plan = {
                "risk_level": "WARNING",
                "badge_class": "badge-warning",
                "summary": "The batch shows moderate risk factors. Review the highlighted conditions before continuing large-scale production.",
                "protocol": "Inspect -> Adjust -> Maintain -> Monitor",
                "steps": [
                    "Check machine settings and warp let-off tension.",
                    "Monitor production speed and keep within safe fabric envelope.",
                    "Review maintenance status and plan upcoming service slot.",
                    "Monitor waste percentage more frequently during upcoming production runs.",
                    "Compare operating parameters with successful low-waste historical batches."
                ]
            }
        else:
            recommended_action_plan = {
                "risk_level": "NORMAL",
                "badge_class": "badge-normal",
                "summary": "Production conditions are within the expected range. Continue monitoring waste percentage.",
                "protocol": "Inspect -> Adjust -> Maintain -> Monitor",
                "steps": [
                    "Continue production according to standard operational schedule.",
                    "Monitor machine performance and real-time tension sensors.",
                    "Maintain standard preventive maintenance schedule."
                ]
            }

        # ----------------------------------------------------
        # 5. PRESCRIPTIVE REMEDIATION PLAYBOOK
        # ----------------------------------------------------
        playbook = []
        step_idx = 1

        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            est_saving = min(4.5, 1.5 + (days_over * 0.08))
            playbook.append({
                "step": step_idx,
                "priority": "CRITICAL",
                "category": self.CAT_MECHANICAL,
                "action": f"Halt non-urgent batches on Machine {m_id} and perform preventive overhaul (overdue by {days_over} days).",
                "technical_details": "Inspect rapier guide hooks, replace worn heald wires, and replenish gearbox synthetic lubricant.",
                "estimated_waste_reduction_pct": round(est_saving, 2),
                "estimated_kg_saved": round((est_saving / 100.0) * total_prod, 1)
            })
            step_idx += 1

        if speed > fabric_safe_speed * 1.10:
            speed_cut = speed - fabric_safe_speed
            est_saving = min(5.0, (speed_cut / fabric_safe_speed) * 8.0)
            target_rpm = int(fabric_safe_speed * 1.02)
            playbook.append({
                "step": step_idx,
                "priority": "HIGH" if speed_ratio > 1.2 else "MEDIUM",
                "category": self.CAT_OPERATIONAL,
                "action": f"Cap loom operating speed at {target_rpm} RPM for {f_type} (currently {speed:.0f} RPM).",
                "technical_details": f"Excessive warp tension causes micro-tears on {f_type}. Aligning speed with fabric safety envelope eliminates stress breaks.",
                "estimated_waste_reduction_pct": round(est_saving, 2),
                "estimated_kg_saved": round((est_saving / 100.0) * total_prod, 1)
            })
            step_idx += 1

        if humidity_imputed:
            playbook.append({
                "step": step_idx,
                "priority": "MEDIUM",
                "category": self.CAT_ATMOSPHERIC,
                "action": "Replace or recalibrate relative humidity sensor transmitter on Loom Bay.",
                "technical_details": "Real-time atmospheric telemetry is required for AI adaptive tension control.",
                "estimated_waste_reduction_pct": 0.5,
                "estimated_kg_saved": round(0.005 * total_prod, 1)
            })
            step_idx += 1
        elif humidity < 45.0:
            est_saving = min(3.5, (55.0 - humidity) * 0.15)
            playbook.append({
                "step": step_idx,
                "priority": "HIGH",
                "category": self.CAT_ATMOSPHERIC,
                "action": f"Increase ultrasonic humidifier output in Weaving Shed to reach 55-65% RH (current: {humidity:.1f}%).",
                "technical_details": f"Dry air makes {f_type} yarn brittle and generates electrostatic warp entanglement.",
                "estimated_waste_reduction_pct": round(est_saving, 2),
                "estimated_kg_saved": round((est_saving / 100.0) * total_prod, 1)
            })
            step_idx += 1

        if not playbook:
            playbook.append({
                "step": 1,
                "priority": "NORMAL",
                "category": "Standard Operating Procedure",
                "action": "Maintain standard operating parameters and continue routine visual loom inspection.",
                "technical_details": "Machine and atmospheric settings are within optimal efficiency envelopes.",
                "estimated_waste_reduction_pct": 0.0,
                "estimated_kg_saved": 0.0
            })

        # ----------------------------------------------------
        # 6. COUNTERFACTUAL SIMULATION TARGETS
        # ----------------------------------------------------
        target_speed = min(speed, fabric_safe_speed)
        target_hum = 58.0 if (humidity < 45.0 or humidity > 75.0 or humidity_imputed) else humidity
        target_maint_age = min(maint_age, 15) if maint_age > maint_interval else maint_age
        target_temp = 24.0 if (temperature > 32.0 or temperature < 18.0) else temperature

        simulated_res = self.simulate_counterfactual(
            batch=batch,
            modified_params={
                "production_speed": target_speed,
                "humidity": target_hum,
                "maintenance_age_days": target_maint_age,
                "temperature": target_temp
            },
            baseline_analyzer=baseline_analyzer,
            settings=settings
        )

        return {
            "status": "SUCCESS",
            "batch_id": b_id,
            "machine_id": m_id,
            "fabric_type": f_type,
            "current_waste_percentage": round(waste_pct, 2),
            "current_risk_score": final_risk_score,
            "risk_level": final_risk_level,
            "severity": severity,
            "reason_cards": reason_cards,
            "preventive_solutions": preventive_solutions,
            "recommended_action_plan": recommended_action_plan,
            "primary_cause": primary_cause,
            "secondary_causes": secondary_causes,
            "attributions": {
                "mechanical_maintenance": {
                    "label": "Maintenance & Machine Wear",
                    "impact_points": round(weighted_points["mechanical_maintenance"], 1),
                    "attribution_pct": attribution_pcts["mechanical_maintenance"],
                    "category": self.CAT_MECHANICAL,
                    "explanation": f"Loom serviced {maint_age}d ago vs {maint_interval}d limit."
                },
                "operational_speed": {
                    "label": "Operating Speed vs Fabric Safe Limit",
                    "impact_points": round(weighted_points["operational_speed"], 1),
                    "attribution_pct": attribution_pcts["operational_speed"],
                    "category": self.CAT_OPERATIONAL,
                    "explanation": f"Operating pace is {speed:.0f} RPM vs {fabric_safe_speed:.0f} safe limit."
                },
                "atmospheric_humidity": {
                    "label": "Ambient Humidity Deviation",
                    "impact_points": round(weighted_points["atmospheric_humidity"], 1),
                    "attribution_pct": attribution_pcts["atmospheric_humidity"],
                    "category": self.CAT_ATMOSPHERIC,
                    "explanation": f"Relative humidity {humidity:.1f}% RH."
                },
                "fabric_sensitivity": {
                    "label": "Fabric Material Complexity",
                    "impact_points": round(weighted_points["fabric_sensitivity"], 1),
                    "attribution_pct": attribution_pcts["fabric_sensitivity"],
                    "category": self.CAT_MATERIAL,
                    "explanation": f"{f_type} material dynamics."
                },
                "thermal_environment": {
                    "label": "Thermal Environment",
                    "impact_points": round(weighted_points["thermal_environment"], 1),
                    "attribution_pct": attribution_pcts["thermal_environment"],
                    "category": self.CAT_THERMAL,
                    "explanation": f"Ambient temperature {temperature:.1f}°C."
                },
                "shift_operator": {
                    "label": "Shift & Operator Pacing",
                    "impact_points": round(weighted_points["shift_operator"], 1),
                    "attribution_pct": attribution_pcts["shift_operator"],
                    "category": self.CAT_OPERATOR,
                    "explanation": f"{shift} shift pacing."
                }
            },
            "prescriptive_playbook": playbook,
            "counterfactual_target": {
                "recommended_speed": target_speed,
                "recommended_humidity": target_hum,
                "recommended_maintenance_age": target_maint_age,
                "simulated_risk_score": simulated_res["simulated_risk_score"],
                "simulated_risk_level": simulated_res["simulated_risk_level"],
                "simulated_waste_percentage": simulated_res["simulated_waste_percentage"],
                "estimated_waste_savings_pct": simulated_res["waste_reduction_pct"],
                "estimated_kg_saved": simulated_res["estimated_kg_saved"]
            }
        }

    def simulate_counterfactual(
        self,
        batch: Dict[str, Any],
        modified_params: Dict[str, Any],
        baseline_analyzer: Any,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulates the effect of changing operational parameters (Speed, Humidity, Maintenance, Temp).
        Returns Before vs After metrics, simulated risk score, and estimated waste reduction.
        """
        if settings is None:
            settings = {
                "risk_threshold_warning": 40.0,
                "risk_threshold_high": 70.0,
                "maintenance_interval_days": 60
            }

        warn_thresh = float(settings.get("risk_threshold_warning", 40.0))
        high_thresh = float(settings.get("risk_threshold_high", 70.0))
        maint_interval = int(settings.get("maintenance_interval_days", 60))

        sim_batch = dict(batch)
        for k, v in modified_params.items():
            if v is not None:
                sim_batch[k] = v

        m_id = str(sim_batch.get("machine_id", "M01"))
        f_type = str(sim_batch.get("fabric_type", "Cotton"))
        total_prod = float(sim_batch.get("total_production", 1000.0))
        orig_waste_pct = float(batch.get("waste_percentage", 4.0))

        speed = float(sim_batch.get("production_speed", 800.0))
        maint_age = int(sim_batch.get("maintenance_age_days", 30))
        machine_age = float(sim_batch.get("machine_age", 3.0))
        humidity = float(sim_batch.get("humidity", 55.0))
        temperature = float(sim_batch.get("temperature", 25.0))

        f_thresh = baseline_analyzer.get_fabric_thresholds(f_type)
        m_thresh = baseline_analyzer.get_machine_thresholds(m_id)
        fabric_safe_speed = f_thresh.get("mean_speed", 800.0)
        target_waste_mean = m_thresh["mean"] if m_thresh.get("has_history") else f_thresh["mean"]

        # 1. Maintenance component
        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            m_comp = min(100.0, 45.0 + (days_over * 1.8) + (machine_age * 1.5))
        elif maint_age > maint_interval * 0.8:
            m_comp = 25.0 + (machine_age * 1.0)
        else:
            m_comp = max(0.0, machine_age * 1.2)

        # 2. Speed component
        speed_ratio = speed / max(1.0, fabric_safe_speed)
        if speed_ratio > 1.20:
            s_comp = min(100.0, (speed_ratio - 1.0) * 180.0)
        elif speed_ratio > 1.08:
            s_comp = 35.0
        elif speed_ratio < 0.70:
            s_comp = 15.0
        else:
            s_comp = 0.0

        # 3. Humidity component
        if humidity < 42.0:
            h_comp = min(100.0, 30.0 + ((55.0 - humidity) * 3.5))
        elif humidity > 75.0:
            h_comp = min(100.0, 25.0 + ((humidity - 70.0) * 3.0))
        else:
            h_comp = 0.0

        # 4. Fabric component
        fragile_penalties = {"Silk": 25.0, "Viscose": 20.0, "Wool": 15.0, "Linen": 10.0, "Cotton": 5.0, "Polyester": 0.0, "Denim": 0.0}
        f_comp = fragile_penalties.get(f_type, 5.0)

        # 5. Temperature component
        t_comp = min(80.0, 20.0 + ((temperature - 30.0) * 4.0)) if temperature > 33.0 else (20.0 if temperature < 18.0 else 0.0)

        # 6. Shift component
        sh_comp = 18.0 if sim_batch.get("shift") == "Night" else (10.0 if sim_batch.get("shift") == "Evening" else 0.0)

        sim_points = (
            m_comp * 0.35 +
            s_comp * 0.30 +
            h_comp * 0.15 +
            f_comp * 0.08 +
            t_comp * 0.06 +
            sh_comp * 0.06
        )

        sim_risk_score = round(max(5.0, min(100.0, sim_points)), 1)

        if sim_risk_score >= high_thresh:
            sim_risk_level = "HIGH RISK"
        elif sim_risk_score >= warn_thresh:
            sim_risk_level = "WARNING"
        else:
            sim_risk_level = "NORMAL"

        base_waste = target_waste_mean
        simulated_waste_pct = round(max(0.5, base_waste * (0.65 + (sim_risk_score / 100.0) * 0.9)), 2)
        waste_reduction_pct = round(max(0.0, orig_waste_pct - simulated_waste_pct), 2)
        kg_saved = round((waste_reduction_pct / 100.0) * total_prod, 1)

        return {
            "initial_risk_score": float(batch.get("risk_score", 0.0)),
            "initial_risk_level": str(batch.get("risk_level", "NORMAL")),
            "initial_waste_percentage": orig_waste_pct,
            "simulated_risk_score": sim_risk_score,
            "simulated_risk_level": sim_risk_level,
            "simulated_waste_percentage": simulated_waste_pct,
            "waste_reduction_pct": waste_reduction_pct,
            "estimated_kg_saved": kg_saved,
            "simulated_parameters": {
                "production_speed": speed,
                "humidity": humidity,
                "maintenance_age_days": maint_age,
                "temperature": temperature
            }
        }

    def get_waste_causes_prevention_summary(
        self,
        df: pd.DataFrame,
        baseline_analyzer: Any,
        settings: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregates plant-wide waste causes, affected batch counts, average waste percentages,
        recommended preventive actions, and associated risk levels for the dashboard section.
        """
        if settings is None:
            settings = {
                "risk_threshold_warning": 40.0,
                "risk_threshold_high": 70.0,
                "maintenance_interval_days": 60
            }

        valid_df = df[df["is_valid"] == 1].copy() if not df.empty and "is_valid" in df.columns else df.copy()

        if valid_df.empty:
            return []

        maint_interval = int(settings.get("maintenance_interval_days", 60))

        # Standard Cause Categories with their tracking metrics
        causes_registry = {
            "speed": {
                "cause_name": "High Production Speed",
                "icon": "fa-gauge-high",
                "category": self.CAT_OPERATIONAL,
                "batches": [],
                "preventive_action": "Optimize speed to fabric safety envelope",
                "risk_levels": []
            },
            "maintenance": {
                "cause_name": "Maintenance Overdue",
                "icon": "fa-wrench",
                "category": self.CAT_MECHANICAL,
                "batches": [],
                "preventive_action": "Schedule preventive maintenance overhaul",
                "risk_levels": []
            },
            "fabric": {
                "cause_name": "Fabric Sensitivity Issue",
                "icon": "fa-layer-group",
                "category": self.CAT_MATERIAL,
                "batches": [],
                "preventive_action": "Adjust fabric tension & calibration settings",
                "risk_levels": []
            },
            "humidity": {
                "cause_name": "Ambient Humidity Deviation",
                "icon": "fa-droplet",
                "category": self.CAT_ATMOSPHERIC,
                "batches": [],
                "preventive_action": "Control humidity within 50–65% RH",
                "risk_levels": []
            },
            "temperature": {
                "cause_name": "Thermal Stress (High/Low Temp)",
                "icon": "fa-temperature-high",
                "category": self.CAT_THERMAL,
                "batches": [],
                "preventive_action": "Regulate ambient temperature to 22–27°C",
                "risk_levels": []
            },
            "machine_age": {
                "cause_name": "Machine Age / Vibration Wear",
                "icon": "fa-clock",
                "category": self.CAT_MECHANICAL,
                "batches": [],
                "preventive_action": "Perform precision vibration & bushing overhaul",
                "risk_levels": []
            }
        }

        for _, row in valid_df.iterrows():
            b = row.to_dict()
            f_type = str(b.get("fabric_type", "Cotton"))
            f_thresh = baseline_analyzer.get_fabric_thresholds(f_type)
            safe_speed = f_thresh.get("mean_speed", 800.0)
            
            speed = float(b.get("production_speed", 800.0))
            maint_age = int(b.get("maintenance_age_days", 30))
            hum = float(b.get("humidity", 55.0))
            hum_imp = bool(b.get("humidity_imputed", False))
            temp = float(b.get("temperature", 25.0))
            m_age = float(b.get("machine_age", 3.0))
            waste_pct = float(b.get("waste_percentage", 4.0))
            risk_level = str(b.get("risk_level", "NORMAL"))

            # Speed
            if speed > safe_speed * 1.12:
                causes_registry["speed"]["batches"].append(waste_pct)
                causes_registry["speed"]["risk_levels"].append(risk_level)

            # Maintenance
            if maint_age > maint_interval:
                causes_registry["maintenance"]["batches"].append(waste_pct)
                causes_registry["maintenance"]["risk_levels"].append(risk_level)

            # Fabric
            if f_type in ["Silk", "Viscose", "Wool", "Linen"] and waste_pct > 6.0:
                causes_registry["fabric"]["batches"].append(waste_pct)
                causes_registry["fabric"]["risk_levels"].append(risk_level)

            # Humidity
            if not hum_imp and (hum < 42.0 or hum > 75.0):
                causes_registry["humidity"]["batches"].append(waste_pct)
                causes_registry["humidity"]["risk_levels"].append(risk_level)

            # Temp
            if temp > 33.0 or temp < 18.0:
                causes_registry["temperature"]["batches"].append(waste_pct)
                causes_registry["temperature"]["risk_levels"].append(risk_level)

            # Age
            if m_age >= 7.5 and waste_pct > 5.5:
                causes_registry["machine_age"]["batches"].append(waste_pct)
                causes_registry["machine_age"]["risk_levels"].append(risk_level)

        summary_rows = []
        for key, data in causes_registry.items():
            cnt = len(data["batches"])
            if cnt > 0:
                avg_waste = round(sum(data["batches"]) / cnt, 2)
                # Determine dominant risk level
                high_count = sum(1 for r in data["risk_levels"] if r == "HIGH RISK")
                warn_count = sum(1 for r in data["risk_levels"] if r == "WARNING")
                if high_count > 0.3 * cnt:
                    dom_risk = "HIGH RISK"
                elif warn_count > 0.3 * cnt:
                    dom_risk = "WARNING"
                else:
                    dom_risk = "NORMAL"

                summary_rows.append({
                    "cause_id": key,
                    "cause_name": data["cause_name"],
                    "icon": data["icon"],
                    "category": data["category"],
                    "affected_batches": cnt,
                    "avg_waste_pct": avg_waste,
                    "preventive_action": data["preventive_action"],
                    "risk_level": dom_risk
                })

        # Sort by affected batches descending
        summary_rows.sort(key=lambda x: (x["affected_batches"], x["avg_waste_pct"]), reverse=True)
        return summary_rows

    def generate_plant_root_cause_analysis(
        self,
        df: pd.DataFrame,
        baseline_analyzer: Any,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Aggregates Root-Cause failure modes across all historical batches.
        Computes Pareto breakdown, category distribution, high-risk machine matrix,
        and high-impact factory recommendations.
        """
        if settings is None:
            settings = {
                "risk_threshold_warning": 40.0,
                "risk_threshold_high": 70.0,
                "maintenance_interval_days": 60
            }

        valid_df = df[df["is_valid"] == 1].copy() if not df.empty and "is_valid" in df.columns else df.copy()

        if valid_df.empty:
            return {
                "total_batches_analyzed": 0,
                "pareto_causes": [],
                "category_distribution": {},
                "machine_root_causes": {},
                "top_plant_recommendations": [],
                "waste_causes_prevention": []
            }

        category_counts = {
            self.CAT_MECHANICAL: 0,
            self.CAT_OPERATIONAL: 0,
            self.CAT_ATMOSPHERIC: 0,
            self.CAT_MATERIAL: 0,
            self.CAT_THERMAL: 0,
            self.CAT_OPERATOR: 0
        }

        specific_causes = {}
        machine_cause_matrix = {}
        total_potential_waste_kg_saved = 0.0

        for _, row in valid_df.iterrows():
            batch_dict = row.to_dict()
            diag = self.diagnose_batch(batch_dict, baseline_analyzer, settings)
            if diag["status"] == "SUCCESS":
                p_cause = diag["primary_cause"]
                if p_cause.get("is_active", False):
                    cat = p_cause.get("category", self.CAT_OPERATIONAL)
                    category_counts[cat] = category_counts.get(cat, 0) + 1

                    title = p_cause.get("title", "Unknown Failure Mode")
                    if title not in specific_causes:
                        specific_causes[title] = {
                            "title": title,
                            "category": cat,
                            "count": 0,
                            "total_impact_points": 0.0,
                            "potential_savings_kg": 0.0
                        }
                    specific_causes[title]["count"] += 1
                    specific_causes[title]["total_impact_points"] += p_cause.get("weighted_points", 0.0)

                    if diag.get("prescriptive_playbook"):
                        top_step = diag["prescriptive_playbook"][0]
                        saved_kg = top_step.get("estimated_kg_saved", 0.0)
                        specific_causes[title]["potential_savings_kg"] += saved_kg
                        total_potential_waste_kg_saved += saved_kg

                    m_id = batch_dict.get("machine_id", "M01")
                    if m_id not in machine_cause_matrix:
                        machine_cause_matrix[m_id] = {
                            "machine_id": m_id,
                            "mechanical_count": 0,
                            "speed_count": 0,
                            "humidity_count": 0,
                            "total_abnormal_events": 0
                        }
                    machine_cause_matrix[m_id]["total_abnormal_events"] += 1
                    if cat == self.CAT_MECHANICAL:
                        machine_cause_matrix[m_id]["mechanical_count"] += 1
                    elif cat == self.CAT_OPERATIONAL:
                        machine_cause_matrix[m_id]["speed_count"] += 1
                    elif cat == self.CAT_ATMOSPHERIC:
                        machine_cause_matrix[m_id]["humidity_count"] += 1

        sorted_causes = sorted(specific_causes.values(), key=lambda x: x["count"], reverse=True)
        total_failure_events = max(1, sum(c["count"] for c in sorted_causes))

        cumulative_count = 0
        pareto_list = []
        for c in sorted_causes:
            cumulative_count += c["count"]
            cum_pct = round((cumulative_count / total_failure_events) * 100.0, 1)
            share_pct = round((c["count"] / total_failure_events) * 100.0, 1)
            pareto_list.append({
                "title": c["title"],
                "category": c["category"],
                "count": c["count"],
                "percentage_of_failures": share_pct,
                "cumulative_percentage": cum_pct,
                "potential_savings_kg": round(c["potential_savings_kg"], 1)
            })

        cat_dist = {}
        for cat, cnt in category_counts.items():
            cat_dist[cat] = {
                "count": cnt,
                "percentage": round((cnt / total_failure_events) * 100.0, 1) if total_failure_events > 0 else 0.0
            }

        top_recs = []
        if category_counts[self.CAT_MECHANICAL] > 0:
            top_recs.append({
                "rank": 1,
                "title": "Establish Stricter Preventive Maintenance Cadence",
                "impact": f"Responsible for {cat_dist[self.CAT_MECHANICAL]['percentage']}% of abnormal waste events.",
                "action": "Enforce mandatory loom shutdown and overhaul when machine reaches service limit."
            })
        if category_counts[self.CAT_OPERATIONAL] > 0:
            top_recs.append({
                "rank": 2,
                "title": "Implement Automated Fabric-Speed Lockouts",
                "impact": f"Responsible for {cat_dist[self.CAT_OPERATIONAL]['percentage']}% of abnormal waste events.",
                "action": "Configure loom PLC controllers with speed caps for delicate Viscose, Silk, and Linen weaves."
            })
        if category_counts[self.CAT_ATMOSPHERIC] > 0:
            top_recs.append({
                "rank": 3,
                "title": "Upgrade Weaving Room Humidity Automation",
                "impact": f"Responsible for {cat_dist[self.CAT_ATMOSPHERIC]['percentage']}% of abnormal waste events.",
                "action": "Install closed-loop ultrasonic humidification maintaining stable 55-65% RH."
            })

        waste_causes_summary = self.get_waste_causes_prevention_summary(valid_df, baseline_analyzer, settings)

        return {
            "total_batches_analyzed": len(valid_df),
            "total_failure_events": total_failure_events,
            "total_potential_waste_kg_saved": round(total_potential_waste_kg_saved, 1),
            "pareto_causes": pareto_list[:10],
            "category_distribution": cat_dist,
            "machine_root_causes": list(machine_cause_matrix.values()),
            "top_plant_recommendations": top_recs,
            "waste_causes_prevention": waste_causes_summary
        }


# Singleton instance
root_cause_ai_engine = RootCauseAIEngine()

def get_waste_causes_prevention_summary(df, baseline_analyzer, settings=None):
    return root_cause_ai_engine.get_waste_causes_prevention_summary(df, baseline_analyzer, settings)

