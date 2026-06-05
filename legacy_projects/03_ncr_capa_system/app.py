"""
NCR/CAPA Management System
Run: streamlit run app.py
"""

import os, sys
from datetime import date, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from shared_styles import apply_styles, style_fig, kpi_card, alert, section, page_header, C

from database import (
    init_db, get_all_ncrs, get_ncr, insert_ncr, update_ncr, ncr_next_id, ncr_due_date,
    get_all_capas, get_capa, insert_capa, update_capa, capa_next_id, import_draft_ncrs,
)
from ncr_capa_report_generator_v2 import ncr_report, capa_report, eight_d_report

st.set_page_config(page_title="NCR/CAPA System", layout="wide", initial_sidebar_state="expanded")
apply_styles()

STATUSES     = ["Open","Containment Pending","Containment Complete","RCA Pending",
                "RCA Complete","CAPA Open","Verification Pending","Closed"]
SEVERITIES   = ["Critical","Major","Minor"]
DISPOSITIONS = ["Use-As-Is","Rework","Repair","Scrap","Return to Supplier","MRB Review"]
DETECTED_AT  = ["Receiving Inspection","In-Process Inspection","Final Assembly",
                "End-of-Line Test","Customer Field Return"]
VERIF_METHODS= ["Repeat Inspection","Process Audit","Supplier 8D Review",
                "First Article Inspection","End-of-Line Test Review","Yield Monitoring"]
OWNERS       = ["QE-Torres","QE-Patel","QE-Nguyen","QE-Brooks","QE-Osei","SQE-Li","MFG-Chen"]

DISP_RULES = {
    "Use-As-Is":        "Engineering justification required.",
    "Rework":           "Rework instruction required.",
    "Repair":           "Repair method and verification plan required.",
    "Scrap":            "Scrap cost impact required.",
    "Return to Supplier":"Supplier notification details required.",
    "MRB Review":       "Assigned MRB reviewer required.",
}

def safe_date(val):
    try:   return pd.to_datetime(val).date()
    except: return date.today()

def capa_can_close(capa):
    required = {
        "problem_statement":"Problem statement","containment_action":"Containment action",
        "root_cause":"Root cause","corrective_action":"Corrective action",
        "preventive_action":"Preventive action","verification_method":"Verification method",
        "verification_result":"Verification result",
        "effectiveness_check_date":"Effectiveness check date",
        "five_why_root_cause":"5-Why root cause",
    }
    missing = [label for k, label in required.items() if not str(capa.get(k,"")).strip()]
    return len(missing) == 0, missing

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div style="padding:16px 0 8px">
    <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;
                color:{C['muted']};font-family:'JetBrains Mono',monospace;margin-bottom:4px">
        Quality Management
    </div>
    <div style="font-size:14px;font-weight:500;color:{C['text']}">NCR / CAPA System</div>
    <div style="font-size:11px;color:{C['muted']};font-family:'JetBrains Mono',monospace">
        Drone Manufacturing
    </div>
