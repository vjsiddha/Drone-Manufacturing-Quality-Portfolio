"""
Drone Manufacturing Quality Dashboard — with SPC
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from shared_styles import apply_styles, style_fig, kpi_card, alert, section, page_header, C

st.set_page_config(page_title="Manufacturing Quality Dashboard", layout="wide", initial_sidebar_state="expanded")
apply_styles()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

@st.cache_data
def load_data():
    insp  = pd.read_csv(f"{DATA_DIR}/inspection_records.csv", parse_dates=["date"])
    prod  = pd.read_csv(f"{DATA_DIR}/production_records.csv", parse_dates=["date"])
    ncr   = pd.read_csv(f"{DATA_DIR}/ncr_records.csv",        parse_dates=["date_opened","date_closed"])
    spc   = pd.read_csv(f"{DATA_DIR}/spc_measurements.csv",   parse_dates=["date"])
    supps = pd.read_csv(f"{DATA_DIR}/suppliers.csv")
    parts = pd.read_csv(f"{DATA_DIR}/parts.csv")
    insp  = insp.merge(parts[["part_number","part_name","subsystem"]], on="part_number", how="left")
    insp  = insp.merge(supps[["supplier_id","supplier_name"]], on="supplier_id", how="left")
    ncr   = ncr.merge(supps[["supplier_id","supplier_name"]], on="supplier_id", how="left")
    return insp, prod, ncr, spc, supps, parts

insp_raw, prod_raw, ncr_raw, spc_raw, supps, parts = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div style="padding:16px 0 8px">
    <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;
                color:{C['muted']};font-family:'JetBrains Mono',monospace;margin-bottom:4px">
        Quality Dashboard
    </div>
    <div style="font-size:14px;font-weight:500;color:{C['text']}">Drone Manufacturing</div>
</div>
<hr style="border:none;border-top:1px solid {C['border']};margin:8px 0 16px">
""", unsafe_allow_html=True)

