
"""
app.py — Drone Manufacturing NCR/CAPA Management System

Run:
    streamlit run app.py

Purpose:
    Full workflow from NCR intake through containment, disposition, RCA,
    CAPA, 8D reporting, verification, and closure.
"""

import os
from datetime import date, timedelta
import pandas as pd
import streamlit as st
import plotly.express as px

from database import (
    init_db, get_all_ncrs, get_ncr, insert_ncr, update_ncr, ncr_next_id, ncr_due_date,
    get_all_capas, get_capa, insert_capa, update_capa, capa_next_id, import_draft_ncrs
)
from report_generator import ncr_report, capa_report, eight_d_report

st.set_page_config(page_title="NCR/CAPA System", layout="wide")

STATUSES = [
    "Open", "Containment Pending", "Containment Complete", "RCA Pending",
    "RCA Complete", "CAPA Open", "Verification Pending", "Closed"
]
SEVERITIES = ["Critical", "Major", "Minor"]
DISPOSITIONS = ["Use-As-Is", "Rework", "Repair", "Scrap", "Return to Supplier", "MRB Review"]
DETECTED_AT = ["Receiving Inspection", "In-Process Inspection", "Final Assembly", "End-of-Line Test", "Customer Field Return"]
VERIFICATION_METHODS = ["Repeat Inspection", "Process Audit", "Supplier 8D Review", "First Article Inspection", "End-of-Line Test Review", "Yield Monitoring"]
OWNERS = ["QE-Torres", "QE-Patel", "QE-Nguyen", "QE-Brooks", "QE-Osei", "SQE-Li", "MFG-Chen"]


def safe_date(value):
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return date.today()


def require_disposition_notes(disposition: str) -> str:
    rules = {
        "Use-As-Is": "Engineering justification is required.",
        "Rework": "Rework instruction is required.",
        "Repair": "Repair method and verification plan are required.",
        "Scrap": "Scrap cost impact is required.",
        "Return to Supplier": "Supplier notification details are required.",
        "MRB Review": "Assigned MRB reviewer is required.",
    }
    return rules.get(disposition, "Disposition notes are required.")


def capa_can_close(capa: dict) -> tuple[bool, list]:
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
    missing = [label for key, label in required.items() if not str(capa.get(key, "")).strip()]
    return len(missing) == 0, missing


def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("Filters")
        if df.empty:
            return df
        statuses = st.multiselect("Status", STATUSES, default=[])
        severities = st.multiselect("Severity", SEVERITIES, default=[])
        suppliers = st.multiselect("Supplier", sorted(df["supplier_name"].dropna().unique().tolist()), default=[])
        parts = st.multiselect("Part Number", sorted(df["part_number"].dropna().unique().tolist()), default=[])

    out = df.copy()
    if statuses:
        out = out[out["status"].isin(statuses)]
    if severities:
        out = out[out["severity"].isin(severities)]
    if suppliers:
        out = out[out["supplier_name"].isin(suppliers)]
    if parts:
        out = out[out["part_number"].isin(parts)]
    return out


