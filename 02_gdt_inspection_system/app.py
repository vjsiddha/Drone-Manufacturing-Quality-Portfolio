"""
Automated GD&T Inspection System — Streamlit App
Part: MMB-001 Drone Motor Mount Bracket
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os, io, tempfile

from inspection_engine import InspectionEngine
from report_generator   import generate_markdown_report, generate_csv_report
from ncr_generator      import generate_ncrs

# ─── CONFIG ──────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GD&T Inspection System",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.result-pass       { color:#3fb950; font-weight:700; font-family:'IBM Plex Mono',monospace; }
.result-fail       { color:#f85149; font-weight:700; font-family:'IBM Plex Mono',monospace; }
.result-borderline { color:#d29922; font-weight:700; font-family:'IBM Plex Mono',monospace; }
.result-mrb        { color:#d29922; font-weight:700; font-family:'IBM Plex Mono',monospace; }
.kpi-card {
    background:linear-gradient(135deg,#161b22,#1c2128);
    border:1px solid #30363d; border-radius:8px;
    padding:18px 20px; text-align:center;
}
.kpi-label { font-size:11px; font-weight:600; letter-spacing:1.5px;
             text-transform:uppercase; color:#8b949e;
             font-family:'IBM Plex Mono',monospace; }
.kpi-value { font-size:30px; font-weight:600; color:#f0f6fc; margin:4px 0;
             font-family:'IBM Plex Mono',monospace; }
.kpi-value.green { color:#3fb950; }
.kpi-value.red   { color:#f85149; }
.kpi-value.amber { color:#d29922; }
.section-hdr {
    font-size:12px; font-weight:600; letter-spacing:2px;
    text-transform:uppercase; color:#58a6ff;
    font-family:'IBM Plex Mono',monospace;
    border-bottom:1px solid #21262d; padding-bottom:6px; margin-bottom:12px;
}
.insight { background:#161b22; border-left:3px solid #58a6ff;
           border-radius:0 6px 6px 0; padding:10px 14px;
           font-size:13px; color:#c9d1d9; margin-bottom:8px; }
.insight.red   { border-left-color:#f85149; }
.insight.green { border-left-color:#3fb950; }
.insight.amber { border-left-color:#d29922; }
</style>
""", unsafe_allow_html=True)

DIR   = os.path.dirname(os.path.abspath(__file__))
OUT   = os.path.join(DIR, "output")
os.makedirs(OUT, exist_ok=True)

REQS_DEFAULT = os.path.join(DIR, "inspection_requirements.yaml")
MEAS_DEFAULT = os.path.join(DIR, "sample_measurements.csv")

PLOT_BG   = "#0d1117"
PAPER_BG  = "#0d1117"
GRID      = "#21262d"
GREEN     = "#3fb950"
RED       = "#f85149"
AMBER     = "#d29922"
BLUE      = "#58a6ff"

def style_fig(fig, height=320):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        height=height, margin=dict(l=16,r=16,t=36,b=16),
        font=dict(family="IBM Plex Mono", size=11, color="#c9d1d9"),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig

def kpi(label, value, color=""):
    return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value {color}">{value}</div></div>'

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────

st.sidebar.markdown("## 📐 GD&T Inspection")
st.sidebar.markdown("**MMB-001 Motor Mount Bracket**")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate", [
    "📤 Upload Data",
    "📊 Inspection Results",
    "❌ Failed Features",
    "📄 Generated Report",
    "🚨 NCR Preview",
])

