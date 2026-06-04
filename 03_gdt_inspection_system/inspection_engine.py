"""
inspection_engine.py
Core GD&T evaluation logic.
Reads requirements YAML + measurements CSV, returns structured results.
"""

import pandas as pd
import numpy as np
import yaml
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FeatureResult:
    feature_id: str
    feature_name: str
    gdandt_type: str
    criticality: str
    nominal_value: Optional[float]
    nominal_x: Optional[float]
    nominal_y: Optional[float]
    measured_value: float
    measured_x: Optional[float]
    measured_y: Optional[float]
    tolerance: float
    lower_limit: Optional[float]
    upper_limit: Optional[float]
    deviation: float
    margin: float
    margin_pct: float
    result: str               # PASS / FAIL / BORDERLINE
    datum_reference: Optional[str]
    measurement_unit: str
    inspector: str
    inspection_date: str


@dataclass
class PartResult:
    part_serial_number: str
    lot_number: str
    supplier_id: str
    inspection_date: str
    inspector: str
    features: list = field(default_factory=list)
    disposition: str = ""
    critical_failures: list = field(default_factory=list)
    non_critical_failures: list = field(default_factory=list)
    borderline_items: list = field(default_factory=list)
    total_features: int = 0
    passed_features: int = 0
    failed_features: int = 0


