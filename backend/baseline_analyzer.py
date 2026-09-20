"""
Baseline statistics and multi-dimensional analysis module for Textile Waste Prediction.
Computes machine-wise, fabric-wise, shift-wise, operator-wise, and maintenance analytics.
Calculates IQR and Z-score abnormal batch thresholds for adaptive, segment-specific risk evaluation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime


class BaselineAnalyzer:
    """
    Analyzes historical production data to construct baselines, segment statistics,
    and adaptive anomaly thresholds.
    """

    def __init__(self, df: Optional[pd.DataFrame] = None):
        self.df = df if df is not None and not df.empty else pd.DataFrame()
        self.factory_stats: Dict[str, Any] = {}
        self.machine_stats: Dict[str, Any] = {}
        self.fabric_stats: Dict[str, Any] = {}
        self.shift_stats: Dict[str, Any] = {}
        self.operator_stats: Dict[str, Any] = {}
        self.machine_fabric_stats: Dict[str, Any] = {}

        if not self.df.empty:
            self.refresh_baselines()

    def set_data(self, df: pd.DataFrame):
        """Updates internal dataset and recalculates all baseline profiles."""
        self.df = df[df["is_valid"] == 1].copy() if "is_valid" in df.columns else df.copy()
        self.refresh_baselines()

    def refresh_baselines(self):
        """Computes statistical baselines for overall factory, machines, fabrics, shifts, and operators."""
        if self.df.empty:
            return

        df = self.df

        # 1. Factory-wide overall baseline
        waste_pcts = df["waste_percentage"].dropna().values
        q1 = float(np.percentile(waste_pcts, 25)) if len(waste_pcts) > 0 else 2.0
        q3 = float(np.percentile(waste_pcts, 75)) if len(waste_pcts) > 0 else 5.0
        iqr = max(0.5, q3 - q1)

        self.factory_stats = {
            "mean_waste_pct": float(np.mean(waste_pcts)) if len(waste_pcts) > 0 else 4.0,
            "std_waste_pct": float(np.std(waste_pcts)) if len(waste_pcts) > 0 else 1.5,
            "median_waste_pct": float(np.median(waste_pcts)) if len(waste_pcts) > 0 else 3.8,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "iqr_upper_bound": q3 + 1.5 * iqr,
            "total_batches": len(df),
            "mean_speed": float(df["production_speed"].mean()) if "production_speed" in df else 800.0,
            "std_speed": float(df["production_speed"].std()) if "production_speed" in df else 100.0,
            "mean_humidity": float(df["humidity"].mean()) if "humidity" in df else 55.0,
            "mean_temp": float(df["temperature"].mean()) if "temperature" in df else 25.0
        }

        # 2. Machine-wise baselines
        self.machine_stats = {}
        for m_id, m_df in df.groupby("machine_id"):
            m_waste = m_df["waste_percentage"].values
            m_q1 = float(np.percentile(m_waste, 25)) if len(m_waste) >= 4 else q1
            m_q3 = float(np.percentile(m_waste, 75)) if len(m_waste) >= 4 else q3
            m_iqr = max(0.4, m_q3 - m_q1)

            self.machine_stats[m_id] = {
                "batch_count": len(m_df),
                "mean_waste_pct": float(np.mean(m_waste)),
                "std_waste_pct": float(np.std(m_waste)) if len(m_waste) > 1 else 1.0,
                "median_waste_pct": float(np.median(m_waste)),
                "min_waste_pct": float(np.min(m_waste)),
                "max_waste_pct": float(np.max(m_waste)),
                "q1": m_q1,
                "q3": m_q3,
                "iqr": m_iqr,
                "upper_threshold": m_q3 + 1.5 * m_iqr,
                "mean_speed": float(m_df["production_speed"].mean()),
                "machine_age": float(m_df["machine_age"].iloc[-1]) if "machine_age" in m_df else 3.0,
                "last_maintenance_date": str(m_df["last_maintenance_date"].dropna().iloc[-1]) if "last_maintenance_date" in m_df and not m_df["last_maintenance_date"].dropna().empty else None,
                "latest_maintenance_age_days": int(m_df["maintenance_age_days"].iloc[-1]) if "maintenance_age_days" in m_df else 40,
                "abnormal_batch_count": int(m_df["is_abnormal"].sum()) if "is_abnormal" in m_df else 0
            }

        # 3. Fabric-wise baselines
        self.fabric_stats = {}
        for f_type, f_df in df.groupby("fabric_type"):
            f_waste = f_df["waste_percentage"].values
            f_q1 = float(np.percentile(f_waste, 25)) if len(f_waste) >= 4 else q1
            f_q3 = float(np.percentile(f_waste, 75)) if len(f_waste) >= 4 else q3
            f_iqr = max(0.4, f_q3 - f_q1)

            self.fabric_stats[f_type] = {
                "batch_count": len(f_df),
                "mean_waste_pct": float(np.mean(f_waste)),
                "std_waste_pct": float(np.std(f_waste)) if len(f_waste) > 1 else 1.0,
                "median_waste_pct": float(np.median(f_waste)),
                "q1": f_q1,
                "q3": f_q3,
                "iqr": f_iqr,
                "upper_threshold": f_q3 + 1.5 * f_iqr,
                "mean_speed": float(f_df["production_speed"].mean()),
                "total_production": float(f_df["total_production"].sum()),
                "total_waste": float(f_df["waste_quantity"].sum()),
                "abnormal_batch_count": int(f_df["is_abnormal"].sum()) if "is_abnormal" in f_df else 0
            }

        # 4. Shift-wise baselines
        self.shift_stats = {}
        for s_type, s_df in df.groupby("shift"):
            s_waste = s_df["waste_percentage"].values
            self.shift_stats[s_type] = {
                "batch_count": len(s_df),
                "mean_waste_pct": float(np.mean(s_waste)),
                "std_waste_pct": float(np.std(s_waste)) if len(s_waste) > 1 else 1.0,
                "mean_speed": float(s_df["production_speed"].mean()),
                "abnormal_batch_count": int(s_df["is_abnormal"].sum()) if "is_abnormal" in s_df else 0,
                "operator_count": int(s_df["operator"].nunique()) if "operator" in s_df else 0
            }

        # 5. Operator-wise baselines
        self.operator_stats = {}
        for op, op_df in df.groupby("operator"):
            op_waste = op_df["waste_percentage"].values
            self.operator_stats[op] = {
                "batch_count": len(op_df),
                "mean_waste_pct": float(np.mean(op_waste)),
                "std_waste_pct": float(np.std(op_waste)) if len(op_waste) > 1 else 1.0,
                "mean_speed": float(op_df["production_speed"].mean()),
                "abnormal_batch_count": int(op_df["is_abnormal"].sum()) if "is_abnormal" in op_df else 0,
                "machines_operated": list(op_df["machine_id"].unique()) if "machine_id" in op_df else []
            }

        # 6. Machine + Fabric combination baselines
        self.machine_fabric_stats = {}
        for (m_id, f_type), mf_df in df.groupby(["machine_id", "fabric_type"]):
            mf_waste = mf_df["waste_percentage"].values
            self.machine_fabric_stats[f"{m_id}_{f_type}"] = {
                "machine_id": m_id,
                "fabric_type": f_type,
                "batch_count": len(mf_df),
                "mean_waste_pct": float(np.mean(mf_waste)),
                "std_waste_pct": float(np.std(mf_waste)) if len(mf_waste) > 1 else 1.0,
                "mean_speed": float(mf_df["production_speed"].mean()) if "production_speed" in mf_df else 800.0
            }

    def get_historical_comparison(
        self,
        machine_id: str,
        fabric_type: str,
        shift: str = "Morning",
        expected_waste_pct: float = 0.0
    ) -> Dict[str, Any]:
        """
        Compares the expected waste percentage against overall factory baseline,
        machine-specific average, fabric-specific average, machine+fabric combination, and shift average.
        Returns detailed comparisons and a clear comparative statement.
        """
        factory_avg = self.factory_stats.get("mean_waste_pct", 4.0)
        
        m_stats = self.machine_stats.get(machine_id, {})
        machine_avg = m_stats.get("mean_waste_pct", factory_avg)
        
        f_stats = self.fabric_stats.get(fabric_type, {})
        fabric_avg = f_stats.get("mean_waste_pct", factory_avg)
        
        mf_key = f"{machine_id}_{fabric_type}"
        mf_stats = self.machine_fabric_stats.get(mf_key, {})
        mf_avg = mf_stats.get("mean_waste_pct", round((machine_avg + fabric_avg) / 2.0, 2))
        
        s_stats = self.shift_stats.get(shift, {})
        shift_avg = s_stats.get("mean_waste_pct", factory_avg)
        
        # Build synthesis statement
        higher_than = []
        lower_than = []
        
        if expected_waste_pct > machine_avg * 1.08:
            higher_than.append(f"Machine {machine_id} average ({machine_avg:.1f}%)")
        elif expected_waste_pct < machine_avg * 0.92:
            lower_than.append(f"Machine {machine_id} average ({machine_avg:.1f}%)")
            
        if expected_waste_pct > fabric_avg * 1.08:
            higher_than.append(f"{fabric_type} fabric historical average ({fabric_avg:.1f}%)")
        elif expected_waste_pct < fabric_avg * 0.92:
            lower_than.append(f"{fabric_type} fabric historical average ({fabric_avg:.1f}%)")
            
        if expected_waste_pct > factory_avg * 1.12:
            higher_than.append(f"overall plant baseline ({factory_avg:.1f}%)")
        elif expected_waste_pct < factory_avg * 0.88:
            lower_than.append(f"overall plant baseline ({factory_avg:.1f}%)")
            
        if higher_than:
            statement = f"Expected waste ({expected_waste_pct:.1f}%) is higher than the {', and '.join(higher_than)}."
        elif lower_than:
            statement = f"Expected waste ({expected_waste_pct:.1f}%) is lower than the {', and '.join(lower_than)}, indicating optimal operating parameters."
        else:
            statement = f"Expected waste ({expected_waste_pct:.1f}%) is aligned with the nominal historical baseline for this machine and fabric combination."

        return {
            "factory_average_pct": round(factory_avg, 2),
            "machine_average_pct": round(machine_avg, 2),
            "fabric_average_pct": round(fabric_avg, 2),
            "machine_fabric_combination_avg_pct": round(mf_avg, 2),
            "shift_average_pct": round(shift_avg, 2),
            "variance_from_factory_pct": round(expected_waste_pct - factory_avg, 2),
            "variance_from_machine_pct": round(expected_waste_pct - machine_avg, 2),
            "variance_from_fabric_pct": round(expected_waste_pct - fabric_avg, 2),
            "variance_from_combo_pct": round(expected_waste_pct - mf_avg, 2),
            "comparison_summary": statement
        }

    def get_machine_thresholds(self, machine_id: str) -> Dict[str, float]:
        """Returns baseline mean, std, and upper IQR threshold for a machine, falling back to factory defaults."""
        if machine_id in self.machine_stats and self.machine_stats[machine_id]["batch_count"] >= 3:
            ms = self.machine_stats[machine_id]
            return {
                "mean": ms["mean_waste_pct"],
                "std": ms["std_waste_pct"],
                "upper_threshold": ms["upper_threshold"],
                "mean_speed": ms["mean_speed"],
                "has_history": True,
                "batch_count": ms["batch_count"]
            }
        # Fallback for new machine
        return {
            "mean": self.factory_stats.get("mean_waste_pct", 4.0),
            "std": self.factory_stats.get("std_waste_pct", 1.5),
            "upper_threshold": self.factory_stats.get("iqr_upper_bound", 6.5),
            "mean_speed": self.factory_stats.get("mean_speed", 800.0),
            "has_history": False,
            "batch_count": 0
        }

    def get_fabric_thresholds(self, fabric_type: str) -> Dict[str, float]:
        """Returns baseline stats for a fabric type."""
        if fabric_type in self.fabric_stats:
            fs = self.fabric_stats[fabric_type]
            return {
                "mean": fs["mean_waste_pct"],
                "std": fs["std_waste_pct"],
                "upper_threshold": fs["upper_threshold"],
                "mean_speed": fs["mean_speed"],
                "has_history": True
            }
        return {
            "mean": self.factory_stats.get("mean_waste_pct", 4.0),
            "std": self.factory_stats.get("std_waste_pct", 1.5),
            "upper_threshold": self.factory_stats.get("iqr_upper_bound", 6.5),
            "mean_speed": self.factory_stats.get("mean_speed", 800.0),
            "has_history": False
        }

    def get_machine_analysis(self, maintenance_interval_days: int = 60) -> Dict[str, Any]:
        """Returns comprehensive machine-wise analytics."""
        if not self.machine_stats:
            return {"machines": [], "highest_waste_machine": None, "lowest_waste_machine": None, "age_correlation": 0.0}

        machines_list = []
        ages = []
        wastes = []

        for m_id, stats in sorted(self.machine_stats.items()):
            m_age_days = stats["latest_maintenance_age_days"]
            maint_status = "OVERDUE" if m_age_days > maintenance_interval_days else (
                "APPROACHING" if m_age_days > maintenance_interval_days * 0.6 else "GOOD"
            )

            machines_list.append({
                "machine_id": m_id,
                "batch_count": stats["batch_count"],
                "average_waste_pct": round(stats["mean_waste_pct"], 2),
                "median_waste_pct": round(stats["median_waste_pct"], 2),
                "min_waste_pct": round(stats["min_waste_pct"], 2),
                "max_waste_pct": round(stats["max_waste_pct"], 2),
                "abnormal_batches": stats["abnormal_batch_count"],
                "abnormal_rate_pct": round((stats["abnormal_batch_count"] / max(1, stats["batch_count"])) * 100, 1),
                "machine_age_years": round(stats["machine_age"], 1),
                "days_since_maintenance": m_age_days,
                "maintenance_status": maint_status,
                "last_maintenance_date": stats["last_maintenance_date"] or "N/A",
                "average_speed": round(stats["mean_speed"], 1)
            })

            ages.append(stats["machine_age"])
            wastes.append(stats["mean_waste_pct"])

        # Find highest and lowest
        sorted_by_waste = sorted(machines_list, key=lambda x: x["average_waste_pct"])
        lowest = sorted_by_waste[0] if sorted_by_waste else None
        highest = sorted_by_waste[-1] if sorted_by_waste else None

        # Calculate age vs waste correlation
        age_corr = 0.0
        if len(ages) > 2 and np.std(ages) > 0 and np.std(wastes) > 0:
            age_corr = round(float(np.corrcoef(ages, wastes)[0, 1]), 3)

        return {
            "machines": machines_list,
            "highest_waste_machine": highest,
            "lowest_waste_machine": lowest,
            "age_waste_correlation": age_corr
        }

    def get_fabric_analysis(self) -> Dict[str, Any]:
        """Returns comprehensive fabric-wise analytics."""
        if not self.fabric_stats:
            return {"fabrics": [], "high_risk_fabrics": []}

        fabrics_list = []
        for f_type, stats in sorted(self.fabric_stats.items()):
            abnormal_rate = (stats["abnormal_batch_count"] / max(1, stats["batch_count"])) * 100
            is_high_risk = stats["mean_waste_pct"] > self.factory_stats.get("mean_waste_pct", 4.0) * 1.15 or abnormal_rate > 15.0

            fabrics_list.append({
                "fabric_type": f_type,
                "batch_count": stats["batch_count"],
                "average_waste_pct": round(stats["mean_waste_pct"], 2),
                "abnormal_batches": stats["abnormal_batch_count"],
                "abnormal_rate_pct": round(abnormal_rate, 1),
                "total_production_kg": round(stats["total_production"], 1),
                "total_waste_kg": round(stats["total_waste"], 1),
                "average_speed": round(stats["mean_speed"], 1),
                "is_high_risk": is_high_risk
            })

        high_risk = [f for f in fabrics_list if f["is_high_risk"]]
        return {
            "fabrics": fabrics_list,
            "high_risk_fabrics": high_risk
        }

    def get_shift_analysis(self) -> Dict[str, Any]:
        """Returns shift-wise analytics."""
        shifts_list = []
        for s_name, stats in self.shift_stats.items():
            shifts_list.append({
                "shift": s_name,
                "batch_count": stats["batch_count"],
                "average_waste_pct": round(stats["mean_waste_pct"], 2),
                "average_speed": round(stats["mean_speed"], 1),
                "abnormal_batches": stats["abnormal_batch_count"],
                "abnormal_rate_pct": round((stats["abnormal_batch_count"] / max(1, stats["batch_count"])) * 100, 1),
                "operator_count": stats["operator_count"]
            })
        return {"shifts": shifts_list}

    def get_operator_analysis(self) -> Dict[str, Any]:
        """Returns objective, constructive operator condition analysis."""
        ops_list = []
        for op_name, stats in sorted(self.operator_stats.items()):
            ops_list.append({
                "operator": op_name,
                "batch_count": stats["batch_count"],
                "average_waste_pct": round(stats["mean_waste_pct"], 2),
                "average_speed": round(stats["mean_speed"], 1),
                "abnormal_batches": stats["abnormal_batch_count"],
                "abnormal_rate_pct": round((stats["abnormal_batch_count"] / max(1, stats["batch_count"])) * 100, 1),
                "machines_operated": stats["machines_operated"]
            })
        return {"operators": ops_list}

    def get_maintenance_analysis(self, maintenance_interval_days: int = 60) -> Dict[str, Any]:
        """Returns maintenance status distribution, overdue list, and degradation curve data."""
        if self.df.empty:
            return {"recently_maintained": [], "approaching": [], "overdue": [], "degradation_bins": []}

        df = self.df
        recently_maintained = []
        approaching = []
        overdue = []

        for m_id, stats in self.machine_stats.items():
            days = stats["latest_maintenance_age_days"]
            info = {
                "machine_id": m_id,
                "days_since_maintenance": days,
                "last_maintenance_date": stats["last_maintenance_date"] or "N/A",
                "average_waste_pct": round(stats["mean_waste_pct"], 2),
                "machine_age_years": round(stats["machine_age"], 1)
            }
            if days > maintenance_interval_days:
                info["days_overdue"] = days - maintenance_interval_days
                overdue.append(info)
            elif days > maintenance_interval_days * 0.6:
                info["days_until_overdue"] = maintenance_interval_days - days
                approaching.append(info)
            else:
                recently_maintained.append(info)

        # Maintenance age degradation bins (e.g. 0-20d, 21-40d, 41-60d, 61-80d, 80+d)
        bins = [0, 20, 40, 60, 80, 200]
        labels = ["0-20 days", "21-40 days", "41-60 days", "61-80 days", "80+ days"]
        if "maintenance_age_days" in df:
            df["maint_bin"] = pd.cut(df["maintenance_age_days"], bins=bins, labels=labels, right=False)
            bin_stats = df.groupby("maint_bin", observed=False)["waste_percentage"].agg(["mean", "count"]).reset_index()
            degradation_bins = [
                {"bin": row["maint_bin"], "avg_waste_pct": round(float(row["mean"]), 2) if not pd.isna(row["mean"]) else 0, "batch_count": int(row["count"])}
                for _, row in bin_stats.iterrows()
            ]
        else:
            degradation_bins = []

        return {
            "recently_maintained": recently_maintained,
            "approaching": approaching,
            "overdue": overdue,
            "degradation_bins": degradation_bins,
            "configured_interval_days": maintenance_interval_days
        }

    def get_correlations(self) -> Dict[str, Any]:
        """Calculates correlations between variables and waste percentage."""
        if self.df.empty or len(self.df) < 5:
            return {"speed_correlation": 0, "maintenance_age_correlation": 0, "machine_age_correlation": 0, "humidity_correlation": 0, "temperature_correlation": 0}

        df = self.df
        def safe_corr(col1, col2):
            if col1 in df and col2 in df and df[col1].std() > 0 and df[col2].std() > 0:
                return round(float(df[col1].corr(df[col2])), 3)
            return 0.0

        return {
            "speed_correlation": safe_corr("production_speed", "waste_percentage"),
            "maintenance_age_correlation": safe_corr("maintenance_age_days", "waste_percentage"),
            "machine_age_correlation": safe_corr("machine_age", "waste_percentage"),
            "humidity_correlation": safe_corr("humidity", "waste_percentage"),
            "temperature_correlation": safe_corr("temperature", "waste_percentage")
        }