st.sidebar.markdown("---")
st.sidebar.markdown("**Load sample data**")
use_sample = st.sidebar.button("▶ Use Sample Data", use_container_width=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────

if "engine"    not in st.session_state: st.session_state.engine    = None
if "results"   not in st.session_state: st.session_state.results   = None
if "results_df"not in st.session_state: st.session_state.results_df= None
if "ncr_df"    not in st.session_state: st.session_state.ncr_df    = None
if "loaded"    not in st.session_state: st.session_state.loaded    = False

def run_inspection(reqs_path, meas_path):
    engine   = InspectionEngine(reqs_path)
    meas_df  = engine.load_measurements(meas_path)
    results  = engine.evaluate(meas_df)
    res_df   = engine.results_to_dataframe(results)
    ncr_df   = generate_ncrs(results, engine.part_number, engine.part_name)

    # Save outputs
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
        run_inspection(REQS_DEFAULT, MEAS_DEFAULT)
    st.sidebar.success("Sample data loaded!")

# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 1 — UPLOAD DATA
# ═══════════════════════════════════════════════════════════════════════════

if page == "📤 Upload Data":
    st.markdown("## 📤 Upload Inspection Data")
    st.markdown("Upload a YAML requirements file and CSV measurement file, or use the sample data.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-hdr">Requirements File (YAML)</div>', unsafe_allow_html=True)
        reqs_file = st.file_uploader("Upload inspection_requirements.yaml", type=["yaml","yml"])
        with st.expander("Preview sample requirements structure"):
            st.code("""
part_number: MMB-001
part_name: Drone Motor Mount Bracket
features:
  - feature_id: HOLE_1_POSITION
    gdandt_type: position
    nominal_x: 20.00
    nominal_y: 20.00
    tolerance: 0.20
    datum_reference: "A|B|C"
    criticality: High
            """, language="yaml")

    with col2:
        st.markdown('<div class="section-hdr">Measurement File (CSV)</div>', unsafe_allow_html=True)
        meas_file = st.file_uploader("Upload sample_measurements.csv", type=["csv"])
        with st.expander("Preview sample measurement columns"):
            st.code("""
inspection_id, part_serial_number, lot_number,
supplier_id, feature_id, gdandt_type,
measured_x, measured_y, measured_value,
nominal_value, tolerance, measurement_unit,
inspector, inspection_date
            """)

    st.markdown("---")

    col_btn, col_info = st.columns([1,3])
    with col_btn:
        run_btn = st.button("▶ Run Inspection Engine", type="primary", use_container_width=True)

    if run_btn:
        if reqs_file and meas_file:
            with tempfile.TemporaryDirectory() as tmp:
                rp = os.path.join(tmp, "reqs.yaml")
                mp = os.path.join(tmp, "meas.csv")
                with open(rp,"wb") as f: f.write(reqs_file.read())
                with open(mp,"wb") as f: f.write(meas_file.read())
                with st.spinner("Evaluating GD&T features..."):
                    run_inspection(rp, mp)
            st.success("✅ Inspection complete! Navigate to Inspection Results.")
        else:
            st.warning("Please upload both files, or click 'Use Sample Data' in the sidebar.")

    if not st.session_state.loaded:
        st.markdown('<div class="insight">💡 Click <b>Use Sample Data</b> in the sidebar to load 50 pre-measured parts across 5 lots, including one bad lot (LOT-203) with elevated defects.</div>', unsafe_allow_html=True)
    else:
        stats = st.session_state.engine.summary_stats(st.session_state.results)
        st.markdown(f'<div class="insight green">✅ Data loaded — {stats["total_parts"]} parts, {len(st.session_state.results_df)} feature measurements evaluated.</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 2 — INSPECTION RESULTS
# ═══════════════════════════════════════════════════════════════════════════

elif page == "📊 Inspection Results":
    st.markdown("## 📊 Inspection Results")

    if not st.session_state.loaded:
        st.warning("No data loaded. Click 'Use Sample Data' in the sidebar or upload files on the Upload page.")
        st.stop()

    engine  = st.session_state.engine
    results = st.session_state.results
    df      = st.session_state.results_df
    stats   = engine.summary_stats(results)

    st.markdown("---")

    # KPIs
    c1,c2,c3,c4,c5 = st.columns(5)
    fpy_color = "green" if stats["part_fpy_pct"] >= 90 else ("amber" if stats["part_fpy_pct"] >= 75 else "red")
    c1.markdown(kpi("Parts Inspected", stats["total_parts"]), unsafe_allow_html=True)
    c2.markdown(kpi("Parts Passed",    stats["passed"],       "green"), unsafe_allow_html=True)
    c3.markdown(kpi("Parts Failed",    stats["failed"],       "red"  if stats["failed"] else "green"), unsafe_allow_html=True)
    c4.markdown(kpi("MRB Review",      stats["mrb_review"],   "amber" if stats["mrb_review"] else "green"), unsafe_allow_html=True)
    c5.markdown(kpi("Part FPY",        f"{stats['part_fpy_pct']}%", fpy_color), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Insight banners
    if stats["failed"] > 0:
        st.markdown(f'<div class="insight red">🔴 <b>{stats["failed"]} parts FAILED</b> — most common failed feature: <b>{stats["worst_feature"]}</b></div>', unsafe_allow_html=True)

    lot_fail = df[df["result"]=="FAIL"].groupby("lot_number").size()
    if not lot_fail.empty:
        worst_lot = lot_fail.idxmax()
        st.markdown(f'<div class="insight amber">⚠️ <b>Worst lot: {worst_lot}</b> — {lot_fail.max()} feature failures</div>', unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-hdr">Part Disposition Summary</div>', unsafe_allow_html=True)
        disp_counts = pd.Series([r.disposition for r in results]).value_counts().reset_index()
        disp_counts.columns = ["Disposition","Count"]
        color_map = {"PASS": GREEN, "FAIL": RED, "MRB REVIEW": AMBER}
        fig = px.pie(disp_counts, names="Disposition", values="Count",
                     color="Disposition", color_discrete_map=color_map)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(style_fig(fig, 300), use_container_width=True)

    with col2:
        st.markdown('<div class="section-hdr">Results by Lot</div>', unsafe_allow_html=True)
        lot_disp = pd.DataFrame([
            {"lot": r.lot_number, "disposition": r.disposition} for r in results
        ])
        lot_summary = lot_disp.groupby(["lot","disposition"]).size().reset_index(name="count")
        fig2 = px.bar(lot_summary, x="lot", y="count", color="disposition",
                      color_discrete_map=color_map, barmode="stack")
        fig2.update_xaxes(title="Lot")
        fig2.update_yaxes(title="Parts")
        st.plotly_chart(style_fig(fig2, 300), use_container_width=True)

    st.markdown('<div class="section-hdr">Feature Pass Rate</div>', unsafe_allow_html=True)
    feat_pass = (
        df.groupby("feature_name")["result"]
        .apply(lambda x: (x=="PASS").sum() / len(x) * 100)
        .sort_values()
        .reset_index()
    )
    feat_pass.columns = ["Feature","Pass Rate %"]
    colors = [RED if v < 80 else (AMBER if v < 95 else GREEN) for v in feat_pass["Pass Rate %"]]
    fig3 = go.Figure(go.Bar(
        x=feat_pass["Pass Rate %"], y=feat_pass["Feature"], orientation="h",
        marker_color=colors,
        text=feat_pass["Pass Rate %"].round(1).astype(str)+"%", textposition="outside",
    ))
    fig3.add_vline(x=95, line_dash="dash", line_color=AMBER, annotation_text="95% target")
    fig3.update_xaxes(range=[0,110])
    st.plotly_chart(style_fig(fig3, 380), use_container_width=True)

    st.markdown('<div class="section-hdr">Part Results Table</div>', unsafe_allow_html=True)
    part_table = pd.DataFrame([{
        "Serial #":         r.part_serial_number,
        "Lot":              r.lot_number,
        "Disposition":      r.disposition,
        "Features":         r.total_features,
        "Passed":           r.passed_features,
        "Failed":           r.failed_features,
        "Borderline":       len(r.borderline_items),
    } for r in results])
    st.dataframe(part_table, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 3 — FAILED FEATURES
# ═══════════════════════════════════════════════════════════════════════════

elif page == "❌ Failed Features":
    st.markdown("## ❌ Failed Features Detail")

    if not st.session_state.loaded:
        st.warning("No data loaded. Click 'Use Sample Data' in the sidebar.")
        st.stop()

    df = st.session_state.results_df
    failed = df[df["result"] == "FAIL"].copy()

    st.markdown("---")

    if failed.empty:
        st.markdown('<div class="insight green">✅ No failures detected across all inspected parts.</div>', unsafe_allow_html=True)
    else:
        c1,c2,c3 = st.columns(3)
        c1.markdown(kpi("Total Failures",     str(len(failed)),                          "red"), unsafe_allow_html=True)
        c2.markdown(kpi("Critical Features",  str((failed["criticality"]=="High").sum()), "red"), unsafe_allow_html=True)
        c3.markdown(kpi("Lots Affected",      str(failed["lot_number"].nunique()),        "amber"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Filter controls
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            feat_filter = st.multiselect(
                "Filter by Feature",
                options=sorted(failed["feature_name"].unique()),
                default=[]
            )
        with col_f2:
            lot_filter = st.multiselect(
                "Filter by Lot",
                options=sorted(failed["lot_number"].unique()),
                default=[]
            )

        view = failed.copy()
        if feat_filter: view = view[view["feature_name"].isin(feat_filter)]
        if lot_filter:  view = view[view["lot_number"].isin(lot_filter)]

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-hdr">Failure Count by Feature</div>', unsafe_allow_html=True)
            fc = failed.groupby("feature_name").size().sort_values().reset_index(name="failures")
            fig = px.bar(fc, x="failures", y="feature_name", orientation="h",
                         color="failures", color_continuous_scale="Reds")
            fig.update_layout(coloraxis_showscale=False, yaxis_title="")
            st.plotly_chart(style_fig(fig, 320), use_container_width=True)

        with col2:
            st.markdown('<div class="section-hdr">Deviation vs Tolerance</div>', unsafe_allow_html=True)
            fig2 = px.scatter(
                failed, x="feature_name", y="deviation",
                color="criticality", size="deviation",
                color_discrete_map={"High": RED, "Medium": AMBER, "Low": GREEN},
                hover_data=["part_serial_number","lot_number","tolerance"],
            )
            # Add tolerance lines per feature
            for feat_name, grp in failed.groupby("feature_name"):
                tol = grp["tolerance"].iloc[0]
                fig2.add_hline(y=tol, line_dash="dash", line_color="#555", opacity=0.5)
            fig2.update_xaxes(tickangle=-30, title="")
            fig2.update_yaxes(title="Deviation (mm)")
            st.plotly_chart(style_fig(fig2, 320), use_container_width=True)

        st.markdown('<div class="section-hdr">Failed Measurements Detail</div>', unsafe_allow_html=True)
        show_cols = ["part_serial_number","lot_number","feature_name","gdandt_type",
                     "criticality","measured_value","tolerance","deviation","margin"]
        st.dataframe(
            view[show_cols].rename(columns={
                "part_serial_number":"Serial #",
                "lot_number":"Lot",
                "feature_name":"Feature",
                "gdandt_type":"Type",
                "criticality":"Criticality",
                "measured_value":"Measured",
                "tolerance":"Tolerance",
                "deviation":"Deviation",
                "margin":"Margin",
            }),
            use_container_width=True,
            hide_index=True,
        )


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 4 — GENERATED REPORT
# ═══════════════════════════════════════════════════════════════════════════

elif page == "📄 Generated Report":
    st.markdown("## 📄 Inspection Report")

    if not st.session_state.loaded:
        st.warning("No data loaded. Click 'Use Sample Data' in the sidebar.")
        st.stop()

    engine  = st.session_state.engine
    results = st.session_state.results
    df      = st.session_state.results_df

    st.markdown("---")

    # Generate report in memory
    md_content = generate_markdown_report(
        engine, results, os.path.join(OUT, "inspection_report.md")
    )

    st.markdown(md_content)

    st.markdown("---")
    st.markdown('<div class="section-hdr">Download Report Files</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download Markdown Report",
            data=md_content.encode(),
            file_name="inspection_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Results CSV",
            data=csv_bytes,
            file_name="inspection_results.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 5 — NCR PREVIEW
# ═══════════════════════════════════════════════════════════════════════════

elif page == "🚨 NCR Preview":
    st.markdown("## 🚨 Draft NCR Preview")
    st.markdown("Failed features automatically generate draft NCRs for import into the NCR/CAPA system (Project 4).")

    if not st.session_state.loaded:
        st.warning("No data loaded. Click 'Use Sample Data' in the sidebar.")
        st.stop()

    ncr_df = st.session_state.ncr_df
    st.markdown("---")

    if ncr_df.empty:
        st.markdown('<div class="insight green">✅ No failures — no draft NCRs generated.</div>', unsafe_allow_html=True)
    else:
        c1,c2,c3 = st.columns(3)
        c1.markdown(kpi("Draft NCRs",    str(len(ncr_df)),                                  "red"), unsafe_allow_html=True)
        c2.markdown(kpi("Major",         str((ncr_df["severity"]=="Major").sum()),            "amber"), unsafe_allow_html=True)
        c3.markdown(kpi("CAPA Required", str((ncr_df["capa_required"]=="Yes").sum()),         "red"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="insight red">⚠️ These draft NCRs are ready for import into the NCR/CAPA Management System (Project 4). Download the CSV and use the import function.</div>', unsafe_allow_html=True)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-hdr">NCRs by Feature</div>', unsafe_allow_html=True)
            fc = ncr_df.groupby("feature_name").size().sort_values().reset_index(name="count")
            fig = px.bar(fc, x="count", y="feature_name", orientation="h",
                         color="count", color_continuous_scale="Reds")
            fig.update_layout(coloraxis_showscale=False, yaxis_title="")
            st.plotly_chart(style_fig(fig, 300), use_container_width=True)

        with col2:
            st.markdown('<div class="section-hdr">NCRs by Severity</div>', unsafe_allow_html=True)
            sc = ncr_df["severity"].value_counts().reset_index()
            sc.columns = ["Severity","Count"]
            color_map = {"Critical": RED, "Major": AMBER, "Minor": BLUE}
            fig2 = px.pie(sc, names="Severity", values="Count",
                          color="Severity", color_discrete_map=color_map)
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(style_fig(fig2, 300), use_container_width=True)

        st.markdown('<div class="section-hdr">Draft NCR Records</div>', unsafe_allow_html=True)
        show = ["ncr_id","part_serial_number","lot_number","feature_name",
                "requirement","actual_result","deviation","severity",
                "recommended_disposition","capa_required","due_date"]
        st.dataframe(ncr_df[show], use_container_width=True, hide_index=True)

        st.markdown("---")
        csv_bytes = ncr_df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Draft NCRs CSV (import into Project 4)",
            data=csv_bytes,
            file_name="draft_ncrs.csv",
            mime="text/csv",
            use_container_width=True,
        )