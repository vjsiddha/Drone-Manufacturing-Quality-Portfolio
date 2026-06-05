"""
ncr_generator.py
Generates draft NCR records for failed inspection features.
Output connects directly to the NCR/CAPA module.
"""

import pandas as pd
from datetime import date, timedelta


SEVERITY_MAP = {
    "High":   "Major",
    "Medium": "Minor",
    "Low":    "Minor",
}

DISPOSITION_MAP = {
    "FAIL":       "MRB Review",
    "MRB REVIEW": "Use-As-Is",
    "BORDERLINE": "Use-As-Is",
}


def generate_ncrs(results: list, part_number: str, part_name: str) -> pd.DataFrame:
    """
    Takes PartResult list from InspectionEngine.evaluate().
    Returns a DataFrame of draft NCR records for all failures.
    """
    rows = []
    ncr_counter = 5000

    for part in results:
        failures = part.critical_failures + part.non_critical_failures
        for fr in failures:
            severity = SEVERITY_MAP.get(fr.criticality, "Minor")
            due_days = 2 if severity == "Critical" else (7 if severity == "Major" else 14)
            due_date = (date.today() + timedelta(days=due_days)).isoformat()

            if fr.gdandt_type in ("diameter", "width", "thickness"):
                requirement = (
                    f"{fr.feature_name}: {fr.nominal_value} ± {fr.tolerance} {fr.measurement_unit}"
                )
                actual = f"Measured: {fr.measured_value} {fr.measurement_unit}"
            elif fr.gdandt_type == "position":
                requirement = (
                    f"{fr.feature_name}: True Position ≤ ⌀{fr.tolerance} {fr.measurement_unit} "
                    f"relative to {fr.datum_reference}"
                )
                actual = f"True Position Error: {fr.deviation} {fr.measurement_unit}"
            else:
                requirement = (
                    f"{fr.feature_name}: ≤ {fr.tolerance} {fr.measurement_unit} "
                    f"relative to Datum {fr.datum_reference}"
                )
                actual = f"Measured: {fr.measured_value} {fr.measurement_unit}"

            rows.append({
                "ncr_id":               f"NCR-DRAFT-{ncr_counter}",
                "source":               "GDT Inspection System",
                "date_opened":          date.today().isoformat(),
                "part_number":          part_number,
                "part_name":            part_name,
                "part_serial_number":   part.part_serial_number,
                "lot_number":           part.lot_number,
                "supplier_id":          part.supplier_id,
                "failed_feature":       fr.feature_id,
                "feature_name":         fr.feature_name,
                "gdandt_type":          fr.gdandt_type,
                "criticality":          fr.criticality,
                "requirement":          requirement,
                "actual_result":        actual,
                "deviation":            fr.deviation,
                "tolerance":            fr.tolerance,
                "margin":               fr.margin,
                "severity":             severity,
                "recommended_disposition": DISPOSITION_MAP.get(part.disposition, "MRB Review"),
                "due_date":             due_date,
                "inspector":            fr.inspector,
                "inspection_date":      fr.inspection_date,
                "status":               "Open",
                "capa_required":        "Yes" if fr.criticality == "High" else "TBD",
            })
            ncr_counter += 1

    return pd.DataFrame(rows)