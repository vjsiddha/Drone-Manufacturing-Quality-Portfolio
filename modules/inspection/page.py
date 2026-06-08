from pathlib import Path
import tempfile

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

try:
    from modules.common.paths import (
        DATA_DIR,
        REPORTS_DIR,
        INSPECTION_REQUIREMENTS,
        SAMPLE_MEASUREMENTS,
        INSPECTION_RESULTS,
        DRAFT_NCRS,
    )
except Exception:
    ROOT_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = ROOT_DIR / "data"
    REPORTS_DIR = ROOT_DIR / "reports"
    INSPECTION_REQUIREMENTS = DATA_DIR / "inspection_requirements.yaml"
    SAMPLE_MEASUREMENTS = DATA_DIR / "sample_measurements.csv"
    INSPECTION_RESULTS = DATA_DIR / "inspection_results.csv"
    DRAFT_NCRS = DATA_DIR / "draft_ncrs.csv"

try:
    from modules.common.ui import product_header, lifecycle_flow
except Exception:
    product_header = None
    lifecycle_flow = None

from modules.inspection.inspection_engine import InspectionEngine
from modules.inspection.ncr_generator import generate_ncrs

try:
    from modules.inspection.gdt_report_generator_v2 import generate_markdown_report, generate_csv_report
except Exception:
    from modules.inspection.report_generator import generate_markdown_report, generate_csv_report

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
INSPECTION_REPORT = REPORTS_DIR / "inspection_report.md"


def _state_key(name: str) -> str:
    return f"inspection_{name}"


