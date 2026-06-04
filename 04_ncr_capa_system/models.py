
"""
models.py
Shared constants and lightweight field documentation for the NCR/CAPA system.
This file is intentionally simple so it can be imported by future modules/tests.
"""

NCR_STATUSES = [
    "Open", "Containment Pending", "Containment Complete", "RCA Pending",
    "RCA Complete", "CAPA Open", "Verification Pending", "Closed"
]

CAPA_STATUSES = ["Open", "Verification Pending", "Closed"]

SEVERITIES = ["Critical", "Major", "Minor"]

DISPOSITIONS = [
    "Use-As-Is", "Rework", "Repair", "Scrap", "Return to Supplier", "MRB Review"
]

DETECTED_AT = [
    "Receiving Inspection", "In-Process Inspection", "Final Assembly",
    "End-of-Line Test", "Customer Field Return"
]

FISHBONE_CATEGORIES = [
    "Manpower", "Machine", "Method", "Material", "Measurement", "Environment"
]

VERIFICATION_METHODS = [
    "Repeat Inspection", "Process Audit", "Supplier 8D Review",
    "First Article Inspection", "End-of-Line Test Review", "Yield Monitoring"
]

DISPOSITION_REQUIREMENTS = {
    "Use-As-Is": "Engineering justification is required.",
    "Rework": "Rework instruction is required.",
    "Repair": "Repair method and verification plan are required.",
    "Scrap": "Scrap cost impact is required.",
    "Return to Supplier": "Supplier notification details are required.",
    "MRB Review": "Assigned MRB reviewer is required.",
}
