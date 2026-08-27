"""
Machine Learning and Hybrid Risk Classification Engine for Textile Waste Prediction.
Combines Random Forest, Isolation Forest Anomaly Detection, and Adaptive Statistical Baselines
to produce normalized Risk Scores (0-100), Risk Classifications, and Confidence levels.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

from backend.baseline_analyzer import BaselineAnalyzer
from backend.root_cause_ai import RootCauseAIEngine


class TextileRiskMLEngine:
    """
    Hybrid ML Engine combining supervised classification, anomaly detection,
    and adaptive baseline rules with Root-Cause AI explainability.
    """

    def __init__(self, baseline_analyzer: BaselineAnalyzer):
        self.baseline_analyzer = baseline_analyzer
        self.root_cause_engine = RootCauseAIEngine()
        self.classifier: Optional[Pipeline] = None
        self.anomaly_detector: Optional[IsolationForest] = None
        self.is_trained = False
        self.feature_columns = [
            "machine_id", "fabric_type", "shift", "operator",
            "total_production", "production_speed", "machine_age",
            "maintenance_age_days", "humidity", "temperature",
            "speed_dev_from_fabric", "maintenance_overdue_flag"
        ]

    def _engineer_features(self, df: pd.DataFrame, maintenance_interval_days: int = 60) -> pd.DataFrame:
        """Derives engineered interaction and deviation features."""
        df_feat = df.copy()

        # Compute speed deviation from fabric baseline
        fabric_speeds = {}
        if self.baseline_analyzer and self.baseline_analyzer.fabric_stats:
            fabric_speeds = {k: v["mean_speed"] for k, v in self.baseline_analyzer.fabric_stats.items()}

        def get_fabric_speed_dev(row):
            f_type = row.get("fabric_type", "Cotton")
            avg_speed = fabric_speeds.get(f_type, 800.0)
            cur_speed = float(row.get("production_speed", 800.0))
            return cur_speed - avg_speed

        df_feat["speed_dev_from_fabric"] = df_feat.apply(get_fabric_speed_dev, axis=1)

        # Maintenance overdue flag
        df_feat["maintenance_overdue_flag"] = (
            df_feat["maintenance_age_days"] > maintenance_interval_days
        ).astype(int)

        # Fill missing values safely
        if "humidity" in df_feat:
            df_feat["humidity"] = df_feat["humidity"].fillna(55.0)
        if "temperature" in df_feat:
            df_feat["temperature"] = df_feat["temperature"].fillna(25.0)

        return df_feat

    def train(self, df: pd.DataFrame, maintenance_interval_days: int = 60):
        """
        Trains the Random Forest Classifier and Isolation Forest Anomaly Detector
        on historical valid batches.
        """
        valid_df = df[df["is_valid"] == 1].copy()
        if len(valid_df) < 10:
            # Need minimum samples for stable ML
            self.is_trained = False
            return

        # Prepare target class if not already existing
        # Risk levels: NORMAL, WARNING, HIGH RISK based on waste % and anomalies
        if "risk_level" not in valid_df.columns or valid_df["risk_level"].nunique() < 2:
            # Create synthetic target based on IQR bounds
            q1 = valid_df["waste_percentage"].quantile(0.25)
            q3 = valid_df["waste_percentage"].quantile(0.75)
            iqr = max(0.5, q3 - q1)
            high_bound = q3 + 1.5 * iqr
            warn_bound = q3 + 0.5 * iqr

            def assign_label(val):
                if val >= high_bound:
                    return "HIGH RISK"
                elif val >= warn_bound:
                    return "WARNING"
                else:
                    return "NORMAL"

            valid_df["risk_level"] = valid_df["waste_percentage"].apply(assign_label)

        df_feat = self._engineer_features(valid_df, maintenance_interval_days)

        categorical_cols = ["machine_id", "fabric_type", "shift", "operator"]
        numeric_cols = [
            "total_production", "production_speed", "machine_age",
            "maintenance_age_days", "humidity", "temperature",
            "speed_dev_from_fabric", "maintenance_overdue_flag"
        ]

        # Build sklearn pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols),
                ("num", StandardScaler(), numeric_cols)
            ]
        )

        clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            class_weight="balanced"
        )

        self.classifier = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", clf)
        ])

        X = df_feat[categorical_cols + numeric_cols]
        y = valid_df["risk_level"]

        self.classifier.fit(X, y)

        # Train Isolation Forest on numeric features for multi-dimensional anomaly detection
        iso_features = df_feat[numeric_cols].values
        self.anomaly_detector = IsolationForest(
            n_estimators=100,
            contamination=0.08,
            random_state=42
        )
        self.anomaly_detector.fit(iso_features)

        self.is_trained = True

    def predict_batch(
        self,
        batch: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a single production batch and returns:
        - risk_level ('NORMAL', 'WARNING', 'HIGH RISK')
        - risk_score (0-100)
        - confidence_score (0-100)
        - is_abnormal (bool)
        - explanation reasons (List[str])
        - recommended actions (List[str])
        - factor_contributions (Dict)
        """
        if settings is None:
            settings = {
                "risk_threshold_warning": 40.0,
                "risk_threshold_high": 70.0,
                "maintenance_interval_days": 60,
                "iqr_multiplier": 1.5,
                "z_score_threshold": 2.0
            }

        warn_thresh = settings.get("risk_threshold_warning", 40.0)
        high_thresh = settings.get("risk_threshold_high", 70.0)
        maint_interval = settings.get("maintenance_interval_days", 60)

        # Check validity (Zero production edge case)
        if not batch.get("is_valid", True):
            return {
                "risk_level": "INVALID",
                "risk_score": 0.0,
                "confidence_score": 0.0,
                "is_abnormal": True,
                "is_new_machine": False,
                "reasons": [
                    "Invalid batch: production quantity is zero. Waste percentage cannot be calculated.",
                    "Waste percentage cannot be computed due to division by zero."
                ],
                "actions": [
                    "Verify raw production meter and enter valid total production quantity.",
                    "Exclude batch from statistical KPI aggregates until corrected."
                ],
                "reason_cards": [
                    {
                        "id": "zero_production",
                        "title": "Invalid Production Quantity (Zero Production)",
                        "severity": "CRITICAL",
                        "badge_color": "danger",
                        "icon": "fa-triangle-exclamation",
                        "observed": "0 kg Production",
                        "benchmark": "> 0 kg Valid Production",
                        "impact": "Division by zero prevents calculation of waste percentage and risk classification.",
                        "evidence_text": "Invalid batch: production quantity is zero. Waste percentage cannot be calculated."
                    }
                ],
                "preventive_solutions": [
                    {
                        "reason_id": "zero_production",
                        "title": "Verify Production Telemetry",
                        "icon": "fa-clipboard-check",
                        "solution": "Inspect meter sensor at Loom Bay and enter valid total production quantity before continuing.",
                        "priority": "CRITICAL"
                    }
                ],
                "recommended_action_plan": {
                    "risk_level": "INVALID",
                    "badge_class": "badge-danger",
                    "summary": "Invalid batch: production quantity is zero. Waste percentage cannot be calculated.",
                    "protocol": "Inspect → Adjust → Maintain → Monitor",
                    "steps": [
                        "Verify raw production meter reading at loom controller.",
                        "Input valid total production quantity greater than zero.",
                        "Re-run prediction analysis after data correction."
                    ]
                },
                "factor_contributions": {}
            }

        # Extract features
        m_id = batch.get("machine_id", "M01")
        f_type = batch.get("fabric_type", "Cotton")
        waste_pct = float(batch.get("waste_percentage", 0.0))
        prod_qty = float(batch.get("total_production", 1000.0))
        speed = float(batch.get("production_speed", 800.0))
        maint_age = int(batch.get("maintenance_age_days", 30))
        machine_age = float(batch.get("machine_age", 3.0))
        humidity = float(batch.get("humidity", 55.0))
        temperature = float(batch.get("temperature", 25.0))
        humidity_imputed = bool(batch.get("humidity_imputed", False))

        # Get baselines
        m_thresh = self.baseline_analyzer.get_machine_thresholds(m_id)
        f_thresh = self.baseline_analyzer.get_fabric_thresholds(f_type)
        factory = self.baseline_analyzer.factory_stats or {
            "mean_waste_pct": 4.0, "std_waste_pct": 1.5, "iqr_upper_bound": 6.5, "mean_speed": 800.0
        }

        # Cold-Start / New Machine check
        is_new_machine = not m_thresh.get("has_history", False)
        base_confidence = 70.0 if is_new_machine else 95.0
        if humidity_imputed:
            base_confidence -= 10.0

        # Statistical Deviation Scoring
        # 1. Machine & Fabric Baseline Deviation
        target_mean = m_thresh["mean"] if not is_new_machine else f_thresh["mean"]
        target_std = max(0.5, m_thresh["std"] if not is_new_machine else f_thresh["std"])
        z_score = (waste_pct - target_mean) / target_std

        # 2. IQR Upper Bound Anomaly Check
        iqr_upper = m_thresh["upper_threshold"] if not is_new_machine else f_thresh["upper_threshold"]
        is_stat_abnormal = waste_pct > iqr_upper or z_score > settings.get("z_score_threshold", 2.0)

        # 3. Factor-wise Risk Contributions (0 - 100 scale components)
        # Component A: Waste Percentage Deviation (Weight: 45%)
        # Base expected range 0 - 10%
        waste_component = min(100.0, max(0.0, (waste_pct / max(0.1, target_mean)) * 35.0 if waste_pct > target_mean else (waste_pct / max(0.1, target_mean)) * 20.0))
        if is_stat_abnormal:
            waste_component = min(100.0, waste_component + 25.0)

        # Component B: Maintenance Health (Weight: 20%)
        maint_component = 0.0
        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            maint_component = min(100.0, 50.0 + (days_over * 1.5))
        elif maint_age > maint_interval * 0.7:
            maint_component = 30.0

        # Component C: Production Speed vs Fabric Safe Speed (Weight: 20%)
        safe_speed = f_thresh.get("mean_speed", 800.0)
        speed_ratio = speed / max(1.0, safe_speed)
        speed_component = 0.0
        if speed_ratio > 1.2:
            speed_component = min(100.0, (speed_ratio - 1.0) * 150.0)
        elif speed_ratio > 1.05:
            speed_component = 25.0

        # Component D: Machine Age & Environmental Factors (Weight: 15%)
        env_component = 0.0
        if machine_age > 8.0:
            env_component += 25.0
        if humidity < 40.0 or humidity > 75.0:
            env_component += 25.0
        if temperature < 18.0 or temperature > 34.0:
            env_component += 20.0
        env_component = min(100.0, env_component)

        # Combined Rule-grounded Risk Score
        rule_risk_score = (
            waste_component * 0.45 +
            maint_component * 0.20 +
            speed_component * 0.20 +
            env_component * 0.15
        )

        # ML Model Inference (if trained)
        ml_risk_score = rule_risk_score
        is_ml_anomaly = False

        if self.is_trained and self.classifier is not None:
            try:
                row_dict = {
                    "machine_id": [m_id],
                    "fabric_type": [f_type],
                    "shift": [batch.get("shift", "Morning")],
                    "operator": [batch.get("operator", "Operator A")],
                    "total_production": [prod_qty],
                    "production_speed": [speed],
                    "machine_age": [machine_age],
                    "maintenance_age_days": [maint_age],
                    "humidity": [humidity],
                    "temperature": [temperature],
                    "speed_dev_from_fabric": [speed - safe_speed],
                    "maintenance_overdue_flag": [1 if maint_age > maint_interval else 0]
                }
                df_single = pd.DataFrame(row_dict)
                probs = self.classifier.predict_proba(df_single)[0]
                classes = list(self.classifier.classes_)

                p_norm = probs[classes.index("NORMAL")] if "NORMAL" in classes else 0.0
                p_warn = probs[classes.index("WARNING")] if "WARNING" in classes else 0.0
                p_high = probs[classes.index("HIGH RISK")] if "HIGH RISK" in classes else 0.0

                ml_risk_score = (p_warn * 55.0) + (p_high * 95.0)

                # Unsupervised Anomaly Detection
                if self.anomaly_detector is not None:
                    num_feats = df_single[[
                        "total_production", "production_speed", "machine_age",
                        "maintenance_age_days", "humidity", "temperature",
                        "speed_dev_from_fabric", "maintenance_overdue_flag"
                    ]].values
                    iso_pred = self.anomaly_detector.predict(num_feats)[0]
                    is_ml_anomaly = (iso_pred == -1)

            except Exception:
                ml_risk_score = rule_risk_score

        # Hybrid Score Aggregation
        # If new machine, weight rules heavily; otherwise 50/50 blend with ML
        if is_new_machine or not self.is_trained:
            final_risk_score = rule_risk_score
        else:
            final_risk_score = (rule_risk_score * 0.5) + (ml_risk_score * 0.5)

        # Cap and round risk score (0 - 100)
        final_risk_score = round(max(0.0, min(100.0, final_risk_score)), 1)

        # Classification based on user-configured thresholds
        if final_risk_score >= high_thresh:
            risk_level = "HIGH RISK"
        elif final_risk_score >= warn_thresh:
            risk_level = "WARNING"
        else:
            risk_level = "NORMAL"

        is_abnormal = bool(is_stat_abnormal or is_ml_anomaly or (risk_level == "HIGH RISK"))

        # Compile Explainability & Action Traces
        reasons, actions = self._generate_explanations(
            batch=batch,
            risk_level=risk_level,
            risk_score=float(final_risk_score),
            m_thresh=m_thresh,
            f_thresh=f_thresh,
            is_new_machine=bool(is_new_machine),
            maint_interval=int(maint_interval),
            z_score=float(z_score)
        )

        # Deep Root-Cause AI Diagnosis & Explainability
        enriched_batch = dict(batch)
        enriched_batch.update({
            "risk_level": str(risk_level),
            "risk_score": float(final_risk_score),
            "confidence_score": float(round(max(10.0, min(100.0, base_confidence)), 1)),
            "is_abnormal": bool(is_abnormal)
        })
        root_cause_diag = self.root_cause_engine.diagnose_batch(
            batch=enriched_batch,
            baseline_analyzer=self.baseline_analyzer,
            settings=settings
        )

        return {
            "risk_level": str(risk_level),
            "risk_score": float(final_risk_score),
            "confidence_score": float(round(max(10.0, min(100.0, base_confidence)), 1)),
            "is_abnormal": bool(is_abnormal),
            "is_new_machine": bool(is_new_machine),
            "reasons": list(reasons),
            "actions": list(actions),
            "reason_cards": root_cause_diag.get("reason_cards", []),
            "preventive_solutions": root_cause_diag.get("preventive_solutions", []),
            "recommended_action_plan": root_cause_diag.get("recommended_action_plan", {}),
            "factor_contributions": {
                "waste_deviation": float(round(waste_component, 1)),
                "maintenance_health": float(round(maint_component, 1)),
                "speed_stress": float(round(speed_component, 1)),
                "environment_age": float(round(env_component, 1))
            },
            "root_cause_analysis": root_cause_diag
        }

    def _generate_explanations(
        self,
        batch: Dict[str, Any],
        risk_level: str,
        risk_score: float,
        m_thresh: Dict[str, Any],
        f_thresh: Dict[str, Any],
        is_new_machine: bool,
        maint_interval: int,
        z_score: float
    ) -> Tuple[List[str], List[str]]:
        """Generates clear, factory-supervisor understandable reasons and actionable advice."""
        reasons = []
        actions = []

        m_id = batch.get("machine_id", "M01")
        f_type = batch.get("fabric_type", "Cotton")
        waste_pct = float(batch.get("waste_percentage", 0.0))
        speed = float(batch.get("production_speed", 800.0))
        maint_age = int(batch.get("maintenance_age_days", 30))
        m_age = float(batch.get("machine_age", 3.0))
        humidity = float(batch.get("humidity", 55.0))
        hum_imputed = bool(batch.get("humidity_imputed", False))

        # Reason 1: Waste Percentage vs Machine / Fabric Baseline
        if is_new_machine:
            reasons.append(
                f"New machine '{m_id}' has limited historical data; evaluated against {f_type} baseline ({f_thresh['mean']:.1f}% avg waste)."
            )
        elif waste_pct > m_thresh["mean"] * 1.3:
            diff_ratio = (waste_pct / max(0.1, m_thresh["mean"]))
            reasons.append(
                f"Waste percentage ({waste_pct:.2f}%) is {diff_ratio:.1f}x higher than Machine {m_id}'s historical baseline ({m_thresh['mean']:.2f}% avg)."
            )
        elif waste_pct <= m_thresh["mean"]:
            reasons.append(
                f"Waste percentage ({waste_pct:.2f}%) is within the optimal operating baseline for Machine {m_id} ({m_thresh['mean']:.2f}% avg)."
            )

        # Reason 2: Maintenance Status
        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            reasons.append(
                f"Machine maintenance is overdue by {days_over} days (last serviced {maint_age} days ago; interval limit is {maint_interval} days)."
            )
            actions.append(f"Schedule immediate preventive maintenance and mechanical alignment for {m_id}.")
        elif maint_age > maint_interval * 0.75:
            reasons.append(
                f"Machine maintenance is approaching due date ({maint_age}/{maint_interval} days)."
            )
            actions.append(f"Prepare maintenance slot for {m_id} within next {maint_interval - maint_age} days.")

        # Reason 3: Production Speed Check
        fabric_safe_speed = f_thresh.get("mean_speed", 800.0)
        if speed > fabric_safe_speed * 1.15:
            pct_high = ((speed - fabric_safe_speed) / fabric_safe_speed) * 100.0
            reasons.append(
                f"Production speed ({speed:.0f} rpm) is {pct_high:.0f}% higher than recommended safe speed for {f_type} ({fabric_safe_speed:.0f} rpm)."
            )
            actions.append(f"Reduce production speed to below {fabric_safe_speed * 1.05:.0f} rpm to avoid yarn breakage and tension defects.")
        elif speed < fabric_safe_speed * 0.7:
            reasons.append(
                f"Production speed ({speed:.0f} rpm) is substantially lower than standard operating pace."
            )

        # Reason 4: Environmental & Missing Humidity
        if hum_imputed:
            reasons.append(
                "Ambient humidity was missing in input and imputed at standard baseline (55.0%); sensor check recommended."
            )
            actions.append("Inspect Loom Bay humidity transmitter to restore real-time environmental telemetry.")
        elif humidity < 40.0:
            reasons.append(
                f"Low relative humidity ({humidity:.1f}%) increases yarn static charge and fiber brittleness."
            )
            actions.append("Increase weaving room humidifier output to achieve 55–65% RH.")
        elif humidity > 75.0:
            reasons.append(
                f"High humidity ({humidity:.1f}%) may cause fabric dampness and sluggish machine movement."
            )

        # Reason 5: High Production / High Absolute Waste Edge Case clarification
        prod_qty = float(batch.get("total_production", 1000.0))
        waste_qty = float(batch.get("waste_quantity", 0.0))
        if prod_qty >= 3000 and waste_pct <= 3.0:
            reasons.append(
                f"High production volume ({prod_qty:.0f} kg) produced {waste_qty:.0f} kg waste, but waste percentage ({waste_pct:.2f}%) remains healthy and within tolerance."
            )

        # Default fallback reasons & actions if list is short
        if risk_level == "NORMAL":
            if not actions:
                actions.append("Maintain current machine speeds and regular operating inspection schedule.")
            reasons.append("All primary production, mechanical, and ambient telemetry variables are within nominal limits.")
        elif risk_level in ["WARNING", "HIGH RISK"]:
            if not actions:
                actions.append(f"Perform loom tension inspection on {m_id} and monitor upcoming batch.")
                actions.append(f"Verify raw material quality batch for {f_type}.")

        return reasons, actions
