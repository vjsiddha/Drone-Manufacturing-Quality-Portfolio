"""
Drone Manufacturing Quality Dashboard
======================================
Python + Streamlit + Pandas + Plotly

Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, date

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Drone MFG Quality Dashboard",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

    .main { background-color: #0d1117; }

    .kpi-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px 24px;
        text-align: center;
        transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: #58a6ff; }
    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #8b949e;
        font-family: 'IBM Plex Mono', monospace;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 600;
        color: #f0f6fc;
        margin: 6px 0 2px;
        font-family: 'IBM Plex Mono', monospace;
    }
    .kpi-value.red   { color: #f85149; }
    .kpi-value.green { color: #3fb950; }
    .kpi-value.amber { color: #d29922; }
    .kpi-delta {
        font-size: 11px;
        color: #8b949e;
        font-family: 'IBM Plex Mono', monospace;
    }

    div[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; }

    .section-header {
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #58a6ff;
        font-family: 'IBM Plex Mono', monospace;
        border-bottom: 1px solid #21262d;
        padding-bottom: 8px;
        margin-bottom: 16px;
        margin-top: 8px;
    }
    .insight-box {
        background: #161b22;
        border-left: 3px solid #58a6ff;
        border-radius: 0 6px 6px 0;
        padding: 12px 16px;
        font-size: 13px;
        color: #c9d1d9;
        margin-bottom: 8px;
    }
    .insight-box.red  { border-left-color: #f85149; }
    .insight-box.green { border-left-color: #3fb950; }
    .insight-box.amber { border-left-color: #d29922; }
</style>
""", unsafe_allow_html=True)

PLOT_TEMPLATE = "plotly_dark"
PLOT_BG = "#0d1117"
PAPER_BG = "#0d1117"
GRID_COLOR = "#21262d"
ACCENT = "#58a6ff"
RED = "#f85149"
GREEN = "#3fb950"
AMBER = "#d29922"

# ─── LOAD DATA ──────────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

@st.cache_data
def load_data():
    insp   = pd.read_csv(f"{DATA_DIR}/inspection_records.csv", parse_dates=["date"])
    prod   = pd.read_csv(f"{DATA_DIR}/production_records.csv", parse_dates=["date"])
    ncr    = pd.read_csv(f"{DATA_DIR}/ncr_records.csv",        parse_dates=["date_opened","date_closed"])
    supps  = pd.read_csv(f"{DATA_DIR}/suppliers.csv")
    parts  = pd.read_csv(f"{DATA_DIR}/parts.csv")

    insp = insp.merge(parts[["part_number","part_name","subsystem"]], on="part_number", how="left")
    insp = insp.merge(supps[["supplier_id","supplier_name"]], on="supplier_id", how="left")
    ncr  = ncr.merge(supps[["supplier_id","supplier_name"]], on="supplier_id", how="left")

    return insp, prod, ncr, supps, parts

insp_raw, prod_raw, ncr_raw, supps, parts = load_data()

# ─── SIDEBAR FILTERS ────────────────────────────────────────────────────────

st.sidebar.markdown("## 🚁 Quality Dashboard")
st.sidebar.markdown("---")

min_date = insp_raw["date"].min().date()
max_date = insp_raw["date"].max().date()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
start_date = pd.Timestamp(date_range[0]) if len(date_range) > 0 else pd.Timestamp(min_date)
end_date   = pd.Timestamp(date_range[1]) if len(date_range) > 1 else pd.Timestamp(max_date)

supplier_options = ["All"] + sorted(supps["supplier_name"].tolist())
sel_supplier = st.sidebar.selectbox("Supplier", supplier_options)

subsystem_options = ["All"] + sorted(parts["subsystem"].dropna().unique().tolist())
sel_subsystem = st.sidebar.selectbox("Subsystem", subsystem_options)

stage_options = ["All"] + sorted(insp_raw["inspection_stage"].dropna().unique().tolist())
sel_stage = st.sidebar.selectbox("Inspection Stage", stage_options)

defect_cat_options = ["All"] + sorted(insp_raw["defect_category"].dropna().unique().tolist())
sel_defect_cat = st.sidebar.selectbox("Defect Category", defect_cat_options)

