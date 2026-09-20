"""
Machine Learning and Hybrid Risk Classification Engine for Textile Waste Prediction.
Combines Random Forest, Isolation Forest Anomaly Detection, and Adaptive Statistical Baselines
to produce normalized Risk Scores (0-100), Risk Classifications, and Confidence levels.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

from backend.baseline_analyzer import BaselineAnalyzer
from backend.root_cause_ai import RootCauseAIEngine


class TextileRiskMLEngine:
    """
    Hybrid ML Engine combining supervised classification, continuous regression,
    anomaly detection, and adaptive baseline rules with Root-Cause AI explainability.
    """

    def __init__(self, baseline_analyzer: BaselineAnalyzer):
        self.baseline_analyzer = baseline_analyzer
        self.root_cause_engine = RootCauseAIEngine()
        self.classifier: Optional[Pipeline] = None
        self.regressor: Optional[Pipeline] = None
        self.anomaly_detector: Optional[IsolationForest] = None
        self.is_trained = False
        self.regression_metrics: Dict[str, Any] = {
            "mae": 0.0,
            "rmse": 0.0,
            "r2": 0.0,
            "sample_count": 0
        }
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
        Trains the Random Forest Classifier, Random Forest Regressor, and Isolation Forest
        Anomaly Detector on historical valid batches.
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

        # Build sklearn preprocessor
        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols),
                ("num", StandardScaler(), numeric_cols)
            ]
        )

        # 1. Classification Pipeline
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
        y_class = valid_df["risk_level"]
        self.classifier.fit(X, y_class)

        # 2. Continuous Regression Pipeline for Expected Waste Percentage
        reg_preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols),
                ("num", StandardScaler(), numeric_cols)
            ]
        )
        reg = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        self.regressor = Pipeline(steps=[
            ("preprocessor", reg_preprocessor),
            ("regressor", reg)
        ])
        y_waste = valid_df["waste_percentage"].values
        self.regressor.fit(X, y_waste)

        # Calculate Regression Evaluation Metrics
        y_pred = self.regressor.predict(X)
        mae = float(mean_absolute_error(y_waste, y_pred))
        rmse = float(root_mean_squared_error(y_waste, y_pred))
        r2 = float(r2_score(y_waste, y_pred))
        self.regression_metrics = {
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "r2": round(r2, 3),
            "sample_count": len(valid_df)
        }

        # 3. Multi-dimensional Anomaly Detection
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
        raw_waste_pct = batch.get("waste_percentage")
        waste_pct = float(raw_waste_pct) if raw_waste_pct is not None else 0.0
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

        # 3. Primary Base Waste Score (0 - 100)
        waste_ratio = waste_pct / max(0.5, target_mean)
        if waste_pct <= 0.0:
            base_waste_score = 0.0
        elif waste_ratio <= 0.85:
            # Low waste (< 85% of mean) -> 5 to 18 score (Excellent)
            base_waste_score = (waste_ratio / 0.85) * 18.0
        elif waste_ratio <= 1.25:
            # Normal waste (85% to 125% of mean) -> 18 to 36 score (NORMAL)
            norm_prog = (waste_ratio - 0.85) / 0.40
            base_waste_score = 18.0 + (norm_prog * 18.0)
        elif waste_ratio <= 1.75:
            # Elevated waste (125% to 175% of mean) -> 42 to 66 score (WARNING)
            warn_prog = (waste_ratio - 1.25) / 0.50
            base_waste_score = 42.0 + (warn_prog * 24.0)
        else:
            # Severe waste (> 175% of mean) -> 72 to 98 score (HIGH RISK)
            high_prog = min(1.0, (waste_ratio - 1.75) / 1.0)
            base_waste_score = 72.0 + (high_prog * 24.0)

        # Absolute waste percentage threshold safeguard (plant-wide safety envelope)
        factory_iqr = factory.get("iqr_upper_bound", 6.5)
        if waste_pct >= 8.5:
            base_waste_score = max(base_waste_score, high_thresh + min(25.0, (waste_pct - 8.5) * 3.0))
        elif waste_pct >= factory_iqr:
            base_waste_score = max(base_waste_score, warn_thresh + min(25.0, (waste_pct - factory_iqr) * 8.0))

        # If statistically abnormal, guarantee base waste score reaches high threshold tier
        if is_stat_abnormal and base_waste_score < high_thresh:
            base_waste_score = max(base_waste_score, high_thresh + min(20.0, max(0.0, z_score - 2.0) * 5.0))

        # 4. Multi-Factor Modifiers (Speed, Maintenance, Environment, Age)
        # Component B: Maintenance Health
        maint_penalty = 0.0
        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            maint_penalty = min(28.0, 10.0 + (days_over * 0.7))
        elif maint_age > maint_interval * 0.8:
            maint_penalty = 6.0

        # Component C: Production Speed vs Fabric Safe Speed
        safe_speed = f_thresh.get("mean_speed", 800.0)
        speed_ratio = speed / max(1.0, safe_speed)
        speed_penalty = 0.0
        if speed_ratio > 1.20:
            speed_penalty = min(28.0, 12.0 + (speed_ratio - 1.20) * 70.0)
        elif speed_ratio > 1.08:
            speed_penalty = 6.0

        # Component D: Machine Age & Environmental Factors
        env_penalty = 0.0
        if machine_age > 8.0:
            env_penalty += 5.0
        if humidity < 38.0 or humidity > 75.0:
            env_penalty += 5.0
        if temperature < 18.0 or temperature > 33.0:
            env_penalty += 4.0

        # Factor contributions for UI bars (0 - 100 scale)
        waste_component = min(100.0, base_waste_score)
        maint_component = min(100.0, maint_penalty * 3.5)
        speed_component = min(100.0, speed_penalty * 3.5)
        env_component = min(100.0, env_penalty * 6.5)

        # Combined Rule-grounded Risk Score
        if base_waste_score >= high_thresh:
            rule_risk_score = min(100.0, base_waste_score + (maint_penalty * 0.3) + (speed_penalty * 0.3) + (env_penalty * 0.2))
        elif base_waste_score >= warn_thresh:
            rule_risk_score = min(100.0, base_waste_score + (maint_penalty * 0.5) + (speed_penalty * 0.5) + (env_penalty * 0.3))
        else:
            rule_risk_score = min(100.0, base_waste_score + maint_penalty + speed_penalty + env_penalty)

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

                ml_risk_score = (p_norm * 10.0) + (p_warn * 55.0) + (p_high * 95.0)

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

        # Hybrid Score Aggregation:
        # If waste is abnormal or high, ML must not dilute critical alarm
        if is_stat_abnormal or base_waste_score >= high_thresh:
            final_risk_score = max(rule_risk_score, ml_risk_score)
        elif is_new_machine or not self.is_trained:
            final_risk_score = rule_risk_score
        elif rule_risk_score >= warn_thresh:
            # If rules flagged WARNING (e.g. overdue maintenance, speed penalty), preserve risk escalation
            blended = (rule_risk_score * 0.70) + (ml_risk_score * 0.30)
            final_risk_score = max(rule_risk_score, blended)
        else:
            final_risk_score = (rule_risk_score * 0.70) + (ml_risk_score * 0.30)

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

        # Pre-production Expected Waste Forecast
        expected_forecast = self.predict_expected_waste(batch, settings)

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
            "expected_waste_percentage": expected_forecast.get("expected_waste_percentage"),
            "expected_waste_kg": expected_forecast.get("expected_waste_kg"),
            "expected_good_production_kg": expected_forecast.get("expected_good_production_kg"),
            "likely_range_pct": expected_forecast.get("likely_range_pct"),
            "likely_range_kg": expected_forecast.get("likely_range_kg"),
            "historical_comparison": expected_forecast.get("historical_comparison", {}),
            "expected_vs_actual": expected_forecast.get("expected_vs_actual"),
            "factor_contributions": {
                "waste_deviation": float(round(waste_component, 1)),
                "maintenance_health": float(round(maint_component, 1)),
                "speed_stress": float(round(speed_component, 1)),
                "environment_age": float(round(env_component, 1))
            },
            "root_cause_analysis": root_cause_diag
        }

    def predict_expected_waste(
        self,
        batch: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Continuous Machine Learning Regression and Multi-Factor Prediction of Expected Waste (Pre-Production).
        Predicts:
        - expected_waste_percentage (%)
        - expected_waste_kg (kg)
        - expected_good_production_kg (kg)
        - likely_range_pct & likely_range_kg (uncertainty interval)
        - risk_level ('NORMAL', 'WARNING', 'HIGH RISK')
        - risk_score (0 - 100)
        - historical_comparison (Multi-level comparison matrix)
        - reasons ("WHY IS THIS WASTE EXPECTED?")
        - preventive_solutions ("HOW CAN THE EXPECTED WASTE BE REDUCED?")
        - recommended_action_plan (Inspect -> Adjust -> Maintain -> Monitor)
        - expected_vs_actual (if actual waste is provided)
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
        prod_qty = float(batch.get("total_production", 0.0))

        # 1. Edge Case: Zero Production Guard
        if prod_qty <= 0:
            return {
                "is_valid": False,
                "validation_error": "Production quantity must be greater than 0 kg.",
                "expected_waste_percentage": None,
                "expected_waste_kg": None,
                "expected_good_production_kg": None,
                "likely_range_pct": None,
                "likely_range_kg": None,
                "risk_level": "INVALID",
                "risk_score": 0.0,
                "confidence_score": 0.0,
                "is_abnormal": True,
                "historical_comparison": {},
                "expected_vs_actual": None,
                "reasons": ["Production quantity must be greater than 0 kg."],
                "preventive_solutions": [{
                    "reason_id": "zero_production",
                    "title": "Verify Production Telemetry",
                    "icon": "fa-clipboard-check",
                    "solution": "Inspect meter sensor at Loom Bay and enter valid total production quantity greater than 0 kg.",
                    "priority": "CRITICAL"
                }],
                "reason_cards": [{
                    "id": "zero_production",
                    "title": "Invalid Production Quantity (Zero Production)",
                    "severity": "CRITICAL",
                    "badge_color": "danger",
                    "icon": "fa-triangle-exclamation",
                    "observed": "0 kg Production",
                    "benchmark": "> 0 kg Valid Production",
                    "impact": "Production quantity must be greater than 0 kg to calculate expected waste and risk.",
                    "evidence_text": "Production quantity must be greater than 0 kg."
                }],
                "recommended_action_plan": {
                    "risk_level": "INVALID",
                    "badge_class": "badge-danger",
                    "summary": "Production quantity must be greater than 0 kg.",
                    "protocol": "Inspect → Adjust → Maintain → Monitor",
                    "steps": [
                        "Verify raw production meter reading at loom controller.",
                        "Input valid total production quantity greater than zero.",
                        "Re-run prediction analysis after data correction."
                    ]
                }
            }

        # 2. Extract Features
        m_id = str(batch.get("machine_id", "M01")).strip().upper()
        f_type = str(batch.get("fabric_type", "Cotton")).strip().title()
        shift = str(batch.get("shift", "Morning")).strip().title()
        operator = str(batch.get("operator", "Operator A")).strip().title()
        speed = float(batch.get("production_speed", 800.0))
        machine_age = float(batch.get("machine_age", 3.0))
        maint_age = int(batch.get("maintenance_age_days", 30))
        humidity = float(batch.get("humidity", 55.0))
        temperature = float(batch.get("temperature", 25.0))
        humidity_imputed = bool(batch.get("humidity_imputed", False))

        # 3. Baselines & Benchmarks
        m_thresh = self.baseline_analyzer.get_machine_thresholds(m_id)
        f_thresh = self.baseline_analyzer.get_fabric_thresholds(f_type)
        is_new_machine = not m_thresh.get("has_history", False)
        safe_speed = f_thresh.get("mean_speed", 800.0)
        base_confidence = 70.0 if is_new_machine else 95.0
        if humidity_imputed:
            base_confidence -= 10.0

        # 4. Continuous Regression Prediction
        pred_waste_pct = None
        tree_std = 0.5

        if self.is_trained and self.regressor is not None:
            try:
                row_dict = {
                    "machine_id": [m_id],
                    "fabric_type": [f_type],
                    "shift": [shift],
                    "operator": [operator],
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
                pred_waste_pct = float(self.regressor.predict(df_single)[0])

                # Extract tree ensemble standard deviation for statistical confidence interval
                prep = self.regressor.named_steps["preprocessor"]
                reg_model = self.regressor.named_steps["regressor"]
                X_trans = prep.transform(df_single)
                tree_preds = [float(tree.predict(X_trans)[0]) for tree in reg_model.estimators_]
                tree_std = float(np.std(tree_preds))
            except Exception:
                pred_waste_pct = None

        if pred_waste_pct is None or is_new_machine:
            # Physics / baseline blended estimate for cold start
            base = f_thresh["mean"] if is_new_machine else m_thresh["mean"]
            speed_delta = max(0.0, (speed - safe_speed) / safe_speed) * 3.5 if speed > safe_speed else 0.0
            maint_delta = max(0.0, (maint_age - maint_interval) / 30.0) * 1.6 if maint_age > maint_interval else 0.0
            age_delta = 0.3 if machine_age > 8.0 else 0.0
            env_delta = 0.4 if (humidity < 40.0 or humidity > 75.0 or temperature < 18.0 or temperature > 34.0) else 0.0
            pred_waste_pct = round(base + speed_delta + maint_delta + age_delta + env_delta, 2)
            tree_std = 1.0 if is_new_machine else 0.6

        # Cap predictions safely
        pred_waste_pct = round(max(0.5, min(35.0, pred_waste_pct)), 2)

        # 5. Prediction Uncertainty Range (Likely Range % & kg)
        margin = max(0.6, round(1.645 * max(tree_std, self.regression_metrics.get("rmse", 0.6) * 0.5), 2))
        range_min_pct = round(max(0.2, pred_waste_pct - margin), 2)
        range_max_pct = round(pred_waste_pct + margin, 2)

        expected_waste_kg = round(prod_qty * (pred_waste_pct / 100.0), 2)
        expected_good_production_kg = round(prod_qty - expected_waste_kg, 2)
        likely_range_kg_min = round(prod_qty * (range_min_pct / 100.0), 2)
        likely_range_kg_max = round(prod_qty * (range_max_pct / 100.0), 2)

        # 6. Expected Risk Classification
        warn_thresh = float(settings.get("risk_threshold_warning", 40.0))
        high_thresh = float(settings.get("risk_threshold_high", 70.0))

        target_mean = m_thresh["mean"] if not is_new_machine else f_thresh["mean"]
        waste_ratio = pred_waste_pct / max(0.5, target_mean)

        if waste_ratio <= 0.85:
            base_waste_score = (waste_ratio / 0.85) * 18.0
        elif waste_ratio <= 1.25:
            norm_prog = (waste_ratio - 0.85) / 0.40
            base_waste_score = 18.0 + (norm_prog * 18.0)
        elif waste_ratio <= 1.75:
            warn_prog = (waste_ratio - 1.25) / 0.50
            base_waste_score = 42.0 + (warn_prog * 24.0)
        else:
            high_prog = min(1.0, (waste_ratio - 1.75) / 1.0)
            base_waste_score = 72.0 + (high_prog * 24.0)

        # Multi-factor penalty contributions
        maint_penalty = 0.0
        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            maint_penalty = min(35.0, 15.0 + (days_over * 0.8))
        elif maint_age > maint_interval * 0.8:
            maint_penalty = 8.0

        speed_ratio = speed / max(1.0, safe_speed)
        speed_penalty = 0.0
        if speed_ratio > 1.20:
            speed_penalty = min(35.0, 15.0 + (speed_ratio - 1.20) * 75.0)
        elif speed_ratio > 1.08:
            speed_penalty = 8.0

        env_penalty = 0.0
        if machine_age > 8.0:
            env_penalty += 5.0
        if humidity < 38.0 or humidity > 75.0:
            env_penalty += 6.0
        if temperature < 18.0 or temperature > 33.0:
            env_penalty += 5.0

        if base_waste_score >= high_thresh:
            combined_score = min(100.0, base_waste_score + maint_penalty * 0.3 + speed_penalty * 0.3 + env_penalty * 0.2)
        elif base_waste_score >= warn_thresh:
            combined_score = min(100.0, base_waste_score + maint_penalty * 0.6 + speed_penalty * 0.6 + env_penalty * 0.4)
        else:
            combined_score = min(100.0, base_waste_score + maint_penalty + speed_penalty + env_penalty)

        risk_score = round(max(5.0, min(100.0, combined_score)), 1)

        if risk_score >= high_thresh or pred_waste_pct >= 8.5:
            risk_level = "HIGH RISK"
        elif risk_score >= warn_thresh or pred_waste_pct >= 6.5:
            risk_level = "WARNING"
        else:
            risk_level = "NORMAL"

        # 7. Historical Performance Comparison Matrix
        hist_comp = self.baseline_analyzer.get_historical_comparison(
            machine_id=m_id,
            fabric_type=f_type,
            shift=shift,
            expected_waste_pct=pred_waste_pct
        )

        # 8. Reasons & Preventive Solutions for Expected Waste
        reasons = []
        reason_cards = []
        preventive_solutions = []

        # Speed check
        if speed > safe_speed * 1.12:
            pct_high = ((speed - safe_speed) / safe_speed) * 100.0
            reasons.append(
                f"Production speed is higher than the machine's historical normal speed."
            )
            reason_cards.append({
                "id": "production_speed",
                "title": "Production Speed Higher than Normal Range",
                "severity": "CRITICAL" if speed > safe_speed * 1.30 else "HIGH",
                "badge_color": "danger" if speed > safe_speed * 1.30 else "warning",
                "icon": "fa-gauge-high",
                "observed": f"{speed:.0f} rpm",
                "benchmark": f"{safe_speed:.0f} rpm Historical Safe Speed",
                "impact": f"High operating speed causes excess yarn friction, tension shocks, and warp breaks.",
                "evidence_text": f"Production speed is {pct_high:.0f}% above safe baseline for {f_type}."
            })
            preventive_solutions.append({
                "reason_id": "production_speed",
                "title": "Optimize Production Speed",
                "icon": "fa-gauge",
                "solution": f"Reduce production speed to the validated operating range (below {safe_speed * 1.05:.0f} rpm) to reduce expected waste.",
                "priority": "HIGH"
            })
            if speed > safe_speed * 1.40:
                reasons.append("Production speed is unusually high and may increase expected waste.")

        # Maintenance check
        if maint_age > maint_interval:
            days_over = maint_age - maint_interval
            reasons.append("Machine maintenance is overdue.")
            reason_cards.append({
                "id": "maintenance_overdue",
                "title": "Machine Maintenance Overdue",
                "severity": "CRITICAL" if days_over > 20 else "HIGH",
                "badge_color": "danger" if days_over > 20 else "warning",
                "icon": "fa-screwdriver-wrench",
                "observed": f"{maint_age} Days Since Service",
                "benchmark": f"{maint_interval} Days Interval Limit",
                "impact": f"Mechanical wear, gripper misalignment, and bearing friction generate recurring defects.",
                "evidence_text": f"Machine {m_id} is overdue for maintenance by {days_over} days."
            })
            preventive_solutions.append({
                "reason_id": "maintenance_overdue",
                "title": "Perform Scheduled Machine Maintenance",
                "icon": "fa-wrench",
                "solution": f"Schedule preventive maintenance and inspect the machine before production.",
                "priority": "CRITICAL" if days_over > 20 else "HIGH"
            })

        # Fabric sensitivity check
        if f_thresh["mean"] > 4.5:
            reasons.append(f"Similar batches using this fabric have produced higher waste.")
            reason_cards.append({
                "id": "fabric_sensitivity",
                "title": f"Fabric-Specific High Waste Profile ({f_type})",
                "severity": "MEDIUM",
                "badge_color": "info",
                "icon": "fa-layer-group",
                "observed": f"{f_thresh['mean']:.2f}% Baseline Waste",
                "benchmark": f"{self.baseline_analyzer.factory_stats.get('mean_waste_pct', 4.0):.2f}% Plant Average",
                "impact": f"{f_type} fabric has delicate yarn properties requiring tuned shed tension.",
                "evidence_text": f"Historical batches for {f_type} average {f_thresh['mean']:.2f}% waste."
            })
            preventive_solutions.append({
                "reason_id": "fabric_sensitivity",
                "title": f"Review Settings for {f_type}",
                "icon": "fa-sliders",
                "solution": f"Review machine settings for {f_type} using previous low-waste batches.",
                "priority": "MEDIUM"
            })

        # Environmental check
        if humidity_imputed:
            reasons.append("Humidity unavailable. Prediction is based on the remaining available parameters.")
            preventive_solutions.append({
                "reason_id": "missing_humidity",
                "title": "Verify Humidity Sensors",
                "icon": "fa-tower-broadcast",
                "solution": "Inspect Loom Bay humidity transmitter to restore real-time environmental telemetry.",
                "priority": "LOW"
            })
        elif humidity < 40.0:
            reasons.append(f"Current humidity is outside the normal historical range.")
            preventive_solutions.append({
                "reason_id": "humidity_low",
                "title": "Adjust Environmental Humidity",
                "icon": "fa-droplet",
                "solution": "Adjust environmental conditions to the validated operating range (55–65% RH).",
                "priority": "MEDIUM"
            })
        elif humidity > 75.0:
            reasons.append(f"Current humidity is outside the normal historical range.")
            preventive_solutions.append({
                "reason_id": "humidity_high",
                "title": "Adjust Environmental Conditions",
                "icon": "fa-fan",
                "solution": "Adjust environmental conditions to the validated operating range (55–65% RH).",
                "priority": "MEDIUM"
            })

        # Cold-Start / New machine note
        if is_new_machine:
            reasons.append("Limited historical data available for this machine. Prediction is based on similar machines and overall historical patterns.")
            preventive_solutions.append({
                "reason_id": "new_machine",
                "title": "Initial Machine Calibration",
                "icon": "fa-circle-notch",
                "solution": f"Monitor the initial run of {m_id} closely and record calibration telemetry.",
                "priority": "MEDIUM"
            })

        if not reasons:
            reasons.append("All machine, material, and environmental parameters are within optimal baseline limits.")
            preventive_solutions.append({
                "reason_id": "nominal_production",
                "title": "Maintain Standard Operating Procedures",
                "icon": "fa-circle-check",
                "solution": "Proceed with planned production while monitoring continuous loom sensors.",
                "priority": "LOW"
            })

        # Action Plan Protocol
        if risk_level == "HIGH RISK":
            action_plan = {
                "risk_level": "HIGH RISK",
                "badge_class": "badge-danger",
                "summary": "Expected waste is significantly above target threshold. Pre-production intervention required.",
                "protocol": "Inspect → Adjust → Maintain → Monitor",
                "steps": [
                    f"Inspect Loom Bay settings on machine {m_id} prior to commencing production.",
                    f"Adjust loom operating speed to safe threshold (< {safe_speed * 1.05:.0f} rpm).",
                    f"Perform maintenance checks if overdue ({maint_age} days recorded).",
                    f"Monitor initial production run closely to verify waste rate reduction."
                ]
            }
        elif risk_level == "WARNING":
            action_plan = {
                "risk_level": "WARNING",
                "badge_class": "badge-warning",
                "summary": "Expected waste is moderately elevated. Pre-production parameter tuning recommended.",
                "protocol": "Inspect → Adjust → Maintain → Monitor",
                "steps": [
                    f"Inspect yarn feeder guides and tension controllers on {m_id}.",
                    f"Verify weaving shed humidity is within 55–65% RH.",
                    f"Monitor first batch cut for any selvedge or filling defects."
                ]
            }
        else:
            action_plan = {
                "risk_level": "NORMAL",
                "badge_class": "badge-normal",
                "summary": "Operating conditions are optimal. Expected waste is within nominal factory baseline.",
                "protocol": "Inspect → Adjust → Maintain → Monitor",
                "steps": [
                    "Proceed with scheduled production run under standard supervisor oversight.",
                    "Log end-of-batch actual waste to continuously reinforce AI model accuracy."
                ]
            }

        # 9. Expected vs Actual Comparison (if actual waste quantity was entered)
        has_actual_waste = bool(batch.get("has_actual_waste", False) or (batch.get("waste_quantity") is not None and float(batch.get("waste_quantity", 0)) > 0))
        expected_vs_actual = None
        if has_actual_waste and prod_qty > 0:
            actual_waste_qty = float(batch.get("waste_quantity", 0.0))
            actual_waste_pct = round((actual_waste_qty / prod_qty) * 100.0, 2)
            diff_kg = round(actual_waste_qty - expected_waste_kg, 2)
            abs_error_kg = round(abs(actual_waste_qty - expected_waste_kg), 2)
            acc_pct = round(max(0.0, min(100.0, 100.0 - (abs_error_kg / max(1.0, actual_waste_qty)) * 100.0)), 1)
            expected_vs_actual = {
                "has_actual": True,
                "expected_waste_pct": pred_waste_pct,
                "actual_waste_pct": actual_waste_pct,
                "expected_waste_kg": expected_waste_kg,
                "actual_waste_kg": round(actual_waste_qty, 2),
                "difference_kg": diff_kg,
                "difference_sign": f"+{diff_kg:.1f} kg" if diff_kg > 0 else f"{diff_kg:.1f} kg",
                "absolute_error_kg": abs_error_kg,
                "prediction_accuracy_pct": acc_pct
            }

        return {
            "is_valid": True,
            "validation_error": None,
            "expected_waste_percentage": pred_waste_pct,
            "expected_waste_kg": expected_waste_kg,
            "expected_good_production_kg": expected_good_production_kg,
            "likely_range_pct": {
                "min": range_min_pct,
                "max": range_max_pct,
                "display": f"{range_min_pct:.1f}%-{range_max_pct:.1f}%"
            },
            "likely_range_kg": {
                "min": likely_range_kg_min,
                "max": likely_range_kg_max,
                "display": f"{likely_range_kg_min:.0f}-{likely_range_kg_max:.0f} kg"
            },
            "risk_level": risk_level,
            "risk_score": risk_score,
            "confidence_score": float(round(max(10.0, min(100.0, base_confidence)), 1)),
            "is_abnormal": bool(risk_level == "HIGH RISK"),
            "is_new_machine": bool(is_new_machine),
            "historical_comparison": hist_comp,
            "expected_vs_actual": expected_vs_actual,
            "reasons": list(reasons),
            "reason_cards": reason_cards,
            "preventive_solutions": preventive_solutions,
            "recommended_action_plan": action_plan
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
        raw_waste_pct = batch.get("waste_percentage")
        waste_pct = float(raw_waste_pct) if raw_waste_pct is not None else float(batch.get("expected_waste_percentage") or 0.0)
        speed = float(batch.get("production_speed") if batch.get("production_speed") is not None else 800.0)
        maint_age = int(batch.get("maintenance_age_days") if batch.get("maintenance_age_days") is not None else 30)
        m_age = float(batch.get("machine_age") if batch.get("machine_age") is not None else 3.0)
        humidity = float(batch.get("humidity") if batch.get("humidity") is not None else 55.0)
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
