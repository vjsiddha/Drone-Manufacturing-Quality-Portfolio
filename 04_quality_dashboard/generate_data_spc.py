"""
Synthetic data generator for Drone Manufacturing Quality Dashboard.
Run this script once to create all CSV data files used by app.py.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ─── SUPPLIERS ──────────────────────────────────────────────────────────────

SUPPLIERS = [
    ("SUP-001", "AeroForge Composites",       "USA",    "Tier 1", "Approved",  "James Harlow"),
    ("SUP-002", "PrecisionDynamics Inc.",      "Germany","Tier 1", "Approved",  "Anna Müller"),
    ("SUP-003", "SkyMetal Fabrication",        "Canada", "Tier 2", "Approved",  "Luc Tremblay"),
    ("SUP-004", "FastTrack Electronics",       "Taiwan", "Tier 1", "Approved",  "Wei Chen"),
    ("SUP-005", "OmegaWire Systems",           "USA",    "Tier 2", "Approved",  "Maria Reyes"),
    ("SUP-006", "Carbon Aero Structures",      "France", "Tier 1", "Approved",  "Pierre Dubois"),
    ("SUP-007", "Huanyu Motor Co.",            "China",  "Tier 2", "Conditional","Li Jing"),
    ("SUP-008", "NordBolt Fasteners",          "Sweden", "Tier 3", "Approved",  "Erik Svensson"),
    ("SUP-009", "AlphaComposite Materials",    "USA",    "Tier 1", "Approved",  "Sarah Kim"),
    ("SUP-010", "RedRock Machining",           "Mexico", "Tier 2", "Conditional","Carlos Vega"),
]

df_suppliers = pd.DataFrame(SUPPLIERS, columns=[
    "supplier_id","supplier_name","country","supplier_tier","approved_status","primary_contact"
])
df_suppliers.to_csv(f"{DATA_DIR}/suppliers.csv", index=False)
print("✓ suppliers.csv")

# ─── PARTS ──────────────────────────────────────────────────────────────────

PARTS = [
    ("MMB-001","Motor Mount Bracket",      "Propulsion","Aluminum 7075","High",  "SUP-003", 85.00),
    ("ESC-002","Electronic Speed Controller","Propulsion","PCB/MOSFET",  "High",  "SUP-004", 120.00),
    ("PROP-003","Carbon Fiber Propeller",   "Propulsion","CFRP",         "High",  "SUP-006", 45.00),
    ("MOTOR-004","Brushless Motor 5010",    "Propulsion","Copper/Steel", "High",  "SUP-007", 95.00),
    ("WHAR-005","Wiring Harness Assembly",  "Propulsion","Copper/PVC",   "Medium","SUP-005", 38.00),
    ("BCON-006","Battery Connector XT90",  "Propulsion","Gold Plated",  "High",  "SUP-004", 12.00),
    ("WING-007","Wing Spar Assembly",       "Wing Structure","CFRP",     "High",  "SUP-006", 210.00),
    ("BATT-008","LiPo Battery Pack 6S",    "Battery",   "Lithium",      "High",  "SUP-009", 320.00),
    ("PYLD-009","Payload Release Mechanism","Payload",   "Aluminum/HDPE","Medium","SUP-001", 75.00),
    ("FAST-010","M3 Titanium Fastener Set", "Propulsion","Titanium",     "Low",   "SUP-008", 5.00),
    ("THRM-011","Thermal Interface Pad",    "Propulsion","Silicone",     "Medium","SUP-005", 3.50),
    ("FRAME-012","Main Frame Chassis",      "Wing Structure","CFRP",     "High",  "SUP-001", 450.00),
    ("GPS-013","GPS Module u-blox F9P",    "Avionics",  "PCB",          "High",  "SUP-004", 180.00),
    ("FC-014","Flight Controller Board",   "Avionics",  "PCB",          "High",  "SUP-004", 250.00),
    ("LARM-015","Landing Arm Assembly",    "Wing Structure","Aluminum",  "Medium","SUP-010", 65.00),
]

df_parts = pd.DataFrame(PARTS, columns=[
    "part_number","part_name","subsystem","material","criticality_level","supplier_id","unit_cost"
])
df_parts.to_csv(f"{DATA_DIR}/parts.csv", index=False)
print("✓ parts.csv")

# ─── HELPERS ────────────────────────────────────────────────────────────────

DEFECT_TYPES = [
    "Dimensional Out-of-Tolerance","Surface Finish","Missing Hardware",
    "Solder Joint Failure","Delamination","Incorrect Part Number","Contamination",
    "Crack / Fracture","Insulation Damage","Corrosion","Wrong Material Cert",
    "Thread Damage","Connector Misalignment","Electrical Short","Documentation Missing",
]

DEFECT_CATEGORIES = {
    "Dimensional Out-of-Tolerance":"Dimensional",
    "Surface Finish":"Cosmetic",
    "Missing Hardware":"Assembly",
    "Solder Joint Failure":"Electrical",
    "Delamination":"Composite",
    "Incorrect Part Number":"Documentation",
    "Contamination":"Cosmetic",
    "Crack / Fracture":"Composite",
    "Insulation Damage":"Electrical",
    "Corrosion":"Cosmetic",
    "Wrong Material Cert":"Documentation",
    "Thread Damage":"Dimensional",
    "Connector Misalignment":"Assembly",
    "Electrical Short":"Electrical",
    "Documentation Missing":"Documentation",
}

STAGES = ["Receiving Inspection","In-Process Inspection","Final Assembly","End-of-Line Test"]
DISPOSITIONS = ["Accept","Reject","Rework","Use-As-Is","MRB Review","Supplier Return"]
INSPECTORS = ["QE-Torres","QE-Patel","QE-Nguyen","QE-Brooks","QE-Osei"]
STATIONS = ["Wing Assembly","Motor Installation","Battery Installation","Payload Assembly","Final Assembly","End-of-Line Test"]

part_numbers = [p[0] for p in PARTS]
supplier_ids = [s[0] for s in SUPPLIERS]

# ─── INSPECTION RECORDS ─────────────────────────────────────────────────────

def rand_date(start="2023-01-01", end="2024-12-31"):
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end,   "%Y-%m-%d")
    return s + timedelta(days=random.randint(0, (e - s).days))

# Supplier defect rate bias (some are worse)
supplier_defect_bias = {
    "SUP-001":0.03,"SUP-002":0.02,"SUP-003":0.06,"SUP-004":0.04,
    "SUP-005":0.05,"SUP-006":0.02,"SUP-007":0.12,"SUP-008":0.01,
    "SUP-009":0.03,"SUP-010":0.09,
}

records = []
ncr_refs = []

for i in range(1, 10001):
    part = random.choice(PARTS)
    pn = part[0]
    # match supplier to part
    sup_id = part[5]
    defect_rate = supplier_defect_bias.get(sup_id, 0.05)

    date = rand_date()
    qty_recv = random.randint(10, 200)
    qty_insp = random.randint(max(1, qty_recv // 4), qty_recv)
    expected_fail = max(0, int(qty_insp * np.random.beta(2, max(2, int(1/defect_rate)))))
    qty_fail = min(expected_fail, qty_insp)

    defect = random.choice(DEFECT_TYPES) if qty_fail > 0 else None
    defect_cat = DEFECT_CATEGORIES.get(defect, None) if defect else None
    stage = random.choice(STAGES)

    if qty_fail == 0:
        disp = "Accept"
        ncr_id = None
    elif qty_fail / qty_insp > 0.15:
        disp = random.choice(["Reject","Supplier Return","MRB Review"])
        ncr_id = f"NCR-{random.randint(1000,9999)}"
    else:
        disp = random.choice(["Rework","Use-As-Is","Reject"])
        ncr_id = f"NCR-{random.randint(1000,9999)}" if random.random() < 0.4 else None

    cost_impact = round(qty_fail * part[6] * random.uniform(0.5, 2.5), 2) if qty_fail > 0 else 0.0

    records.append({
        "inspection_id":  f"INS-{i:05d}",
        "date":           date.strftime("%Y-%m-%d"),
        "part_number":    pn,
        "supplier_id":    sup_id,
        "lot_number":     f"LOT-{random.randint(100,999)}",
        "quantity_received":  qty_recv,
        "quantity_inspected": qty_insp,
        "quantity_failed":    qty_fail,
        "defect_type":        defect,
        "defect_category":    defect_cat,
        "inspection_stage":   stage,
        "inspector":          random.choice(INSPECTORS),
        "disposition":        disp,
        "ncr_id":             ncr_id,
        "cost_impact":        cost_impact,
    })

df_inspection = pd.DataFrame(records)
df_inspection.to_csv(f"{DATA_DIR}/inspection_records.csv", index=False)
print(f"✓ inspection_records.csv  ({len(df_inspection)} rows)")

# ─── PRODUCTION RECORDS ──────────────────────────────────────────────────────

# Station FPY bias (some stations are worse)
station_fpy = {
    "Wing Assembly":0.88, "Motor Installation":0.91, "Battery Installation":0.94,
    "Payload Assembly":0.90, "Final Assembly":0.87, "End-of-Line Test":0.83,
}

prod_records = []
for i in range(1, 3001):
    station = random.choice(STATIONS)
    date = rand_date()
    units_started = random.randint(20, 100)
    fpy = np.random.normal(station_fpy[station], 0.04)
    fpy = min(max(fpy, 0.60), 0.99)
    units_pass = int(units_started * fpy)
    remaining = units_started - units_pass
    units_rework = int(remaining * random.uniform(0.4, 0.75))
    units_scrap = remaining - units_rework
    units_completed = units_started - units_scrap
    cycle = random.gauss(45 + STATIONS.index(station)*3, 8)

    prod_records.append({
        "production_id":         f"PROD-{i:05d}",
        "date":                  date.strftime("%Y-%m-%d"),
        "station_name":          station,
        "units_started":         units_started,
        "units_completed":       max(units_completed, 1),
        "units_passed_first_time": units_pass,
        "units_reworked":        units_rework,
        "units_scrapped":        units_scrap,
        "cycle_time_minutes":    round(max(cycle, 10), 1),
        "shift":                 random.choice(["Day","Night","Swing"]),
        "operator_team":         random.choice(["Team-A","Team-B","Team-C","Team-D"]),
    })

df_production = pd.DataFrame(prod_records)
df_production.to_csv(f"{DATA_DIR}/production_records.csv", index=False)
print(f"✓ production_records.csv  ({len(df_production)} rows)")

# ─── NCR RECORDS ─────────────────────────────────────────────────────────────

NCR_STATUSES = ["Open","Under Review","Containment Complete","RCA Complete","CAPA In Progress","Closed"]
RC_CATEGORIES = ["Process Deviation","Supplier Non-Conformance","Design Deficiency",
                 "Measurement Error","Training Gap","Incoming Material","Tooling Wear"]
OWNERS = ["QE-Torres","QE-Patel","QE-Nguyen","QE-Brooks","QE-Osei"]

ncr_records = []
for i in range(1, 501):
    date_opened = rand_date()
    status = random.choices(
        NCR_STATUSES,
        weights=[0.15, 0.10, 0.10, 0.10, 0.15, 0.40]
    )[0]
    if status == "Closed":
        days_to_close = random.randint(3, 45)
        date_closed = (date_opened + timedelta(days=days_to_close)).strftime("%Y-%m-%d")
    else:
        date_closed = None

    part = random.choice(PARTS)
    sup_id = part[5]
    severity = random.choices(["Critical","Major","Minor"], weights=[0.15, 0.50, 0.35])[0]

    ncr_records.append({
        "ncr_id":                f"NCR-{1000+i}",
        "date_opened":           date_opened.strftime("%Y-%m-%d"),
        "date_closed":           date_closed,
        "part_number":           part[0],
        "supplier_id":           sup_id,
        "defect_type":           random.choice(DEFECT_TYPES),
        "severity":              severity,
        "status":                status,
        "owner":                 random.choice(OWNERS),
        "root_cause_category":   random.choice(RC_CATEGORIES) if status not in ["Open","Under Review"] else None,
        "corrective_action_status": random.choice(["Not Started","In Progress","Complete"]) if status not in ["Open"] else "Not Started",
    })

df_ncr = pd.DataFrame(ncr_records)
df_ncr.to_csv(f"{DATA_DIR}/ncr_records.csv", index=False)
print(f"✓ ncr_records.csv  ({len(df_ncr)} rows)")

print("\n✅ All data files generated successfully.")
# ─── SPC MEASUREMENT RECORDS ────────────────────────────────────────────────
# Statistical Process Control dataset for critical GD&T / dimensional features.
# This supports the SPC Monitoring page in the dashboard.

SPC_FEATURES = [
    {
        "feature_id": "MMB_HOLE_POSITION_TP",
        "feature_name": "Motor Mount Hole True Position",
        "part_number": "MMB-001",
        "unit": "mm",
        "nominal": 0.00,
        "lsl": 0.00,
        "usl": 0.20,
        "target_sigma": 0.035,
        "measurement_type": "gdandt_position",
    },
    {
        "feature_id": "MMB_HOLE_DIAMETER",
        "feature_name": "Motor Mount Hole Diameter",
        "part_number": "MMB-001",
        "unit": "mm",
        "nominal": 5.00,
        "lsl": 4.95,
        "usl": 5.05,
        "target_sigma": 0.012,
        "measurement_type": "dimension",
    },
    {
        "feature_id": "MMB_BRACKET_THICKNESS",
        "feature_name": "Motor Mount Bracket Thickness",
        "part_number": "MMB-001",
        "unit": "mm",
        "nominal": 6.00,
        "lsl": 5.90,
        "usl": 6.10,
        "target_sigma": 0.025,
        "measurement_type": "dimension",
    },
    {
        "feature_id": "MMB_SLOT_WIDTH",
        "feature_name": "Motor Mount Alignment Slot Width",
        "part_number": "MMB-001",
        "unit": "mm",
        "nominal": 8.00,
        "lsl": 7.90,
        "usl": 8.10,
        "target_sigma": 0.022,
        "measurement_type": "dimension",
    },
]

spc_records = []
start = datetime.strptime("2024-01-01", "%Y-%m-%d")
subgroups_per_feature = 90
subgroup_size = 5

for feature in SPC_FEATURES:
    # Add a small intentional process drift after subgroup 55 so the dashboard
    # has realistic SPC signals to detect.
    for subgroup in range(1, subgroups_per_feature + 1):
        measurement_date = start + timedelta(days=subgroup * 2)
        drift_factor = max(0, subgroup - 55)

        if feature["measurement_type"] == "gdandt_position":
            # True position error is one-sided: lower is better, upper spec is critical.
            process_mean = 0.085 + drift_factor * 0.0018
            values = np.random.normal(process_mean, feature["target_sigma"], subgroup_size)
            values = np.clip(values, 0.0, None)
        else:
            # Two-sided dimensions drift slowly upward after subgroup 55.
            process_mean = feature["nominal"] + drift_factor * 0.0012
            values = np.random.normal(process_mean, feature["target_sigma"], subgroup_size)

        for sample_idx, measured_value in enumerate(values, start=1):
            out_of_spec = measured_value < feature["lsl"] or measured_value > feature["usl"]
            spc_records.append({
                "measurement_id": f"SPC-{feature['feature_id']}-{subgroup:03d}-{sample_idx}",
                "date": measurement_date.strftime("%Y-%m-%d"),
                "subgroup_id": subgroup,
                "sample_number": sample_idx,
                "part_number": feature["part_number"],
                "feature_id": feature["feature_id"],
                "feature_name": feature["feature_name"],
                "measurement_type": feature["measurement_type"],
                "nominal": feature["nominal"],
                "lsl": feature["lsl"],
                "usl": feature["usl"],
                "measured_value": round(float(measured_value), 4),
                "unit": feature["unit"],
                "out_of_spec": bool(out_of_spec),
            })

df_spc = pd.DataFrame(spc_records)
df_spc.to_csv(f"{DATA_DIR}/spc_measurements.csv", index=False)
print(f"✓ spc_measurements.csv  ({len(df_spc)} rows)")