severity_options = ["All"] + sorted(ncr_raw["severity"].dropna().unique().tolist())
sel_severity = st.sidebar.selectbox("NCR Severity", severity_options)

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["Executive Overview", "Defect Pareto Analysis", "Supplier Quality",
     "Station Quality", "NCR Overview"],
    label_visibility="collapsed"
)

# ─── APPLY FILTERS ──────────────────────────────────────────────────────────

def filter_insp(df):
    d = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    if sel_supplier != "All":
        d = d[d["supplier_name"] == sel_supplier]
    if sel_subsystem != "All":
        d = d[d["subsystem"] == sel_subsystem]
    if sel_stage != "All":
        d = d[d["inspection_stage"] == sel_stage]
    if sel_defect_cat != "All":
        d = d[d["defect_category"] == sel_defect_cat]
    return d

def filter_prod(df):
    return df[(df["date"] >= start_date) & (df["date"] <= end_date)]

def filter_ncr(df):
    d = df[(df["date_opened"] >= start_date) & (df["date_opened"] <= end_date)]
    if sel_supplier != "All":
        d = d[d["supplier_name"] == sel_supplier]
    if sel_severity != "All":
        d = d[d["severity"] == sel_severity]
    return d

insp = filter_insp(insp_raw)
prod = filter_prod(prod_raw)
ncr  = filter_ncr(ncr_raw)

# ─── METRIC CALCULATIONS ────────────────────────────────────────────────────

def calc_fpy(df):
    total = df["units_completed"].sum()
    passed = df["units_passed_first_time"].sum()
    return (passed / total * 100) if total > 0 else 0

def calc_defect_rate(df):
    total_insp = df["quantity_inspected"].sum()
    total_fail = df["quantity_failed"].sum()
    return (total_fail / total_insp * 100) if total_insp > 0 else 0

def calc_scrap_rate(df):
    total = df["units_completed"].sum()
    scrapped = df["units_scrapped"].sum()
    return (scrapped / total * 100) if total > 0 else 0

def calc_rework_rate(df):
    total = df["units_completed"].sum()
    rework = df["units_reworked"].sum()
    return (rework / total * 100) if total > 0 else 0

overall_fpy       = calc_fpy(prod)
overall_defect_rt = calc_defect_rate(insp)
overall_scrap_rt  = calc_scrap_rate(prod)
overall_rework_rt = calc_rework_rate(prod)
open_ncr_count    = (ncr["status"] != "Closed").sum()
cost_of_pq        = insp["cost_impact"].sum()

# Worst supplier
sup_defect = (
    insp.groupby("supplier_name")
    .apply(lambda x: x["quantity_failed"].sum() / x["quantity_inspected"].sum() * 100 if x["quantity_inspected"].sum() > 0 else 0)
    .sort_values(ascending=False)
)
worst_supplier = sup_defect.index[0] if len(sup_defect) > 0 else "N/A"

# Worst station
st_fpy = (
    prod.groupby("station_name")
    .apply(lambda x: x["units_passed_first_time"].sum() / x["units_completed"].sum() * 100 if x["units_completed"].sum() > 0 else 0)
    .sort_values()
)
worst_station = st_fpy.index[0] if len(st_fpy) > 0 else "N/A"

# ─── CHART HELPERS ──────────────────────────────────────────────────────────

def style_fig(fig, height=320):
    fig.update_layout(
        template=PLOT_TEMPLATE,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        height=height,
        margin=dict(l=16, r=16, t=36, b=16),
        font=dict(family="IBM Plex Mono", size=11, color="#c9d1d9"),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
    )
    return fig