def dashboard():
    st.title("Drone Manufacturing NCR/CAPA Dashboard")
    ncrs = get_all_ncrs()
    capas = get_all_capas()

    if ncrs.empty:
        st.info("No NCRs found. Create one manually, import draft NCRs, or run seed_data.py.")
        return

    df = sidebar_filters(ncrs)

    open_ncrs = df[df["status"] != "Closed"]
    overdue = open_ncrs[pd.to_datetime(open_ncrs["due_date"], errors="coerce").dt.date < date.today()]
    closed = df[df["status"] == "Closed"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total NCRs", len(df))
    c2.metric("Open NCRs", len(open_ncrs))
    c3.metric("Overdue NCRs", len(overdue))
    c4.metric("Critical NCRs", int((df["severity"] == "Critical").sum()))
    c5.metric("CAPAs", len(capas))

    st.subheader("NCR Status and Severity")
    col1, col2 = st.columns(2)
    with col1:
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        st.plotly_chart(px.bar(status_counts, x="status", y="count", title="NCRs by Status"), use_container_width=True)
    with col2:
        sev_counts = df["severity"].value_counts().reset_index()
        sev_counts.columns = ["severity", "count"]
        st.plotly_chart(px.pie(sev_counts, names="severity", values="count", title="NCRs by Severity"), use_container_width=True)

    st.subheader("Supplier and Defect Trends")
    col3, col4 = st.columns(2)
    with col3:
        supplier_counts = df["supplier_name"].value_counts().head(10).reset_index()
        supplier_counts.columns = ["supplier_name", "count"]
        st.plotly_chart(px.bar(supplier_counts, x="supplier_name", y="count", title="Top Suppliers by NCR Count"), use_container_width=True)
    with col4:
        defect_counts = df["defect_type"].value_counts().head(10).reset_index()
        defect_counts.columns = ["defect_type", "count"]
        st.plotly_chart(px.bar(defect_counts, x="defect_type", y="count", title="Top Defect Types"), use_container_width=True)

    st.subheader("NCR Aging")
    aging = open_ncrs.copy()
    aging["date_opened_dt"] = pd.to_datetime(aging["date_opened"], errors="coerce")
    aging["age_days"] = (pd.Timestamp.today() - aging["date_opened_dt"]).dt.days
    if not aging.empty:
        st.plotly_chart(px.histogram(aging, x="age_days", nbins=20, title="Open NCR Age Distribution"), use_container_width=True)
        st.dataframe(aging[["ncr_id","date_opened","age_days","part_number","supplier_name","severity","status","owner","due_date"]], use_container_width=True)

    st.subheader("All NCRs")
    st.dataframe(df, use_container_width=True)


def create_ncr():
    st.title("Create NCR")

    with st.form("create_ncr_form"):
        col1, col2 = st.columns(2)
        with col1:
            part_number = st.text_input("Part Number", "MMB-001")
            part_name = st.text_input("Part Name", "Drone Motor Mount Bracket")
            part_revision = st.text_input("Part Revision", "A")
            serial_number = st.text_input("Serial Number", "SN-0001")
            lot_number = st.text_input("Lot Number", "LOT-100")
            supplier_id = st.text_input("Supplier ID", "SUP-003")
            supplier_name = st.text_input("Supplier Name", "AeroForge Precision")
        with col2:
            defect_type = st.text_input("Defect Type", "Dimensional Out-of-Tolerance")
            detected_at = st.selectbox("Detected At", DETECTED_AT)
            severity = st.selectbox("Severity", SEVERITIES, index=1)
            quantity_affected = st.number_input("Quantity Affected", min_value=1, value=1)
            owner = st.selectbox("Owner", OWNERS)
            disposition = st.selectbox("Initial Disposition", DISPOSITIONS, index=5)

        defect_description = st.text_area("Defect Description", "Hole true position exceeds drawing tolerance.")
        requirement = st.text_area("Requirement", "Engineering drawing Rev A: true position <= 0.20 mm relative to A|B|C.")
        actual_result = st.text_area("Actual Result", "Measured true position = 0.32 mm.")
        disposition_notes = st.text_area("Disposition Notes", require_disposition_notes(disposition))

        submitted = st.form_submit_button("Create NCR")

    if submitted:
        ncr_id = ncr_next_id()
        record = {
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
        }
        insert_ncr(record)
        st.success(f"Created {ncr_id}")


def import_page():
    st.title("Import Draft NCRs from GD&T Inspection System")
    st.write("Upload the `draft_ncrs.csv` generated by Project 3. Failed GD&T features will become NCRs.")

    uploaded = st.file_uploader("Upload draft_ncrs.csv", type=["csv"])
    if uploaded:
        tmp_path = "uploaded_draft_ncrs.csv"
        with open(tmp_path, "wb") as f:
            f.write(uploaded.getbuffer())
        if st.button("Import Draft NCRs"):
            try:
                imported, skipped = import_draft_ncrs(tmp_path)
                st.success(f"Imported {imported} NCRs. Skipped {skipped}.")
            except Exception as e:
                st.error(f"Import failed: {e}")
        st.subheader("Preview")
        st.dataframe(pd.read_csv(tmp_path), use_container_width=True)


def ncr_detail():
    st.title("NCR Detail and Disposition")
    ncrs = get_all_ncrs()
    if ncrs.empty:
        st.info("No NCRs available.")
        return

    selected = st.selectbox("Select NCR", ncrs["ncr_id"].tolist())
    ncr = get_ncr(selected)
    if not ncr:
        return

    st.subheader(f"{selected}: {ncr.get('defect_type','')}")
    st.json(ncr)

    with st.form("update_ncr"):
        col1, col2, col3 = st.columns(3)
        status = col1.selectbox("Status", STATUSES, index=STATUSES.index(ncr.get("status")) if ncr.get("status") in STATUSES else 0)
        disposition = col2.selectbox("Disposition", DISPOSITIONS, index=DISPOSITIONS.index(ncr.get("disposition")) if ncr.get("disposition") in DISPOSITIONS else 5)
        owner = col3.selectbox("Owner", OWNERS, index=OWNERS.index(ncr.get("owner")) if ncr.get("owner") in OWNERS else 0)
        notes = st.text_area("Disposition Notes / MRB Notes", ncr.get("disposition_notes") or require_disposition_notes(disposition))
        submit = st.form_submit_button("Update NCR")

    if submit:
        update_ncr(selected, {"status": status, "disposition": disposition, "owner": owner, "disposition_notes": notes})
        st.success("NCR updated.")

    st.subheader("Generate NCR Report")
    md = ncr_report(ncr)
    st.download_button("Download NCR Markdown Report", data=md, file_name=f"{selected}_ncr_report.md")
    st.markdown(md)


def create_capa():
    st.title("Create CAPA from NCR")
    ncrs = get_all_ncrs()
    if ncrs.empty:
        st.info("No NCRs available.")
        return

    candidates = ncrs[ncrs["status"] != "Closed"]
    selected = st.selectbox("Select source NCR", candidates["ncr_id"].tolist())
    ncr = get_ncr(selected)

    with st.form("create_capa_form"):
        problem_statement = st.text_area("Problem Statement", f"{ncr.get('defect_type')} found on {ncr.get('part_number')} from {ncr.get('supplier_name')}.")
        containment_action = st.text_area("Containment Action", "Quarantine affected lot; stop use until MRB disposition is complete.")
        action_owner = st.selectbox("Action Owner", OWNERS)
        due_date = st.date_input("CAPA Due Date", date.today() + timedelta(days=14))
        submit = st.form_submit_button("Create CAPA")

    if submit:
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
        })
        st.success(f"Created {capa_id} linked to {selected}")


