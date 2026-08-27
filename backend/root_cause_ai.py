"""
Root-Cause AI & Explainability Engine for Textile Waste Prediction System.

Provides:
1. Multi-factor mathematical attribution / SHAP-like feature decomposition
2. Primary and Secondary Root Cause Identification and Severity Tagging
3. Prescriptive Remediation Playbooks with Quantified Waste Reduction Estimates
4. Interactive Counterfactual "What-If" Simulation & Optimization Engine
5. Factory-Wide Root Cause Diagnostic Aggregator & Pareto Analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class RootCauseAIEngine:
    """
    AI Root Cause Analyzer and Explainer for Textile Production Batches.
    Deconstructs multi-dimensional risk into explainable mechanical, operational,
    material, and environmental causal factors.
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

        # Extract telemetry
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

        if not is_valid or total_prod <= 0:
            return {
                "status": "INVALID_BATCH",
                "severity": "CRITICAL",
                "summary": "Invalid production data: total production quantity is zero or missing.",
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
                        "estimated_waste_reduction_pct": 0.0
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

        # ----------------------------------------------------
        # 1. QUANTITATIVE MULTI-FACTOR ATTRIBUTION DECOMPOSITION
        # Compute exact raw risk impact points (0 - 100 scale per factor)
        # ----------------------------------------------------

        # Factor A: Maintenance Lag & Mechanical Wear
        raw_maint_impact = 0.0
        maint_explanation = ""
        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            raw_maint_impact = min(100.0, 45.0 + (days_over * 1.8) + (machine_age * 1.5))
            maint_explanation = f"Maintenance is overdue by {days_over} days (last serviced {maint_age}d ago vs {maint_interval}d limit). Machine age {machine_age:.1f} yrs amplifies vibration and wear."
        elif maint_age > maint_interval * 0.8:
            raw_maint_impact = 25.0 + (machine_age * 1.0)
            maint_explanation = f"Maintenance approaching due threshold ({maint_age}/{maint_interval} days)."
        else:
            raw_maint_impact = max(0.0, machine_age * 1.2)
            maint_explanation = f"Machine mechanical condition is within normal maintenance cycle ({maint_age}/{maint_interval} days)."

        # Factor B: Operating Speed vs Fabric Tolerance
        raw_speed_impact = 0.0
        speed_explanation = ""
        speed_ratio = speed / max(1.0, fabric_safe_speed)
        if speed_ratio > 1.20:
            pct_over = (speed_ratio - 1.0) * 100.0
            raw_speed_impact = min(100.0, (speed_ratio - 1.0) * 180.0)
            speed_explanation = f"Operating speed ({speed:.0f} RPM) is {pct_over:.0f}% higher than safe threshold for {f_type} ({fabric_safe_speed:.0f} RPM), creating yarn tension shock."
        elif speed_ratio > 1.08:
            pct_over = (speed_ratio - 1.0) * 100.0
            raw_speed_impact = 35.0
            speed_explanation = f"Speed ({speed:.0f} RPM) moderately exceeds recommended pace for {f_type} (+{pct_over:.0f}%)."
        elif speed_ratio < 0.70:
            raw_speed_impact = 15.0
            speed_explanation = f"Speed ({speed:.0f} RPM) is abnormally sluggish compared to standard {fabric_safe_speed:.0f} RPM."
        else:
            raw_speed_impact = 0.0
            speed_explanation = f"Operating speed ({speed:.0f} RPM) is well-matched to {f_type} safe limits ({fabric_safe_speed:.0f} RPM)."

        # Factor C: Atmospheric & Humidity Deviation
        raw_humidity_impact = 0.0
        humidity_explanation = ""
        if humidity_imputed:
            raw_humidity_impact = 25.0
            humidity_explanation = "Humidity telemetry was missing from loom sensors; imputed at standard baseline (55% RH)."
        elif humidity < 42.0:
            deficit = 55.0 - humidity
            raw_humidity_impact = min(100.0, 30.0 + (deficit * 3.5))
            humidity_explanation = f"Low relative humidity ({humidity:.1f}% RH) creates dry, brittle yarn fibers and severe static charge."
        elif humidity > 75.0:
            excess = humidity - 70.0
            raw_humidity_impact = min(100.0, 25.0 + (excess * 3.0))
            humidity_explanation = f"High relative humidity ({humidity:.1f}% RH) causes fiber moisture swelling and sluggish harness motion."
        else:
            raw_humidity_impact = 0.0
            humidity_explanation = f"Relative humidity ({humidity:.1f}% RH) is within optimal weaving range (50-65% RH)."

        # Factor D: Fabric Material Sensitivity & Complexity
        raw_fabric_impact = 0.0
        fabric_explanation = ""
        # High fragility fabrics have higher natural variance
        fragile_fabrics = {
            "Silk": {"difficulty": 30.0, "safe_rh": "60-65%"},
            "Viscose": {"difficulty": 25.0, "safe_rh": "55-65%"},
            "Wool": {"difficulty": 20.0, "safe_rh": "60-70%"},
            "Linen": {"difficulty": 15.0, "safe_rh": "55-65%"},
            "Cotton": {"difficulty": 5.0, "safe_rh": "50-65%"},
            "Polyester": {"difficulty": 0.0, "safe_rh": "45-60%"},
            "Denim": {"difficulty": 0.0, "safe_rh": "50-60%"}
        }
        fabric_info = fragile_fabrics.get(f_type, {"difficulty": 10.0, "safe_rh": "50-65%"})
        base_diff = fabric_info["difficulty"]
        if f_thresh["mean"] > 4.5:
            raw_fabric_impact = base_diff + ((f_thresh["mean"] - 3.5) * 6.0)
            fabric_explanation = f"{f_type} is a high-sensitivity weave (factory historical baseline {f_thresh['mean']:.2f}% avg waste)."
        else:
            raw_fabric_impact = base_diff
            fabric_explanation = f"{f_type} is a standard, resilient weave with low inherent fiber complexity."

        # Factor E: Thermal & Environmental Fluctuation
        raw_temp_impact = 0.0
        temp_explanation = ""
        if temperature > 33.0:
            t_excess = temperature - 30.0
            raw_temp_impact = min(80.0, 20.0 + (t_excess * 4.0))
            temp_explanation = f"High ambient temperature ({temperature:.1f}°C) degrades machine lubrication viscosity and synthetic yarn elongation."
        elif temperature < 18.0:
            raw_temp_impact = 20.0
            temp_explanation = f"Low ambient temperature ({temperature:.1f}°C) stiffens sizing chemicals and reduces loom flexibility."
        else:
            raw_temp_impact = 0.0
            temp_explanation = f"Ambient temperature ({temperature:.1f}°C) is in optimal operating comfort zone (20-28°C)."

        # Factor F: Shift & Operator Pacing Dynamics
        raw_shift_impact = 0.0
        shift_explanation = ""
        if shift == "Night":
            raw_shift_impact = 18.0
            shift_explanation = f"Night shift operations historically show higher pacing variance across weaving units."
        elif shift == "Evening":
            raw_shift_impact = 10.0
            shift_explanation = f"Evening shift operating cycle with moderate shift handover variance."
        else:
            raw_shift_impact = 0.0
            shift_explanation = f"Standard morning shift operating cycle."

        # ----------------------------------------------------
        # 2. FACTOR WEIGHTING & SHAP-LIKE PERCENTAGE NORMALIZATION
        # ----------------------------------------------------
        weighted_points = {
            "mechanical_maintenance": raw_maint_impact * 0.35,
            "operational_speed": raw_speed_impact * 0.30,
            "atmospheric_humidity": raw_humidity_impact * 0.15,
            "fabric_sensitivity": raw_fabric_impact * 0.08,
            "thermal_environment": raw_temp_impact * 0.06,
            "shift_operator": raw_shift_impact * 0.06
        }

        total_weighted_points = sum(weighted_points.values())
        total_risk_score = round(min(100.0, max(5.0, total_weighted_points)), 1)

        # Calculate percentages of total risk
        if total_weighted_points > 0:
            attribution_pcts = {
                k: round((v / total_weighted_points) * 100.0, 1)
                for k, v in weighted_points.items()
            }
        else:
            attribution_pcts = {k: 16.7 for k in weighted_points.keys()}

        # ----------------------------------------------------
        # 3. IDENTIFY PRIMARY AND SECONDARY ROOT CAUSES
        # ----------------------------------------------------
        cause_candidates = [
            {
                "category": self.CAT_MECHANICAL,
                "factor_key": "mechanical_maintenance",
                "raw_impact": raw_maint_impact,
                "weighted_points": round(weighted_points["mechanical_maintenance"], 1),
                "attribution_pct": attribution_pcts["mechanical_maintenance"],
                "title": f"Maintenance Overdue by {max(0, maint_age - maint_interval)} Days" if maint_age > maint_interval else "Mechanical Calibration Wear",
                "explanation": maint_explanation,
                "is_active": raw_maint_impact >= 20.0
            },
            {
                "category": self.CAT_OPERATIONAL,
                "factor_key": "operational_speed",
                "raw_impact": raw_speed_impact,
                "weighted_points": round(weighted_points["operational_speed"], 1),
                "attribution_pct": attribution_pcts["operational_speed"],
                "title": f"Excess Loom Speed ({speed:.0f} RPM vs {fabric_safe_speed:.0f} RPM Safe Limit)",
                "explanation": speed_explanation,
                "is_active": raw_speed_impact >= 20.0
            },
            {
                "category": self.CAT_ATMOSPHERIC,
                "factor_key": "atmospheric_humidity",
                "raw_impact": raw_humidity_impact,
                "weighted_points": round(weighted_points["atmospheric_humidity"], 1),
                "attribution_pct": attribution_pcts["atmospheric_humidity"],
                "title": f"Dry Yarn Brittleness ({humidity:.1f}% RH)" if humidity < 42.0 else (f"Excess Ambient Humidity ({humidity:.1f}% RH)" if humidity > 75.0 else "Missing Humidity Telemetry"),
                "explanation": humidity_explanation,
                "is_active": raw_humidity_impact >= 20.0
            },
            {
                "category": self.CAT_MATERIAL,
                "factor_key": "fabric_sensitivity",
                "raw_impact": raw_fabric_impact,
                "weighted_points": round(weighted_points["fabric_sensitivity"], 1),
                "attribution_pct": attribution_pcts["fabric_sensitivity"],
                "title": f"High Fragility Material Dynamics ({f_type})",
                "explanation": fabric_explanation,
                "is_active": raw_fabric_impact >= 18.0
            },
            {
                "category": self.CAT_THERMAL,
                "factor_key": "thermal_environment",
                "raw_impact": raw_temp_impact,
                "weighted_points": round(weighted_points["thermal_environment"], 1),
                "attribution_pct": attribution_pcts["thermal_environment"],
                "title": f"Thermal Stress ({temperature:.1f}°C)",
                "explanation": temp_explanation,
                "is_active": raw_temp_impact >= 20.0
            },
            {
                "category": self.CAT_OPERATOR,
                "factor_key": "shift_operator",
                "raw_impact": raw_shift_impact,
                "weighted_points": round(weighted_points["shift_operator"], 1),
                "attribution_pct": attribution_pcts["shift_operator"],
                "title": f"{shift} Shift Operating Variance",
                "explanation": shift_explanation,
                "is_active": raw_shift_impact >= 15.0
            }
        ]

        # Sort candidates by weighted points descending
        sorted_causes = sorted(cause_candidates, key=lambda x: x["weighted_points"], reverse=True)

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

        # Severity determination
        if total_risk_score >= settings.get("risk_threshold_high", 70.0) or (primary_cause["raw_impact"] >= 65.0):
            severity = "CRITICAL"
        elif total_risk_score >= settings.get("risk_threshold_warning", 40.0) or (primary_cause["raw_impact"] >= 35.0):
            severity = "HIGH"
        elif total_risk_score >= 25.0:
            severity = "MODERATE"
        else:
            severity = "NOMINAL"

        # ----------------------------------------------------
        # 4. PRESCRIPTIVE REMEDIATION PLAYBOOK GENERATION
        # ----------------------------------------------------
        playbook = []
        step_idx = 1

        # Playbook item 1: Maintenance actions
        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            est_saving = min(4.5, 1.5 + (days_over * 0.08))
            playbook.append({
                "step": step_idx,
                "priority": "CRITICAL",
                "category": self.CAT_MECHANICAL,
                "action": f"Halt non-urgent batches on Machine {m_id} and perform preventive overhaul (overdue by {days_over} days).",
                "technical_details": f"Inspect rapier guide hooks, replace worn heald wires, and replenish gearbox synthetic lubricant.",
                "estimated_waste_reduction_pct": round(est_saving, 2),
                "estimated_kg_saved": round((est_saving / 100.0) * total_prod, 1)
            })
            step_idx += 1
        elif maint_age > maint_interval * 0.8:
            playbook.append({
                "step": step_idx,
                "priority": "MEDIUM",
                "category": self.CAT_MECHANICAL,
                "action": f"Schedule maintenance window for Machine {m_id} within next {maint_interval - maint_age} days.",
                "technical_details": "Perform scheduled lubrication and reed alignment before heavy weave batches.",
                "estimated_waste_reduction_pct": 0.8,
                "estimated_kg_saved": round(0.008 * total_prod, 1)
            })
            step_idx += 1

        # Playbook item 2: Speed actions
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

        # Playbook item 3: Humidity actions
        if humidity_imputed:
            playbook.append({
                "step": step_idx,
                "priority": "HIGH",
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
        elif humidity > 75.0:
            playbook.append({
                "step": step_idx,
                "priority": "MEDIUM",
                "category": self.CAT_ATMOSPHERIC,
                "action": f"Activate HVAC dehumidification cycle in Loom Bay (current: {humidity:.1f}% RH).",
                "technical_details": "Excess humidity swells fiber diameter and increases reed friction.",
                "estimated_waste_reduction_pct": 0.9,
                "estimated_kg_saved": round(0.009 * total_prod, 1)
            })
            step_idx += 1

        # Playbook item 4: Temperature / Shift
        if temperature > 32.0:
            playbook.append({
                "step": step_idx,
                "priority": "LOW",
                "category": self.CAT_THERMAL,
                "action": f"Engage bay chillers to reduce ambient temperature to 24-27°C (current: {temperature:.1f}°C).",
                "technical_details": "Prevents machine motor overheating and keeps yarn sizing binder polymers stable.",
                "estimated_waste_reduction_pct": 0.6,
                "estimated_kg_saved": round(0.006 * total_prod, 1)
            })
            step_idx += 1

        if not playbook:
            playbook.append({
                "step": 1,
                "priority": "NORMAL",
                "category": "Standard Operating Procedure",
                "action": f"Maintain standard operating parameters and continue routine visual loom inspection.",
                "technical_details": "Machine and atmospheric settings are within optimal efficiency envelopes.",
                "estimated_waste_reduction_pct": 0.0,
                "estimated_kg_saved": 0.0
            })

        # ----------------------------------------------------
        # 5. COUNTERFACTUAL "WHAT-IF" OPTIMIZER
        # Calculate ideal setpoints to bring risk score < 35 (NORMAL)
        # ----------------------------------------------------
        target_speed = min(speed, fabric_safe_speed)
        target_hum = 58.0 if (humidity < 45.0 or humidity > 75.0 or humidity_imputed) else humidity
        target_maint_age = min(maint_age, 15) if maint_age > maint_interval else maint_age
        target_temp = 24.0 if (temperature > 32.0 or temperature < 18.0) else temperature

        # Simulate waste savings if optimal targets are met
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
            "batch_id": batch.get("batch_id", "N/A"),
            "machine_id": m_id,
            "fabric_type": f_type,
            "current_waste_percentage": round(waste_pct, 2),
            "current_risk_score": total_risk_score,
            "severity": severity,
            "primary_cause": primary_cause,
            "secondary_causes": secondary_causes,
            "attributions": {
                "mechanical_maintenance": {
                    "label": "Maintenance & Machine Wear",
                    "impact_points": round(weighted_points["mechanical_maintenance"], 1),
                    "attribution_pct": attribution_pcts["mechanical_maintenance"],
                    "category": self.CAT_MECHANICAL,
                    "explanation": maint_explanation
                },
                "operational_speed": {
                    "label": "Operating Speed vs Fabric Safe Limit",
                    "impact_points": round(weighted_points["operational_speed"], 1),
                    "attribution_pct": attribution_pcts["operational_speed"],
                    "category": self.CAT_OPERATIONAL,
                    "explanation": speed_explanation
                },
                "atmospheric_humidity": {
                    "label": "Ambient Humidity Deviation",
                    "impact_points": round(weighted_points["atmospheric_humidity"], 1),
                    "attribution_pct": attribution_pcts["atmospheric_humidity"],
                    "category": self.CAT_ATMOSPHERIC,
                    "explanation": humidity_explanation
                },
                "fabric_sensitivity": {
                    "label": "Fabric Material Complexity",
                    "impact_points": round(weighted_points["fabric_sensitivity"], 1),
                    "attribution_pct": attribution_pcts["fabric_sensitivity"],
                    "category": self.CAT_MATERIAL,
                    "explanation": fabric_explanation
                },
                "thermal_environment": {
                    "label": "Thermal Environment",
                    "impact_points": round(weighted_points["thermal_environment"], 1),
                    "attribution_pct": attribution_pcts["thermal_environment"],
                    "category": self.CAT_THERMAL,
                    "explanation": temp_explanation
                },
                "shift_operator": {
                    "label": "Shift & Operator Pacing",
                    "impact_points": round(weighted_points["shift_operator"], 1),
                    "attribution_pct": attribution_pcts["shift_operator"],
                    "category": self.CAT_OPERATOR,
                    "explanation": shift_explanation
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

        warn_thresh = settings.get("risk_threshold_warning", 40.0)
        high_thresh = settings.get("risk_threshold_high", 70.0)
        maint_interval = int(settings.get("maintenance_interval_days", 60))

        # Create cloned batch with modified parameters
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

        # Estimate simulated waste percentage based on risk deviation
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
                "top_plant_recommendations": []
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

        # Scan batches to aggregate causes
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

                    # Tally savings from top playbook step
                    if diag.get("prescriptive_playbook"):
                        top_step = diag["prescriptive_playbook"][0]
                        saved_kg = top_step.get("estimated_kg_saved", 0.0)
                        specific_causes[title]["potential_savings_kg"] += saved_kg
                        total_potential_waste_kg_saved += saved_kg

                    # Machine breakdown
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

        # Build Pareto distribution
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

        # Category distribution percentages
        cat_dist = {}
        for cat, cnt in category_counts.items():
            cat_dist[cat] = {
                "count": cnt,
                "percentage": round((cnt / total_failure_events) * 100.0, 1) if total_failure_events > 0 else 0.0
            }

        # Strategic Plant Recommendations
        top_recs = []
        if category_counts[self.CAT_MECHANICAL] > 0:
            top_recs.append({
                "rank": 1,
                "title": "Establish Stricter Preventive Maintenance Cadence",
                "impact": f"Responsible for {cat_dist[self.CAT_MECHANICAL]['percentage']}% of abnormal waste events.",
                "action": "Enforce mandatory loom shutdown and overhaul when machine reaches 60-day service limit."
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

        return {
            "total_batches_analyzed": len(valid_df),
            "total_failure_events": total_failure_events,
            "total_potential_waste_kg_saved": round(total_potential_waste_kg_saved, 1),
            "pareto_causes": pareto_list[:10],
            "category_distribution": cat_dist,
            "machine_root_causes": list(machine_cause_matrix.values()),
            "top_plant_recommendations": top_recs
        }
