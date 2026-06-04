"""
seed_data.py
Seeds the database with realistic sample NCRs and CAPAs.
Run once before launching the app for the first time.
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, insert_ncr, insert_capa, ncr_next_id, capa_next_id, ncr_due_date
from datetime import date, timedelta
import random

random.seed(99)

init_db()

PARTS = [
    ("MMB-001","Motor Mount Bracket","SUP-003","AeroForge Precision"),
    ("ESC-002","Electronic Speed Controller","SUP-004","FastTrack Electronics"),
    ("PROP-003","Carbon Fiber Propeller","SUP-006","Carbon Aero Structures"),
    ("MOTOR-004","Brushless Motor 5010","SUP-007","Huanyu Motor Co."),
    ("WHAR-005","Wiring Harness Assembly","SUP-005","OmegaWire Systems"),
    ("BCON-006","Battery Connector XT90","SUP-004","FastTrack Electronics"),
    ("WING-007","Wing Spar Assembly","SUP-006","Carbon Aero Structures"),
]

DEFECT_TYPES = [
    "Dimensional Out-of-Tolerance","Solder Joint Failure","Delamination",
    "Connector Misalignment","Insulation Damage","Wrong Material Cert",
    "Surface Finish","Thread Damage","Electrical Short","Documentation Missing",
]

DETECTED_AT = [
    "Receiving Inspection","In-Process Inspection",
    "Final Assembly","End-of-Line Test","Customer Field Return",
]

DISPOSITIONS = ["Use-As-Is","Rework","Repair","Scrap","Return to Supplier","MRB Review"]
OWNERS = ["QE-Torres","QE-Patel","QE-Nguyen","QE-Brooks","QE-Osei"]

STATUSES_OPEN   = ["Open","Containment Pending","Containment Complete","RCA Pending"]
STATUSES_PROGR  = ["RCA Complete","CAPA Open","Verification Pending"]
STATUSES_CLOSED = ["Closed"]

def rand_date(days_back_min, days_back_max):
    offset = random.randint(days_back_min, days_back_max)
    return (date.today() - timedelta(days=offset)).isoformat()

NCR_IDS = []

# ── Seed NCRs ──────────────────────────────────────────────────────────────
for i in range(60):
    part = random.choice(PARTS)
    severity = random.choices(["Critical","Major","Minor"], weights=[0.10,0.55,0.35])[0]

    # Weight toward varied statuses
    bucket = random.choices(["open","progress","closed"], weights=[0.35,0.25,0.40])[0]
    if bucket == "open":
        status = random.choice(STATUSES_OPEN)
    elif bucket == "progress":
        status = random.choice(STATUSES_PROGR)
    else:
        status = "Closed"

    date_opened = rand_date(5, 120)
    due = ncr_due_date(severity)
    ncr_id = ncr_next_id()
    NCR_IDS.append((ncr_id, status, part, severity))

    insert_ncr({
        "ncr_id":             ncr_id,
        "date_opened":        date_opened,
        "created_by":         random.choice(OWNERS),
        "part_number":        part[0],
        "part_name":          part[1],
        "part_revision":      "A",
        "serial_number":      f"SN-{random.randint(1000,9999)}",
        "lot_number":         f"LOT-{random.randint(100,299)}",
        "supplier_id":        part[2],
        "supplier_name":      part[3],
        "defect_type":        random.choice(DEFECT_TYPES),
        "defect_description": f"Non-conformance detected during {random.choice(DETECTED_AT).lower()}",
        "detected_at":        random.choice(DETECTED_AT),
        "severity":           severity,
        "quantity_affected":  random.randint(1, 25),
        "requirement":        "Per engineering drawing rev A",
        "actual_result":      "Out of specification per CMM measurement",
        "disposition":        random.choice(DISPOSITIONS),
        "disposition_notes":  "Pending engineering review",
        "status":             status,
        "owner":              random.choice(OWNERS),
        "due_date":           due,
        "source":             "Manual",
    })

# ── Seed CAPAs for progressed/closed NCRs ─────────────────────────────────
FIVE_WHY_SETS = [
    ("Motor mounts failing true position tolerance",
     "Hole position measured out of tolerance on CMM",
     "CNC fixture showed wear beyond re-qualification interval",
     "Fixture inspection interval not tracked in maintenance system",
     "No formal fixture lifecycle policy existed",
     "Lack of fixture lifecycle management policy",
     "Fixture wear caused CNC position drift"),
    ("ESC solder joints failing at receiving inspection",
     "X-ray shows insufficient solder fill on power pads",
     "Reflow oven temperature profile drifted low",
     "Oven calibration overdue by 6 weeks",
     "Calibration schedule not enforced by production system",
     "No automated calibration alert in production schedule",
     "Reflow oven temperature drift due to missed calibration"),
    ("Propeller delamination found at assembly",
     "CFRP layers separating at root of blade",
     "Moisture ingress during storage in uncontrolled environment",
     "Storage area humidity exceeded spec for composite parts",
     "No humidity monitoring in receiving storage area",
     "Absence of environmental monitoring in storage",
     "Inadequate storage environment for CFRP components"),
]

VERIFICATION_METHODS = [
    "Repeat Inspection","Process Audit","Supplier 8D Review",
    "First Article Inspection","End-of-Line Test Review","Yield Monitoring",
]

capa_count = 0
for ncr_id, status, part, severity in NCR_IDS:
    if status not in STATUSES_PROGR + STATUSES_CLOSED:
        continue
    if capa_count >= 20:
        break

    fw = random.choice(FIVE_WHY_SETS)
    capa_id = capa_next_id()
    closed  = status == "Closed"

    insert_capa({
        "capa_id":                  capa_id,
        "linked_ncr_id":            ncr_id,
        "date_created":             rand_date(3, 60),
        "problem_statement":        fw[0],
        "containment_action":       "Quarantine affected lot; notify production to halt use pending disposition",
        "root_cause":               fw[6],
        "corrective_action":        "Implement immediate corrective control per engineering review",
        "preventive_action":        "Update SOP and add recurring audit checkpoint",
        "action_owner":             random.choice(OWNERS),
        "due_date":                 ncr_due_date(severity),
        "verification_method":      random.choice(VERIFICATION_METHODS),
        "verification_result":      "Verified effective — no recurrence in 30-day monitoring window" if closed else "",
        "effectiveness_check_date": rand_date(1, 15) if closed else "",
        "closure_status":           "Closed" if closed else "Open",
        "five_why_1":               fw[1],
        "five_why_2":               fw[2],
        "five_why_3":               fw[3],
        "five_why_4":               fw[4],
        "five_why_5":               fw[5],
        "five_why_root_cause":      fw[6],
        "fishbone_manpower":        "Operator not trained on updated SOP",
        "fishbone_machine":         "Equipment calibration overdue",
        "fishbone_method":          "Inspection procedure lacked acceptance criteria",
        "fishbone_material":        "Incoming material cert not verified",
        "fishbone_measurement":     "Measurement system not capable (GR&R > 30%)",
        "fishbone_environment":     "Temperature/humidity out of spec in work area",
    })
    capa_count += 1

print(f"✓ Database seeded: {len(NCR_IDS)} NCRs, {capa_count} CAPAs")