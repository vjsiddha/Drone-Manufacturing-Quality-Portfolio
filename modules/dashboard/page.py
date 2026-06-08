
from pathlib import Path
from datetime import date
import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

try:
    from shared_styles import apply_styles, style_fig, kpi_card, alert, section, page_header, C
except Exception:
    C = {
        "text": "#F0F6FC", "subtle": "#C9D1D9", "muted": "#8B949E",
        "surface": "#161B22", "surface2": "#1C2128", "border": "#30363D",
        "border2": "#484F58", "grid": "#21262D", "plot_bg": "#0D1117",
        "green": "#3FB950", "red": "#F85149", "amber": "#D29922", "blue": "#58A6FF",
    }

    def apply_styles():
        return None

    def style_fig(fig, height=320):
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=C["plot_bg"], plot_bgcolor=C["plot_bg"],
            height=height, margin=dict(l=16, r=16, t=36, b=16),
            font=dict(family="Arial", size=11, color=C["subtle"]),
            xaxis=dict(gridcolor=C["grid"]), yaxis=dict(gridcolor=C["grid"]),
            legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        )
        return fig

    def kpi_card(label, value, color="", sub=""):
        color_map = {"green": C["green"], "red": C["red"], "amber": C["amber"], "blue": C["blue"]}
        val_color = color_map.get(color, C["text"])
        return f"""
        <div style="background:{C['surface']};border:1px solid {C['border']};border-radius:8px;padding:16px">
            <div style="font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:{C['muted']}">{label}</div>
            <div style="font-size:28px;font-weight:700;color:{val_color};margin:6px 0">{value}</div>
            <div style="font-size:12px;color:{C['muted']}">{sub}</div>
        </div>
        """

    def alert(text, variant="blue"):
        colors = {"green": C["green"], "red": C["red"], "amber": C["amber"], "blue": C["blue"]}
        color = colors.get(variant, C["blue"])
        return f"<div style='border-left:4px solid {color};background:{C['surface']};padding:12px 14px;border-radius:6px;color:{C['subtle']}'>{text}</div>"

    def section(title):
        return f"<div style='font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:{C['blue']};border-bottom:1px solid {C['border']};padding-bottom:8px;margin:16px 0'>{title}</div>"

    def page_header(title, subtitle=""):
        return f"<h1>{title}</h1><h4>{subtitle}</h4>"


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"
EXPORT_DIR = REPORTS_DIR / "dashboard_exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _read_csv(path: Path, parse_dates=None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, parse_dates=parse_dates)
    except Exception:
        return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_dashboard_data():
    insp = _read_csv(DATA_DIR / "inspection_records.csv", parse_dates=["date"])
    gdnt = _read_csv(DATA_DIR / "inspection_results.csv")
    prod = _read_csv(DATA_DIR / "production_records.csv", parse_dates=["date"])
    spc = _read_csv(DATA_DIR / "spc_measurements.csv", parse_dates=["date"])
    supps = _read_csv(DATA_DIR / "suppliers.csv")
    parts = _read_csv(DATA_DIR / "parts.csv")
    fmea = _read_csv(DATA_DIR / "propulsion_fmea.csv")

    ncr_csv = _read_csv(DATA_DIR / "ncr_records.csv", parse_dates=["date_opened", "date_closed"])
    ncr_db = pd.DataFrame()
    capa_db = pd.DataFrame()
    try:
        from modules.ncr_capa.database import init_db, get_all_ncrs, get_all_capas
        init_db()
        ncr_db = get_all_ncrs()
        capa_db = get_all_capas()
        for col in ["date_opened", "date_closed", "due_date"]:
            if col in ncr_db.columns:
                ncr_db[col] = pd.to_datetime(ncr_db[col], errors="coerce")
        for col in ["date_created", "due_date", "effectiveness_check_date"]:
            if col in capa_db.columns:
                capa_db[col] = pd.to_datetime(capa_db[col], errors="coerce")
    except Exception:
        pass

    ncr = ncr_db if not ncr_db.empty else ncr_csv

    if not insp.empty and not parts.empty and "part_number" in insp.columns:
        add_cols = [c for c in ["part_number", "part_name", "subsystem"] if c in parts.columns]
        insp = insp.merge(parts[add_cols], on="part_number", how="left")
    if not insp.empty and not supps.empty and "supplier_id" in insp.columns:
        add_cols = [c for c in ["supplier_id", "supplier_name"] if c in supps.columns]
        if "supplier_name" not in insp.columns:
            insp = insp.merge(supps[add_cols], on="supplier_id", how="left")

    if not ncr.empty and not supps.empty and "supplier_id" in ncr.columns and "supplier_name" not in ncr.columns:
        add_cols = [c for c in ["supplier_id", "supplier_name"] if c in supps.columns]
        ncr = ncr.merge(supps[add_cols], on="supplier_id", how="left")

    return insp, gdnt, prod, ncr, capa_db, spc, supps, parts, fmea


