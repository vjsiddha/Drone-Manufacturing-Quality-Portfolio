"""
Generate synthetic CMM-style measurement data for MMB-001 Motor Mount Bracket.
Simulates 50 parts across 5 lots with realistic pass/fail distribution.
"""

import pandas as pd
import numpy as np
import os

np.random.seed(42)
OUT = os.path.dirname(os.path.abspath(__file__))

INSPECTORS = ["QE-Torres", "QE-Patel", "QE-Nguyen", "QE-Brooks"]

LOTS = [
    ("LOT-201", "SUP-003", 10, "2024-02-15", 1.0),
    ("LOT-202", "SUP-003", 10, "2024-03-10", 1.0),
    ("LOT-203", "SUP-003", 10, "2024-04-05", 2.5),  # bad lot
    ("LOT-204", "SUP-003", 10, "2024-05-20", 1.0),
    ("LOT-205", "SUP-003", 10, "2024-06-18", 1.0),
]

FEATURES = [
    ("HOLE_1_POSITION",       "position",        20.00, 20.00, None, 0.20, 0.00, 0.05),
    ("HOLE_2_POSITION",       "position",        80.00, 20.00, None, 0.20, 0.00, 0.05),
    ("HOLE_3_POSITION",       "position",        20.00, 60.00, None, 0.20, 0.00, 0.04),
    ("HOLE_4_POSITION",       "position",        80.00, 60.00, None, 0.20, 0.00, 0.06),
    ("MOUNTING_FACE_FLATNESS","flatness",        None,  None,  0.00, 0.05, 0.025, 0.015),
    ("OPP_FACE_PARALLELISM",  "parallelism",     None,  None,  0.00, 0.10, 0.055, 0.030),
    ("MOTOR_BORE_PERP",       "perpendicularity",None,  None,  0.00, 0.15, 0.07,  0.04),
    ("OUTER_PROFILE",         "profile",         None,  None,  0.00, 0.30, 0.12,  0.07),
    ("HOLE_DIAMETER",         "diameter",        None,  None,  5.00, 0.05, 0.00,  0.02),
    ("SLOT_WIDTH",            "width",           None,  None,  8.00, 0.10, 0.01,  0.03),
    ("BRACKET_THICKNESS",     "thickness",       None,  None,  6.00, 0.10, 0.005, 0.025),
]

records = []
inspection_id = 1
serial = 1

for lot_number, supplier_id, qty, insp_date, scale in LOTS:
    inspector = np.random.choice(INSPECTORS)
    for _ in range(qty):
        sn = f"MMB-{serial:04d}"
        serial += 1
        for feat in FEATURES:
            fid, ftype, nom_x, nom_y, nom_val, tol, mean_err, std = feat
            if ftype == "position":
                dx = np.random.normal(0, std * scale)
                dy = np.random.normal(0, std * scale)
                meas_x = round(nom_x + dx, 4)
                meas_y = round(nom_y + dy, 4)
                meas_val = round(2 * np.sqrt(dx**2 + dy**2), 4)
                m_nom_val = ""
            elif ftype in ("diameter", "width", "thickness"):
                meas_x, meas_y = "", ""
                meas_val = round(nom_val + np.random.normal(mean_err * scale, std * scale), 4)
                m_nom_val = nom_val
            else:
                meas_x, meas_y = "", ""
                meas_val = round(abs(np.random.normal(mean_err * scale, std * scale)), 4)
                m_nom_val = nom_val if nom_val is not None else ""

            records.append({
                "inspection_id":      f"INS-GDT-{inspection_id:05d}",
                "part_serial_number": sn,
                "lot_number":         lot_number,
                "supplier_id":        supplier_id,
                "feature_id":         fid,
                "gdandt_type":        ftype,
                "measured_x":         meas_x,
                "measured_y":         meas_y,
                "measured_value":     meas_val,
                "nominal_value":      m_nom_val,
                "nominal_x":          nom_x if nom_x is not None else "",
                "nominal_y":          nom_y if nom_y is not None else "",
                "tolerance":          tol,
                "measurement_unit":   "mm",
                "inspector":          inspector,
                "inspection_date":    insp_date,
            })
            inspection_id += 1

df = pd.DataFrame(records)
df.to_csv(f"{OUT}/sample_measurements.csv", index=False)
print(f"✓ sample_measurements.csv  ({len(df)} rows, {serial-1} parts, {len(LOTS)} lots)")
print("  Note: LOT-203 has 2.5x inflated errors to simulate a bad supplier lot")