def kpi_card(label, value, color="", delta=""):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {color}">{value}</div>
        <div class="kpi-delta">{delta}</div>
    </div>
    """

# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 1 — EXECUTIVE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

if page == "Executive Overview":
    st.markdown("## 🚁 Executive Quality Overview")
    st.markdown("Drone Manufacturing — Production Quality KPIs")
    st.markdown("---")

    # KPI Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    fpy_color  = "green" if overall_fpy >= 90 else ("amber" if overall_fpy >= 80 else "red")
    dr_color   = "green" if overall_defect_rt <= 3 else ("amber" if overall_defect_rt <= 6 else "red")
    sc_color   = "green" if overall_scrap_rt <= 2 else ("amber" if overall_scrap_rt <= 5 else "red")
    rw_color   = "green" if overall_rework_rt <= 5 else ("amber" if overall_rework_rt <= 10 else "red")
    ncr_color  = "green" if open_ncr_count <= 20 else ("amber" if open_ncr_count <= 50 else "red")
    copq_color = "green" if cost_of_pq < 50000 else ("amber" if cost_of_pq < 200000 else "red")

    c1.markdown(kpi_card("First Pass Yield",    f"{overall_fpy:.1f}%",        fpy_color,  "Target ≥ 90%"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Defect Rate",         f"{overall_defect_rt:.2f}%",  dr_color,   "Target ≤ 3%"),  unsafe_allow_html=True)
    c3.markdown(kpi_card("Scrap Rate",          f"{overall_scrap_rt:.2f}%",   sc_color,   "Target ≤ 2%"),  unsafe_allow_html=True)
    c4.markdown(kpi_card("Rework Rate",         f"{overall_rework_rt:.2f}%",  rw_color,   "Target ≤ 5%"),  unsafe_allow_html=True)
    c5.markdown(kpi_card("Open NCRs",           str(int(open_ncr_count)),      ncr_color,  "Active issues"), unsafe_allow_html=True)
    c6.markdown(kpi_card("Cost of Poor Quality", f"${cost_of_pq:,.0f}",       copq_color, "Inspection window"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Worst-performer banners
    col_a, col_b = st.columns(2)
    col_a.markdown(f'<div class="insight-box red">⚠️ <b>Worst Supplier:</b> {worst_supplier} — {sup_defect.iloc[0]:.1f}% defect rate</div>', unsafe_allow_html=True)
    col_b.markdown(f'<div class="insight-box amber">⚠️ <b>Lowest FPY Station:</b> {worst_station} — {st_fpy.iloc[0]:.1f}% FPY</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Trend Charts
    st.markdown('<div class="section-header">Quality Trends Over Time</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # FPY trend by month
        prod_m = prod.copy()
        prod_m["month"] = prod_m["date"].dt.to_period("M").astype(str)
        fpy_trend = prod_m.groupby("month").apply(
            lambda x: x["units_passed_first_time"].sum() / x["units_completed"].sum() * 100
        ).reset_index(name="fpy")
        fig = px.line(fpy_trend, x="month", y="fpy", title="First Pass Yield — Monthly",
                      color_discrete_sequence=[GREEN])
        fig.add_hline(y=90, line_dash="dash", line_color=RED, annotation_text="Target 90%",
                      annotation_font_color=RED)
        fig.update_yaxes(range=[70, 100], title="FPY %")
        fig.update_xaxes(title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with col2:
        # Defect rate trend by month
        insp_m = insp.copy()
        insp_m["month"] = insp_m["date"].dt.to_period("M").astype(str)
        dr_trend = insp_m.groupby("month").apply(
            lambda x: x["quantity_failed"].sum() / x["quantity_inspected"].sum() * 100 if x["quantity_inspected"].sum() > 0 else 0
        ).reset_index(name="defect_rate")
        fig2 = px.line(dr_trend, x="month", y="defect_rate", title="Defect Rate — Monthly",
                       color_discrete_sequence=[RED])
        fig2.add_hline(y=3, line_dash="dash", line_color=AMBER, annotation_text="Target ≤ 3%",
                       annotation_font_color=AMBER)
        fig2.update_yaxes(title="Defect Rate %")
        fig2.update_xaxes(title="")
        st.plotly_chart(style_fig(fig2), use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Open NCR trend by month
        ncr_m = ncr[ncr["status"] != "Closed"].copy()
        ncr_m["month"] = ncr_m["date_opened"].dt.to_period("M").astype(str)
        ncr_trend = ncr_m.groupby("month").size().reset_index(name="open_ncrs")
        fig3 = px.bar(ncr_trend, x="month", y="open_ncrs", title="Open NCRs — Monthly",
                      color_discrete_sequence=[AMBER])
        fig3.update_xaxes(title="")
        fig3.update_yaxes(title="Count")
        st.plotly_chart(style_fig(fig3), use_container_width=True)

    with col4:
        # Cost of poor quality trend
        insp_m2 = insp.copy()
        insp_m2["month"] = insp_m2["date"].dt.to_period("M").astype(str)
        copq_trend = insp_m2.groupby("month")["cost_impact"].sum().reset_index()
        fig4 = px.area(copq_trend, x="month", y="cost_impact", title="Cost of Poor Quality — Monthly",
                       color_discrete_sequence=[RED])
        fig4.update_yaxes(title="Cost ($)")
        fig4.update_xaxes(title="")
        st.plotly_chart(style_fig(fig4), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 2 — DEFECT PARETO
# ═══════════════════════════════════════════════════════════════════════════

elif page == "Defect Pareto Analysis":
    st.markdown("## 📊 Defect Pareto Analysis")
    st.markdown("---")

    failed_insp = insp[insp["quantity_failed"] > 0].copy()

    if failed_insp.empty:
        st.warning("No defect records for selected filters.")
    else:
        # Pareto
        defect_counts = (
            failed_insp.groupby("defect_type")["quantity_failed"].sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        defect_counts["cum_pct"] = (
            defect_counts["quantity_failed"].cumsum() / defect_counts["quantity_failed"].sum() * 100
        )

        top_defect = defect_counts.iloc[0]["defect_type"]
        top_count  = defect_counts.iloc[0]["quantity_failed"]

        st.markdown(f'<div class="insight-box red">🔴 <b>Top Defect:</b> <b>{top_defect}</b> — {int(top_count):,} units failed ({defect_counts.iloc[0]["cum_pct"]:.1f}% cumulative share)</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">Pareto Chart — Defect Types</div>', unsafe_allow_html=True)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(x=defect_counts["defect_type"], y=defect_counts["quantity_failed"],
                   name="Failed Units", marker_color=RED),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=defect_counts["defect_type"], y=defect_counts["cum_pct"],
                       name="Cumulative %", line=dict(color=AMBER, width=2), mode="lines+markers"),
            secondary_y=True,
        )
        fig.add_hline(y=80, line_dash="dash", line_color="#58a6ff", secondary_y=True,
                      annotation_text="80%", annotation_font_color="#58a6ff")
        fig.update_yaxes(title_text="Failed Units", secondary_y=False)
        fig.update_yaxes(title_text="Cumulative %", range=[0, 105], secondary_y=True)
        fig.update_layout(template=PLOT_TEMPLATE, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
                          height=380, margin=dict(l=16,r=16,t=36,b=80),
                          font=dict(family="IBM Plex Mono", size=11, color="#c9d1d9"),
                          xaxis=dict(tickangle=-35, gridcolor=GRID_COLOR),
                          yaxis=dict(gridcolor=GRID_COLOR))
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-header">Defect Category Breakdown</div>', unsafe_allow_html=True)
            cat_counts = (
                failed_insp.groupby("defect_category")["quantity_failed"].sum()
                .sort_values(ascending=False).reset_index()
            )
            fig2 = px.pie(cat_counts, names="defect_category", values="quantity_failed",
                          color_discrete_sequence=px.colors.sequential.Blues_r)
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(style_fig(fig2, height=340), use_container_width=True)

        with col2:
            st.markdown('<div class="section-header">Defects by Subsystem</div>', unsafe_allow_html=True)
            sub_counts = (
                failed_insp.groupby("subsystem")["quantity_failed"].sum()
                .sort_values(ascending=False).reset_index()
            )
            fig3 = px.bar(sub_counts, x="quantity_failed", y="subsystem", orientation="h",
                          color="quantity_failed", color_continuous_scale="Reds")
            fig3.update_layout(coloraxis_showscale=False, yaxis_title="")
            st.plotly_chart(style_fig(fig3, height=340), use_container_width=True)

        st.markdown('<div class="section-header">Top 10 Defect Types — Data Table</div>', unsafe_allow_html=True)
        st.dataframe(
            defect_counts.head(10).rename(columns={
                "defect_type":"Defect Type",
                "quantity_failed":"Failed Units",
                "cum_pct":"Cumulative %"
            }).style.format({"Cumulative %":"{:.1f}%", "Failed Units":"{:,.0f}"}),
            use_container_width=True
        )


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 3 — SUPPLIER QUALITY
# ═══════════════════════════════════════════════════════════════════════════

elif page == "Supplier Quality":
    st.markdown("## 🏭 Supplier Quality")
    st.markdown("---")

    sup_stats = (
        insp.groupby(["supplier_id","supplier_name"]).agg(
            qty_inspected=("quantity_inspected","sum"),
            qty_failed=("quantity_failed","sum"),
            cost_impact=("cost_impact","sum"),
            ncr_count=("ncr_id", lambda x: x.notna().sum()),
        ).reset_index()
    )
    sup_stats["rejection_rate"] = sup_stats["qty_failed"] / sup_stats["qty_inspected"] * 100
    sup_stats["rejection_rate"] = sup_stats["rejection_rate"].fillna(0)

    # Supplier score formula
    max_dr   = sup_stats["rejection_rate"].max() or 1
    max_cost = sup_stats["cost_impact"].max() or 1
    sup_ncr_closed = ncr.groupby("supplier_id").apply(
        lambda x: ((x["date_closed"] - x["date_opened"]).dt.days.mean()) if x["date_closed"].notna().any() else 0
    ).reset_index(name="avg_closure_days")
    sup_stats = sup_stats.merge(sup_ncr_closed, on="supplier_id", how="left")
    sup_stats["avg_closure_days"] = sup_stats["avg_closure_days"].fillna(30)

    sup_stats["defect_penalty"]  = (sup_stats["rejection_rate"] / max_dr * 30).round(1)
    sup_stats["closure_penalty"] = (sup_stats["avg_closure_days"].clip(0, 30) / 30 * 10).round(1)
    sup_stats["cost_penalty"]    = (sup_stats["cost_impact"] / max_cost * 20).round(1)
    sup_stats["score"]           = (100 - sup_stats["defect_penalty"] - sup_stats["closure_penalty"] - sup_stats["cost_penalty"]).clip(0, 100).round(1)
    sup_stats["grade"]           = pd.cut(sup_stats["score"], bins=[0,70,80,90,100], labels=["D","C","B","A"])
    sup_stats = sup_stats.sort_values("score", ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Supplier Rejection Rate</div>', unsafe_allow_html=True)
        fig1 = px.bar(
            sup_stats.sort_values("rejection_rate", ascending=True),
            x="rejection_rate", y="supplier_name", orientation="h",
            color="rejection_rate", color_continuous_scale="RdYlGn_r",
            labels={"rejection_rate":"Rejection Rate %", "supplier_name":""},
        )
        fig1.add_vline(x=5, line_dash="dash", line_color=AMBER, annotation_text="5% threshold")
        fig1.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig1, height=360), use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Cost Impact by Supplier</div>', unsafe_allow_html=True)
        fig2 = px.bar(
            sup_stats.sort_values("cost_impact", ascending=True),
            x="cost_impact", y="supplier_name", orientation="h",
            color="cost_impact", color_continuous_scale="Reds",
            labels={"cost_impact":"Cost Impact ($)", "supplier_name":""},
        )
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig2, height=360), use_container_width=True)

    st.markdown('<div class="section-header">Supplier Scorecard</div>', unsafe_allow_html=True)

    grade_color = {"A": GREEN, "B": ACCENT, "C": AMBER, "D": RED}

    score_display = sup_stats[["supplier_name","score","grade","rejection_rate","ncr_count","cost_impact","avg_closure_days"]].copy()
    score_display.columns = ["Supplier","Score","Grade","Rejection Rate %","NCR Count","Cost Impact ($)","Avg NCR Close (days)"]
    score_display["Score"] = score_display["Score"].round(1)
    score_display["Rejection Rate %"] = score_display["Rejection Rate %"].round(2)
    score_display["Cost Impact ($)"] = score_display["Cost Impact ($)"].map("${:,.0f}".format)
    score_display["Avg NCR Close (days)"] = score_display["Avg NCR Close (days)"].round(1)

    st.dataframe(score_display, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">Rejection Rate vs Cost Impact</div>', unsafe_allow_html=True)
    fig3 = px.scatter(
        sup_stats, x="rejection_rate", y="cost_impact",
        size="ncr_count", color="grade",
        hover_data=["supplier_name"],
        color_discrete_map={"A": GREEN, "B": ACCENT, "C": AMBER, "D": RED},
        labels={"rejection_rate":"Rejection Rate %","cost_impact":"Cost Impact ($)","grade":"Grade"},
        size_max=40,
    )
    fig3.add_vline(x=5, line_dash="dash", line_color="#555")
    st.plotly_chart(style_fig(fig3, height=380), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 4 — STATION QUALITY
# ═══════════════════════════════════════════════════════════════════════════

elif page == "Station Quality":
    st.markdown("## 🔧 Production Station Quality")
    st.markdown("---")

    st_stats = prod.groupby("station_name").agg(
        units_completed=("units_completed","sum"),
        units_passed=("units_passed_first_time","sum"),
        units_reworked=("units_reworked","sum"),
        units_scrapped=("units_scrapped","sum"),
        avg_cycle=("cycle_time_minutes","mean"),
    ).reset_index()

    st_stats["fpy"]        = st_stats["units_passed"]  / st_stats["units_completed"] * 100
    st_stats["rework_rate"]= st_stats["units_reworked"] / st_stats["units_completed"] * 100
    st_stats["scrap_rate"] = st_stats["units_scrapped"] / st_stats["units_completed"] * 100
    st_stats = st_stats.sort_values("fpy")

    bottleneck = st_stats.iloc[0]["station_name"]
    st.markdown(f'<div class="insight-box red">🔴 <b>Bottleneck Station:</b> <b>{bottleneck}</b> — {st_stats.iloc[0]["fpy"]:.1f}% FPY</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">First Pass Yield by Station</div>', unsafe_allow_html=True)
        colors = [RED if v < 85 else (AMBER if v < 90 else GREEN) for v in st_stats["fpy"]]
        fig1 = go.Figure(go.Bar(
            x=st_stats["fpy"], y=st_stats["station_name"], orientation="h",
            marker_color=colors,
            text=st_stats["fpy"].round(1).astype(str) + "%",
            textposition="outside",
        ))
        fig1.add_vline(x=90, line_dash="dash", line_color=AMBER, annotation_text="Target 90%")
        fig1.update_xaxes(range=[60, 105])
        st.plotly_chart(style_fig(fig1, height=340), use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Rework & Scrap by Station</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Rework Rate %", x=st_stats["station_name"], y=st_stats["rework_rate"], marker_color=AMBER))
        fig2.add_trace(go.Bar(name="Scrap Rate %",  x=st_stats["station_name"], y=st_stats["scrap_rate"],  marker_color=RED))
        fig2.update_layout(barmode="group")
        st.plotly_chart(style_fig(fig2, height=340), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-header">Avg Cycle Time by Station</div>', unsafe_allow_html=True)
        fig3 = px.bar(st_stats.sort_values("avg_cycle", ascending=True),
                      x="avg_cycle", y="station_name", orientation="h",
                      color="avg_cycle", color_continuous_scale="Blues",
                      labels={"avg_cycle":"Avg Cycle Time (min)", "station_name":""})
        fig3.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig3, height=300), use_container_width=True)

    with col4:
        st.markdown('<div class="section-header">Cycle Time Trend — All Stations</div>', unsafe_allow_html=True)
        prod_m = prod.copy()
        prod_m["month"] = prod_m["date"].dt.to_period("M").astype(str)
        ct_trend = prod_m.groupby(["month","station_name"])["cycle_time_minutes"].mean().reset_index()
        fig4 = px.line(ct_trend, x="month", y="cycle_time_minutes", color="station_name",
                       labels={"cycle_time_minutes":"Cycle Time (min)","month":""})
        st.plotly_chart(style_fig(fig4, height=300), use_container_width=True)

    st.markdown('<div class="section-header">Station Summary Table</div>', unsafe_allow_html=True)
    display_st = st_stats[["station_name","fpy","rework_rate","scrap_rate","avg_cycle","units_completed"]].copy()
    display_st.columns = ["Station","FPY %","Rework Rate %","Scrap Rate %","Avg Cycle (min)","Units Completed"]
    display_st = display_st.round(2)
    st.dataframe(display_st, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PAGE 5 — NCR OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

elif page == "NCR Overview":
    st.markdown("## 📋 NCR Overview")
    st.markdown("---")

    today = pd.Timestamp(date.today())
    ncr_work = ncr.copy()
    ncr_work["age_days"] = (today - ncr_work["date_opened"]).dt.days
    ncr_work["is_open"]  = ncr_work["status"] != "Closed"

    open_ncrs    = ncr_work[ncr_work["is_open"]]
    closed_ncrs  = ncr_work[~ncr_work["is_open"]]
    overdue_ncrs = open_ncrs[open_ncrs["age_days"] > 30]

    avg_closure  = (closed_ncrs["date_closed"] - closed_ncrs["date_opened"]).dt.days.mean()
    avg_closure  = round(avg_closure, 1) if not np.isnan(avg_closure) else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Open NCRs",          str(len(open_ncrs)),          "red"   if len(open_ncrs) > 50 else "amber"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Overdue (> 30d)",    str(len(overdue_ncrs)),       "red"   if len(overdue_ncrs) > 10 else "amber"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Closed NCRs",        str(len(closed_ncrs)),        "green"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Avg Closure Time",   f"{avg_closure}d",            "green" if avg_closure < 15 else "amber"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">NCR Status Distribution</div>', unsafe_allow_html=True)
        status_counts = ncr_work["status"].value_counts().reset_index()
        status_counts.columns = ["status","count"]
        fig1 = px.pie(status_counts, names="status", values="count",
                      color_discrete_sequence=px.colors.qualitative.Dark24)
        fig1.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(style_fig(fig1, height=320), use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">NCRs by Severity</div>', unsafe_allow_html=True)
        sev_counts = ncr_work.groupby(["severity","is_open"]).size().reset_index(name="count")
        sev_counts["state"] = sev_counts["is_open"].map({True:"Open", False:"Closed"})
        fig2 = px.bar(sev_counts, x="severity", y="count", color="state", barmode="group",
                      color_discrete_map={"Open": RED, "Closed": GREEN},
                      category_orders={"severity":["Critical","Major","Minor"]})
        st.plotly_chart(style_fig(fig2, height=320), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-header">NCRs by Root Cause Category</div>', unsafe_allow_html=True)
        rc_counts = ncr_work["root_cause_category"].dropna().value_counts().reset_index()
        rc_counts.columns = ["root_cause","count"]
        fig3 = px.bar(rc_counts, x="count", y="root_cause", orientation="h",
                      color="count", color_continuous_scale="Blues")
        fig3.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(style_fig(fig3, height=320), use_container_width=True)

    with col4:
        st.markdown('<div class="section-header">NCR Aging Distribution</div>', unsafe_allow_html=True)
        fig4 = px.histogram(
            open_ncrs, x="age_days", nbins=20,
            color_discrete_sequence=[ACCENT],
            labels={"age_days":"Age (Days)","count":"NCR Count"},
        )
        fig4.add_vline(x=30, line_dash="dash", line_color=RED, annotation_text="30d threshold")
        st.plotly_chart(style_fig(fig4, height=320), use_container_width=True)

    st.markdown('<div class="section-header">Open NCR List</div>', unsafe_allow_html=True)
    open_display = open_ncrs[["ncr_id","date_opened","part_number","supplier_name","defect_type","severity","status","owner","age_days"]].copy()
    open_display.columns = ["NCR ID","Opened","Part","Supplier","Defect","Severity","Status","Owner","Age (days)"]
    open_display = open_display.sort_values("Age (days)", ascending=False).head(100)
    st.dataframe(open_display, use_container_width=True, hide_index=True)