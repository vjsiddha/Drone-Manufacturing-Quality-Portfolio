"""
database.py
SQLite-backed persistence for NCR and CAPA records.
All data lives in data/ncr_capa.db at the repository root.
"""

import sqlite3
from pathlib import Path
import pandas as pd
from datetime import date, timedelta

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "ncr_capa.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS ncr (
        ncr_id              TEXT PRIMARY KEY,
        date_opened         TEXT,
        created_by          TEXT,
        part_number         TEXT,
        part_name           TEXT,
        part_revision       TEXT DEFAULT 'A',
        serial_number       TEXT,
        lot_number          TEXT,
        supplier_id         TEXT,
        supplier_name       TEXT,
        defect_type         TEXT,
        defect_description  TEXT,
        detected_at         TEXT,
        severity            TEXT,
        quantity_affected   INTEGER DEFAULT 1,
        requirement         TEXT,
        actual_result       TEXT,
        disposition         TEXT DEFAULT 'MRB Review',
        disposition_notes   TEXT,
        status              TEXT DEFAULT 'Open',
        owner               TEXT,
        due_date            TEXT,
        linked_capa_id      TEXT,
        source              TEXT DEFAULT 'Manual'
    );

    CREATE TABLE IF NOT EXISTS capa (
        capa_id                 TEXT PRIMARY KEY,
        linked_ncr_id           TEXT,
        date_created            TEXT,
        problem_statement       TEXT,
        containment_action      TEXT,
        root_cause              TEXT,
        corrective_action       TEXT,
        preventive_action       TEXT,
        action_owner            TEXT,
        due_date                TEXT,
        verification_method     TEXT,
        verification_result     TEXT,
        effectiveness_check_date TEXT,
        closure_status          TEXT DEFAULT 'Open',
        five_why_1              TEXT,
        five_why_2              TEXT,
        five_why_3              TEXT,
        five_why_4              TEXT,
        five_why_5              TEXT,
        five_why_root_cause     TEXT,
        fishbone_manpower       TEXT,
        fishbone_machine        TEXT,
        fishbone_method         TEXT,
        fishbone_material       TEXT,
        fishbone_measurement    TEXT,
        fishbone_environment    TEXT
    );
    """)
    conn.commit()
    conn.close()


# ─── NCR CRUD ─────────────────────────────────────────────────────────────────

def ncr_next_id() -> str:
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) FROM ncr").fetchone()
    n = row[0] + 1
    conn.close()
    return f"NCR-{n:04d}"


def ncr_due_date(severity: str) -> str:
    days = {"Critical": 2, "Major": 7, "Minor": 14}.get(severity, 7)
    return (date.today() + timedelta(days=days)).isoformat()


def insert_ncr(data: dict):
    conn = get_conn()
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    conn.execute(f"INSERT OR REPLACE INTO ncr ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()


def update_ncr(ncr_id: str, updates: dict):
    if not updates:
        return
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn = get_conn()
    conn.execute(f"UPDATE ncr SET {set_clause} WHERE ncr_id=?", list(updates.values()) + [ncr_id])
    conn.commit()
    conn.close()


def get_all_ncrs() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM ncr ORDER BY date_opened DESC", conn)
    conn.close()
    return df


def get_ncr(ncr_id: str) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM ncr WHERE ncr_id=?", (ncr_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# ─── CAPA CRUD ────────────────────────────────────────────────────────────────

def capa_next_id() -> str:
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) FROM capa").fetchone()
    n = row[0] + 1
    conn.close()
    return f"CAPA-{n:04d}"


def insert_capa(data: dict):
    conn = get_conn()
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    conn.execute(f"INSERT OR REPLACE INTO capa ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()
    # link back to NCR
    if "linked_ncr_id" in data and data["linked_ncr_id"]:
        update_ncr(data["linked_ncr_id"], {
            "linked_capa_id": data["capa_id"],
            "status": "CAPA Open",
        })


def update_capa(capa_id: str, updates: dict):
    if not updates:
        return
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn = get_conn()
    conn.execute(f"UPDATE capa SET {set_clause} WHERE capa_id=?", list(updates.values()) + [capa_id])
    conn.commit()
    conn.close()


def get_all_capas() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM capa ORDER BY date_created DESC", conn)
    conn.close()
    return df


def get_capa(capa_id: str) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM capa WHERE capa_id=?", (capa_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


# ─── IMPORT FROM PROJECT 3 ───────────────────────────────────────────────────

def import_draft_ncrs(csv_path: str) -> tuple[int, int]:
    """Import draft NCRs from GD&T inspection system. Returns (imported, skipped)."""
    df = pd.read_csv(csv_path)
    imported = 0
    skipped  = 0

    conn = get_conn()
    existing = {row[0] for row in conn.execute("SELECT ncr_id FROM ncr").fetchall()}
    conn.close()

    DETECTED_AT_MAP = {
        "GDT Inspection System": "Receiving Inspection",
    }

    for _, row in df.iterrows():
        # Map draft NCR fields → our schema
        new_id = ncr_next_id()
        severity = str(row.get("severity", "Major"))
        record = {
            "ncr_id":             new_id,
            "date_opened":        str(row.get("date_opened", date.today().isoformat())),
            "created_by":         str(row.get("inspector", "GDT System")),
            "part_number":        str(row.get("part_number", "")),
            "part_name":          str(row.get("part_name", "")),
            "serial_number":      str(row.get("part_serial_number", "")),
            "lot_number":         str(row.get("lot_number", "")),
            "supplier_id":        str(row.get("supplier_id", "")),
            "supplier_name":      "AeroForge Precision",
            "defect_type":        str(row.get("failed_feature", "")),
            "defect_description": str(row.get("feature_name", "")),
            "detected_at":        DETECTED_AT_MAP.get(str(row.get("source","")), "Receiving Inspection"),
            "severity":           severity,
            "quantity_affected":  1,
            "requirement":        str(row.get("requirement", "")),
            "actual_result":      str(row.get("actual_result", "")),
            "disposition":        str(row.get("recommended_disposition", "MRB Review")),
            "status":             "Open",
            "owner":              "QE-Torres",
            "due_date":           ncr_due_date(severity),
            "source":             "GDT Inspection Import",
        }
        insert_ncr(record)
        imported += 1

    return imported, skipped