min_date = insp_raw["date"].min().date()
max_date = insp_raw["date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
start_date = pd.Timestamp(date_range[0]) if len(date_range) > 0 else pd.Timestamp(min_date)
end_date   = pd.Timestamp(date_range[1]) if len(date_range) > 1 else pd.Timestamp(max_date)

sel_supplier   = st.sidebar.selectbox("Supplier",         ["All"] + sorted(supps["supplier_name"].tolist()))
sel_subsystem  = st.sidebar.selectbox("Subsystem",        ["All"] + sorted(parts["subsystem"].dropna().unique()))
sel_stage      = st.sidebar.selectbox("Inspection Stage", ["All"] + sorted(insp_raw["inspection_stage"].dropna().unique()))
sel_defect_cat = st.sidebar.selectbox("Defect Category",  ["All"] + sorted(insp_raw["defect_category"].dropna().unique()))
sel_severity   = st.sidebar.selectbox("NCR Severity",     ["All"] + sorted(ncr_raw["severity"].dropna().unique()))

st.sidebar.markdown(f'<hr style="border:none;border-top:1px solid {C["border"]};margin:16px 0">', unsafe_allow_html=True)
page = st.sidebar.radio("", ["Executive Overview","Defect Pareto","Supplier Quality",
                              "Station Quality","NCR Overview","SPC Monitoring"],
                        label_visibility="collapsed")

# ── Filters ───────────────────────────────────────────────────────────────────
def filter_insp(df):
    d = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    if sel_supplier   != "All": d = d[d["supplier_name"]    == sel_supplier]
    if sel_subsystem  != "All": d = d[d["subsystem"]        == sel_subsystem]
    if sel_stage      != "All": d = d[d["inspection_stage"] == sel_stage]
    if sel_defect_cat != "All": d = d[d["defect_category"]  == sel_defect_cat]
    return d

def filter_prod(df): return df[(df["date"] >= start_date) & (df["date"] <= end_date)]
def filter_ncr(df):
    d = df[(df["date_opened"] >= start_date) & (df["date_opened"] <= end_date)]
    if sel_supplier != "All": d = d[d["supplier_name"] == sel_supplier]
    if sel_severity != "All": d = d[d["severity"]      == sel_severity]
    return d
def filter_spc(df): return df[(df["date"] >= start_date) & (df["date"] <= end_date)]

insp = filter_insp(insp_raw)
prod = filter_prod(prod_raw)
ncr  = filter_ncr(ncr_raw)
spc  = filter_spc(spc_raw)

# ── KPI helpers ───────────────────────────────────────────────────────────────
def fpy(df):
    t = df["units_completed"].sum(); return df["units_passed_first_time"].sum() / t * 100 if t > 0 else 0
def defect_rate(df):
    t = df["quantity_inspected"].sum(); return df["quantity_failed"].sum() / t * 100 if t > 0 else 0
def scrap_rate(df):
    t = df["units_completed"].sum(); return df["units_scrapped"].sum() / t * 100 if t > 0 else 0
def rework_rate(df):
    t = df["units_completed"].sum(); return df["units_reworked"].sum() / t * 100 if t > 0 else 0

overall_fpy    = fpy(prod)
overall_defect = defect_rate(insp)
overall_scrap  = scrap_rate(prod)
overall_rework = rework_rate(prod)
open_ncr_count = (ncr["status"] != "Closed").sum()
copq           = insp["cost_impact"].sum()

sup_defect = (
    insp.groupby("supplier_name")
    .apply(lambda x: x["quantity_failed"].sum() / x["quantity_inspected"].sum() * 100
           if x["quantity_inspected"].sum() > 0 else 0)
    .sort_values(ascending=False)
)
worst_supplier = sup_defect.index[0] if len(sup_defect) > 0 else "N/A"

st_fpy_s = (
    prod.groupby("station_name")
    .apply(lambda x: x["units_passed_first_time"].sum() / x["units_completed"].sum() * 100
           if x["units_completed"].sum() > 0 else 0)
    .sort_values()
)
worst_station = st_fpy_s.index[0] if len(st_fpy_s) > 0 else "N/A"

def hr(): return f'<hr style="border:none;border-top:1px solid {C["border"]};margin:20px 0">'

# ══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Executive Overview":
    st.markdown(page_header("Executive Overview", "Drone Manufacturing — Production Quality KPIs"), unsafe_allow_html=True)
    st.markdown(hr(), unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.markdown(kpi_card("First Pass Yield",     f"{overall_fpy:.1f}%",
                "green" if overall_fpy>=90 else ("amber" if overall_fpy>=80 else "red"), "Target ≥ 90%"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Defect Rate",          f"{overall_defect:.2f}%",
                "green" if overall_defect<=3 else ("amber" if overall_defect<=6 else "red"), "Target ≤ 3%"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Scrap Rate",           f"{overall_scrap:.2f}%",
                "green" if overall_scrap<=2 else ("amber" if overall_scrap<=5 else "red"), "Target ≤ 2%"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Rework Rate",          f"{overall_rework:.2f}%",
                "green" if overall_rework<=5 else ("amber" if overall_rework<=10 else "red"), "Target ≤ 5%"), unsafe_allow_html=True)
    c5.markdown(kpi_card("Open NCRs",            str(int(open_ncr_count)),
                "green" if open_ncr_count<=20 else ("amber" if open_ncr_count<=50 else "red"), "Active issues"), unsafe_allow_html=True)
    c6.markdown(kpi_card("Cost of Poor Quality", f"${copq:,.0f}",
                "green" if copq<50000 else ("amber" if copq<200000 else "red"), "Inspection window"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    col_a.markdown(alert(f"Worst supplier: <b>{worst_supplier}</b> — {sup_defect.iloc[0]:.1f}% defect rate", "red"), unsafe_allow_html=True)
    col_b.markdown(alert(f"Lowest FPY station: <b>{worst_station}</b> — {st_fpy_s.iloc[0]:.1f}% FPY", "amber"), unsafe_allow_html=True)

    st.markdown(hr(), unsafe_allow_html=True)
    st.markdown(section("Quality Trends"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        pm = prod.copy(); pm["month"] = pm["date"].dt.to_period("M").astype(str)
        fpy_trend = pm.groupby("month").apply(
            lambda x: x["units_passed_first_time"].sum() / x["units_completed"].sum() * 100
        ).reset_index(name="fpy")
        fig = px.line(fpy_trend, x="month", y="fpy", title="First Pass Yield — Monthly",
                      color_discrete_sequence=[C["green"]])
        fig.add_hline(y=90, line_dash="dot", line_color=C["red"],
                      annotation_text="90%", annotation_font_color=C["muted"], annotation_font_size=10)
        fig.update_yaxes(range=[70,100], title="FPY %"); fig.update_xaxes(title="")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with col2:
        im = insp.copy(); im["month"] = im["date"].dt.to_period("M").astype(str)
        dr = im.groupby("month").apply(
            lambda x: x["quantity_failed"].sum() / x["quantity_inspected"].sum() * 100
            if x["quantity_inspected"].sum() > 0 else 0
        ).reset_index(name="defect_rate")
        fig2 = px.line(dr, x="month", y="defect_rate", title="Defect Rate — Monthly",
                       color_discrete_sequence=[C["red"]])
        fig2.add_hline(y=3, line_dash="dot", line_color=C["amber"],
                       annotation_text="3%", annotation_font_color=C["muted"], annotation_font_size=10)
        fig2.update_yaxes(title="Defect Rate %"); fig2.update_xaxes(title="")
        st.plotly_chart(style_fig(fig2), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        nm = ncr[ncr["status"] != "Closed"].copy()
        nm["month"] = nm["date_opened"].dt.to_period("M").astype(str)
        nt = nm.groupby("month").size().reset_index(name="open_ncrs")
        fig3 = px.bar(nt, x="month", y="open_ncrs", title="Open NCRs — Monthly",
                      color_discrete_sequence=[C["amber"]])
        fig3.update_traces(marker_line_width=0)
        fig3.update_xaxes(title=""); fig3.update_yaxes(title="Count")
        st.plotly_chart(style_fig(fig3), use_container_width=True)

    with col4:
        im2 = insp.copy(); im2["month"] = im2["date"].dt.to_period("M").astype(str)
        ct = im2.groupby("month")["cost_impact"].sum().reset_index()
        fig4 = px.area(ct, x="month", y="cost_impact", title="Cost of Poor Quality — Monthly",
                       color_discrete_sequence=[C["red"]])
        fig4.update_traces(line_width=1)
        fig4.update_yaxes(title="Cost ($)"); fig4.update_xaxes(title="")
        st.plotly_chart(style_fig(fig4), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# DEFECT PARETO
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Defect Pareto":
    st.markdown(page_header("Defect Pareto Analysis", "Identify and prioritise top defect types by volume"), unsafe_allow_html=True)
    st.markdown(hr(), unsafe_allow_html=True)

    failed_insp = insp[insp["quantity_failed"] > 0].copy()
    if failed_insp.empty:
        st.warning("No defect records for selected filters.")
    else:
        dc = (failed_insp.groupby("defect_type")["quantity_failed"].sum()
              .sort_values(ascending=False).reset_index())
        dc["cum_pct"] = dc["quantity_failed"].cumsum() / dc["quantity_failed"].sum() * 100

        st.markdown(alert(f"Top defect: <b>{dc.iloc[0]['defect_type']}</b> — {int(dc.iloc[0]['quantity_failed']):,} units failed · {dc.iloc[0]['cum_pct']:.1f}% cumulative share", "red"), unsafe_allow_html=True)
        st.markdown(section("Pareto — Defect Types"), unsafe_allow_html=True)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=dc["defect_type"], y=dc["quantity_failed"],
                             name="Failed Units", marker_color=C["red"], marker_line_width=0), secondary_y=False)
        fig.add_trace(go.Scatter(x=dc["defect_type"], y=dc["cum_pct"],
                                 name="Cumulative %", line=dict(color=C["amber"], width=2),
                                 mode="lines+markers", marker=dict(size=5)), secondary_y=True)
        fig.add_hline(y=80, line_dash="dot", line_color=C["border2"], secondary_y=True,
                      annotation_text="80%", annotation_font_color=C["muted"], annotation_font_size=10)
        fig.update_yaxes(title_text="Failed Units", secondary_y=False, gridcolor=C["grid"])
        fig.update_yaxes(title_text="Cumulative %", range=[0,105], secondary_y=True, gridcolor=C["grid"])
        fig.update_layout(template="plotly_dark", paper_bgcolor=C["plot_bg"], plot_bgcolor=C["plot_bg"],
                          height=380, margin=dict(l=16,r=16,t=32,b=80),
                          font=dict(family="JetBrains Mono", size=11, color=C["subtle"]),
                          xaxis=dict(tickangle=-35, gridcolor=C["grid"]),
                          legend=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(section("By Category"), unsafe_allow_html=True)
            cc = (failed_insp.groupby("defect_category")["quantity_failed"].sum()
                  .sort_values(ascending=False).reset_index())
            fig2 = px.bar(cc, x="quantity_failed", y="defect_category", orientation="h",
                          color_discrete_sequence=[C["blue"]])
            fig2.update_traces(marker_line_width=0)
            fig2.update_layout(yaxis_title="", xaxis_title="Failed Units")
            st.plotly_chart(style_fig(fig2, 300), use_container_width=True)

        with col2:
            st.markdown(section("By Subsystem"), unsafe_allow_html=True)
            sc = (failed_insp.groupby("subsystem")["quantity_failed"].sum()
                  .sort_values(ascending=False).reset_index())
            fig3 = px.bar(sc, x="quantity_failed", y="subsystem", orientation="h",
                          color_discrete_sequence=[C["amber"]])
            fig3.update_traces(marker_line_width=0)
            fig3.update_layout(yaxis_title="", xaxis_title="Failed Units")
            st.plotly_chart(style_fig(fig3, 300), use_container_width=True)

        st.markdown(section("Top 10 Defect Types"), unsafe_allow_html=True)
        st.dataframe(dc.head(10).rename(columns={
            "defect_type":"Defect Type","quantity_failed":"Failed Units","cum_pct":"Cumulative %"
        }).style.format({"Cumulative %":"{:.1f}%","Failed Units":"{:,.0f}"}), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SUPPLIER QUALITY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Supplier Quality":
    st.markdown(page_header("Supplier Quality", "Rejection rates, cost impact, and scored supplier performance"), unsafe_allow_html=True)
    st.markdown(hr(), unsafe_allow_html=True)

    sup_stats = (
        insp.groupby(["supplier_id","supplier_name"]).agg(
            qty_inspected=("quantity_inspected","sum"),
            qty_failed=("quantity_failed","sum"),
            cost_impact=("cost_impact","sum"),
            ncr_count=("ncr_id", lambda x: x.notna().sum()),
        ).reset_index()
    )
    sup_stats["rejection_rate"] = (sup_stats["qty_failed"] / sup_stats["qty_inspected"] * 100).fillna(0)
    max_dr = sup_stats["rejection_rate"].max() or 1
    max_cost = sup_stats["cost_impact"].max() or 1
    sup_ncr_closed = ncr.groupby("supplier_id").apply(
        lambda x: (x["date_closed"] - x["date_opened"]).dt.days.mean()
        if x["date_closed"].notna().any() else 0
    ).reset_index(name="avg_closure_days")
    sup_stats = sup_stats.merge(sup_ncr_closed, on="supplier_id", how="left")
    sup_stats["avg_closure_days"] = sup_stats["avg_closure_days"].fillna(30)
    sup_stats["score"] = (100
        - sup_stats["rejection_rate"] / max_dr * 30
        - sup_stats["avg_closure_days"].clip(0,30) / 30 * 10
        - sup_stats["cost_impact"] / max_cost * 20
    ).clip(0,100).round(1)
    sup_stats["grade"] = pd.cut(sup_stats["score"], bins=[0,70,80,90,100], labels=["D","C","B","A"])
    sup_stats = sup_stats.sort_values("score", ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("Rejection Rate"), unsafe_allow_html=True)
        fig1 = px.bar(sup_stats.sort_values("rejection_rate", ascending=True),
                      x="rejection_rate", y="supplier_name", orientation="h",
                      color="rejection_rate",
                      color_continuous_scale=[[0,C["green"]],[0.4,C["amber"]],[1,C["red"]]],
                      labels={"rejection_rate":"Rejection Rate %","supplier_name":""})
        fig1.update_traces(marker_line_width=0)
        fig1.add_vline(x=5, line_dash="dot", line_color=C["border2"],
                       annotation_text="5% threshold", annotation_font_color=C["muted"], annotation_font_size=10)
        fig1.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig1, 360), use_container_width=True)

    with col2:
        st.markdown(section("Cost Impact"), unsafe_allow_html=True)
        fig2 = px.bar(sup_stats.sort_values("cost_impact", ascending=True),
                      x="cost_impact", y="supplier_name", orientation="h",
                      color="cost_impact",
                      color_continuous_scale=[[0,C["surface2"]],[1,C["red"]]],
                      labels={"cost_impact":"Cost Impact ($)","supplier_name":""})
        fig2.update_traces(marker_line_width=0)
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig2, 360), use_container_width=True)

    st.markdown(section("Supplier Scorecard"), unsafe_allow_html=True)
    sc = sup_stats[["supplier_name","score","grade","rejection_rate","ncr_count","cost_impact","avg_closure_days"]].copy()
    sc.columns = ["Supplier","Score","Grade","Rejection Rate %","NCR Count","Cost Impact ($)","Avg NCR Close (days)"]
    sc["Rejection Rate %"] = sc["Rejection Rate %"].round(2)
    sc["Cost Impact ($)"]  = sc["Cost Impact ($)"].map("${:,.0f}".format)
    sc["Avg NCR Close (days)"] = sc["Avg NCR Close (days)"].round(1)
    st.dataframe(sc, use_container_width=True, hide_index=True)

    st.markdown(section("Rejection Rate vs Cost Impact"), unsafe_allow_html=True)
    grade_colors = {"A":C["green"],"B":C["blue"],"C":C["amber"],"D":C["red"]}
    fig3 = px.scatter(sup_stats, x="rejection_rate", y="cost_impact",
                      size="ncr_count", color="grade", hover_data=["supplier_name"],
                      color_discrete_map=grade_colors, size_max=40,
                      labels={"rejection_rate":"Rejection Rate %","cost_impact":"Cost Impact ($)","grade":"Grade"})
    fig3.add_vline(x=5, line_dash="dot", line_color=C["border2"])
    st.plotly_chart(style_fig(fig3, 380), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# STATION QUALITY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Station Quality":
    st.markdown(page_header("Station Quality", "FPY, rework, scrap, and cycle time by production station"), unsafe_allow_html=True)
    st.markdown(hr(), unsafe_allow_html=True)

    st_stats = prod.groupby("station_name").agg(
        units_completed=("units_completed","sum"),
        units_passed=("units_passed_first_time","sum"),
        units_reworked=("units_reworked","sum"),
        units_scrapped=("units_scrapped","sum"),
        avg_cycle=("cycle_time_minutes","mean"),
    ).reset_index()
    st_stats["fpy"]         = st_stats["units_passed"]   / st_stats["units_completed"] * 100
    st_stats["rework_rate"] = st_stats["units_reworked"] / st_stats["units_completed"] * 100
    st_stats["scrap_rate"]  = st_stats["units_scrapped"] / st_stats["units_completed"] * 100
    st_stats = st_stats.sort_values("fpy")

    st.markdown(alert(f"Bottleneck station: <b>{st_stats.iloc[0]['station_name']}</b> — {st_stats.iloc[0]['fpy']:.1f}% FPY. Prioritise RCA at this station.", "red"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("First Pass Yield by Station"), unsafe_allow_html=True)
        bar_colors = [C["red"] if v<85 else (C["amber"] if v<90 else C["green"]) for v in st_stats["fpy"]]
        fig1 = go.Figure(go.Bar(
            x=st_stats["fpy"], y=st_stats["station_name"], orientation="h",
            marker_color=bar_colors, marker_line_width=0,
            text=st_stats["fpy"].round(1).astype(str)+"%", textposition="outside",
            textfont=dict(family="JetBrains Mono", size=11, color=C["subtle"]),
        ))
        fig1.add_vline(x=90, line_dash="dot", line_color=C["border2"],
                       annotation_text="90%", annotation_font_color=C["muted"], annotation_font_size=10)
        fig1.update_xaxes(range=[60,105], title="")
        fig1.update_yaxes(title="")
        st.plotly_chart(style_fig(fig1, 340), use_container_width=True)

    with col2:
        st.markdown(section("Rework and Scrap by Station"), unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Rework %", x=st_stats["station_name"], y=st_stats["rework_rate"],
                              marker_color=C["amber"], marker_line_width=0))
        fig2.add_trace(go.Bar(name="Scrap %",  x=st_stats["station_name"], y=st_stats["scrap_rate"],
                              marker_color=C["red"], marker_line_width=0))
        fig2.update_layout(barmode="group", xaxis_title="", yaxis_title="%")
        st.plotly_chart(style_fig(fig2, 340), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(section("Avg Cycle Time by Station"), unsafe_allow_html=True)
        fig3 = px.bar(st_stats.sort_values("avg_cycle", ascending=True),
                      x="avg_cycle", y="station_name", orientation="h",
                      color_discrete_sequence=[C["blue"]],
                      labels={"avg_cycle":"Avg Cycle Time (min)","station_name":""})
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(style_fig(fig3, 300), use_container_width=True)

    with col4:
        st.markdown(section("Cycle Time Trend"), unsafe_allow_html=True)
        pm = prod.copy(); pm["month"] = pm["date"].dt.to_period("M").astype(str)
        ct = pm.groupby(["month","station_name"])["cycle_time_minutes"].mean().reset_index()
        fig4 = px.line(ct, x="month", y="cycle_time_minutes", color="station_name",
                       labels={"cycle_time_minutes":"Cycle Time (min)","month":""})
        st.plotly_chart(style_fig(fig4, 300), use_container_width=True)

    st.markdown(section("Station Summary"), unsafe_allow_html=True)
    disp = st_stats[["station_name","fpy","rework_rate","scrap_rate","avg_cycle","units_completed"]].copy()
    disp.columns = ["Station","FPY %","Rework %","Scrap %","Avg Cycle (min)","Units Completed"]
    st.dataframe(disp.round(2), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# NCR OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
elif page == "NCR Overview":
    st.markdown(page_header("NCR Overview", "Open non-conformances, aging, root cause distribution, and closure performance"), unsafe_allow_html=True)
    st.markdown(hr(), unsafe_allow_html=True)

    today    = pd.Timestamp(date.today())
    nw       = ncr.copy()
    nw["age_days"] = (today - nw["date_opened"]).dt.days
    nw["is_open"]  = nw["status"] != "Closed"
    open_ncrs   = nw[nw["is_open"]]
    closed_ncrs = nw[~nw["is_open"]]
    overdue     = open_ncrs[open_ncrs["age_days"] > 30]
    avg_closure = (closed_ncrs["date_closed"] - closed_ncrs["date_opened"]).dt.days.mean()
    avg_closure = round(avg_closure, 1) if not np.isnan(avg_closure) else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi_card("Open NCRs",     len(open_ncrs),   "red"   if len(open_ncrs)>50  else "amber", "Active"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Overdue > 30d", len(overdue),     "red"   if len(overdue)>10    else "amber", "Past due"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Closed",        len(closed_ncrs), "green", "Resolved"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Avg Closure",   f"{avg_closure}d","green" if avg_closure<15 else "amber", "Days to close"), unsafe_allow_html=True)

    st.markdown(hr(), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("Status Distribution"), unsafe_allow_html=True)
        sc = nw["status"].value_counts().reset_index(); sc.columns = ["status","count"]
        fig1 = px.bar(sc, x="status", y="count", color_discrete_sequence=[C["blue"]])
        fig1.update_traces(marker_line_width=0)
        fig1.update_layout(xaxis_title="", yaxis_title="Count", xaxis_tickangle=-20)
        st.plotly_chart(style_fig(fig1, 300), use_container_width=True)

    with col2:
        st.markdown(section("NCRs by Severity"), unsafe_allow_html=True)
        sv = nw.groupby(["severity","is_open"]).size().reset_index(name="count")
        sv["state"] = sv["is_open"].map({True:"Open",False:"Closed"})
        fig2 = px.bar(sv, x="severity", y="count", color="state", barmode="group",
                      color_discrete_map={"Open":C["red"],"Closed":C["green"]},
                      category_orders={"severity":["Critical","Major","Minor"]})
        fig2.update_traces(marker_line_width=0)
        fig2.update_layout(xaxis_title="", yaxis_title="Count", legend_title="")
        st.plotly_chart(style_fig(fig2, 300), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(section("Root Cause Category"), unsafe_allow_html=True)
        rc = nw["root_cause_category"].dropna().value_counts().reset_index()
        rc.columns = ["root_cause","count"]
        fig3 = px.bar(rc, x="count", y="root_cause", orientation="h",
                      color_discrete_sequence=[C["blue"]])
        fig3.update_traces(marker_line_width=0)
        fig3.update_layout(yaxis_title="", xaxis_title="Count")
        st.plotly_chart(style_fig(fig3, 300), use_container_width=True)

    with col4:
        st.markdown(section("NCR Aging — Open Only"), unsafe_allow_html=True)
        fig4 = px.histogram(open_ncrs, x="age_days", nbins=20,
                            color_discrete_sequence=[C["amber"]],
                            labels={"age_days":"Age (days)"})
        fig4.update_traces(marker_line_width=0)
        fig4.add_vline(x=30, line_dash="dot", line_color=C["red"],
                       annotation_text="30d", annotation_font_color=C["muted"], annotation_font_size=10)
        fig4.update_layout(yaxis_title="Count")
        st.plotly_chart(style_fig(fig4, 300), use_container_width=True)

    st.markdown(section("Open NCR List — Sorted by Age"), unsafe_allow_html=True)
    od = open_ncrs[["ncr_id","date_opened","part_number","supplier_name",
                    "defect_type","severity","status","owner","age_days"]].copy()
    od.columns = ["NCR ID","Opened","Part","Supplier","Defect","Severity","Status","Owner","Age (days)"]
    st.dataframe(od.sort_values("Age (days)", ascending=False).head(100),
                 use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# SPC MONITORING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "SPC Monitoring":
    st.markdown(page_header("SPC Monitoring", "Statistical process control — Cp, Cpk, control charts, and capability by feature"), unsafe_allow_html=True)
    st.markdown(hr(), unsafe_allow_html=True)

    if spc.empty:
        st.warning("No SPC records for selected date range.")
    else:
        feature_options = sorted(spc["feature_name"].dropna().unique())
        selected_feature = st.selectbox("Critical Feature", feature_options)
        feature_df = spc[spc["feature_name"] == selected_feature].copy()

        subgroup = (
            feature_df.groupby(["subgroup_id","date","feature_id","feature_name"])
            .agg(xbar=("measured_value","mean"),
                 subgroup_range=("measured_value", lambda x: x.max()-x.min()),
                 sample_count=("measured_value","count"),
                 lsl=("lsl","first"), usl=("usl","first"),
                 nominal=("nominal","first"),
                 out_of_spec_count=("out_of_spec","sum"))
            .reset_index().sort_values("subgroup_id")
        )

        values = feature_df["measured_value"].dropna()
        mean   = values.mean()
        sigma  = values.std(ddof=1)
        lsl    = float(feature_df["lsl"].iloc[0])
        usl    = float(feature_df["usl"].iloc[0])
        nominal= float(feature_df["nominal"].iloc[0])
        unit   = feature_df["unit"].iloc[0]

        ucl = mean + 3 * sigma
        lcl = max(mean - 3 * sigma, 0) if lsl >= 0 else mean - 3 * sigma

        cp  = (usl - lsl) / (6 * sigma) if sigma > 0 else np.nan
        cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma)) if sigma > 0 else np.nan
        oos_rate = feature_df["out_of_spec"].mean() * 100
        ctrl_violations = subgroup[(subgroup["xbar"] > ucl) | (subgroup["xbar"] < lcl)]

        recent_n = min(15, max(1, len(subgroup) // 3))
        drift = subgroup.tail(recent_n)["xbar"].mean() - subgroup.head(recent_n)["xbar"].mean()
        drift_label = "Drifting Up" if drift > sigma else ("Drifting Down" if drift < -sigma else "Stable")

        cap_status = "Capable" if cpk >= 1.33 else ("Marginal" if cpk >= 1.0 else "Not Capable")
        ctrl_status = "In Control" if len(ctrl_violations) == 0 else "Out of Control"

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.markdown(kpi_card("Cp",  f"{cp:.2f}",  "green" if cp>=1.33  else ("amber" if cp>=1.0  else "red"), "Potential"), unsafe_allow_html=True)
        c2.markdown(kpi_card("Cpk", f"{cpk:.2f}", "green" if cpk>=1.33 else ("amber" if cpk>=1.0 else "red"), cap_status), unsafe_allow_html=True)
        c3.markdown(kpi_card("Control Violations", len(ctrl_violations), "green" if len(ctrl_violations)==0 else "red", ctrl_status), unsafe_allow_html=True)
        c4.markdown(kpi_card("Out-of-Spec",  f"{oos_rate:.2f}%", "green" if oos_rate==0 else ("amber" if oos_rate<2 else "red"), "Actual failures"), unsafe_allow_html=True)
        c5.markdown(kpi_card("Process Drift", drift_label, "green" if drift_label=="Stable" else "amber", f"delta {drift:.4f} {unit}"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if cap_status == "Not Capable":
            st.markdown(alert("Process Cpk is below 1.00. The process is not consistently capable of meeting specification limits. Immediate investigation required.", "red"), unsafe_allow_html=True)
        elif cap_status == "Marginal":
            st.markdown(alert("Process Cpk is between 1.00 and 1.33. Monitor closely. Consider process improvement to achieve Cpk ≥ 1.33.", "amber"), unsafe_allow_html=True)
        else:
            st.markdown(alert(f"Process Cpk is {cpk:.2f} — acceptable capability. Continue monitoring for drift.", "green"), unsafe_allow_html=True)

        st.markdown(hr(), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(section("X-Bar Control Chart"), unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=subgroup["subgroup_id"], y=subgroup["xbar"],
                                     mode="lines+markers", name="Subgroup Mean",
                                     line=dict(color=C["blue"], width=2),
                                     marker=dict(size=5)))
            fig.add_hline(y=mean, line_dash="solid", line_color=C["green"],
                          annotation_text="Mean", annotation_font_color=C["muted"], annotation_font_size=10)
            fig.add_hline(y=ucl, line_dash="dash", line_color=C["red"],
                          annotation_text="UCL", annotation_font_color=C["muted"], annotation_font_size=10)
            fig.add_hline(y=lcl, line_dash="dash", line_color=C["red"],
                          annotation_text="LCL", annotation_font_color=C["muted"], annotation_font_size=10)
            fig.add_hline(y=usl, line_dash="dot", line_color=C["amber"],
                          annotation_text="USL", annotation_font_color=C["muted"], annotation_font_size=10)
            fig.add_hline(y=lsl, line_dash="dot", line_color=C["amber"],
                          annotation_text="LSL", annotation_font_color=C["muted"], annotation_font_size=10)
            if not ctrl_violations.empty:
                fig.add_trace(go.Scatter(x=ctrl_violations["subgroup_id"], y=ctrl_violations["xbar"],
                                         mode="markers", name="Violation",
                                         marker=dict(color=C["red"], size=10, symbol="x")))
            fig.update_xaxes(title="Subgroup")
            fig.update_yaxes(title=f"Value ({unit})")
            st.plotly_chart(style_fig(fig, 400), use_container_width=True)

        with col2:
            st.markdown(section("Range Chart"), unsafe_allow_html=True)
            rbar = subgroup["subgroup_range"].mean()
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=subgroup["subgroup_id"], y=subgroup["subgroup_range"],
                                      mode="lines+markers", name="Range",
                                      line=dict(color=C["amber"], width=2),
                                      marker=dict(size=5)))
            fig2.add_hline(y=rbar, line_dash="solid", line_color=C["green"],
                           annotation_text="R-bar", annotation_font_color=C["muted"], annotation_font_size=10)
            fig2.update_xaxes(title="Subgroup")
            fig2.update_yaxes(title=f"Range ({unit})")
            st.plotly_chart(style_fig(fig2, 400), use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown(section("Distribution vs Specification"), unsafe_allow_html=True)
            fig3 = px.histogram(feature_df, x="measured_value", nbins=35,
                                color_discrete_sequence=[C["blue"]],
                                labels={"measured_value":f"Measured ({unit})"})
            fig3.update_traces(marker_line_width=0)
            fig3.add_vline(x=lsl,  line_dash="dash",  line_color=C["red"],   annotation_text="LSL", annotation_font_color=C["muted"], annotation_font_size=10)
            fig3.add_vline(x=usl,  line_dash="dash",  line_color=C["red"],   annotation_text="USL", annotation_font_color=C["muted"], annotation_font_size=10)
            fig3.add_vline(x=mean, line_dash="solid", line_color=C["green"], annotation_text="Mean",annotation_font_color=C["muted"], annotation_font_size=10)
            fig3.update_yaxes(title="Count")
            st.plotly_chart(style_fig(fig3, 320), use_container_width=True)

        with col4:
            st.markdown(section("Process Summary"), unsafe_allow_html=True)
            summary = pd.DataFrame([
                ["Feature",         selected_feature],
                ["Nominal",         f"{nominal:.4f} {unit}"],
                ["LSL",             f"{lsl:.4f} {unit}"],
                ["USL",             f"{usl:.4f} {unit}"],
                ["Process Mean",    f"{mean:.4f} {unit}"],
                ["Std Dev",         f"{sigma:.4f} {unit}"],
                ["Cp",              f"{cp:.3f}"],
                ["Cpk",             f"{cpk:.3f}"],
                ["Capability",      cap_status],
                ["Control Status",  ctrl_status],
                ["Drift",           drift_label],
            ], columns=["Metric","Value"])
            st.dataframe(summary, use_container_width=True, hide_index=True)

        st.markdown(section("Capability Summary — All Features"), unsafe_allow_html=True)
        cap_rows = []
        for fname, grp in spc.groupby("feature_name"):
            vals = grp["measured_value"].dropna()
            sig  = vals.std(ddof=1)
            avg  = vals.mean()
            gl   = float(grp["lsl"].iloc[0])
            gu   = float(grp["usl"].iloc[0])
            gcp  = (gu - gl) / (6 * sig) if sig > 0 else np.nan
            gcpk = min((gu - avg) / (3 * sig), (avg - gl) / (3 * sig)) if sig > 0 else np.nan
            cap_rows.append({
                "Feature": fname, "Mean": avg, "Std Dev": sig,
                "Cp": gcp, "Cpk": gcpk,
                "Out-of-Spec %": grp["out_of_spec"].mean() * 100,
                "Status": "Capable" if gcpk >= 1.33 else ("Marginal" if gcpk >= 1.0 else "Not Capable"),
            })
        cap_df = pd.DataFrame(cap_rows).sort_values("Cpk")
        st.dataframe(
            cap_df.style.format({"Mean":"{:.4f}","Std Dev":"{:.4f}","Cp":"{:.2f}","Cpk":"{:.2f}","Out-of-Spec %":"{:.2f}%"}),
            use_container_width=True, hide_index=True,
        )