
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from ..common.paths import DATA_DIR, REPORTS_DIR, DRAFT_NCRS, NCR_DB_PATH
from ..common.ui import product_header, metric_card, status_badge, lifecycle_flow

try:
    from shared_styles import kpi_card, alert, section, page_header, C
except Exception:
    kpi_card = alert = section = page_header = None
    C = {"surface":"#111827","border":"#374151","text":"#f9fafb","subtle":"#d1d5db","muted":"#9ca3af","blue":"#4ea1ff","red":"#ff4b4b","amber":"#f5b642","green":"#35c46b"}

from modules.ncr_capa.database import (
    init_db,
    get_all_ncrs,
    get_ncr,
    insert_ncr,
    update_ncr,
    ncr_next_id,
    ncr_due_date,
    get_all_capas,
    get_capa,
    insert_capa,
    update_capa,
    capa_next_id,
    import_draft_ncrs,
)

try:
    from modules.ncr_capa.models import (
        NCR_STATUSES,
        CAPA_STATUSES,
        SEVERITIES,
        DISPOSITIONS,
        DETECTED_AT,
        VERIFICATION_METHODS,
        DISPOSITION_REQUIREMENTS,
    )
except Exception:
    NCR_STATUSES = ["Open", "Containment Pending", "Containment Complete", "RCA Pending", "RCA Complete", "CAPA Open", "Verification Pending", "Closed"]
    CAPA_STATUSES = ["Open", "Verification Pending", "Closed"]
    SEVERITIES = ["Critical", "Major", "Minor"]
    DISPOSITIONS = ["Use-As-Is", "Rework", "Repair", "Scrap", "Return to Supplier", "MRB Review"]
    DETECTED_AT = ["Receiving Inspection", "In-Process Inspection", "Final Assembly", "End-of-Line Test", "Customer Field Return"]
    VERIFICATION_METHODS = ["Repeat Inspection", "Process Audit", "Supplier 8D Review", "First Article Inspection", "End-of-Line Test Review", "Yield Monitoring"]
    DISPOSITION_REQUIREMENTS = {
        "Use-As-Is": "Engineering justification is required.",
        "Rework": "Rework instruction is required.",
        "Repair": "Repair method and verification plan are required.",
        "Scrap": "Scrap cost impact is required.",
        "Return to Supplier": "Supplier notification details are required.",
        "MRB Review": "Assigned MRB reviewer is required.",
    }

from modules.ncr_capa.ncr_capa_report_generator_v2 import ncr_report, capa_report, eight_d_report


OWNERS = ["QE-Torres", "QE-Patel", "QE-Nguyen", "QE-Brooks", "QE-Osei", "SQE-Li", "MFG-Chen"]
REPORTS_NCR_DIR = REPORTS_DIR / "ncr_reports"
REPORTS_CAPA_DIR = REPORTS_DIR / "capa_reports"
REPORTS_NCR_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_CAPA_DIR.mkdir(parents=True, exist_ok=True)


def _safe_date(value, default_days=0):
    try:
        if pd.isna(value) or value == "":
            return date.today() + timedelta(days=default_days)
        return pd.to_datetime(value).date()
    except Exception:
        return date.today() + timedelta(days=default_days)


def _normalize_status_for_model(status):
    if status == "CAPA In Progress":
        return "CAPA Open"
    if status in NCR_STATUSES:
        return status
    return "Open"


def _supplier_lookup():
    path = DATA_DIR / "suppliers.csv"
    if not path.exists():
        return {}
    try:
        sup = pd.read_csv(path)
        return dict(zip(sup["supplier_id"].astype(str), sup["supplier_name"].astype(str)))
    except Exception:
        return {}