def capa_dashboard():
    st.title("CAPA Dashboard")
    capas = get_all_capas()
    if capas.empty:
        st.info("No CAPAs available.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Total CAPAs", len(capas))
    c2.metric("Open CAPAs", int((capas["closure_status"] != "Closed").sum()))
    c3.metric("Closed CAPAs", int((capas["closure_status"] == "Closed").sum()))

    counts = capas["closure_status"].value_counts().reset_index()
    counts.columns = ["closure_status", "count"]
    st.plotly_chart(px.bar(counts, x="closure_status", y="count", title="CAPA Closure Status"), use_container_width=True)
    st.dataframe(capas, use_container_width=True)


def rca_builder():
    st.title("RCA Builder: 5-Why, Fishbone, Corrective Actions")
    capas = get_all_capas()
    if capas.empty:
        st.info("No CAPAs available.")
        return

    selected = st.selectbox("Select CAPA", capas["capa_id"].tolist())
    capa = get_capa(selected)
    ncr = get_ncr(capa.get("linked_ncr_id","")) if capa.get("linked_ncr_id") else {}

    with st.form("rca_form"):
        st.subheader("5-Why Analysis")
        problem_statement = st.text_area("Problem Statement", capa.get("problem_statement",""))
        why1 = st.text_input("Why 1", capa.get("five_why_1",""))
        why2 = st.text_input("Why 2", capa.get("five_why_2",""))
        why3 = st.text_input("Why 3", capa.get("five_why_3",""))
        why4 = st.text_input("Why 4", capa.get("five_why_4",""))
        why5 = st.text_input("Why 5", capa.get("five_why_5",""))
        five_root = st.text_area("5-Why Root Cause", capa.get("five_why_root_cause",""))

        st.subheader("Fishbone Analysis")
        col1, col2 = st.columns(2)
        manpower = col1.text_area("Manpower", capa.get("fishbone_manpower",""))
        machine = col1.text_area("Machine", capa.get("fishbone_machine",""))
        method = col1.text_area("Method", capa.get("fishbone_method",""))
        material = col2.text_area("Material", capa.get("fishbone_material",""))
        measurement = col2.text_area("Measurement", capa.get("fishbone_measurement",""))
        environment = col2.text_area("Environment", capa.get("fishbone_environment",""))

        st.subheader("CAPA Actions")
        root_cause = st.text_area("Final Root Cause Statement", capa.get("root_cause","") or five_root)
        corrective_action = st.text_area("Corrective Action", capa.get("corrective_action",""))
        preventive_action = st.text_area("Preventive Action", capa.get("preventive_action",""))
        verification_method = st.selectbox("Verification Method", VERIFICATION_METHODS, index=0)
        verification_result = st.text_area("Verification Result", capa.get("verification_result",""))
        effectiveness_check_date = st.date_input("Effectiveness Check Date", safe_date(capa.get("effectiveness_check_date")))

        requested_status = st.selectbox("Closure Status", ["Open", "Verification Pending", "Closed"], index=0)
        submit = st.form_submit_button("Save RCA/CAPA")

    if submit:
        updates = {
            "problem_statement": problem_statement,
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
            "verification_method": verification_method,
            "verification_result": verification_result,
            "effectiveness_check_date": effectiveness_check_date.isoformat(),
            "closure_status": requested_status,
        }
        if requested_status == "Closed":
            merged = {**capa, **updates}
            ok, missing = capa_can_close(merged)
            if not ok:
                st.error("Cannot close CAPA. Missing: " + ", ".join(missing))
                updates["closure_status"] = "Verification Pending"
        update_capa(selected, updates)

        if updates["closure_status"] == "Closed" and capa.get("linked_ncr_id"):
            update_ncr(capa["linked_ncr_id"], {"status": "Closed"})
        st.success("CAPA updated.")

    st.subheader("Report Preview")
    refreshed = get_capa(selected)
    st.download_button("Download CAPA Report", data=capa_report(refreshed, ncr), file_name=f"{selected}_capa_report.md")
    st.download_button("Download 8D Report", data=eight_d_report(refreshed, ncr), file_name=f"{selected}_8d_report.md")
    st.markdown(eight_d_report(refreshed, ncr))