def _init_state():
    defaults = {
        "engine": None,
        "results": None,
        "results_df": None,
        "ncr_df": None,
        "report_md": None,
        "loaded": False,
        "source_label": "Shared sample data",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(_state_key(key), value)


def _html_metric(label, value, sub="", tone="neutral"):
    colors = {
        "green": ("#0f5132", "#d1e7dd"),
        "red": ("#842029", "#f8d7da"),
        "amber": ("#664d03", "#fff3cd"),
        "blue": ("#084298", "#cfe2ff"),
        "neutral": ("#1f2937", "#f3f4f6"),
    }
    fg, bg = colors.get(tone, colors["neutral"])
    st.markdown(
        f"""
        <div style="
            border:1px solid rgba(255,255,255,0.18);
            border-radius:14px;
            padding:18px 18px;
            background:{bg};
            min-height:126px;
            margin:0 0 18px 0;
            box-sizing:border-box;
        ">
            <div style="font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:{fg};font-weight:800">{label}</div>
            <div style="font-size:30px;font-weight:850;color:{fg};margin-top:10px;line-height:1.1">{value}</div>
            <div style="font-size:12px;color:{fg};opacity:.75;margin-top:10px;line-height:1.35">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _status_message(text, tone="blue"):
    palette = {
        "green": ("#0f5132", "#d1e7dd"),
        "red": ("#842029", "#f8d7da"),
        "amber": ("#664d03", "#fff3cd"),
        "blue": ("#084298", "#cfe2ff"),
    }
    fg, bg = palette.get(tone, palette["blue"])
    st.markdown(
        f"<div style='border-radius:12px;padding:13px 15px;background:{bg};color:{fg};font-weight:600'>{text}</div>",
        unsafe_allow_html=True,
    )


def _run_inspection(requirements_path: Path, measurements_path: Path, source_label="Shared sample data"):
    engine = InspectionEngine(str(requirements_path))
    measurements_df = engine.load_measurements(str(measurements_path))
    results = engine.evaluate(measurements_df)
    results_df = engine.results_to_dataframe(results)
    ncr_df = generate_ncrs(results, engine.part_number, engine.part_name)

    results_df.to_csv(INSPECTION_RESULTS, index=False)
    ncr_df.to_csv(DRAFT_NCRS, index=False)
    report_md = generate_markdown_report(engine, results, str(INSPECTION_REPORT))

    try:
        generate_csv_report(engine, results, str(INSPECTION_RESULTS))
    except Exception:
        pass

    st.session_state[_state_key("engine")] = engine
    st.session_state[_state_key("results")] = results
    st.session_state[_state_key("results_df")] = results_df
    st.session_state[_state_key("ncr_df")] = ncr_df
    st.session_state[_state_key("report_md")] = report_md
    st.session_state[_state_key("loaded")] = True
    st.session_state[_state_key("source_label")] = source_label


def _load_existing_outputs_if_available():
    if st.session_state[_state_key("loaded")]:
        return
    if INSPECTION_RESULTS.exists():
        df = pd.read_csv(INSPECTION_RESULTS)
        st.session_state[_state_key("results_df")] = df
        st.session_state[_state_key("ncr_df")] = pd.read_csv(DRAFT_NCRS) if DRAFT_NCRS.exists() else pd.DataFrame()
        st.session_state[_state_key("report_md")] = INSPECTION_REPORT.read_text() if INSPECTION_REPORT.exists() else ""
        st.session_state[_state_key("loaded")] = True
        st.session_state[_state_key("source_label")] = "Existing saved inspection_results.csv"


def _summary_metrics(df: pd.DataFrame):
    total_features = len(df)
    passed = int((df["result"] == "PASS").sum()) if "result" in df else 0
    failed = int((df["result"] == "FAIL").sum()) if "result" in df else 0
    pass_rate = round((passed / total_features) * 100, 1) if total_features else 0
    failed_df = df[df["result"] == "FAIL"] if "result" in df else pd.DataFrame()
    failed_lots = failed_df["lot_number"].nunique() if not failed_df.empty else 0
    failed_serials = failed_df["part_serial_number"].nunique() if not failed_df.empty else 0
    worst_feature = failed_df["feature_id"].value_counts().idxmax() if not failed_df.empty else "None"
    return total_features, passed, failed, pass_rate, failed_lots, failed_serials, worst_feature


def _render_summary_cards(df: pd.DataFrame):
    total, passed, failed, pass_rate, failed_lots, failed_serials, worst_feature = _summary_metrics(df)

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        _html_metric("Total Features", f"{total:,}", "GD&T checks evaluated", "blue")
    with c2:
        _html_metric("Passed", f"{passed:,}", "Within tolerance", "green")
    with c3:
        _html_metric("Failed", f"{failed:,}", "Nonconforming features", "red" if failed else "green")
    with c4:
        _html_metric("Pass Rate", f"{pass_rate}%", "Feature-level yield", "green" if pass_rate >= 95 else "amber" if pass_rate >= 80 else "red")

    c5, c6, c7 = st.columns(3, gap="medium")
    with c5:
        _html_metric("Failed Lots", failed_lots, "Lots requiring review", "amber" if failed_lots else "green")
    with c6:
        _html_metric("Failed Serials", failed_serials, "Parts with failures", "red" if failed_serials else "green")
    with c7:
        _html_metric("Worst Feature", worst_feature, "Highest failure count", "red" if worst_feature != "None" else "green")


def _require_results():
    if not st.session_state[_state_key("loaded")]:
        _status_message("Run the GD&T evaluation first using the Workflow tab.", "amber")
        st.stop()
    df = st.session_state[_state_key("results_df")]
    if df is None or df.empty:
        _status_message("No inspection results are available yet.", "amber")
        st.stop()
    return df


def _render_workflow_tab():
    st.subheader("Case Intake")
    st.caption("Select evidence sources → run GD&T evaluation → analyze failure patterns → generate case report → escalate into NCR/CAPA.")

    if lifecycle_flow:
        try:
            lifecycle_flow(["Risk Assessment / FMEA", "Inspection & Verification", "NCR / CAPA", "Quality Analytics", "Continuous Improvement"])
        except TypeError:
            lifecycle_flow()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Requirements Source")
        st.write(f"Shared YAML: `{INSPECTION_REQUIREMENTS}`")
        req_upload = st.file_uploader("Override inspection_requirements.yaml", type=["yaml", "yml"])
        with st.expander("Required requirement structure"):
            st.code("feature_id, gdandt_type, nominal_x, nominal_y, nominal_value, tolerance, datum_reference, criticality", language="text")
    with col2:
        st.markdown("#### Measurement Source")
        st.write(f"Shared CSV: `{SAMPLE_MEASUREMENTS}`")
        meas_upload = st.file_uploader("Override sample_measurements.csv", type=["csv"])
        with st.expander("Required measurement columns"):
            st.code("part_serial_number, lot_number, supplier_id, feature_id, measured_x, measured_y, measured_value, inspection_date, inspector", language="text")

    use_uploads = req_upload is not None and meas_upload is not None
    run_col, save_col = st.columns([1, 2])
    with run_col:
        run_clicked = st.button("Review Inspection Evidence", type="primary", use_container_width=True)

    if run_clicked:
        try:
            with st.spinner("Reviewing inspection evidence against GD&T requirements..."):
                if use_uploads:
                    with tempfile.TemporaryDirectory() as tmp:
                        req_path = Path(tmp) / "inspection_requirements.yaml"
                        meas_path = Path(tmp) / "sample_measurements.csv"
                        req_path.write_bytes(req_upload.read())
                        meas_path.write_bytes(meas_upload.read())
                        _run_inspection(req_path, meas_path, "Uploaded inspection files")
                else:
                    _run_inspection(Path(INSPECTION_REQUIREMENTS), Path(SAMPLE_MEASUREMENTS), "Shared sample data")
            _status_message("Evidence review complete. Results, case report, and draft NCR file were written to shared data/report locations.", "green")
        except Exception as exc:
            st.error(f"Inspection run failed: {exc}")

    if st.session_state[_state_key("loaded")]:
        df = st.session_state[_state_key("results_df")]
        total, passed, failed, pass_rate, failed_lots, failed_serials, worst_feature = _summary_metrics(df)
        _status_message(
            f"Loaded source: {st.session_state[_state_key('source_label')]} · {total:,} feature checks available. "
            f"Evidence summary: {passed:,} passed, {failed:,} failed, {pass_rate}% pass rate.",
            "blue",
        )
        st.markdown(
            f"""
            <div style="background:rgba(74,127,165,0.08);border:1px solid rgba(74,127,165,0.25);border-radius:12px;padding:16px 18px;margin:18px 0 4px;">
                <div style="font-size:12px;letter-spacing:1.6px;text-transform:uppercase;color:#94a3b8;font-family:'JetBrains Mono',monospace;margin-bottom:8px;">Case Intake Complete</div>
                <div style="font-size:14px;line-height:1.6;color:#e2e8f0;">
                    The evidence package has been loaded. Open <b>Evidence Summary</b> for the KPI cards and part disposition, or continue to <b>Root Cause Clues</b> to analyze failure patterns.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        _status_message("No current run loaded. Click Review Inspection Evidence to use the shared YAML + sample measurement CSV.", "amber")


def _render_results_tab():
    df = _require_results()
    _case_file_banner(df)
    _investigation_route(df)
    st.subheader("Evidence Summary")
    _render_summary_cards(df)

    st.markdown("#### Part Disposition")
    if "part_disposition" in df.columns:
        part_table = (
            df.groupby(["part_serial_number", "lot_number", "supplier_id", "part_disposition"])
            .agg(features=("feature_id", "count"), passed=("result", lambda s: (s == "PASS").sum()), failed=("result", lambda s: (s == "FAIL").sum()), borderline=("result", lambda s: (s == "BORDERLINE").sum()))
            .reset_index()
            .sort_values(["part_disposition", "failed"], ascending=[True, False])
        )
        c1, c2 = st.columns(2)
        with c1:
            disp_counts = part_table["part_disposition"].value_counts().reset_index()
            disp_counts.columns = ["Disposition", "Count"]
            fig = px.bar(disp_counts, x="Disposition", y="Count", color="Disposition", title="Disposition Count")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            lot_summary = part_table.groupby(["lot_number", "part_disposition"]).size().reset_index(name="count")
            fig = px.bar(lot_summary, x="lot_number", y="count", color="part_disposition", barmode="stack", title="Disposition by Lot")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(part_table, use_container_width=True, hide_index=True)

    st.markdown("#### Feature-Level Results")
    c1, c2, c3 = st.columns(3)
    with c1:
        result_filter = st.multiselect("Result", sorted(df["result"].dropna().unique()), default=sorted(df["result"].dropna().unique()))
    with c2:
        type_filter = st.multiselect("GD&T Type", sorted(df["gdandt_type"].dropna().unique()))
    with c3:
        lot_filter = st.multiselect("Lot", sorted(df["lot_number"].dropna().unique()))
    view = df.copy()
    if result_filter: view = view[view["result"].isin(result_filter)]
    if type_filter: view = view[view["gdandt_type"].isin(type_filter)]
    if lot_filter: view = view[view["lot_number"].isin(lot_filter)]
    st.dataframe(view, use_container_width=True, hide_index=True)


def _render_failure_tab():
    df = _require_results()
    _case_file_banner(df)
    failed = df[df["result"] == "FAIL"].copy()
    st.subheader("Root Cause Clues")
    if failed.empty:
        _status_message("No failed features detected. No root-cause clue analysis required.", "green")
        return

    c1, c2, c3 = st.columns(3)
    with c1: _html_metric("Failed Features", len(failed), "Feature-level defects", "red")
    with c2: _html_metric("Failure Types", failed["gdandt_type"].nunique(), "GD&T categories affected", "amber")
    with c3: _html_metric("Lots Affected", failed["lot_number"].nunique(), "Containment scope", "amber")

    col1, col2 = st.columns(2)
    with col1:
        by_type = failed["gdandt_type"].value_counts().reset_index()
        by_type.columns = ["GD&T Type", "Failures"]
        fig = px.bar(by_type, x="GD&T Type", y="Failures", title="Failures by GD&T Type")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        by_lot = failed["lot_number"].value_counts().reset_index()
        by_lot.columns = ["Lot", "Failures"]
        fig = px.bar(by_lot, x="Lot", y="Failures", title="Failures by Lot")
        st.plotly_chart(fig, use_container_width=True)

    by_feature = failed["feature_id"].value_counts().reset_index()
    by_feature.columns = ["Feature ID", "Failures"]
    by_feature["Cumulative %"] = (by_feature["Failures"].cumsum() / by_feature["Failures"].sum() * 100).round(1)
    fig = go.Figure()
    fig.add_bar(x=by_feature["Feature ID"], y=by_feature["Failures"], name="Failures")
    fig.add_scatter(x=by_feature["Feature ID"], y=by_feature["Cumulative %"], name="Cumulative %", yaxis="y2", mode="lines+markers")
    fig.update_layout(title="Pareto of Failed Features", yaxis=dict(title="Failures"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 110]), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Evidence Detail — Failed Features")
    cols = ["part_serial_number", "lot_number", "supplier_id", "feature_id", "feature_name", "gdandt_type", "criticality", "deviation", "tolerance", "margin", "inspector", "inspection_date"]
    st.dataframe(failed[[c for c in cols if c in failed.columns]].sort_values("margin"), use_container_width=True, hide_index=True)


def _render_technical_tab():
    df = _require_results()
    _case_file_banner(df)
    st.subheader("Technical Evidence")
    st.markdown("True position error is calculated as `2 * sqrt((measured_x - nominal_x)^2 + (measured_y - nominal_y)^2)`. Tolerance margin is `tolerance - deviation`.")

    pos = df[df["gdandt_type"] == "position"].copy()
    if not pos.empty:
        pos["x_error"] = pos["measured_x"] - pos["nominal_x"]
        pos["y_error"] = pos["measured_y"] - pos["nominal_y"]
        pos["true_position_calc"] = 2 * ((pos["x_error"] ** 2 + pos["y_error"] ** 2) ** 0.5)
        pos["true_position_calc"] = pos["true_position_calc"].round(5)
        st.markdown("#### True Position Evidence")
        show = ["part_serial_number", "lot_number", "feature_id", "nominal_x", "nominal_y", "measured_x", "measured_y", "x_error", "y_error", "true_position_calc", "tolerance", "margin", "result"]
        st.dataframe(pos[show], use_container_width=True, hide_index=True)

        fig = px.scatter(pos, x="true_position_calc", y="margin", color="result", hover_data=["part_serial_number", "lot_number", "feature_id"], title="True Position Error vs Tolerance Margin")
        fig.add_vline(x=float(pos["tolerance"].max()), line_dash="dash", annotation_text="Max TP tolerance")
        fig.add_hline(y=0, line_dash="dash", annotation_text="Fail threshold")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Deviation Evidence by Feature")
    tech = df.copy()
    tech["tolerance_margin"] = tech["margin"]
    tech["deviation_from_nominal"] = tech["deviation"]
    cols = ["part_serial_number", "lot_number", "feature_id", "gdandt_type", "nominal_value", "measured_value", "deviation_from_nominal", "tolerance", "tolerance_margin", "margin_pct", "result"]
    st.dataframe(tech[[c for c in cols if c in tech.columns]].sort_values("tolerance_margin"), use_container_width=True, hide_index=True)


def _render_report_tab():
    _require_results()
    engine = st.session_state[_state_key("engine")]
    results = st.session_state[_state_key("results")]
    df = st.session_state[_state_key("results_df")]

    st.subheader("Investigation Case Report")
    if engine is not None and results is not None:
        if st.button("Regenerate Investigation Case Report", type="primary"):
            st.session_state[_state_key("report_md")] = generate_markdown_report(engine, results, str(INSPECTION_REPORT))
            generate_csv_report(engine, results, str(INSPECTION_RESULTS))
            _status_message(f"Report saved to `{INSPECTION_REPORT}`", "green")

    md = st.session_state[_state_key("report_md")]
    if not md and INSPECTION_REPORT.exists():
        md = INSPECTION_REPORT.read_text()
    if md:
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download inspection_report.md", md, file_name="inspection_report.md", mime="text/markdown", use_container_width=True)
        with c2:
            st.download_button("Download inspection_results.csv", df.to_csv(index=False), file_name="inspection_results.csv", mime="text/csv", use_container_width=True)
        st.markdown(md)
    else:
        _status_message("Run a fresh inspection to generate the markdown report with the full engine context.", "amber")


def _render_ncr_tab():
    df = _require_results()
    _case_file_banner(df)
    _investigation_route(df)
    st.subheader("Escalation Center")
    ncr_df = st.session_state[_state_key("ncr_df")]

    engine = st.session_state[_state_key("engine")]
    results = st.session_state[_state_key("results")]
    if st.button("Generate Escalation Records from Failed Features", type="primary"):
        if engine is None or results is None:
            _status_message("Draft NCR regeneration requires a fresh inspection run first.", "amber")
        else:
            ncr_df = generate_ncrs(results, engine.part_number, engine.part_name)
            ncr_df.to_csv(DRAFT_NCRS, index=False)
            st.session_state[_state_key("ncr_df")] = ncr_df
            _status_message(f"Escalation Records saved to `{DRAFT_NCRS}`", "green")

    if ncr_df is None or ncr_df.empty:
        failed_count = int((df["result"] == "FAIL").sum())
        if failed_count:
            _status_message("Failures exist, but draft NCRs are not loaded. Click Generate Escalation Records.", "amber")
        else:
            _status_message("No failed features detected, so no draft NCRs are required.", "green")
        return

    c1, c2, c3 = st.columns(3)
    with c1: _html_metric("Escalation Records", len(ncr_df), "Generated from failures", "red")
    with c2: _html_metric("Major Severity", int((ncr_df["severity"] == "Major").sum()), "MRB priority", "amber")
    with c3: _html_metric("CAPA Required", int((ncr_df["capa_required"] == "Yes").sum()), "High-criticality failures", "red")

    _status_message("Next step: go to Case Management and import `data/draft_ncrs.csv` to open formal investigations, containment actions, RCA, and CAPAs.", "blue")

    col1, col2 = st.columns(2)
    with col1:
        fc = ncr_df["feature_name"].value_counts().reset_index()
        fc.columns = ["Feature", "Escalation Records"]
        fig = px.bar(fc, x="Escalation Records", y="Feature", orientation="h", title="Escalation Records by Feature")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        sc = ncr_df["severity"].value_counts().reset_index()
        sc.columns = ["Severity", "Count"]
        fig = px.bar(sc, x="Severity", y="Count", title="Escalation Records by Severity")
        st.plotly_chart(fig, use_container_width=True)

    show = ["ncr_id", "part_serial_number", "lot_number", "feature_name", "gdandt_type", "severity", "deviation", "tolerance", "margin", "recommended_disposition", "capa_required", "due_date"]
    st.dataframe(ncr_df[[c for c in show if c in ncr_df.columns]], use_container_width=True, hide_index=True)
    st.download_button("Download draft_ncrs.csv", ncr_df.to_csv(index=False), file_name="draft_ncrs.csv", mime="text/csv", use_container_width=True)



def _case_file_banner(df: pd.DataFrame):
    total, passed, failed, pass_rate, failed_lots, failed_serials, worst_feature = _summary_metrics(df)
    status = "Evidence Escalation Required" if failed else "Evidence Review Clear"
    tone = "#842029" if failed else "#0f5132"
    bg = "#f8d7da" if failed else "#d1e7dd"
    case_id = f"CASE-GDT-{failed_lots:02d}{failed_serials:03d}" if failed else "CASE-GDT-CLEAR"
    st.markdown(
        f"""
        <div style="border:1px solid #e5e7eb;border-radius:16px;padding:18px 20px;background:{bg};margin-bottom:16px">
            <div style="font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:{tone};font-weight:800">Investigation Case File</div>
            <div style="font-size:24px;font-weight:850;color:{tone};margin-top:6px">{case_id}</div>
            <div style="font-size:13px;color:{tone};margin-top:6px;line-height:1.5">
                <b>Status:</b> {status} · <b>Worst signal:</b> {worst_feature} · <b>Failed features:</b> {failed:,} · <b>Pass rate:</b> {pass_rate}%
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _investigation_route(df: pd.DataFrame):
    total, passed, failed, pass_rate, failed_lots, failed_serials, worst_feature = _summary_metrics(df)
    if failed:
        msg = (
            f"<b>Recommended route:</b> Evidence Review → Root Cause Clues → Escalation Center → Case Management. "
            f"Focus first on <b>{worst_feature}</b>, then contain {failed_lots} affected lot(s) and {failed_serials} serial(s)."
        )
        _status_message(msg, "amber")
    else:
        _status_message("Recommended route: document evidence review and continue SPC monitoring. No NCR escalation is currently required.", "green")

def render():
    _init_state()
    _load_existing_outputs_if_available()

    if product_header:
        try:
            product_header("Evidence Review Center", "Analyze inspection evidence, validate quality signals, and determine whether escalation is required.")
        except TypeError:
            product_header("Evidence Review Center")
    else:
        st.title("Evidence Review Center")
        st.caption("Analyze inspection evidence, validate quality signals, and determine whether escalation is required.")

    st.markdown("""
    **Quality Detective role:** this is the evidence room. Use inspection results, true-position math, deviation margins, and failed-feature patterns to decide whether the issue needs formal NCR/CAPA escalation.

    This module reviews CMM / GD&T measurement evidence against engineering requirements, identifies failed features, quantifies deviation, produces an investigation report, and creates draft NCR records for escalation into Case Management.
    """)

    tabs = st.tabs([
        "1. Case Intake",
        "2. Evidence Summary",
        "3. Root Cause Clues",
        "4. Technical Evidence",
        "5. Case Report",
        "6. Escalation Center",
    ])

    with tabs[0]:
        _render_workflow_tab()
    with tabs[1]:
        _render_results_tab()
    with tabs[2]:
        _render_failure_tab()
    with tabs[3]:
        _render_technical_tab()
    with tabs[4]:
        _render_report_tab()
    with tabs[5]:
        _render_ncr_tab()