def _pct(num, den):
    import numpy as np
    import pandas as pd

    num_is_series = isinstance(num, pd.Series)
    den_is_series = isinstance(den, pd.Series)

    if num_is_series or den_is_series:
        num_s = pd.to_numeric(num, errors="coerce")
        den_s = pd.to_numeric(den, errors="coerce").replace(0, np.nan)
        return (num_s / den_s * 100).replace([np.inf, -np.inf], np.nan).fillna(0)

    try:
        num_v = float(num)
        den_v = float(den)
    except Exception:
        return 0.0

    if den_v == 0 or np.isnan(den_v):
        return 0.0

    return num_v / den_v * 100


def calc_fpy(prod):
    if prod.empty:
        return 0
    return _pct(prod["units_passed_first_time"].sum(), prod["units_completed"].sum())


def calc_defect_rate(insp, gdnt):
    if not insp.empty and {"quantity_failed", "quantity_inspected"}.issubset(insp.columns):
        return _pct(insp["quantity_failed"].sum(), insp["quantity_inspected"].sum())
    if not gdnt.empty and "result" in gdnt.columns:
        return _pct((gdnt["result"] == "FAIL").sum(), len(gdnt))
    return 0


def calc_scrap_rate(prod):
    if prod.empty:
        return 0
    return _pct(prod["units_scrapped"].sum(), prod["units_completed"].sum())


def calc_rework_rate(prod):
    if prod.empty:
        return 0
    return _pct(prod["units_reworked"].sum(), prod["units_completed"].sum())


def control_stats(values, lsl=None, usl=None):
    vals = pd.Series(values).dropna().astype(float)
    if vals.empty:
        return {"mean": 0, "std": 0, "ucl": 0, "lcl": 0, "cp": 0, "cpk": 0}
    mean = vals.mean()
    std = vals.std(ddof=1) if len(vals) > 1 else 0
    ucl = mean + 3 * std
    lcl = mean - 3 * std
    cp = np.nan
    cpk = np.nan
    if std and std > 0 and pd.notna(lsl) and pd.notna(usl):
        cp = (usl - lsl) / (6 * std)
        cpk = min((usl - mean) / (3 * std), (mean - lsl) / (3 * std))
    return {"mean": mean, "std": std, "ucl": ucl, "lcl": lcl, "cp": cp, "cpk": cpk}


def risk_color(value, good_threshold, warn_threshold, lower_is_better=False):
    if lower_is_better:
        return "green" if value <= good_threshold else ("amber" if value <= warn_threshold else "red")
    return "green" if value >= good_threshold else ("amber" if value >= warn_threshold else "red")


def lifecycle_summary(fmea, gdnt, ncr, capa, prod):
    rows = []
    if not fmea.empty:
        rows.append(("Risk Intelligence", len(fmea), f"{(fmea['rpn'] >= 150).sum() if 'rpn' in fmea.columns else 0} high-risk failure modes"))
    if not gdnt.empty:
        rows.append(("Evidence Review", len(gdnt), f"{(gdnt['result'] == 'FAIL').sum() if 'result' in gdnt.columns else 0} failed GD&T features"))
    if not ncr.empty:
        rows.append(("Case Management", len(ncr), f"{(ncr['status'].astype(str) != 'Closed').sum() if 'status' in ncr.columns else 0} open Cases"))
    if not capa.empty:
        status_col = "closure_status" if "closure_status" in capa.columns else "status"
        rows.append(("Corrective Action Verification", len(capa), f"{(capa[status_col].astype(str) == 'Closed').sum()} closed CAPAs"))
    if not prod.empty:
        rows.append(("Verification Monitoring", int(prod["units_completed"].sum()), f"{calc_fpy(prod):.1f}% FPY"))
    return pd.DataFrame(rows, columns=["Lifecycle Stage", "Records", "Signal"])


