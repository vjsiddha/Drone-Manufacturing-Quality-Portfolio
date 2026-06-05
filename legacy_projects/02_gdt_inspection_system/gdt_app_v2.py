"""
Automated GD&T Inspection System
Part: MMB-001 Drone Motor Mount Bracket
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os, tempfile, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from shared_styles import apply_styles, style_fig, kpi_card, badge, alert, section, page_header, C

from inspection_engine import InspectionEngine
from gdt_report_generator_v2  import generate_markdown_report, generate_csv_report
from ncr_generator     import generate_ncrs

st.set_page_config(page_title="GD&T Inspection — MMB-001", layout="wide", initial_sidebar_state="expanded")
apply_styles()

DIR  = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(DIR, "output")
os.makedirs(OUT, exist_ok=True)
REQS = os.path.join(DIR, "inspection_requirements.yaml")
MEAS = os.path.join(DIR, "sample_measurements.csv")

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div style="padding:16px 0 8px">
    <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;
                color:{C['muted']};font-family:'JetBrains Mono',monospace;margin-bottom:4px">
        GD&T Inspection
    </div>
    <div style="font-size:14px;font-weight:500;color:{C['text']}">MMB-001</div>
    <div style="font-size:11px;color:{C['muted']};font-family:'JetBrains Mono',monospace">
        Motor Mount Bracket
    </div>
</div>
<hr style="border:none;border-top:1px solid {C['border']};margin:12px 0">
""", unsafe_allow_html=True)

NAV = ["Upload Data", "Inspection Results", "Failed Features", "Report", "Draft NCRs"]
page = st.sidebar.radio("", NAV, label_visibility="collapsed")

st.sidebar.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:12px 0">', unsafe_allow_html=True)
use_sample = st.sidebar.button("Load Sample Data", use_container_width=True)

# ── Session state ──────────────────────────────────────────────────────────────
for k in ["engine","results","results_df","ncr_df","loaded"]:
    if k not in st.session_state:
        st.session_state[k] = None if k != "loaded" else False

def run_inspection(reqs_path, meas_path):
    engine  = InspectionEngine(reqs_path)
    meas_df = engine.load_measurements(meas_path)
    results = engine.evaluate(meas_df)
    res_df  = engine.results_to_dataframe(results)
    ncr_df  = generate_ncrs(results, engine.part_number, engine.part_name)
    generate_markdown_report(engine, results, os.path.join(OUT, "inspection_report.md"))
    generate_csv_report(engine, results, os.path.join(OUT, "inspection_results.csv"))
    ncr_df.to_csv(os.path.join(OUT, "draft_ncrs.csv"), index=False)
    st.session_state.engine     = engine
    st.session_state.results    = results
    st.session_state.results_df = res_df
    st.session_state.ncr_df     = ncr_df
    st.session_state.loaded     = True

if use_sample:
    with st.spinner("Running inspection engine..."):
        run_inspection(REQS, MEAS)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