def supplier_feedback():
    st.title("Supplier Feedback Report")
    ncrs = get_all_ncrs()
    if ncrs.empty:
        st.info("No NCRs available.")
        return

    supplier = st.selectbox("Supplier", sorted(ncrs["supplier_name"].dropna().unique().tolist()))
    df = ncrs[ncrs["supplier_name"] == supplier].copy()

    st.metric("Total NCRs for Supplier", len(df))
    if not df.empty:
        st.dataframe(df[["ncr_id","date_opened","part_number","defect_type","severity","status","disposition","due_date"]], use_container_width=True)

        summary = [
            f"# Supplier Quality Feedback Report — {supplier}",
            "",
            f"Generated: {date.today().isoformat()}",
            "",
            "## Summary",
            f"- Total NCRs: {len(df)}",
            f"- Open NCRs: {(df['status'] != 'Closed').sum()}",
            f"- Critical NCRs: {(df['severity'] == 'Critical').sum()}",
            "",
            "## Top Defects",
            df["defect_type"].value_counts().head(10).to_markdown(),
            "",
            "## Requested Supplier Actions",
            "1. Review attached NCR list.",
            "2. Provide containment response for all open Major/Critical issues.",
            "3. Submit supplier 8D for recurring or critical defects.",
            "4. Provide evidence of corrective action implementation.",
            "5. Confirm preventive action to avoid recurrence.",
        ]
        report = "\n".join(summary)
        st.download_button("Download Supplier Feedback Report", report, file_name=f"{supplier.replace(' ','_')}_supplier_feedback.md")
        st.markdown(report)


def main():
    init_db()
    st.sidebar.title("NCR/CAPA System")
    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Create NCR",
            "Import Draft NCRs",
            "NCR Detail",
            "Create CAPA",
            "CAPA Dashboard",
            "RCA Builder / 8D",
            "Supplier Feedback",
        ],
    )

    if page == "Dashboard":
        dashboard()
    elif page == "Create NCR":
        create_ncr()
    elif page == "Import Draft NCRs":
        import_page()
    elif page == "NCR Detail":
        ncr_detail()
    elif page == "Create CAPA":
        create_capa()
    elif page == "CAPA Dashboard":
        capa_dashboard()
    elif page == "RCA Builder / 8D":
        rca_builder()
    elif page == "Supplier Feedback":
        supplier_feedback()


if __name__ == "__main__":
    main()