def render():
    apply_styles()
    st.markdown(page_header(
        "4. Verification & Monitoring Center",
        "Verify whether investigations and corrective actions actually improved process health, supplier performance, and SPC stability."
    ), unsafe_allow_html=True)

    st.markdown(
        alert(
            "<b>Quality Detective role:</b> this is the verification room. Use production KPIs, defect trends, supplier scorecards, NCR/CAPA aging, SPC capability, and improvement backlog data to confirm whether quality issues are contained, corrected, and staying fixed.",
            "blue",
        ),
        unsafe_allow_html=True,
    )

    insp_raw, gdnt_raw, prod_raw, ncr_raw, capa_raw, spc_raw, supps, parts, fmea_raw = load_dashboard_data()

    if prod_raw.empty and insp_raw.empty and spc_raw.empty and gdnt_raw.empty:
        st.warning("No quality monitoring data found. Add production_records.csv, inspection_records.csv, inspection_results.csv, and spc_measurements.csv to data/.")
        return

    st.markdown(section("Verification Route"), unsafe_allow_html=True)
    st.markdown("""
**Risk Intelligence** identifies the expected failure mode → **Evidence Review** confirms the defect → **Case Management** drives NCR/CAPA → **Verification & Monitoring** proves whether the corrective action worked.
""")

    # Date filters are shown inside this module instead of using another app-level sidebar.
    date_candidates = []
    for df, col in [(insp_raw, "date"), (prod_raw, "date"), (spc_raw, "date"), (ncr_raw, "date_opened")]:
        if not df.empty and col in df.columns:
            s = pd.to_datetime(df[col], errors="coerce").dropna()
            if not s.empty:
                date_candidates += [s.min().date(), s.max().date()]

    min_date = min(date_candidates) if date_candidates else date(2024, 1, 1)
    max_date = max(date_candidates) if date_candidates else date.today()

    with st.expander("Analytics Filters", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        date_range = c1.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        start_date = pd.Timestamp(date_range[0]) if isinstance(date_range, (list, tuple)) and len(date_range) > 0 else pd.Timestamp(min_date)
        end_date = pd.Timestamp(date_range[1]) if isinstance(date_range, (list, tuple)) and len(date_range) > 1 else pd.Timestamp(max_date)

        supplier_options = ["All"]
        if "supplier_name" in insp_raw.columns:
            supplier_options += sorted(insp_raw["supplier_name"].dropna().unique().tolist())
        elif "supplier_name" in ncr_raw.columns:
            supplier_options += sorted(ncr_raw["supplier_name"].dropna().unique().tolist())
        sel_supplier = c2.selectbox("Supplier", supplier_options)

        subsystem_options = ["All"]
        if "subsystem" in insp_raw.columns:
            subsystem_options += sorted(insp_raw["subsystem"].dropna().unique().tolist())
        elif "subsystem" in parts.columns:
            subsystem_options += sorted(parts["subsystem"].dropna().unique().tolist())
        sel_subsystem = c3.selectbox("Subsystem", subsystem_options)

        stage_options = ["All"] + (sorted(insp_raw["inspection_stage"].dropna().unique().tolist()) if "inspection_stage" in insp_raw.columns else [])
        sel_stage = c4.selectbox("Inspection stage", stage_options)

    def filter_by_date(df, col):
        if df.empty or col not in df.columns:
            return df
        x = df.copy()
        x[col] = pd.to_datetime(x[col], errors="coerce")
        return x[(x[col] >= start_date) & (x[col] <= end_date)]

    insp = filter_by_date(insp_raw, "date")
    prod = filter_by_date(prod_raw, "date")
    spc = filter_by_date(spc_raw, "date")
    ncr = filter_by_date(ncr_raw, "date_opened")

    if sel_supplier != "All":
        if "supplier_name" in insp.columns:
            insp = insp[insp["supplier_name"] == sel_supplier]
        if "supplier_name" in ncr.columns:
            ncr = ncr[ncr["supplier_name"] == sel_supplier]
    if sel_subsystem != "All" and "subsystem" in insp.columns:
        insp = insp[insp["subsystem"] == sel_subsystem]
    if sel_stage != "All" and "inspection_stage" in insp.columns:
        insp = insp[insp["inspection_stage"] == sel_stage]

    tab_overview, tab_prod, tab_supplier, tab_ncr, tab_spc, tab_ci = st.tabs([
        "Verification Overview",
        "Process Evidence",
        "Supplier Signals",
        "Case Effectiveness",
        "SPC Health",
        "Quality Detective Improvement Backlog"
    ])

    with tab_overview:
        overall_fpy = calc_fpy(prod)
        defect_rt = calc_defect_rate(insp, gdnt_raw)
        scrap_rt = calc_scrap_rate(prod)
        rework_rt = calc_rework_rate(prod)
        open_ncr = int((ncr["status"].astype(str) != "Closed").sum()) if not ncr.empty and "status" in ncr.columns else 0
        copq = float(insp["cost_impact"].sum()) if not insp.empty and "cost_impact" in insp.columns else 0
        avg_rpn = float(fmea_raw["rpn"].mean()) if not fmea_raw.empty and "rpn" in fmea_raw.columns else 0

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.markdown(kpi_card("First Pass Yield", f"{overall_fpy:.1f}%", risk_color(overall_fpy, 90, 80), "Target ≥ 90%"), unsafe_allow_html=True)
        c2.markdown(kpi_card("Defect Rate", f"{defect_rt:.2f}%", risk_color(defect_rt, 3, 6, True), "Target ≤ 3%"), unsafe_allow_html=True)
        c3.markdown(kpi_card("Scrap Rate", f"{scrap_rt:.2f}%", risk_color(scrap_rt, 2, 5, True), "Target ≤ 2%"), unsafe_allow_html=True)
        c4.markdown(kpi_card("Rework Rate", f"{rework_rt:.2f}%", risk_color(rework_rt, 5, 10, True), "Target ≤ 5%"), unsafe_allow_html=True)
        c5.markdown(kpi_card("Open Cases", f"{open_ncr}", risk_color(open_ncr, 20, 50, True), "Active cases"), unsafe_allow_html=True)
        c6.markdown(kpi_card("Avg RPN", f"{avg_rpn:.1f}", risk_color(avg_rpn, 80, 130, True), "Design/process risk"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        signals = []
        if not insp.empty and "supplier_name" in insp.columns and {"quantity_failed", "quantity_inspected"}.issubset(insp.columns):
            sup_defect = insp.groupby("supplier_name").apply(lambda x: _pct(x["quantity_failed"].sum(), x["quantity_inspected"].sum())).sort_values(ascending=False)
            if not sup_defect.empty:
                signals.append(("red", f"Worst supplier: <b>{sup_defect.index[0]}</b> — {sup_defect.iloc[0]:.1f}% defect rate"))
        if not prod.empty and "station_name" in prod.columns:
            station_fpy = prod.groupby("station_name").apply(lambda x: _pct(x["units_passed_first_time"].sum(), x["units_completed"].sum())).sort_values()
            if not station_fpy.empty:
                signals.append(("amber", f"Lowest FPY station: <b>{station_fpy.index[0]}</b> — {station_fpy.iloc[0]:.1f}% FPY"))
        if not signals:
            signals.append(("blue", "Quality system data loaded. Use filters to drill into supplier, station, and inspection performance."))

        cols = st.columns(len(signals))
        for col, (variant, text) in zip(cols, signals):
            col.markdown(alert(text, variant), unsafe_allow_html=True)

        st.markdown(section("Investigation Signal Map"), unsafe_allow_html=True)
        st.dataframe(lifecycle_summary(fmea_raw, gdnt_raw, ncr, capa_raw, prod), use_container_width=True, hide_index=True)

        st.markdown(section("Verification Trends"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            if not prod.empty and "date" in prod.columns:
                tmp = prod.copy()
                tmp["month"] = pd.to_datetime(tmp["date"], errors="coerce").dt.to_period("M").astype(str)
                trend = tmp.groupby("month").apply(lambda x: _pct(x["units_passed_first_time"].sum(), x["units_completed"].sum())).reset_index(name="FPY %")
                fig = px.line(trend, x="month", y="FPY %", markers=True, title="First Pass Yield — Monthly")
                fig.add_hline(y=90, line_dash="dot", line_color=C["red"], annotation_text="90% target")
                fig.update_yaxes(range=[max(0, trend["FPY %"].min() - 5), 100])
                st.plotly_chart(style_fig(fig, 330), use_container_width=True)
        with col2:
            if not insp.empty and "date" in insp.columns and {"quantity_failed", "quantity_inspected"}.issubset(insp.columns):
                tmp = insp.copy()
                tmp["month"] = pd.to_datetime(tmp["date"], errors="coerce").dt.to_period("M").astype(str)
                trend = tmp.groupby("month").apply(lambda x: _pct(x["quantity_failed"].sum(), x["quantity_inspected"].sum())).reset_index(name="Defect Rate %")
                fig = px.line(trend, x="month", y="Defect Rate %", markers=True, title="Defect Rate — Monthly")
                fig.add_hline(y=3, line_dash="dot", line_color=C["amber"], annotation_text="3% target")
                st.plotly_chart(style_fig(fig, 330), use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            if not ncr.empty and "date_opened" in ncr.columns:
                tmp = ncr.copy()
                tmp["month"] = pd.to_datetime(tmp["date_opened"], errors="coerce").dt.to_period("M").astype(str)
                trend = tmp.groupby("month").size().reset_index(name="Cases")
                fig = px.bar(trend, x="month", y="Cases", title="Case Creation Trend")
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(style_fig(fig, 300), use_container_width=True)
        with col4:
            if not insp.empty and "cost_impact" in insp.columns:
                tmp = insp.copy()
                tmp["month"] = pd.to_datetime(tmp["date"], errors="coerce").dt.to_period("M").astype(str)
                trend = tmp.groupby("month")["cost_impact"].sum().reset_index()
                fig = px.area(trend, x="month", y="cost_impact", title="Cost of Poor Quality")
                fig.update_yaxes(title="Cost ($)")
                st.plotly_chart(style_fig(fig, 300), use_container_width=True)

    with tab_prod:
        st.markdown(section("Process Evidence by Station"), unsafe_allow_html=True)
        if not prod.empty and "station_name" in prod.columns:
            station = prod.groupby("station_name").agg(
                units_completed=("units_completed", "sum"),
                units_passed=("units_passed_first_time", "sum"),
                units_reworked=("units_reworked", "sum"),
                units_scrapped=("units_scrapped", "sum"),
                avg_cycle=("cycle_time_minutes", "mean"),
            ).reset_index()
            station["fpy"] = _pct(station["units_passed"], station["units_completed"])
            station["rework_rate"] = _pct(station["units_reworked"], station["units_completed"])
            station["scrap_rate"] = _pct(station["units_scrapped"], station["units_completed"])
            station = station.sort_values("fpy")

            if not station.empty:
                st.markdown(alert(f"Bottleneck station: <b>{station.iloc[0]['station_name']}</b> — {station.iloc[0]['fpy']:.1f}% FPY.", "red"), unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure(go.Bar(
                    x=station["fpy"], y=station["station_name"], orientation="h",
                    text=station["fpy"].round(1).astype(str) + "%",
                    textposition="outside"
                ))
                fig.add_vline(x=90, line_dash="dot", line_color=C["red"], annotation_text="90% target")
                fig.update_xaxes(range=[max(0, station["fpy"].min() - 10), 105], title="FPY %")
                fig.update_yaxes(title="")
                st.plotly_chart(style_fig(fig, 350), use_container_width=True)
            with col2:
                long = station.melt(id_vars="station_name", value_vars=["rework_rate", "scrap_rate"], var_name="Metric", value_name="Rate %")
                fig = px.bar(long, x="station_name", y="Rate %", color="Metric", barmode="group", title="Rework and Scrap by Station")
                fig.update_xaxes(tickangle=-30)
                st.plotly_chart(style_fig(fig, 350), use_container_width=True)

            st.dataframe(station.rename(columns={
                "station_name": "Station", "units_completed": "Completed", "units_passed": "First-Time Pass",
                "units_reworked": "Reworked", "units_scrapped": "Scrapped", "avg_cycle": "Avg Cycle (min)",
                "fpy": "FPY %", "rework_rate": "Rework %", "scrap_rate": "Scrap %"
            }).style.format({"FPY %": "{:.1f}", "Rework %": "{:.1f}", "Scrap %": "{:.1f}", "Avg Cycle (min)": "{:.1f}"}), use_container_width=True)

        st.markdown(section("Defect Evidence Pareto"), unsafe_allow_html=True)
        if not insp.empty and "quantity_failed" in insp.columns and "defect_type" in insp.columns:
            failed = insp[insp["quantity_failed"] > 0].copy()
            if not failed.empty:
                dc = failed.groupby("defect_type")["quantity_failed"].sum().sort_values(ascending=False).reset_index()
                dc["cum_pct"] = dc["quantity_failed"].cumsum() / dc["quantity_failed"].sum() * 100

                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x=dc["defect_type"], y=dc["quantity_failed"], name="Failed Units"), secondary_y=False)
                fig.add_trace(go.Scatter(x=dc["defect_type"], y=dc["cum_pct"], name="Cumulative %", mode="lines+markers"), secondary_y=True)
                fig.add_hline(y=80, line_dash="dot", line_color=C["border2"], secondary_y=True, annotation_text="80%")
                fig.update_xaxes(tickangle=-35)
                fig.update_yaxes(title_text="Failed Units", secondary_y=False)
                fig.update_yaxes(title_text="Cumulative %", range=[0, 105], secondary_y=True)
                st.plotly_chart(style_fig(fig, 420), use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    if "defect_category" in failed.columns:
                        cat = failed.groupby("defect_category")["quantity_failed"].sum().sort_values().reset_index()
                        fig = px.bar(cat, x="quantity_failed", y="defect_category", orientation="h", title="Failures by Category")
                        st.plotly_chart(style_fig(fig, 300), use_container_width=True)
                with col2:
                    if "subsystem" in failed.columns:
                        sub = failed.groupby("subsystem")["quantity_failed"].sum().sort_values().reset_index()
                        fig = px.bar(sub, x="quantity_failed", y="subsystem", orientation="h", title="Failures by Subsystem")
                        st.plotly_chart(style_fig(fig, 300), use_container_width=True)

                st.dataframe(dc.head(10).rename(columns={"defect_type": "Defect Type", "quantity_failed": "Failed Units", "cum_pct": "Cumulative %"}).style.format({"Cumulative %": "{:.1f}%"}), use_container_width=True)
            else:
                st.success("No defects in selected filter range.")
        elif not gdnt_raw.empty and "result" in gdnt_raw.columns:
            failed = gdnt_raw[gdnt_raw["result"] == "FAIL"]
            dc = failed["feature_name"].value_counts().head(10).reset_index()
            dc.columns = ["Feature", "Failures"]
            fig = px.bar(dc, x="Failures", y="Feature", orientation="h", title="GD&T Failure Pareto")
            st.plotly_chart(style_fig(fig, 360), use_container_width=True)

    with tab_supplier:
        st.markdown(section("Supplier Signal Scorecard"), unsafe_allow_html=True)
        if not insp.empty and "supplier_name" in insp.columns and {"quantity_inspected", "quantity_failed"}.issubset(insp.columns):
            sup = insp.groupby(["supplier_id", "supplier_name"], dropna=False).agg(
                qty_inspected=("quantity_inspected", "sum"),
                qty_failed=("quantity_failed", "sum"),
                cost_impact=("cost_impact", "sum") if "cost_impact" in insp.columns else ("quantity_failed", "sum"),
                ncr_count=("ncr_id", lambda x: x.notna().sum()) if "ncr_id" in insp.columns else ("quantity_failed", "sum"),
            ).reset_index()
            sup["rejection_rate"] = _pct(sup["qty_failed"], sup["qty_inspected"])
            max_rej = sup["rejection_rate"].max() or 1
            max_cost = sup["cost_impact"].max() or 1
            sup["score"] = (100 - sup["rejection_rate"] / max_rej * 35 - sup["cost_impact"] / max_cost * 25 - sup["ncr_count"] / (sup["ncr_count"].max() or 1) * 15).clip(0, 100).round(1)
            sup["grade"] = pd.cut(sup["score"], bins=[-1, 70, 80, 90, 100], labels=["D", "C", "B", "A"])
            sup = sup.sort_values("score", ascending=False)

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(sup.sort_values("rejection_rate"), x="rejection_rate", y="supplier_name", orientation="h", title="Rejection Rate by Supplier")
                fig.add_vline(x=5, line_dash="dot", line_color=C["red"], annotation_text="5% threshold")
                st.plotly_chart(style_fig(fig, 380), use_container_width=True)
            with col2:
                fig = px.scatter(sup, x="rejection_rate", y="cost_impact", size="ncr_count", color="grade", hover_name="supplier_name", title="Supplier Risk Map")
                fig.add_vline(x=5, line_dash="dot", line_color=C["border2"])
                st.plotly_chart(style_fig(fig, 380), use_container_width=True)

            show = sup[["supplier_name", "score", "grade", "rejection_rate", "qty_failed", "ncr_count", "cost_impact"]].copy()
            show.columns = ["Supplier", "Score", "Grade", "Rejection Rate %", "Failed Units", "Case Count", "Cost Impact"]
            st.dataframe(show.style.format({"Score": "{:.1f}", "Rejection Rate %": "{:.2f}", "Cost Impact": "${:,.0f}"}), use_container_width=True, hide_index=True)
        else:
            st.info("Supplier analytics require inspection_records.csv with supplier_name/supplier_id, quantity_inspected, and quantity_failed.")

    with tab_ncr:
        st.markdown(section("Case and Corrective Action Effectiveness"), unsafe_allow_html=True)
        if not ncr.empty:
            status_col = "status" if "status" in ncr.columns else None
            sev_col = "severity" if "severity" in ncr.columns else None
            c1, c2, c3, c4 = st.columns(4)
            total = len(ncr)
            open_count = int((ncr[status_col].astype(str) != "Closed").sum()) if status_col else 0
            critical = int((ncr[sev_col].astype(str) == "Critical").sum()) if sev_col else 0
            overdue = 0
            if "due_date" in ncr.columns and status_col:
                overdue = int(((pd.to_datetime(ncr["due_date"], errors="coerce").dt.date < date.today()) & (ncr[status_col].astype(str) != "Closed")).sum())
            c1.markdown(kpi_card("Total Cases", total, "blue"), unsafe_allow_html=True)
            c2.markdown(kpi_card("Open Cases", open_count, risk_color(open_count, 20, 50, True)), unsafe_allow_html=True)
            c3.markdown(kpi_card("Critical", critical, risk_color(critical, 3, 8, True)), unsafe_allow_html=True)
            c4.markdown(kpi_card("Overdue", overdue, risk_color(overdue, 3, 8, True)), unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if status_col:
                    sc = ncr[status_col].value_counts().reset_index()
                    sc.columns = ["Status", "Count"]
                    fig = px.bar(sc, x="Status", y="Count", title="Case Status Distribution")
                    fig.update_xaxes(tickangle=-25)
                    st.plotly_chart(style_fig(fig, 320), use_container_width=True)
            with col2:
                if sev_col:
                    sv = ncr[sev_col].value_counts().reset_index()
                    sv.columns = ["Severity", "Count"]
                    fig = px.bar(sv, x="Severity", y="Count", title="Case Severity Breakdown")
                    st.plotly_chart(style_fig(fig, 320), use_container_width=True)

            if "date_opened" in ncr.columns:
                age = ncr.copy()
                age["age_days"] = (pd.Timestamp.today() - pd.to_datetime(age["date_opened"], errors="coerce")).dt.days
                if status_col:
                    age = age[age[status_col].astype(str) != "Closed"]
                if not age.empty:
                    fig = px.histogram(age, x="age_days", nbins=20, title="Open Case Aging")
                    fig.add_vline(x=30, line_dash="dot", line_color=C["red"], annotation_text="30d")
                    st.plotly_chart(style_fig(fig, 280), use_container_width=True)

            show_cols = [c for c in ["ncr_id", "date_opened", "part_number", "supplier_name", "defect_type", "severity", "status", "owner", "due_date"] if c in ncr.columns]
            if show_cols:
                st.dataframe(ncr[show_cols].head(200), use_container_width=True, hide_index=True)
        else:
            st.info("No NCR records found in the integrated NCR/CAPA database or ncr_records.csv.")

        if not capa_raw.empty:
            st.markdown(section("CAPA Closure Performance"), unsafe_allow_html=True)
            status_col = "closure_status" if "closure_status" in capa_raw.columns else "status" if "status" in capa_raw.columns else None
            if status_col:
                cs = capa_raw[status_col].value_counts().reset_index()
                cs.columns = ["CAPA Status", "Count"]
                fig = px.bar(cs, x="CAPA Status", y="Count", title="CAPA Closure Status")
                st.plotly_chart(style_fig(fig, 280), use_container_width=True)
                st.dataframe(capa_raw[[c for c in ["capa_id", "linked_ncr_id", "date_created", "action_owner", "due_date", status_col, "verification_method"] if c in capa_raw.columns]].head(200), use_container_width=True, hide_index=True)

    with tab_spc:
        st.markdown(section("SPC Health Center"), unsafe_allow_html=True)
        if spc.empty:
            st.info("No spc_measurements.csv found.")
        else:
            feature_options = sorted(spc["feature_name"].dropna().unique().tolist()) if "feature_name" in spc.columns else []
            selected_feature = st.selectbox("SPC Feature", feature_options) if feature_options else None
            view = spc[spc["feature_name"] == selected_feature].copy() if selected_feature else spc.copy()

            if not view.empty and "measured_value" in view.columns:
                lsl = view["lsl"].dropna().iloc[0] if "lsl" in view.columns and view["lsl"].notna().any() else None
                usl = view["usl"].dropna().iloc[0] if "usl" in view.columns and view["usl"].notna().any() else None
                nominal = view["nominal"].dropna().iloc[0] if "nominal" in view.columns and view["nominal"].notna().any() else None
                stats = control_stats(view["measured_value"], lsl, usl)
                out_of_spec_pct = view["out_of_spec"].mean() * 100 if "out_of_spec" in view.columns else 0

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.markdown(kpi_card("Mean", f"{stats['mean']:.4f}", "blue", f"Nominal {nominal}" if nominal is not None else ""), unsafe_allow_html=True)
                c2.markdown(kpi_card("Std Dev", f"{stats['std']:.4f}", "blue"), unsafe_allow_html=True)
                c3.markdown(kpi_card("Cp", f"{stats['cp']:.2f}" if pd.notna(stats["cp"]) else "N/A", risk_color(stats["cp"] if pd.notna(stats["cp"]) else 0, 1.33, 1.0)), unsafe_allow_html=True)
                c4.markdown(kpi_card("Cpk", f"{stats['cpk']:.2f}" if pd.notna(stats["cpk"]) else "N/A", risk_color(stats["cpk"] if pd.notna(stats["cpk"]) else 0, 1.33, 1.0)), unsafe_allow_html=True)
                c5.markdown(kpi_card("Out of Spec", f"{out_of_spec_pct:.2f}%", risk_color(out_of_spec_pct, 1, 3, True)), unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                chart_df = view.sort_values(["date", "subgroup_id", "sample_number"] if {"date", "subgroup_id", "sample_number"}.issubset(view.columns) else view.index.name or "measurement_id").reset_index(drop=True)
                chart_df["sequence"] = np.arange(1, len(chart_df) + 1)

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=chart_df["sequence"], y=chart_df["measured_value"], mode="lines+markers", name="Measured"))
                fig.add_hline(y=stats["mean"], line_dash="solid", line_color=C["blue"], annotation_text="Mean")
                fig.add_hline(y=stats["ucl"], line_dash="dot", line_color=C["amber"], annotation_text="UCL")
                fig.add_hline(y=stats["lcl"], line_dash="dot", line_color=C["amber"], annotation_text="LCL")
                if usl is not None:
                    fig.add_hline(y=usl, line_dash="dash", line_color=C["red"], annotation_text="USL")
                if lsl is not None:
                    fig.add_hline(y=lsl, line_dash="dash", line_color=C["red"], annotation_text="LSL")
                fig.update_layout(title=f"Control Chart — {selected_feature or 'Measurement'}")
                fig.update_xaxes(title="Measurement Sequence")
                fig.update_yaxes(title=f"Measured Value ({view['unit'].iloc[0] if 'unit' in view.columns else ''})")
                st.plotly_chart(style_fig(fig, 430), use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    fig = px.histogram(view, x="measured_value", nbins=30, title="Distribution vs Specification")
                    if lsl is not None:
                        fig.add_vline(x=lsl, line_dash="dash", line_color=C["red"], annotation_text="LSL")
                    if usl is not None:
                        fig.add_vline(x=usl, line_dash="dash", line_color=C["red"], annotation_text="USL")
                    if nominal is not None:
                        fig.add_vline(x=nominal, line_dash="dot", line_color=C["blue"], annotation_text="Nominal")
                    st.plotly_chart(style_fig(fig, 320), use_container_width=True)
                with col2:
                    if "subgroup_id" in view.columns:
                        sub = view.groupby("subgroup_id").agg(xbar=("measured_value", "mean"), rng=("measured_value", lambda x: x.max() - x.min())).reset_index()
                        fig = px.line(sub, x="subgroup_id", y="xbar", markers=True, title="Subgroup X-bar Trend")
                        fig.add_hline(y=stats["mean"], line_dash="dot", line_color=C["blue"])
                        st.plotly_chart(style_fig(fig, 320), use_container_width=True)

                st.markdown(section("Capability by Feature"), unsafe_allow_html=True)
                rows = []
                for fname, g in spc.groupby("feature_name") if "feature_name" in spc.columns else [("All", spc)]:
                    glsl = g["lsl"].dropna().iloc[0] if "lsl" in g.columns and g["lsl"].notna().any() else None
                    gusl = g["usl"].dropna().iloc[0] if "usl" in g.columns and g["usl"].notna().any() else None
                    gs = control_stats(g["measured_value"], glsl, gusl)
                    rows.append({
                        "Feature": fname,
                        "Mean": gs["mean"],
                        "Std Dev": gs["std"],
                        "Cp": gs["cp"],
                        "Cpk": gs["cpk"],
                        "Out-of-Spec %": g["out_of_spec"].mean() * 100 if "out_of_spec" in g.columns else 0,
                        "Status": "Capable" if pd.notna(gs["cpk"]) and gs["cpk"] >= 1.33 else ("Marginal" if pd.notna(gs["cpk"]) and gs["cpk"] >= 1.0 else "Not Capable"),
                    })
                cap_df = pd.DataFrame(rows).sort_values("Cpk")
                st.dataframe(cap_df.style.format({"Mean": "{:.4f}", "Std Dev": "{:.4f}", "Cp": "{:.2f}", "Cpk": "{:.2f}", "Out-of-Spec %": "{:.2f}%"}), use_container_width=True, hide_index=True)

    with tab_ci:
        st.markdown(section("Improvement Verification"), unsafe_allow_html=True)
        st.markdown(alert("This view closes the investigation loop by connecting risk signals, evidence review, case management, corrective actions, and process monitoring into one verification workflow.", "blue"), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if not fmea_raw.empty and {"rpn", "revised_rpn", "failure_mode"}.issubset(fmea_raw.columns):
                fmea = fmea_raw.copy()
                fmea["rpn_reduction"] = fmea["rpn"] - fmea["revised_rpn"]
                top = fmea.sort_values("rpn_reduction", ascending=False).head(10)
                fig = px.bar(top, x="rpn_reduction", y="failure_mode", orientation="h", title="Largest FMEA Risk Reductions")
                fig.update_yaxes(title="")
                st.plotly_chart(style_fig(fig, 380), use_container_width=True)
        with col2:
            if not prod.empty and "date" in prod.columns:
                tmp = prod.copy()
                tmp["month"] = pd.to_datetime(tmp["date"], errors="coerce").dt.to_period("M").astype(str)
                trend = tmp.groupby("month").apply(lambda x: _pct(x["units_passed_first_time"].sum(), x["units_completed"].sum())).reset_index(name="fpy")
                if len(trend) >= 2:
                    first = trend.iloc[:max(1, len(trend)//4)]["fpy"].mean()
                    last = trend.iloc[-max(1, len(trend)//4):]["fpy"].mean()
                    improvement = last - first
                    st.markdown(kpi_card("FPY Improvement", f"{improvement:+.1f} pts", "green" if improvement >= 0 else "red", "Latest period vs earliest period"), unsafe_allow_html=True)
                fig = px.line(trend, x="month", y="fpy", markers=True, title="FPY Improvement Trend")
                fig.add_hline(y=90, line_dash="dot", line_color=C["red"])
                st.plotly_chart(style_fig(fig, 315), use_container_width=True)

        st.markdown(section("Quality Detective Improvement Backlog"), unsafe_allow_html=True)
        backlog_frames = []
        if not fmea_raw.empty and {"fmea_id", "component", "failure_mode", "recommended_action", "action_owner", "target_completion_date", "status", "rpn"}.issubset(fmea_raw.columns):
            f = fmea_raw[["fmea_id", "component", "failure_mode", "recommended_action", "action_owner", "target_completion_date", "status", "rpn"]].copy()
            f.columns = ["ID", "Area", "Issue", "Action", "Owner", "Due Date", "Status", "Priority"]
            f["Source"] = "FMEA"
            backlog_frames.append(f)
        if not ncr.empty and {"ncr_id", "defect_type", "owner", "due_date", "status"}.issubset(ncr.columns):
            n = ncr[ncr["status"].astype(str) != "Closed"].copy()
            n["Area"] = n["part_number"] if "part_number" in n.columns else "NCR"
            n["Action"] = "Complete containment, RCA, disposition, and CAPA decision"
            n["Priority"] = n["severity"].map({"Critical": 300, "Major": 200, "Minor": 100}) if "severity" in n.columns else 100
            n = n.rename(columns={"ncr_id": "ID", "defect_type": "Issue", "owner": "Owner", "due_date": "Due Date", "status": "Status"})
            n["Source"] = "NCR"
            backlog_frames.append(n[["ID", "Area", "Issue", "Action", "Owner", "Due Date", "Status", "Priority", "Source"]])

        if backlog_frames:
            backlog = pd.concat(backlog_frames, ignore_index=True, sort=False)
            backlog = backlog.sort_values("Priority", ascending=False)
            st.dataframe(backlog.head(100), use_container_width=True, hide_index=True)
            export_path = EXPORT_DIR / "continuous_improvement_backlog.csv"
            backlog.to_csv(export_path, index=False)
            st.download_button("Download Quality Detective Improvement Backlog", data=backlog.to_csv(index=False), file_name="continuous_improvement_backlog.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("No FMEA or NCR backlog items available.")