def _hydrate_legacy_ncr_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    supplier_names = _supplier_lookup()
    rows = []
    for _, row in df.iterrows():
        severity = str(row.get("severity", "Major"))
        supplier_id = str(row.get("supplier_id", ""))
        status = _normalize_status_for_model(str(row.get("status", "Open")))
        rows.append({
            "ncr_id": str(row.get("ncr_id", ncr_next_id())),
            "date_opened": str(row.get("date_opened", date.today().isoformat())),
            "created_by": "Legacy NCR CSV",
            "part_number": str(row.get("part_number", "")),
            "part_name": "Drone Manufacturing Part",
            "part_revision": "A",
            "serial_number": "",
            "lot_number": "",
            "supplier_id": supplier_id,
            "supplier_name": supplier_names.get(supplier_id, supplier_id or "Unknown Supplier"),
            "defect_type": str(row.get("defect_type", "")),
            "defect_description": f"{row.get('defect_type', 'Non-conformance')} identified during quality review.",
            "detected_at": "Quality Analytics Import",
            "severity": severity,
            "quantity_affected": 1,
            "requirement": "Per engineering drawing, specification, or supplier quality requirement.",
            "actual_result": f"Root cause category: {row.get('root_cause_category', 'Pending investigation')}",
            "disposition": "MRB Review",
            "disposition_notes": "",
            "status": status,
            "owner": str(row.get("owner", "QE-Torres")),
            "due_date": ncr_due_date(severity),
            "linked_capa_id": "",
            "source": "Legacy NCR CSV",
        })
    return pd.DataFrame(rows)


def _save_report(content: str, folder: Path, filename: str):
    path = folder / filename
    path.write_text(content, encoding="utf-8")
    return path


def _load_reference_csvs():
    ncr_csv = DATA_DIR / "ncr_records.csv"
    suppliers_csv = DATA_DIR / "suppliers.csv"
    return ncr_csv, suppliers_csv


def _status_variant(value):
    if value in ("Closed", "PASS"):
        return "success"
    if value in ("Critical", "FAIL", "Overdue"):
        return "danger"
    if value in ("Major", "CAPA Open", "Verification Pending", "RCA Pending", "Containment Pending"):
        return "warning"
    return "info"



def _case_alert(text: str, variant: str = "blue"):
    if alert:
        st.markdown(alert(text, variant), unsafe_allow_html=True)
    else:
        getattr(st, "warning" if variant == "amber" else "error" if variant == "red" else "info")(text)


def _section(title: str):
    if section:
        st.markdown(section(title), unsafe_allow_html=True)
    else:
        st.markdown(f"### {title}")


def _case_kpi(label: str, value, tone: str = "blue", sub: str = ""):
    if kpi_card:
        st.markdown(kpi_card(label, value, tone, sub), unsafe_allow_html=True)
    else:
        st.metric(label, value, help=sub or None)