class InspectionEngine:
    BORDERLINE_THRESHOLD = 0.10  # within 10% of tolerance = borderline

    def __init__(self, requirements_path: str):
        with open(requirements_path, "r") as f:
            self.requirements = yaml.safe_load(f)
        self.part_number = self.requirements["part_number"]
        self.part_name   = self.requirements["part_name"]
        self.revision    = self.requirements["revision"]
        self.supplier    = self.requirements["supplier"]
        self.feature_reqs = {
            feat["feature_id"]: feat
            for feat in self.requirements["features"]
        }

    def load_measurements(self, measurements_path: str) -> pd.DataFrame:
        df = pd.read_csv(measurements_path)
        required_cols = [
            "part_serial_number", "lot_number", "supplier_id",
            "feature_id", "measured_value", "inspection_date", "inspector"
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Measurement CSV missing columns: {missing}")
        unknown = set(df["feature_id"].unique()) - set(self.feature_reqs.keys())
        if unknown:
            raise ValueError(f"Unknown feature IDs in measurements: {unknown}")
        return df

    def _evaluate_feature(self, req: dict, row: pd.Series) -> FeatureResult:
        ftype   = req["gdandt_type"]
        tol     = float(req["tolerance"])
        nom_val = req.get("nominal_value")
        nom_x   = req.get("nominal_x")
        nom_y   = req.get("nominal_y")
        crit    = req.get("criticality", "Medium")
        datum   = req.get("datum_reference")
        unit    = req.get("measurement_unit", "mm")

        meas_val = float(row["measured_value"])
        meas_x   = float(row["measured_x"]) if str(row.get("measured_x","")).strip() not in ("","nan") else None
        meas_y   = float(row["measured_y"]) if str(row.get("measured_y","")).strip() not in ("","nan") else None

        lower_limit = None
        upper_limit = None

        if ftype == "position":
            if meas_x is not None and meas_y is not None and nom_x and nom_y:
                true_pos = 2 * np.sqrt((meas_x - nom_x)**2 + (meas_y - nom_y)**2)
            else:
                true_pos = abs(meas_val)
            deviation = round(true_pos, 5)
            margin    = round(tol - true_pos, 5)

        elif ftype in ("flatness","parallelism","perpendicularity","profile"):
            deviation = round(abs(meas_val), 5)
            margin    = round(tol - deviation, 5)

        elif ftype in ("diameter","width","thickness"):
            nom_val   = float(nom_val)
            lower_limit = round(nom_val - tol, 5)
            upper_limit = round(nom_val + tol, 5)
            deviation   = round(abs(meas_val - nom_val), 5)
            margin      = round(tol - deviation, 5)

        else:
            deviation = round(abs(meas_val), 5)
            margin    = round(tol - deviation, 5)

        margin_pct = round(margin / tol * 100, 1) if tol > 0 else 0.0

        if margin < 0:
            result = "FAIL"
        elif margin_pct <= (self.BORDERLINE_THRESHOLD * 100):
            result = "BORDERLINE"
        else:
            result = "PASS"

        return FeatureResult(
            feature_id=req["feature_id"], feature_name=req["feature_name"],
            gdandt_type=ftype, criticality=crit,
            nominal_value=float(nom_val) if nom_val is not None else None,
            nominal_x=nom_x, nominal_y=nom_y,
            measured_value=round(meas_val,4), measured_x=round(meas_x,4) if meas_x else None,
            measured_y=round(meas_y,4) if meas_y else None,
            tolerance=tol, lower_limit=lower_limit, upper_limit=upper_limit,
            deviation=deviation, margin=margin, margin_pct=margin_pct,
            result=result, datum_reference=datum, measurement_unit=unit,
            inspector=str(row.get("inspector","")),
            inspection_date=str(row.get("inspection_date","")),
        )

    def _disposition(self, part: PartResult) -> str:
        if part.critical_failures:
            return "FAIL"
        if part.non_critical_failures or part.borderline_items:
            return "MRB REVIEW"
        return "PASS"

    def evaluate(self, measurements_df: pd.DataFrame) -> list:
        results = []
        for sn, group in measurements_df.groupby("part_serial_number"):
            row0 = group.iloc[0]
            part = PartResult(
                part_serial_number=sn, lot_number=str(row0["lot_number"]),
                supplier_id=str(row0["supplier_id"]),
                inspection_date=str(row0["inspection_date"]),
                inspector=str(row0["inspector"]),
            )
            for _, mrow in group.iterrows():
                fid = mrow["feature_id"]
                if fid not in self.feature_reqs:
                    continue
                fr = self._evaluate_feature(self.feature_reqs[fid], mrow)
                part.features.append(fr)
                if fr.result == "FAIL":
                    if fr.criticality == "High":
                        part.critical_failures.append(fr)
                    else:
                        part.non_critical_failures.append(fr)
                elif fr.result == "BORDERLINE":
                    part.borderline_items.append(fr)

            part.total_features  = len(part.features)
            part.passed_features = sum(1 for f in part.features if f.result == "PASS")
            part.failed_features = sum(1 for f in part.features if f.result == "FAIL")
            part.disposition     = self._disposition(part)
            results.append(part)
        return results

    def results_to_dataframe(self, results: list) -> pd.DataFrame:
        rows = []
        for part in results:
            for fr in part.features:
                rows.append({
                    "part_serial_number": part.part_serial_number,
                    "lot_number": part.lot_number,
                    "supplier_id": part.supplier_id,
                    "part_disposition": part.disposition,
                    "feature_id": fr.feature_id,
                    "feature_name": fr.feature_name,
                    "gdandt_type": fr.gdandt_type,
                    "criticality": fr.criticality,
                    "nominal_x": fr.nominal_x, "nominal_y": fr.nominal_y,
                    "measured_x": fr.measured_x, "measured_y": fr.measured_y,
                    "measured_value": fr.measured_value,
                    "nominal_value": fr.nominal_value,
                    "tolerance": fr.tolerance,
                    "lower_limit": fr.lower_limit, "upper_limit": fr.upper_limit,
                    "deviation": fr.deviation, "margin": fr.margin,
                    "margin_pct": fr.margin_pct, "result": fr.result,
                    "datum_reference": fr.datum_reference,
                    "inspector": fr.inspector, "inspection_date": fr.inspection_date,
                })
        return pd.DataFrame(rows)

    def summary_stats(self, results: list) -> dict:
        total  = len(results)
        passed = sum(1 for r in results if r.disposition == "PASS")
        failed = sum(1 for r in results if r.disposition == "FAIL")
        mrb    = sum(1 for r in results if r.disposition == "MRB REVIEW")
        df     = self.results_to_dataframe(results)
        feat_fpy = (df["result"] == "PASS").mean() * 100
        fail_mask = df["result"] == "FAIL"
        worst = df[fail_mask]["feature_id"].value_counts().idxmax() if fail_mask.any() else "None"
        return {
            "total_parts": total, "passed": passed, "failed": failed,
            "mrb_review": mrb,
            "part_fpy_pct": round(passed / total * 100, 1) if total else 0,
            "feature_fpy_pct": round(feat_fpy, 1),
            "lots_inspected": list({r.lot_number for r in results}),
            "worst_feature": worst,
        }