if page == "Upload Data":
    st.markdown(page_header("Upload Inspection Data", "YAML requirements + CMM measurement CSV"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("Requirements File — YAML"), unsafe_allow_html=True)
        reqs_file = st.file_uploader("inspection_requirements.yaml", type=["yaml","yml"], label_visibility="collapsed")
        with st.expander("Expected structure"):
            st.code("""part_number: MMB-001
features:
  - feature_id: HOLE_1_POSITION
    gdandt_type: position
    nominal_x: 20.00
    nominal_y: 20.00
    tolerance: 0.20
    criticality: High""", language="yaml")

    with col2:
        st.markdown(section("Measurement File — CSV"), unsafe_allow_html=True)
        meas_file = st.file_uploader("sample_measurements.csv", type=["csv"], label_visibility="collapsed")
        with st.expander("Required columns"):
            st.code("part_serial_number, lot_number, supplier_id,\nfeature_id, measured_x, measured_y,\nmeasured_value, tolerance, inspector, inspection_date")

    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:24px 0">', unsafe_allow_html=True)

    run_btn = st.button("Run Inspection Engine", type="primary")
    if run_btn:
        if reqs_file and meas_file:
            with tempfile.TemporaryDirectory() as tmp:
                rp = os.path.join(tmp, "reqs.yaml")
                mp = os.path.join(tmp, "meas.csv")
                open(rp,"wb").write(reqs_file.read())
                open(mp,"wb").write(meas_file.read())
                with st.spinner("Evaluating features..."):
                    run_inspection(rp, mp)
            st.success("Inspection complete. Navigate to Inspection Results.")
        else:
            st.warning("Upload both files, or use Load Sample Data in the sidebar.")

    if st.session_state.loaded:
        stats = st.session_state.engine.summary_stats(st.session_state.results)
        st.markdown(alert(f"Data loaded — {stats['total_parts']} parts · {len(st.session_state.results_df)} feature measurements", "green"), unsafe_allow_html=True)
    else:
        st.markdown(alert("Click <b>Load Sample Data</b> in the sidebar to run the engine on 50 pre-measured parts across 5 lots. LOT-203 contains elevated errors to simulate a non-conforming supplier lot.", "blue"), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INSPECTION RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Inspection Results":
    if not st.session_state.loaded:
        st.warning("No data loaded — use Load Sample Data in the sidebar.")
        st.stop()

    engine  = st.session_state.engine
    results = st.session_state.results
    df      = st.session_state.results_df
    stats   = engine.summary_stats(results)

    st.markdown(page_header("Inspection Results", f"{engine.part_number} — {engine.part_name} — Rev {engine.revision}"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns(5)
    fpy_col = "green" if stats["part_fpy_pct"] >= 90 else ("amber" if stats["part_fpy_pct"] >= 75 else "red")
    c1.markdown(kpi_card("Parts Inspected",  stats["total_parts"],           sub=f"{len(stats['lots_inspected'])} lots"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Pass",             stats["passed"],       "green", sub="All features within tolerance"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Fail",             stats["failed"],       "red"  if stats["failed"] else "green", sub="Critical feature failure"), unsafe_allow_html=True)
    c4.markdown(kpi_card("MRB Review",       stats["mrb_review"],   "amber" if stats["mrb_review"] else "green", sub="Engineering disposition required"), unsafe_allow_html=True)
    c5.markdown(kpi_card("Part FPY",         f"{stats['part_fpy_pct']}%", fpy_col, sub="Feature FPY: " + str(stats['feature_fpy_pct']) + "%"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if stats["failed"] > 0:
        st.markdown(alert(f"{stats['failed']} parts failed inspection. Most common failure: <b>{stats['worst_feature']}</b>.", "red"), unsafe_allow_html=True)
    lot_fail = df[df["result"]=="FAIL"].groupby("lot_number").size()
    if not lot_fail.empty:
        st.markdown(alert(f"Worst performing lot: <b>{lot_fail.idxmax()}</b> with {lot_fail.max()} feature failures. Review LOT-203 for systematic non-conformance.", "amber"), unsafe_allow_html=True)

    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:20px 0">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("Part Disposition"), unsafe_allow_html=True)
        disp_counts = pd.Series([r.disposition for r in results]).value_counts().reset_index()
        disp_counts.columns = ["Disposition","Count"]
        color_map = {"PASS": C["green"], "FAIL": C["red"], "MRB REVIEW": C["amber"]}
        fig = px.bar(disp_counts, x="Disposition", y="Count", color="Disposition",
                     color_discrete_map=color_map)
        fig.update_traces(marker_line_width=0)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Parts")
        st.plotly_chart(style_fig(fig, 280), use_container_width=True)

    with col2:
        st.markdown(section("Results by Lot"), unsafe_allow_html=True)
        lot_disp = pd.DataFrame([{"lot": r.lot_number, "disposition": r.disposition} for r in results])
        lot_summary = lot_disp.groupby(["lot","disposition"]).size().reset_index(name="count")
        fig2 = px.bar(lot_summary, x="lot", y="count", color="disposition",
                      color_discrete_map=color_map, barmode="stack")
        fig2.update_traces(marker_line_width=0)
        fig2.update_layout(xaxis_title="", yaxis_title="Parts", legend_title="")
        st.plotly_chart(style_fig(fig2, 280), use_container_width=True)

    st.markdown(section("Feature Pass Rate"), unsafe_allow_html=True)
    feat_pass = (
        df.groupby("feature_name")["result"]
        .apply(lambda x: (x=="PASS").sum() / len(x) * 100)
        .sort_values().reset_index()
    )
    feat_pass.columns = ["Feature","Pass Rate %"]
    colors = [C["red"] if v < 80 else (C["amber"] if v < 95 else C["green"]) for v in feat_pass["Pass Rate %"]]
    fig3 = go.Figure(go.Bar(
        x=feat_pass["Pass Rate %"], y=feat_pass["Feature"], orientation="h",
        marker_color=colors, marker_line_width=0,
        text=feat_pass["Pass Rate %"].round(1).astype(str)+"%",
        textposition="outside",
        textfont=dict(family="JetBrains Mono", size=11, color=C["subtle"]),
    ))
    fig3.add_vline(x=95, line_dash="dot", line_color=C["border2"],
                   annotation_text="95% target", annotation_font_color=C["muted"],
                   annotation_font_size=10)
    fig3.update_xaxes(range=[0,110], title="")
    fig3.update_yaxes(title="")
    st.plotly_chart(style_fig(fig3, 360), use_container_width=True)

    st.markdown(section("Part Results"), unsafe_allow_html=True)
    part_table = pd.DataFrame([{
        "Serial":     r.part_serial_number,
        "Lot":        r.lot_number,
        "Disposition":r.disposition,
        "Features":   r.total_features,
        "Passed":     r.passed_features,
        "Failed":     r.failed_features,
        "Borderline": len(r.borderline_items),
    } for r in results])
    st.dataframe(part_table, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# FAILED FEATURES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Failed Features":
    if not st.session_state.loaded:
        st.warning("No data loaded.")
        st.stop()

    df     = st.session_state.results_df
    failed = df[df["result"] == "FAIL"].copy()

    st.markdown(page_header("Failed Features", "Feature-level non-conformances across all inspected parts"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    if failed.empty:
        st.markdown(alert("No failures detected across all inspected parts.", "green"), unsafe_allow_html=True)
    else:
        c1,c2,c3 = st.columns(3)
        c1.markdown(kpi_card("Total Failures",    len(failed),                           "red"),   unsafe_allow_html=True)
        c2.markdown(kpi_card("Critical Features", (failed["criticality"]=="High").sum(), "red"),   unsafe_allow_html=True)
        c3.markdown(kpi_card("Lots Affected",     failed["lot_number"].nunique(),        "amber"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            feat_filter = st.multiselect("Filter by feature", options=sorted(failed["feature_name"].unique()))
        with col_f2:
            lot_filter = st.multiselect("Filter by lot", options=sorted(failed["lot_number"].unique()))

        view = failed.copy()
        if feat_filter: view = view[view["feature_name"].isin(feat_filter)]
        if lot_filter:  view = view[view["lot_number"].isin(lot_filter)]

        st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:20px 0">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(section("Failure Count by Feature"), unsafe_allow_html=True)
            fc = failed.groupby("feature_name").size().sort_values().reset_index(name="Failures")
            fig = px.bar(fc, x="Failures", y="feature_name", orientation="h",
                         color_discrete_sequence=[C["red"]])
            fig.update_traces(marker_line_width=0)
            fig.update_layout(yaxis_title="", xaxis_title="Failures")
            st.plotly_chart(style_fig(fig, 300), use_container_width=True)

        with col2:
            st.markdown(section("Deviation vs Tolerance"), unsafe_allow_html=True)
            fig2 = px.scatter(
                failed, x="feature_name", y="deviation",
                color="criticality", size="deviation",
                color_discrete_map={"High": C["red"], "Medium": C["amber"], "Low": C["green"]},
                hover_data=["part_serial_number","lot_number","tolerance"],
            )
            fig2.update_xaxes(tickangle=-30, title="")
            fig2.update_yaxes(title="Deviation (mm)")
            st.plotly_chart(style_fig(fig2, 300), use_container_width=True)

        st.markdown(section("Failure Detail"), unsafe_allow_html=True)
        show = view[["part_serial_number","lot_number","feature_name","gdandt_type",
                      "criticality","measured_value","tolerance","deviation","margin"]].copy()
        show.columns = ["Serial","Lot","Feature","Type","Criticality","Measured","Tolerance","Deviation","Margin"]
        st.dataframe(show, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# REPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Report":
    if not st.session_state.loaded:
        st.warning("No data loaded.")
        st.stop()

    engine  = st.session_state.engine
    results = st.session_state.results
    df      = st.session_state.results_df

    st.markdown(page_header("Inspection Report", f"Generated {__import__('datetime').date.today().isoformat()}"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    md_content = generate_markdown_report(engine, results, os.path.join(OUT, "inspection_report.md"))
    with col1:
        st.download_button("Download Report — Markdown", data=md_content.encode(),
                           file_name="inspection_report.md", mime="text/markdown", use_container_width=True)
    with col2:
        st.download_button("Download Results — CSV", data=df.to_csv(index=False).encode(),
                           file_name="inspection_results.csv", mime="text/csv", use_container_width=True)

    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:20px 0">', unsafe_allow_html=True)
    st.markdown(md_content)

# ══════════════════════════════════════════════════════════════════════════════
# DRAFT NCRs
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Draft NCRs":
    if not st.session_state.loaded:
        st.warning("No data loaded.")
        st.stop()

    ncr_df = st.session_state.ncr_df

    st.markdown(page_header("Draft NCRs", "Auto-generated from failed inspection features — ready for import into Project 3"), unsafe_allow_html=True)
    st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:0 0 24px">', unsafe_allow_html=True)

    if ncr_df.empty:
        st.markdown(alert("No failures detected — no draft NCRs generated.", "green"), unsafe_allow_html=True)
    else:
        c1,c2,c3 = st.columns(3)
        c1.markdown(kpi_card("Draft NCRs",    len(ncr_df),                              "red"),   unsafe_allow_html=True)
        c2.markdown(kpi_card("Major",         (ncr_df["severity"]=="Major").sum(),      "amber"), unsafe_allow_html=True)
        c3.markdown(kpi_card("CAPA Required", (ncr_df["capa_required"]=="Yes").sum(),   "red"),   unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(alert("These records are ready to import into the NCR/CAPA Management System. Download the CSV and use the import function on the Create NCR page.", "amber"), unsafe_allow_html=True)

        st.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:20px 0">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(section("NCRs by Feature"), unsafe_allow_html=True)
            fc = ncr_df.groupby("feature_name").size().sort_values().reset_index(name="Count")
            fig = px.bar(fc, x="Count", y="feature_name", orientation="h",
                         color_discrete_sequence=[C["red"]])
            fig.update_traces(marker_line_width=0)
            fig.update_layout(yaxis_title="")
            st.plotly_chart(style_fig(fig, 280), use_container_width=True)

        with col2:
            st.markdown(section("NCRs by Severity"), unsafe_allow_html=True)
            sc = ncr_df["severity"].value_counts().reset_index()
            sc.columns = ["Severity","Count"]
            cmap = {"Critical": C["red"], "Major": C["amber"], "Minor": C["blue"]}
            fig2 = px.bar(sc, x="Severity", y="Count", color="Severity", color_discrete_map=cmap)
            fig2.update_traces(marker_line_width=0)
            fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
            st.plotly_chart(style_fig(fig2, 280), use_container_width=True)

        st.markdown(section("Draft NCR Records"), unsafe_allow_html=True)
        show = ["ncr_id","part_serial_number","lot_number","feature_name",
                "severity","deviation","recommended_disposition","capa_required","due_date"]
        st.dataframe(ncr_df[show], use_container_width=True, hide_index=True)

        st.download_button("Download Draft NCRs — CSV",
                           data=ncr_df.to_csv(index=False).encode(),
                           file_name="draft_ncrs.csv", mime="text/csv",
                           use_container_width=True)     