def _case_file_banner(ncrs: pd.DataFrame, capas: pd.DataFrame):
    open_cases = 0
    critical_cases = 0
    containment = 0
    verification = 0
    if not ncrs.empty and "status" in ncrs.columns:
        open_cases = int((ncrs["status"].astype(str) != "Closed").sum())
        containment = int(ncrs["status"].astype(str).str.contains("Containment", case=False, na=False).sum())
        verification = int(ncrs["status"].astype(str).str.contains("Verification", case=False, na=False).sum())
    if not ncrs.empty and "severity" in ncrs.columns:
        critical_cases = int((ncrs["severity"].astype(str) == "Critical").sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1: _case_kpi("Open Cases", open_cases, "red" if open_cases else "green", "Active NCR investigations")
    with c2: _case_kpi("Critical Cases", critical_cases, "red" if critical_cases else "green", "Highest priority")
    with c3: _case_kpi("Containment Active", containment, "amber" if containment else "blue", "Product control stage")
    with c4: _case_kpi("CAPAs", len(capas), "blue", "Corrective action records")


def _timeline(status: str = "Open", has_capa: bool = False):
    steps = [
        ("Evidence Intake", True),
        ("Containment", status in ["Containment Complete", "RCA Pending", "RCA Complete", "CAPA Open", "Verification Pending", "Closed"]),
        ("Root Cause", status in ["RCA Complete", "CAPA Open", "Verification Pending", "Closed"]),
        ("Corrective Action", has_capa or status in ["CAPA Open", "Verification Pending", "Closed"]),
        ("Verification", status in ["Verification Pending", "Closed"]),
        ("Closure", status == "Closed"),
    ]
    cols = st.columns(len(steps))
    for col, (name, done) in zip(cols, steps):
        symbol = "✓" if done else "○"
        tone = "green" if done else "neutral"
        with col:
            _case_kpi(name, symbol, tone, "Investigation timeline")

def _show_workflow_banner():
    _case_alert(
        "<b>Quality Detective workflow:</b> Evidence Review creates escalation records → Case Management opens investigations → "
        "quality engineers contain suspect product, identify root cause, launch CAPAs, verify effectiveness, and close the case.",
        "blue",
    )


def _ensure_db():
    init_db()


def dashboard():
    ncrs = get_all_ncrs()
    capas = get_all_capas()

    if ncrs.empty:
        st.warning("No investigation cases found yet. Import escalation records from Evidence Review or load the legacy NCR CSV to populate the case queue.")
        return

    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        selected_status = st.multiselect("Filter case status", sorted(ncrs["status"].dropna().unique()))
    with colf2:
        selected_severity = st.multiselect("Filter case severity", SEVERITIES)
    with colf3:
        selected_supplier = st.multiselect("Filter supplier / source", sorted(ncrs["supplier_name"].dropna().unique()))

    df = ncrs.copy()
    if selected_status:
        df = df[df["status"].isin(selected_status)]
    if selected_severity:
        df = df[df["severity"].isin(selected_severity)]
    if selected_supplier:
        df = df[df["supplier_name"].isin(selected_supplier)]

    open_ncrs = df[df["status"] != "Closed"].copy()
    due_dates = pd.to_datetime(open_ncrs["due_date"], errors="coerce").dt.date
    overdue = open_ncrs[due_dates < date.today()] if not open_ncrs.empty else open_ncrs
    critical = df[df["severity"] == "Critical"]

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Total Cases", len(df), "All filtered investigations")
    with c2:
        metric_card("Open Cases", len(open_ncrs), "Require investigation")
    with c3:
        metric_card("Overdue", len(overdue), "Past due date")
    with c4:
        metric_card("Critical", len(critical), "Highest priority")
    with c5:
        metric_card("CAPAs", len(capas), "Corrective action records")

    if len(overdue) > 0:
        st.error(f"{len(overdue)} open case(s) are overdue. Review owner assignments, containment status, and verification plans.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Case Status Distribution")
        chart = df["status"].fillna("Unknown").value_counts().reset_index()
        chart.columns = ["Status", "Count"]
        st.plotly_chart(px.bar(chart, x="Status", y="Count"), use_container_width=True)

    with col2:
        st.subheader("Case Severity Breakdown")
        sev = df["severity"].fillna("Unknown").value_counts().reset_index()
        sev.columns = ["Severity", "Count"]
        st.plotly_chart(px.bar(sev, x="Severity", y="Count"), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top Suppliers by Case Count")
        supplier = df["supplier_name"].fillna("Unknown").value_counts().head(10).sort_values().reset_index()
        supplier.columns = ["Supplier", "Case Count"]
        st.plotly_chart(px.bar(supplier, x="Case Count", y="Supplier", orientation="h"), use_container_width=True)

    with col4:
        st.subheader("Top Investigation Themes")
        defect = df["defect_type"].fillna("Unknown").value_counts().head(10).sort_values().reset_index()
        defect.columns = ["Defect Type", "Count"]
        st.plotly_chart(px.bar(defect, x="Count", y="Defect Type", orientation="h"), use_container_width=True)

    st.subheader("Open Case Aging")
    aging = open_ncrs.copy()
    if not aging.empty:
        aging["date_opened_dt"] = pd.to_datetime(aging["date_opened"], errors="coerce")
        aging["age_days"] = (pd.Timestamp.today() - aging["date_opened_dt"]).dt.days
        st.plotly_chart(px.histogram(aging, x="age_days", nbins=20), use_container_width=True)
        st.dataframe(
            aging[["ncr_id", "date_opened", "age_days", "part_number", "supplier_name", "severity", "status", "owner", "due_date"]]
            .sort_values("age_days", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


def create_ncr():
    st.subheader("Open New Case")
    st.caption("Manually open an investigation case when a quality signal is found outside automated Evidence Review.")

    with st.form("create_ncr_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Part / Supplier")
            part_number = st.text_input("Part Number", "MMB-001")
            part_name = st.text_input("Part Name", "Drone Motor Mount Bracket")
            part_revision = st.text_input("Revision", "A")
            serial_number = st.text_input("Serial Number", "SN-0001")
            lot_number = st.text_input("Lot Number", "LOT-201")
            supplier_id = st.text_input("Supplier ID", "SUP-003")
            supplier_name = st.text_input("Supplier Name", "AeroForge Precision")

        with col2:
            st.markdown("#### Quality Signal")
            defect_type = st.text_input("Defect Type", "Dimensional Out-of-Tolerance")
            detected_at = st.selectbox("Detected At", DETECTED_AT)
            severity = st.selectbox("Severity", SEVERITIES, index=1)
            quantity_affected = st.number_input("Quantity Affected", min_value=1, value=1)
            owner = st.selectbox("Owner", OWNERS)
            disposition = st.selectbox("Initial Case Disposition", DISPOSITIONS, index=5)

        defect_description = st.text_area("Issue Description", "True position exceeds engineering drawing tolerance.")
        requirement = st.text_area("Requirement", "Engineering drawing Rev A: true position ≤ 0.20 mm relative to A|B|C.")
        actual_result = st.text_area("Evidence / Actual Result", "Measured true position exceeded drawing requirement.")
        disposition_notes = st.text_area("Disposition Notes", DISPOSITION_REQUIREMENTS.get(disposition, "Disposition notes required."))

        submitted = st.form_submit_button("Open New Case", type="primary")

    if submitted:
        ncr_id = ncr_next_id()
        insert_ncr({
            "ncr_id": ncr_id,
            "date_opened": date.today().isoformat(),
            "created_by": "Manual Entry",
            "part_number": part_number,
            "part_name": part_name,
            "part_revision": part_revision,
            "serial_number": serial_number,
            "lot_number": lot_number,
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "defect_type": defect_type,
            "defect_description": defect_description,
            "detected_at": detected_at,
            "severity": severity,
            "quantity_affected": int(quantity_affected),
            "requirement": requirement,
            "actual_result": actual_result,
            "disposition": disposition,
            "disposition_notes": disposition_notes,
            "status": "Open",
            "owner": owner,
            "due_date": ncr_due_date(severity),
            "source": "Manual",
        })
        st.success(f"Opened investigation case {ncr_id}. Due date: {ncr_due_date(severity)}")


def import_center():
    st.subheader("Evidence Intake")
    st.caption("Pull escalation records from Evidence Review into Case Management.")

    ncr_csv, suppliers_csv = _load_reference_csvs()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### From Evidence Review Center")
        st.write(f"Expected escalation file: `{DRAFT_NCRS}`")
        if DRAFT_NCRS.exists():
            preview = pd.read_csv(DRAFT_NCRS)
            st.dataframe(preview.head(15), use_container_width=True, hide_index=True)
            if st.button("Open cases from shared draft_ncrs.csv", type="primary", use_container_width=True):
                imported, skipped = import_draft_ncrs(str(DRAFT_NCRS))
                st.success(f"Imported {imported} escalation records. Skipped {skipped}.")
        else:
            st.warning("No shared draft_ncrs.csv found yet. Generate escalation records from Inspection Workbench first.")

    with col2:
        st.markdown("#### Upload Escalation CSV")
        uploaded = st.file_uploader("Upload draft_ncrs.csv", type=["csv"])
        if uploaded is not None:
            tmp = DATA_DIR / "_uploaded_draft_ncrs.csv"
            tmp.write_bytes(uploaded.getbuffer())
            preview = pd.read_csv(tmp)
            st.dataframe(preview.head(15), use_container_width=True, hide_index=True)
            if st.button("Import uploaded escalation records", use_container_width=True):
                imported, skipped = import_draft_ncrs(str(tmp))
                st.success(f"Imported {imported} escalation records. Skipped {skipped}.")

    st.divider()
    st.markdown("#### Optional: Load Historical Case Records")
    st.caption("Use this only if your database is empty or you want the historical dashboard dataset available in the integrated product.")
    if ncr_csv.exists():
        legacy_preview = pd.read_csv(ncr_csv)
        st.dataframe(legacy_preview.head(10), use_container_width=True, hide_index=True)
        if st.button("Load data/ncr_records.csv into NCR database"):
            legacy = _hydrate_legacy_ncr_csv(ncr_csv)
            count = 0
            for _, record in legacy.iterrows():
                insert_ncr(record.dropna().to_dict())
                count += 1
            st.success(f"Loaded {count} historical investigation cases into the database.")
    else:
        st.info("data/ncr_records.csv not found.")


def ncr_detail():
    st.subheader("Case Detail & Disposition")
    ncrs = get_all_ncrs()

    if ncrs.empty:
        st.warning("No cases available.")
        return

    display = ncrs.copy()
    display["selector"] = display["ncr_id"] + " | " + display["part_number"].fillna("") + " | " + display["defect_type"].fillna("") + " | " + display["status"].fillna("")
    selected_label = st.selectbox("Select Case", display["selector"].tolist())
    selected = selected_label.split(" | ")[0]
    ncr = get_ncr(selected)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Case ID", ncr.get("ncr_id", ""))
    with col2:
        metric_card("Severity", ncr.get("severity", ""))
    with col3:
        metric_card("Status", ncr.get("status", ""))
    with col4:
        metric_card("Due Date", ncr.get("due_date", ""))

    _section("Investigation Timeline")
    _timeline(ncr.get("status", "Open"), bool(ncr.get("linked_capa_id")))
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Requirement")
        st.info(ncr.get("requirement", "—"))
    with c2:
        st.markdown("#### Evidence / Actual Result")
        st.error(ncr.get("actual_result", "—"))

    st.markdown("#### Case Record")
    st.dataframe(pd.DataFrame([ncr]), use_container_width=True, hide_index=True)

    st.markdown("#### Update Case")
    with st.form("update_ncr_form"):
        u1, u2, u3 = st.columns(3)
        status = u1.selectbox("Status", NCR_STATUSES, index=NCR_STATUSES.index(ncr.get("status")) if ncr.get("status") in NCR_STATUSES else 0)
        disposition = u2.selectbox("Disposition", DISPOSITIONS, index=DISPOSITIONS.index(ncr.get("disposition")) if ncr.get("disposition") in DISPOSITIONS else 5)
        owner = u3.selectbox("Owner", OWNERS, index=OWNERS.index(ncr.get("owner")) if ncr.get("owner") in OWNERS else 0)
        notes = st.text_area("Disposition Notes", ncr.get("disposition_notes") or DISPOSITION_REQUIREMENTS.get(disposition, ""))
        submitted = st.form_submit_button("Save Case Updates", type="primary")

    if submitted:
        update_ncr(selected, {"status": status, "disposition": disposition, "owner": owner, "disposition_notes": notes})
        st.success("Case updated.")

    st.markdown("#### Case Report")
    refreshed = get_ncr(selected)
    report = ncr_report(refreshed)
    report_path = _save_report(report, REPORTS_NCR_DIR, f"{selected}_ncr_report.md")
    st.download_button("Download Case Report", data=report, file_name=f"{selected}_ncr_report.md", mime="text/markdown")
    with st.expander(f"Preview saved report: {report_path}"):
        st.markdown(report)


def create_capa():
    st.subheader("Create Corrective Action")
    st.caption("Create a corrective action linked to an active investigation case.")

    ncrs = get_all_ncrs()
    if ncrs.empty:
        st.warning("No cases available.")
        return

    candidates = ncrs[ncrs["status"] != "Closed"].copy()
    if candidates.empty:
        st.success("All NCRs are closed. No corrective action candidates available.")
        return

    candidates["selector"] = candidates["ncr_id"] + " | " + candidates["part_number"].fillna("") + " | " + candidates["defect_type"].fillna("")
    selected_label = st.selectbox("Source Case", candidates["selector"].tolist())
    selected = selected_label.split(" | ")[0]
    ncr = get_ncr(selected)

    st.info(f"Creating corrective action for {selected}: {ncr.get('defect_type', '')} on {ncr.get('part_number', '')}")

    with st.form("create_capa_form"):
        problem_statement = st.text_area(
            "Problem Statement",
            f"{ncr.get('defect_type','Non-conformance')} found on {ncr.get('part_number','')} from {ncr.get('supplier_name','')}."
        )
        containment_action = st.text_area("Containment Action", "Quarantine affected lot. Stop use pending MRB disposition.")
        action_owner = st.selectbox("Action Owner", OWNERS)
        due_date = st.date_input("CAPA Due Date", date.today() + timedelta(days=14))
        submitted = st.form_submit_button("Create Corrective Action", type="primary")

    if submitted:
        capa_id = capa_next_id()
        insert_capa({
            "capa_id": capa_id,
            "linked_ncr_id": selected,
            "date_created": date.today().isoformat(),
            "problem_statement": problem_statement,
            "containment_action": containment_action,
            "root_cause": "",
            "corrective_action": "",
            "preventive_action": "",
            "action_owner": action_owner,
            "due_date": due_date.isoformat(),
            "verification_method": "",
            "verification_result": "",
            "effectiveness_check_date": "",
            "closure_status": "Open",
            "five_why_1": "",
            "five_why_2": "",
            "five_why_3": "",
            "five_why_4": "",
            "five_why_5": "",
            "five_why_root_cause": "",
            "fishbone_manpower": "",
            "fishbone_machine": "",
            "fishbone_method": "",
            "fishbone_material": "",
            "fishbone_measurement": "",
            "fishbone_environment": "",
        })
        st.success(f"Created corrective action {capa_id} and linked it to case {selected}.")


def capa_dashboard():
    st.subheader("Corrective Action Dashboard")
    capas = get_all_capas()

    if capas.empty:
        st.warning("No corrective actions available. Create one from an open case.")
        return

    open_c = capas[capas["closure_status"] != "Closed"]
    closed_c = capas[capas["closure_status"] == "Closed"]

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Total CAPAs", len(capas))
    with c2:
        metric_card("Open", len(open_c))
    with c3:
        metric_card("Closed", len(closed_c))

    col1, col2 = st.columns(2)
    with col1:
        status = capas["closure_status"].fillna("Unknown").value_counts().reset_index()
        status.columns = ["Status", "Count"]
        st.plotly_chart(px.bar(status, x="Status", y="Count"), use_container_width=True)

    with col2:
        owner = open_c["action_owner"].fillna("Unassigned").value_counts().reset_index()
        owner.columns = ["Owner", "Open CAPAs"]
        st.plotly_chart(px.bar(owner, x="Open CAPAs", y="Owner", orientation="h"), use_container_width=True)

    st.dataframe(capas, use_container_width=True, hide_index=True)


def _capa_can_close(capa):
    required = {
        "problem_statement": "Problem statement",
        "containment_action": "Containment action",
        "root_cause": "Root cause",
        "corrective_action": "Corrective action",
        "preventive_action": "Preventive action",
        "verification_method": "Verification method",
        "verification_result": "Verification result",
        "effectiveness_check_date": "Effectiveness check date",
        "five_why_root_cause": "5-Why root cause",
    }
    missing = [label for field, label in required.items() if not str(capa.get(field, "") or "").strip()]
    return len(missing) == 0, missing


def rca_builder():
    st.subheader("Root Cause Lab / 8D")
    st.caption("Complete 5-Why, fishbone factors, corrective/preventive actions, and effectiveness verification.")

    capas = get_all_capas()
    if capas.empty:
        st.warning("No CAPAs available.")
        return

    capas["selector"] = capas["capa_id"] + " | " + capas["linked_ncr_id"].fillna("") + " | " + capas["closure_status"].fillna("")
    selected_label = st.selectbox("Select CAPA", capas["selector"].tolist())
    selected = selected_label.split(" | ")[0]
    capa = get_capa(selected)
    ncr = get_ncr(capa.get("linked_ncr_id", "")) if capa.get("linked_ncr_id") else {}

    if ncr:
        st.info(f"Linked Case: {ncr.get('ncr_id')} | {ncr.get('defect_type')} | {ncr.get('part_number')} | {ncr.get('supplier_name')}")

    with st.form("rca_form"):
        st.markdown("#### Problem & Containment")
        problem_statement = st.text_area("Problem Statement", capa.get("problem_statement", ""))
        containment_action = st.text_area("Containment Action", capa.get("containment_action", ""))

        st.markdown("#### 5-Why Analysis")
        why1 = st.text_input("Why 1", capa.get("five_why_1", ""))
        why2 = st.text_input("Why 2", capa.get("five_why_2", ""))
        why3 = st.text_input("Why 3", capa.get("five_why_3", ""))
        why4 = st.text_input("Why 4", capa.get("five_why_4", ""))
        why5 = st.text_input("Why 5", capa.get("five_why_5", ""))
        five_root = st.text_area("5-Why Root Cause", capa.get("five_why_root_cause", ""))

        st.markdown("#### Fishbone Contributing Factors")
        f1, f2 = st.columns(2)
        manpower = f1.text_area("Manpower", capa.get("fishbone_manpower", ""))
        machine = f1.text_area("Machine", capa.get("fishbone_machine", ""))
        method = f1.text_area("Method", capa.get("fishbone_method", ""))
        material = f2.text_area("Material", capa.get("fishbone_material", ""))
        measurement = f2.text_area("Measurement", capa.get("fishbone_measurement", ""))
        environment = f2.text_area("Environment", capa.get("fishbone_environment", ""))

        st.markdown("#### Corrective / Preventive Action")
        root_cause = st.text_area("Final Root Cause", capa.get("root_cause", "") or five_root)
        corrective_action = st.text_area("Corrective Action", capa.get("corrective_action", ""))
        preventive_action = st.text_area("Preventive Action", capa.get("preventive_action", ""))
        action_owner = st.selectbox("Action Owner", OWNERS, index=OWNERS.index(capa.get("action_owner")) if capa.get("action_owner") in OWNERS else 0)
        due_date = st.date_input("Due Date", _safe_date(capa.get("due_date"), 14))

        st.markdown("#### Verification")
        current_method = capa.get("verification_method", "")
        method_index = VERIFICATION_METHODS.index(current_method) if current_method in VERIFICATION_METHODS else 0
        verification_method = st.selectbox("Verification Method", VERIFICATION_METHODS, index=method_index)
        verification_result = st.text_area("Verification Result", capa.get("verification_result", ""))
        effectiveness_date = st.date_input("Effectiveness Check Date", _safe_date(capa.get("effectiveness_check_date"), 30))
        requested_status = st.selectbox("Closure Status", CAPA_STATUSES, index=CAPA_STATUSES.index(capa.get("closure_status")) if capa.get("closure_status") in CAPA_STATUSES else 0)

        submitted = st.form_submit_button("Save RCA / CAPA", type="primary")

    if submitted:
        updates = {
            "problem_statement": problem_statement,
            "containment_action": containment_action,
            "five_why_1": why1,
            "five_why_2": why2,
            "five_why_3": why3,
            "five_why_4": why4,
            "five_why_5": why5,
            "five_why_root_cause": five_root,
            "fishbone_manpower": manpower,
            "fishbone_machine": machine,
            "fishbone_method": method,
            "fishbone_material": material,
            "fishbone_measurement": measurement,
            "fishbone_environment": environment,
            "root_cause": root_cause,
            "corrective_action": corrective_action,
            "preventive_action": preventive_action,
            "action_owner": action_owner,
            "due_date": due_date.isoformat(),
            "verification_method": verification_method,
            "verification_result": verification_result,
            "effectiveness_check_date": effectiveness_date.isoformat(),
            "closure_status": requested_status,
        }
        if requested_status == "Closed":
            ok, missing = _capa_can_close({**capa, **updates})
            if not ok:
                updates["closure_status"] = "Verification Pending"
                st.error(f"Cannot close CAPA yet. Missing: {', '.join(missing)}")
            else:
                if capa.get("linked_ncr_id"):
                    update_ncr(capa["linked_ncr_id"], {"status": "Closed"})
        update_capa(selected, updates)
        st.success("CAPA saved.")

    refreshed = get_capa(selected)
    linked_ncr = get_ncr(refreshed.get("linked_ncr_id", "")) if refreshed.get("linked_ncr_id") else {}
    col1, col2 = st.columns(2)
    capa_md = capa_report(refreshed, linked_ncr)
    eight_md = eight_d_report(refreshed, linked_ncr)
    _save_report(capa_md, REPORTS_CAPA_DIR, f"{selected}_capa_report.md")
    _save_report(eight_md, REPORTS_CAPA_DIR, f"{selected}_8d_report.md")

    with col1:
        st.download_button("Download CAPA Report", data=capa_md, file_name=f"{selected}_capa_report.md", mime="text/markdown", use_container_width=True)
    with col2:
        st.download_button("Download 8D Report", data=eight_md, file_name=f"{selected}_8d_report.md", mime="text/markdown", use_container_width=True)

    with st.expander("Preview 8D Report"):
        st.markdown(eight_md)


def supplier_feedback():
    st.subheader("Supplier Case Feedback")
    st.caption("Generate supplier-facing quality feedback from investigation case history.")

    ncrs = get_all_ncrs()
    if ncrs.empty:
        st.warning("No cases available.")
        return

    supplier = st.selectbox("Supplier", sorted(ncrs["supplier_name"].dropna().unique()))
    df = ncrs[ncrs["supplier_name"] == supplier].copy()

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Total Cases", len(df))
    with c2:
        metric_card("Open Cases", int((df["status"] != "Closed").sum()))
    with c3:
        metric_card("Critical Cases", int((df["severity"] == "Critical").sum()))

    st.dataframe(
        df[["ncr_id", "date_opened", "part_number", "defect_type", "severity", "status", "disposition", "due_date"]],
        use_container_width=True,
        hide_index=True,
    )

    top_defects = df["defect_type"].value_counts().head(5)
    report_lines = [
        "# Supplier Case Feedback Report",
        f"## {supplier}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Generated | {date.today().isoformat()} |",
        f"| Total Cases | {len(df)} |",
        f"| Open Cases | {(df['status'] != 'Closed').sum()} |",
        f"| Critical Cases | {(df['severity'] == 'Critical').sum()} |",
        "",
        "## Top Investigation Themes",
        "",
        "| Defect Type | Count |",
        "|---|---|",
    ]
    report_lines += [f"| {defect} | {count} |" for defect, count in top_defects.items()]
    report_lines += [
        "",
        "## Required Supplier Actions",
        "",
        "1. Acknowledge receipt of this quality notification within 2 business days.",
        "2. Provide containment response for all open Major and Critical Cases.",
        "3. Submit supplier 8D report for recurring or critical quality signals.",
        "4. Provide objective evidence of corrective action implementation.",
        "5. Confirm preventive action to prevent recurrence across affected part numbers.",
        "",
        f"*Generated {date.today().isoformat()} — AeroQMS Supplier Quality*",
    ]
    report = "\n".join(report_lines)
    safe_supplier = supplier.replace(" ", "_").replace("/", "_")
    _save_report(report, REPORTS_NCR_DIR, f"{safe_supplier}_supplier_feedback.md")

    st.download_button("Download Supplier Case Feedback Report", data=report, file_name=f"{safe_supplier}_supplier_feedback.md", mime="text/markdown")
    with st.expander("Preview supplier report"):
        st.markdown(report)


def render():
    _ensure_db()

    st.markdown("""
# Case Management Center

### Manage investigation cases, containment, root cause analysis, corrective actions, verification, and supplier closure.

**Quality Detective role:** this is the investigation room. Evidence from inspection becomes formal cases, cases drive RCA/CAPA, and completed actions are verified before closure.
""")

    st.markdown("---")

    st.markdown(
        alert(
            "<b>Investigation flow:</b> Evidence Review → Case Intake → Containment → Root Cause Lab → Corrective Action → Verification → Case Closure",
            "blue",
        ),
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "Overview",
        "Evidence Intake",
        "Open New Case",
        "NCR Detail",
        "Create Corrective Action",
        "Corrective Action Dashboard",
        "RCA / 8D",
        "Supplier Case Feedback",
    ])

    with tabs[0]:
        dashboard()
    with tabs[1]:
        import_center()
    with tabs[2]:
        create_ncr()
    with tabs[3]:
        ncr_detail()
    with tabs[4]:
        create_capa()
    with tabs[5]:
        capa_dashboard()
    with tabs[6]:
        rca_builder()
    with tabs[7]:
        supplier_feedback()