</div>
<hr style="border:none;border-top:1px solid {C['border']};margin:8px 0 16px">
""", unsafe_allow_html=True)

NAV = ["Dashboard","Create NCR","Import Draft NCRs","NCR Detail",
       "Create CAPA","CAPA Dashboard","RCA Builder / 8D","Supplier Feedback"]
page = st.sidebar.radio("", NAV, label_visibility="collapsed")

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def dashboard():
    st.markdown(page_header("NCR / CAPA Dashboard", "Non-conformance activity, aging, and corrective action status"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    ncrs  = get_all_ncrs()
    capas = get_all_capas()

    if ncrs.empty:
        st.markdown(alert("No NCRs found. Create one manually, import draft NCRs from Project 3, or run seed_data.py.", "blue"), unsafe_allow_html=True)
        return

    # Sidebar filters
    with st.sidebar:
        st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:8px 0">', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{C["muted"]};font-family:\'JetBrains Mono\',monospace;margin-bottom:8px">Filters</div>', unsafe_allow_html=True)
        sel_status   = st.multiselect("Status",   STATUSES,   default=[])
        sel_severity = st.multiselect("Severity", SEVERITIES, default=[])
        sel_supplier = st.multiselect("Supplier", sorted(ncrs["supplier_name"].dropna().unique()), default=[])

    df = ncrs.copy()
    if sel_status:   df = df[df["status"].isin(sel_status)]
    if sel_severity: df = df[df["severity"].isin(sel_severity)]
    if sel_supplier: df = df[df["supplier_name"].isin(sel_supplier)]

    open_ncrs = df[df["status"] != "Closed"]
    overdue   = open_ncrs[pd.to_datetime(open_ncrs["due_date"], errors="coerce").dt.date < date.today()]
    closed    = df[df["status"] == "Closed"]

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi_card("Total NCRs",    len(df),                                    sub="All statuses"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Open",          len(open_ncrs), "red" if len(open_ncrs)>30 else "amber", sub="Active"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Overdue",       len(overdue),   "red" if len(overdue)>5 else "amber",    sub="Past due date"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Critical",      int((df["severity"]=="Critical").sum()), "red" if (df["severity"]=="Critical").sum()>5 else "amber", sub="Severity level"), unsafe_allow_html=True)
    c5.markdown(kpi_card("CAPAs",         len(capas),                                 sub="Total created"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if len(overdue) > 0:
        st.markdown(alert(f"{len(overdue)} NCR(s) are past their due date and require immediate attention.", "red"), unsafe_allow_html=True)

    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:20px 0">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("Status Distribution"), unsafe_allow_html=True)
        sc = df["status"].value_counts().reset_index()
        sc.columns = ["status","count"]
        fig = px.bar(sc, x="status", y="count", color_discrete_sequence=[C["blue"]])
        fig.update_traces(marker_line_width=0)
        fig.update_layout(xaxis_title="", yaxis_title="NCR Count", xaxis_tickangle=-20)
        st.plotly_chart(style_fig(fig, 300), use_container_width=True)

    with col2:
        st.markdown(section("Severity Breakdown"), unsafe_allow_html=True)
        sev = df["severity"].value_counts().reset_index()
        sev.columns = ["severity","count"]
        cmap = {"Critical": C["red"], "Major": C["amber"], "Minor": C["blue"]}
        fig2 = px.bar(sev, x="severity", y="count", color="severity", color_discrete_map=cmap)
        fig2.update_traces(marker_line_width=0)
        fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="Count")
        st.plotly_chart(style_fig(fig2, 300), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(section("Top Suppliers by NCR Count"), unsafe_allow_html=True)
        sup = df["supplier_name"].value_counts().head(8).sort_values().reset_index()
        sup.columns = ["supplier","count"]
        fig3 = px.bar(sup, x="count", y="supplier", orientation="h",
                      color_discrete_sequence=[C["amber"]])
        fig3.update_traces(marker_line_width=0)
        fig3.update_layout(yaxis_title="", xaxis_title="NCR Count")
        st.plotly_chart(style_fig(fig3, 300), use_container_width=True)

    with col4:
        st.markdown(section("Top Defect Types"), unsafe_allow_html=True)
        dt = df["defect_type"].value_counts().head(8).sort_values().reset_index()
        dt.columns = ["defect","count"]
        fig4 = px.bar(dt, x="count", y="defect", orientation="h",
                      color_discrete_sequence=[C["red"]])
        fig4.update_traces(marker_line_width=0)
        fig4.update_layout(yaxis_title="", xaxis_title="Count")
        st.plotly_chart(style_fig(fig4, 300), use_container_width=True)

    st.markdown(section("NCR Aging — Open Only"), unsafe_allow_html=True)
    aging = open_ncrs.copy()
    aging["date_opened_dt"] = pd.to_datetime(aging["date_opened"], errors="coerce")
    aging["age_days"] = (pd.Timestamp.today() - aging["date_opened_dt"]).dt.days
    if not aging.empty:
        fig5 = px.histogram(aging, x="age_days", nbins=20, color_discrete_sequence=[C["amber"]])
        fig5.update_traces(marker_line_width=0)
        fig5.add_vline(x=30, line_dash="dot", line_color=C["red"],
                       annotation_text="30d", annotation_font_color=C["muted"], annotation_font_size=10)
        fig5.update_layout(xaxis_title="Age (days)", yaxis_title="Count")
        st.plotly_chart(style_fig(fig5, 260), use_container_width=True)

        st.markdown(section("Open NCR List — Sorted by Age"), unsafe_allow_html=True)
        show = aging[["ncr_id","date_opened","age_days","part_number","supplier_name",
                       "severity","status","owner","due_date"]].sort_values("age_days", ascending=False)
        show.columns = ["NCR ID","Opened","Age (d)","Part","Supplier","Severity","Status","Owner","Due"]
        st.dataframe(show, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# CREATE NCR
# ══════════════════════════════════════════════════════════════════════════════
def create_ncr():
    st.markdown(page_header("Create NCR", "Document a new non-conformance manually"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    with st.form("create_ncr_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(section("Part Information"), unsafe_allow_html=True)
            part_number   = st.text_input("Part Number",   "MMB-001")
            part_name     = st.text_input("Part Name",     "Drone Motor Mount Bracket")
            part_revision = st.text_input("Revision",      "A")
            serial_number = st.text_input("Serial Number", "SN-0001")
            lot_number    = st.text_input("Lot Number",    "LOT-100")
            supplier_id   = st.text_input("Supplier ID",   "SUP-003")
            supplier_name = st.text_input("Supplier Name", "AeroForge Precision")

        with col2:
            st.markdown(section("Non-Conformance"), unsafe_allow_html=True)
            defect_type        = st.text_input("Defect Type", "Dimensional Out-of-Tolerance")
            detected_at        = st.selectbox("Detected At", DETECTED_AT)
            severity           = st.selectbox("Severity", SEVERITIES, index=1)
            quantity_affected  = st.number_input("Quantity Affected", min_value=1, value=1)
            owner              = st.selectbox("Owner", OWNERS)
            disposition        = st.selectbox("Initial Disposition", DISPOSITIONS, index=5)

        defect_description = st.text_area("Defect Description", "Hole true position exceeds drawing tolerance.")
        requirement        = st.text_area("Requirement", "Engineering drawing Rev A: true position ≤ 0.20 mm relative to A|B|C.")
        actual_result      = st.text_area("Actual Result", "Measured true position = 0.32 mm.")
        disposition_notes  = st.text_area("Disposition Notes", DISP_RULES.get(disposition, "Notes required."))
        submitted          = st.form_submit_button("Create NCR")

    if submitted:
        ncr_id = ncr_next_id()
        insert_ncr({
            "ncr_id": ncr_id, "date_opened": date.today().isoformat(),
            "created_by": "Manual Entry", "part_number": part_number,
            "part_name": part_name, "part_revision": part_revision,
            "serial_number": serial_number, "lot_number": lot_number,
            "supplier_id": supplier_id, "supplier_name": supplier_name,
            "defect_type": defect_type, "defect_description": defect_description,
            "detected_at": detected_at, "severity": severity,
            "quantity_affected": int(quantity_affected), "requirement": requirement,
            "actual_result": actual_result, "disposition": disposition,
            "disposition_notes": disposition_notes, "status": "Open",
            "owner": owner, "due_date": ncr_due_date(severity), "source": "Manual",
        })
        st.markdown(alert(f"Created {ncr_id} — due {ncr_due_date(severity)}", "green"), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# IMPORT DRAFT NCRs
# ══════════════════════════════════════════════════════════════════════════════
def import_page():
    st.markdown(page_header("Import Draft NCRs", "Upload draft_ncrs.csv from the GD&T Inspection System"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    st.markdown(alert("Upload the <b>draft_ncrs.csv</b> generated by Project 3. Each failed GD&T feature becomes a separate NCR with requirement, measured value, and deviation pre-filled.", "blue"), unsafe_allow_html=True)

    uploaded = st.file_uploader("draft_ncrs.csv", type=["csv"], label_visibility="collapsed")
    if uploaded:
        tmp = "uploaded_draft_ncrs.csv"
        open(tmp,"wb").write(uploaded.getbuffer())

        st.markdown(section("File Preview"), unsafe_allow_html=True)
        preview = pd.read_csv(tmp)
        st.dataframe(preview.head(20), use_container_width=True, hide_index=True)

        if st.button("Import All Records", type="primary"):
            try:
                imported, skipped = import_draft_ncrs(tmp)
                st.markdown(alert(f"Imported {imported} NCRs successfully.", "green"), unsafe_allow_html=True)
            except Exception as e:
                st.markdown(alert(f"Import failed: {e}", "red"), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# NCR DETAIL
# ══════════════════════════════════════════════════════════════════════════════
def ncr_detail():
    st.markdown(page_header("NCR Detail", "Review, update disposition, and generate report"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    ncrs = get_all_ncrs()
    if ncrs.empty:
        st.markdown(alert("No NCRs available.", "blue"), unsafe_allow_html=True)
        return

    selected = st.selectbox("Select NCR", ncrs["ncr_id"].tolist(), label_visibility="collapsed")
    ncr = get_ncr(selected)
    if not ncr: return

    sev_variant = {"Critical":"red","Major":"amber","Minor":"neutral"}.get(ncr.get("severity",""),"neutral")
    st_variant  = "green" if ncr.get("status") == "Closed" else "amber"

    st.markdown(f"""
    <div style="background:{C['surface']};border:1px solid {C['border']};border-radius:4px;padding:20px 24px;margin-bottom:20px">
        <div style="font-size:11px;color:{C['muted']};font-family:'JetBrains Mono',monospace;letter-spacing:1px;margin-bottom:6px">{ncr.get('part_number','')} / {ncr.get('lot_number','')}</div>
        <div style="font-size:18px;font-weight:500;color:{C['text']};margin-bottom:10px">{ncr.get('defect_type','')}</div>
        <div style="font-size:13px;color:{C['subtle']};margin-bottom:14px">{ncr.get('defect_description','')}</div>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
            <div style="font-size:11px;font-family:'JetBrains Mono',monospace;color:{C['muted']}">Supplier: <span style="color:{C['text']}">{ncr.get('supplier_name','')}</span></div>
            <div style="font-size:11px;font-family:'JetBrains Mono',monospace;color:{C['muted']}">Owner: <span style="color:{C['text']}">{ncr.get('owner','')}</span></div>
            <div style="font-size:11px;font-family:'JetBrains Mono',monospace;color:{C['muted']}">Due: <span style="color:{C['text']}">{ncr.get('due_date','')}</span></div>
            <div style="font-size:11px;font-family:'JetBrains Mono',monospace;color:{C['muted']}">CAPA: <span style="color:{C['text']}">{ncr.get('linked_capa_id','None')}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_req, col_act = st.columns(2)
    col_req.markdown(f'<div style="background:{C["surface"]};border:1px solid {C["border"]};border-radius:4px;padding:16px"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{C["muted"]};font-family:\'JetBrains Mono\',monospace;margin-bottom:8px">Requirement</div><div style="font-size:13px;color:{C["subtle"]}">{ncr.get("requirement","—")}</div></div>', unsafe_allow_html=True)
    col_act.markdown(f'<div style="background:{C["surface"]};border:1px solid {C["border"]};border-radius:4px;padding:16px"><div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{C["muted"]};font-family:\'JetBrains Mono\',monospace;margin-bottom:8px">Actual Result</div><div style="font-size:13px;color:{C["red"]}">{ncr.get("actual_result","—")}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section("Update NCR"), unsafe_allow_html=True)

    with st.form("update_ncr"):
        col1, col2, col3 = st.columns(3)
        status      = col1.selectbox("Status",      STATUSES,      index=STATUSES.index(ncr.get("status")) if ncr.get("status") in STATUSES else 0)
        disposition = col2.selectbox("Disposition", DISPOSITIONS,  index=DISPOSITIONS.index(ncr.get("disposition")) if ncr.get("disposition") in DISPOSITIONS else 5)
        owner       = col3.selectbox("Owner",       OWNERS,        index=OWNERS.index(ncr.get("owner")) if ncr.get("owner") in OWNERS else 0)
        notes       = st.text_area("Disposition Notes", ncr.get("disposition_notes") or DISP_RULES.get(disposition,""))
        submit      = st.form_submit_button("Update NCR")

    if submit:
        update_ncr(selected, {"status":status,"disposition":disposition,"owner":owner,"disposition_notes":notes})
        st.markdown(alert("NCR updated.", "green"), unsafe_allow_html=True)

    st.markdown(section("Report"), unsafe_allow_html=True)
    md = ncr_report(ncr)
    col_dl, _ = st.columns([1,3])
    col_dl.download_button("Download NCR Report", data=md, file_name=f"{selected}_ncr_report.md",
                           mime="text/markdown", use_container_width=True)
    with st.expander("Preview report"):
        st.markdown(md)

# ══════════════════════════════════════════════════════════════════════════════
# CREATE CAPA
# ══════════════════════════════════════════════════════════════════════════════
def create_capa():
    st.markdown(page_header("Create CAPA", "Initiate a corrective action linked to an open NCR"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    ncrs = get_all_ncrs()
    if ncrs.empty:
        st.markdown(alert("No NCRs available.", "blue"), unsafe_allow_html=True)
        return

    candidates = ncrs[ncrs["status"] != "Closed"]
    if candidates.empty:
        st.markdown(alert("All NCRs are closed. No CAPA needed.", "green"), unsafe_allow_html=True)
        return

    selected = st.selectbox("Source NCR", candidates["ncr_id"].tolist())
    ncr = get_ncr(selected)

    st.markdown(alert(f"Creating CAPA for <b>{selected}</b> — {ncr.get('defect_type','')} on {ncr.get('part_number','')} from {ncr.get('supplier_name','')}", "amber"), unsafe_allow_html=True)

    with st.form("create_capa_form"):
        problem_statement  = st.text_area("Problem Statement", f"{ncr.get('defect_type','')} found on {ncr.get('part_number','')} from {ncr.get('supplier_name','')}.")
        containment_action = st.text_area("Containment Action", "Quarantine affected lot. Stop use pending MRB disposition.")
        action_owner       = st.selectbox("Action Owner", OWNERS)
        due_date           = st.date_input("Due Date", date.today() + timedelta(days=14))
        submit             = st.form_submit_button("Create CAPA")

    if submit:
        capa_id = capa_next_id()
        insert_capa({
            "capa_id": capa_id, "linked_ncr_id": selected,
            "date_created": date.today().isoformat(),
            "problem_statement": problem_statement,
            "containment_action": containment_action,
            "root_cause":"","corrective_action":"","preventive_action":"",
            "action_owner": action_owner, "due_date": due_date.isoformat(),
            "verification_method":"","verification_result":"",
            "effectiveness_check_date":"","closure_status":"Open",
        })
        st.markdown(alert(f"Created {capa_id} linked to {selected}.", "green"), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CAPA DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def capa_dashboard():
    st.markdown(page_header("CAPA Dashboard", "Corrective action status and closure performance"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    capas = get_all_capas()
    if capas.empty:
        st.markdown(alert("No CAPAs available.", "blue"), unsafe_allow_html=True)
        return

    open_c   = (capas["closure_status"] != "Closed").sum()
    closed_c = (capas["closure_status"] == "Closed").sum()

    c1,c2,c3 = st.columns(3)
    c1.markdown(kpi_card("Total CAPAs", len(capas),  sub="All"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Open",        open_c,   "red" if open_c > 10 else "amber", sub="In progress"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Closed",      closed_c, "green", sub="Resolved"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 20px">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("Closure Status"), unsafe_allow_html=True)
        cs = capas["closure_status"].value_counts().reset_index()
        cs.columns = ["status","count"]
        cmap = {"Closed": C["green"], "Open": C["red"], "Verification Pending": C["amber"]}
        fig = px.bar(cs, x="status", y="count", color="status", color_discrete_map=cmap)
        fig.update_traces(marker_line_width=0)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Count")
        st.plotly_chart(style_fig(fig, 280), use_container_width=True)

    with col2:
        st.markdown(section("Owner Workload"), unsafe_allow_html=True)
        ow = capas[capas["closure_status"]!="Closed"].groupby("action_owner").size().sort_values().reset_index()
        ow.columns = ["owner","open_capas"]
        if not ow.empty:
            fig2 = px.bar(ow, x="open_capas", y="owner", orientation="h",
                          color_discrete_sequence=[C["blue"]])
            fig2.update_traces(marker_line_width=0)
            fig2.update_layout(yaxis_title="", xaxis_title="Open CAPAs")
            st.plotly_chart(style_fig(fig2, 280), use_container_width=True)

    st.markdown(section("All CAPAs"), unsafe_allow_html=True)
    show = ["capa_id","linked_ncr_id","date_created","action_owner","due_date","closure_status","verification_method"]
    st.dataframe(capas[show], use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# RCA BUILDER / 8D
# ══════════════════════════════════════════════════════════════════════════════
def rca_builder():
    st.markdown(page_header("RCA Builder / 8D", "5-Why analysis, fishbone contributing factors, corrective actions, and 8D report"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    capas = get_all_capas()
    if capas.empty:
        st.markdown(alert("No CAPAs available. Create one from the Create CAPA page.", "blue"), unsafe_allow_html=True)
        return

    selected = st.selectbox("Select CAPA", capas["capa_id"].tolist())
    capa = get_capa(selected)
    ncr  = get_ncr(capa.get("linked_ncr_id","")) if capa.get("linked_ncr_id") else {}

    if ncr:
        st.markdown(alert(f"CAPA linked to <b>{capa.get('linked_ncr_id','')}</b> — {ncr.get('defect_type','')} on {ncr.get('part_number','')} / {ncr.get('lot_number','')}", "blue"), unsafe_allow_html=True)

    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:16px 0">', unsafe_allow_html=True)

    with st.form("rca_form"):
        st.markdown(section("Problem Statement"), unsafe_allow_html=True)
        problem_statement = st.text_area("", capa.get("problem_statement",""), label_visibility="collapsed")

        st.markdown(section("5-Why Analysis"), unsafe_allow_html=True)
        why1       = st.text_input("Why 1", capa.get("five_why_1",""))
        why2       = st.text_input("Why 2", capa.get("five_why_2",""))
        why3       = st.text_input("Why 3", capa.get("five_why_3",""))
        why4       = st.text_input("Why 4", capa.get("five_why_4",""))
        why5       = st.text_input("Why 5", capa.get("five_why_5",""))
        five_root  = st.text_area("Root Cause Statement", capa.get("five_why_root_cause",""))

        st.markdown(section("Fishbone — Contributing Factors"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        manpower    = col1.text_area("Manpower",    capa.get("fishbone_manpower",""))
        machine     = col1.text_area("Machine",     capa.get("fishbone_machine",""))
        method      = col1.text_area("Method",      capa.get("fishbone_method",""))
        material    = col2.text_area("Material",    capa.get("fishbone_material",""))
        measurement = col2.text_area("Measurement", capa.get("fishbone_measurement",""))
        environment = col2.text_area("Environment", capa.get("fishbone_environment",""))

        st.markdown(section("Corrective and Preventive Actions"), unsafe_allow_html=True)
        root_cause          = st.text_area("Final Root Cause",    capa.get("root_cause","") or five_root)
        corrective_action   = st.text_area("Corrective Action",   capa.get("corrective_action",""))
        preventive_action   = st.text_area("Preventive Action",   capa.get("preventive_action",""))
        verification_method = st.selectbox("Verification Method", VERIF_METHODS)
        verification_result = st.text_area("Verification Result", capa.get("verification_result",""))
        effectiveness_date  = st.date_input("Effectiveness Check Date", safe_date(capa.get("effectiveness_check_date")))
        requested_status    = st.selectbox("Closure Status", ["Open","Verification Pending","Closed"])
        submit              = st.form_submit_button("Save RCA / CAPA")

    if submit:
        updates = {
            "problem_statement": problem_statement,
            "five_why_1": why1, "five_why_2": why2, "five_why_3": why3,
            "five_why_4": why4, "five_why_5": why5,
            "five_why_root_cause": five_root,
            "fishbone_manpower": manpower, "fishbone_machine": machine,
            "fishbone_method": method, "fishbone_material": material,
            "fishbone_measurement": measurement, "fishbone_environment": environment,
            "root_cause": root_cause, "corrective_action": corrective_action,
            "preventive_action": preventive_action,
            "verification_method": verification_method,
            "verification_result": verification_result,
            "effectiveness_check_date": effectiveness_date.isoformat(),
            "closure_status": requested_status,
        }
        if requested_status == "Closed":
            ok, missing = capa_can_close({**capa, **updates})
            if not ok:
                st.markdown(alert(f"Cannot close CAPA. Missing: {', '.join(missing)}", "red"), unsafe_allow_html=True)
                updates["closure_status"] = "Verification Pending"
        update_capa(selected, updates)
        if updates["closure_status"] == "Closed" and capa.get("linked_ncr_id"):
            update_ncr(capa["linked_ncr_id"], {"status":"Closed"})
        st.markdown(alert("CAPA saved.", "green"), unsafe_allow_html=True)

    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:20px 0">', unsafe_allow_html=True)
    st.markdown(section("Reports"), unsafe_allow_html=True)

    refreshed = get_capa(selected)
    col1, col2 = st.columns(2)
    col1.download_button("Download CAPA Report", data=capa_report(refreshed, ncr),
                         file_name=f"{selected}_capa.md", mime="text/markdown", use_container_width=True)
    col2.download_button("Download 8D Report", data=eight_d_report(refreshed, ncr),
                         file_name=f"{selected}_8d.md", mime="text/markdown", use_container_width=True)

    with st.expander("Preview 8D Report"):
        st.markdown(eight_d_report(refreshed, ncr))

# ══════════════════════════════════════════════════════════════════════════════
# SUPPLIER FEEDBACK
# ══════════════════════════════════════════════════════════════════════════════
def supplier_feedback():
    st.markdown(page_header("Supplier Feedback Report", "Generate a quality feedback summary for a specific supplier"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    ncrs = get_all_ncrs()
    if ncrs.empty:
        st.markdown(alert("No NCRs available.", "blue"), unsafe_allow_html=True)
        return

    supplier = st.selectbox("Supplier", sorted(ncrs["supplier_name"].dropna().unique()))
    df = ncrs[ncrs["supplier_name"] == supplier].copy()

    c1,c2,c3 = st.columns(3)
    c1.markdown(kpi_card("Total NCRs",    len(df),                              sub=supplier), unsafe_allow_html=True)
    c2.markdown(kpi_card("Open",          (df["status"]!="Closed").sum(),       "red" if (df["status"]!="Closed").sum()>5 else "amber"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Critical",      (df["severity"]=="Critical").sum(),   "red" if (df["severity"]=="Critical").sum()>0 else "green"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not df.empty:
        st.markdown(section("NCR List"), unsafe_allow_html=True)
        st.dataframe(
            df[["ncr_id","date_opened","part_number","defect_type","severity","status","disposition","due_date"]],
            use_container_width=True, hide_index=True
        )

        top_defects = df["defect_type"].value_counts().head(5)
        report_lines = [
            f"# Supplier Quality Feedback Report",
            f"## {supplier}",
            "",
            f"| | |",
            f"|---|---|",
            f"| Generated | {date.today().isoformat()} |",
            f"| Total NCRs | {len(df)} |",
            f"| Open NCRs | {(df['status'] != 'Closed').sum()} |",
            f"| Critical NCRs | {(df['severity'] == 'Critical').sum()} |",
            "",
            "---",
            "",
            "## Top Defect Types",
            "",
            "| Defect Type | Count |",
            "|-------------|-------|",
        ] + [f"| {d} | {c} |" for d, c in top_defects.items()] + [
            "",
            "---",
            "",
            "## Required Supplier Actions",
            "",
            "1. Acknowledge receipt of this quality notification within 2 business days.",
            "2. Provide containment response for all open Major and Critical NCRs.",
            "3. Submit supplier 8D report for any recurring or critical defect.",
            "4. Provide objective evidence of corrective action implementation.",
            "5. Confirm preventive action to prevent recurrence across all affected part numbers.",
            "",
            "---",
            "",
            f"*Generated {date.today().isoformat()} — Drone Manufacturing Quality Engineering*",
        ]
        report = "\n".join(report_lines)

        col_dl, _ = st.columns([1,3])
        col_dl.download_button(
            "Download Supplier Feedback Report",
            data=report,
            file_name=f"{supplier.replace(' ','_')}_feedback.md",
            mime="text/markdown",
            use_container_width=True,
        )
        with st.expander("Preview report"):
            st.markdown(report)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    init_db()
    if page == "Dashboard":            dashboard()
    elif page == "Create NCR":         create_ncr()
    elif page == "Import Draft NCRs":  import_page()
    elif page == "NCR Detail":         ncr_detail()
    elif page == "Create CAPA":        create_capa()
    elif page == "CAPA Dashboard":     capa_dashboard()
    elif page == "RCA Builder / 8D":   rca_builder()
    elif page == "Supplier Feedback":  supplier_feedback()

if __name__ == "__main__":
    main()