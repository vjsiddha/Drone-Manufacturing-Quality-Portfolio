from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

try:
    from shared_styles import apply_styles, style_fig, kpi_card, alert, section, page_header, C
except Exception:
    def apply_styles(): pass
    def style_fig(fig, height=320):
        fig.update_layout(height=height, margin=dict(l=10, r=10, t=35, b=10))
        return fig
    def kpi_card(label, value, color="neutral", sub=""):
        return f"**{label}**\n\n### {value}\n{sub}"
    def alert(msg, color="blue"):
        return f"<div style='padding:14px;border-radius:8px;border:1px solid #333'>{msg}</div>"
    def section(title):
        return f"### {title}"
    def page_header(title, subtitle=""):
        return f"# {title}\n#### {subtitle}" if subtitle else f"# {title}"
    C = {"red":"#ff4b4b","amber":"#f5b642","green":"#35c46b","blue":"#4ea1ff",
         "muted":"#999","text":"#fff","subtle":"#ddd","border":"#333","border2":"#555","surface":"#111"}

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"

FMEA_CSV = DATA_DIR / "propulsion_fmea.csv"
FMEA_XLSX = DATA_DIR / "propulsion_fmea.xlsx"
SUMMARY_REPORT = REPORTS_DIR / "fmea_summary_report.md"
TOP_10_REPORT = REPORTS_DIR / "top_10_risks.md"
ACTIONS_REPORT = REPORTS_DIR / "recommended_actions.md"

HIGH_RPN = 150
MODERATE_RPN = 80

def risk_band(rpn):
    if pd.isna(rpn):
        return "Unknown"
    if rpn >= HIGH_RPN:
        return "High"
    if rpn >= MODERATE_RPN:
        return "Moderate"
    return "Low"

def load_fmea():
    if not FMEA_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(FMEA_CSV)
    if "rpn" not in df.columns and {"severity","occurrence","detection"}.issubset(df.columns):
        df["rpn"] = df["severity"] * df["occurrence"] * df["detection"]
    if "revised_rpn" not in df.columns and {"revised_severity","revised_occurrence","revised_detection"}.issubset(df.columns):
        df["revised_rpn"] = df["revised_severity"] * df["revised_occurrence"] * df["revised_detection"]
    df["risk_band"] = df["rpn"].apply(risk_band)
    if "revised_rpn" in df.columns:
        df["rpn_reduction"] = df["rpn"] - df["revised_rpn"]
        df["rpn_reduction_pct"] = ((df["rpn"] - df["revised_rpn"]) / df["rpn"] * 100).round(1)
        df["residual_band"] = df["revised_rpn"].apply(risk_band)
    return df

def save_fmea(df):
    export = df.drop(columns=[c for c in ["risk_band","rpn_reduction","rpn_reduction_pct","residual_band"] if c in df.columns])
    export.to_csv(FMEA_CSV, index=False)

def make_reports(df):
    REPORTS_DIR.mkdir(exist_ok=True)
    high = df[df["rpn"] >= HIGH_RPN].sort_values("rpn", ascending=False)
    top10 = df.sort_values("rpn", ascending=False).head(10)
    avg_reduction = ((df["rpn"] - df["revised_rpn"]) / df["rpn"] * 100).mean() if "revised_rpn" in df.columns else 0

    summary = [
        "# FMEA Summary Report",
        "## Drone Propulsion System — Rev A",
        "",
        "| | |",
        "|---|---|",
        f"| Document | Propulsion FMEA Rev A |",
        f"| Date | {date.today().isoformat()} |",
        f"| Prepared by | Quality Engineering |",
        f"| Scope | Autonomous Delivery Drone — Propulsion Subsystem |",
        f"| RPN Formula | Severity × Occurrence × Detection |",
        "",
        "---",
        "## Risk Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total failure modes | {len(df)} |",
        f"| High-risk items (RPN ≥ {HIGH_RPN}) | {len(high)} |",
        f"| Average RPN — before | {df['rpn'].mean():.1f} |",
        f"| Average RPN — after | {df['revised_rpn'].mean():.1f} |" if "revised_rpn" in df.columns else "",
        f"| Average RPN reduction | {avg_reduction:.1f}% |" if "revised_rpn" in df.columns else "",
        f"| Highest RPN | {df['rpn'].max()} — {df.loc[df['rpn'].idxmax(), 'failure_mode']} |",
        "",
        "---",
        "## Top 10 Risks by RPN",
        "",
        "| Rank | Component | Failure Mode | S | O | D | RPN |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]
    for i, (_, r) in enumerate(top10.iterrows(), 1):
        summary.append(f"| {i} | {r['component']} | {r['failure_mode']} | {r['severity']} | {r['occurrence']} | {r['detection']} | {r['rpn']} |")
    summary += ["", "---", "## Connection to Manufacturing Quality", "",
                "| Downstream System | How This FMEA Feeds It |",
                "|---|---|",
                "| Inspection Plans | High S×O items trigger increased AQL sampling and CMM/SPC checks |",
                "| NCR Defect Library | Failure modes become standardized defect categories |",
                "| CAPA | High RPN recurring failures become CAPA candidates |",
                "| Quality Analytics | Residual risk is monitored through defect trends and SPC |"]
    SUMMARY_REPORT.write_text("\n".join([x for x in summary if x != ""]))

    top_lines = ["# Top 10 FMEA Risk Items", "## Drone Propulsion System — Ranked by RPN", ""]
    for i, (_, r) in enumerate(top10.iterrows(), 1):
        red = int(r["rpn"] - r.get("revised_rpn", r["rpn"]))
        pct = (red / r["rpn"] * 100) if r["rpn"] else 0
        top_lines += [
            f"## Rank {i} — {r['failure_mode']}",
            "",
            "| | |",
            "|---|---|",
            f"| Component | {r['component']} |",
            f"| Risk Band | {risk_band(r['rpn']).upper()} |",
            f"| RPN | {r['rpn']} (S={r['severity']} × O={r['occurrence']} × D={r['detection']}) |",
            f"| Failure Effect | {r['failure_effect']} |",
            f"| Potential Cause | {r['potential_cause']} |",
            f"| Recommended Action | {r['recommended_action']} |",
            f"| Owner | {r['action_owner']} |",
            f"| Due Date | {r['target_completion_date']} |",
            f"| Revised RPN | {r.get('revised_rpn','—')} — reduction of {red} points ({pct:.0f}%) |",
            f"| Status | {r['status']} |",
            "",
            "---",
            "",
        ]
    TOP_10_REPORT.write_text("\n".join(top_lines))

    actions = df[df["recommended_action"].notna()].copy()
    act_lines = ["# FMEA Recommended Actions", "## Drone Propulsion System — Rev A", "",
                 "| | |", "|---|---|", f"| Date | {date.today().isoformat()} |",
                 f"| Total Actions | {len(actions)} |",
                 f"| Complete | {(actions['status']=='Complete').sum()} |",
                 f"| In Progress | {(actions['status']=='In Progress').sum()} |",
                 f"| Open | {(actions['status']=='Open').sum()} |", "", "---", ""]
    for owner, group in actions.groupby("action_owner"):
        act_lines += [f"## {owner}", "", "| ID | Component | Failure Mode | Action | Due Date | Status |",
                      "|---:|---|---|---|---|---|"]
        for _, r in group.iterrows():
            act_lines.append(f"| {r['fmea_id']} | {r['component']} | {r['failure_mode']} | {r['recommended_action']} | {r['target_completion_date']} | {r['status']} |")
        act_lines.append("")
    ACTIONS_REPORT.write_text("\n".join(act_lines))

def filtered_df(df):
    with st.sidebar:
        st.markdown("---")
        st.caption("Risk filters")
        components = st.multiselect("Component", sorted(df["component"].dropna().unique()))
        bands = st.multiselect("Risk band", ["High","Moderate","Low"])
        statuses = st.multiselect("Action status", sorted(df["status"].dropna().unique()))
        owners = st.multiselect("Owner", sorted(df["action_owner"].dropna().unique()))
        search = st.text_input("Search failure mode / cause")
    view = df.copy()
    if components:
        view = view[view["component"].isin(components)]
    if bands:
        view = view[view["risk_band"].isin(bands)]
    if statuses:
        view = view[view["status"].isin(statuses)]
    if owners:
        view = view[view["action_owner"].isin(owners)]
    if search:
        s = search.lower()
        view = view[
            view["failure_mode"].str.lower().str.contains(s, na=False) |
            view["potential_cause"].str.lower().str.contains(s, na=False) |
            view["recommended_action"].str.lower().str.contains(s, na=False)
        ]
    return view

def investigation_case_card(row):
    band = risk_band(row.get("rpn"))
    variant = "red" if band == "High" else "amber" if band == "Moderate" else "green"
    color = C.get(variant, C.get("blue", "#4ea1ff"))
    return f"""
    <div style="background:{C['surface']};border:1px solid {C['border']};border-left:4px solid {color};
                border-radius:8px;padding:16px 18px;margin-bottom:10px;">
        <div style="font-size:10px;letter-spacing:1.6px;text-transform:uppercase;color:{C['muted']};
                    font-family:'JetBrains Mono',monospace;margin-bottom:6px">
            Risk Signal / FMEA-{row.get('fmea_id', '—')}
        </div>
        <div style="font-size:18px;font-weight:650;color:{C['text']};margin-bottom:6px">
            {row.get('failure_mode', 'Unknown failure mode')}
        </div>
        <div style="font-size:13px;color:{C['subtle']};line-height:1.55;margin-bottom:10px">
            <b>Component:</b> {row.get('component', '—')} &nbsp; | &nbsp;
            <b>RPN:</b> {row.get('rpn', '—')} &nbsp; | &nbsp;
            <b>Band:</b> {band} &nbsp; | &nbsp;
            <b>Status:</b> {row.get('status', '—')}
        </div>
        <div style="font-size:13px;color:{C['subtle']};line-height:1.55">
            <b>Likely cause:</b> {row.get('potential_cause', '—')}<br>
            <b>Recommended action:</b> {row.get('recommended_action', '—')}
        </div>
    </div>
    """


def set_active_risk_case(row):
    st.session_state["active_quality_case"] = {
        "source": "FMEA",
        "case_type": "Risk Signal",
        "fmea_id": str(row.get("fmea_id", "")),
        "component": str(row.get("component", "")),
        "issue": str(row.get("failure_mode", "")),
        "rpn": str(row.get("rpn", "")),
        "status": str(row.get("status", "")),
        "recommended_action": str(row.get("recommended_action", "")),
    }


def investigation_route(row):
    st.markdown(section("Recommended Investigation Route"), unsafe_allow_html=True)
    route_rows = [
        {"Step": "1", "Investigation Action": "Review known failure mode", "Evidence Source": f"FMEA ID {row.get('fmea_id', '—')} / RPN {row.get('rpn', '—')}"},
        {"Step": "2", "Investigation Action": "Check related inspection controls", "Evidence Source": "Inspection Workbench / GD&T requirements"},
        {"Step": "3", "Investigation Action": "Confirm whether failures exist", "Evidence Source": "Inspection results + draft NCRs"},
        {"Step": "4", "Investigation Action": "Open or link NCR/CAPA if recurring", "Evidence Source": "Case Management / 8D workflow"},
        {"Step": "5", "Investigation Action": "Verify effectiveness", "Evidence Source": "Quality Analytics + SPC trends"},
    ]
    st.dataframe(pd.DataFrame(route_rows), use_container_width=True, hide_index=True)


def overview(df):
    total = len(df)
    high = int((df["rpn"] >= HIGH_RPN).sum())
    open_actions = int((df["status"] != "Complete").sum())
    avg_rpn = df["rpn"].mean()
    avg_rev = df["revised_rpn"].mean()
    max_row = df.loc[df["rpn"].idxmax()]

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi_card("Failure Modes", total, sub="Propulsion FMEA"), unsafe_allow_html=True)
    c2.markdown(kpi_card("High Risks", high, "red" if high else "green", sub=f"RPN ≥ {HIGH_RPN}"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Avg RPN", f"{avg_rpn:.1f}", "amber", sub=f"After: {avg_rev:.1f}"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Open Actions", open_actions, "amber" if open_actions else "green", sub="Not complete"), unsafe_allow_html=True)
    c5.markdown(kpi_card("Highest RPN", int(max_row["rpn"]), "red", sub=max_row["failure_mode"]), unsafe_allow_html=True)

    if high:
        st.markdown(alert(f"{high} high-risk signals require mitigation. Highest-priority case is <b>{max_row['failure_mode']}</b> on <b>{max_row['component']}</b>.", "red"), unsafe_allow_html=True)

    st.markdown(section("Open a Risk Case"), unsafe_allow_html=True)
    top_cases = df.sort_values("rpn", ascending=False).head(10).copy()
    selected_case = st.selectbox(
        "Select a risk signal to investigate",
        top_cases["fmea_id"].tolist(),
        format_func=lambda x: f"FMEA-{x} — {top_cases.loc[top_cases['fmea_id'] == x, 'failure_mode'].iloc[0]}"
    )
    case_row = top_cases[top_cases["fmea_id"] == selected_case].iloc[0]
    st.markdown(investigation_case_card(case_row), unsafe_allow_html=True)
    c_case1, c_case2, c_case3 = st.columns(3)
    if c_case1.button("Set as Active Investigation", use_container_width=True):
        set_active_risk_case(case_row)
        st.success("Risk signal saved as the active Quality Detective case.")
    if c_case2.button("Go to Evidence Review", use_container_width=True):
        set_active_risk_case(case_row)
        st.session_state["target_page"] = "2. Inspection & Verification"
        st.rerun()
    if c_case3.button("Go to Verification", use_container_width=True):
        set_active_risk_case(case_row)
        st.session_state["target_page"] = "4. Quality Analytics Dashboard"
        st.rerun()
    investigation_route(case_row)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("Risk Signal Exposure by Component"), unsafe_allow_html=True)
        comp = df.groupby("component").agg(avg_rpn=("rpn","mean"), max_rpn=("rpn","max"), count=("rpn","count")).round(1).reset_index().sort_values("avg_rpn")
        fig = px.bar(comp, x="avg_rpn", y="component", orientation="h", text="avg_rpn")
        fig.add_vline(x=HIGH_RPN, line_dash="dot", annotation_text="High-risk threshold")
        fig.update_layout(xaxis_title="Average RPN", yaxis_title="")
        st.plotly_chart(style_fig(fig, 330), use_container_width=True)
    with col2:
        st.markdown(section("Mitigation Status"), unsafe_allow_html=True)
        status = df["status"].value_counts().reset_index()
        status.columns = ["status","count"]
        fig2 = px.bar(status, x="status", y="count")
        fig2.update_layout(xaxis_title="", yaxis_title="Count")
        st.plotly_chart(style_fig(fig2, 330), use_container_width=True)

    st.markdown(section("How Risk Intelligence Feeds the Investigation"), unsafe_allow_html=True)
    st.markdown("""
**Risk Intelligence** identifies known failure modes and likely causes before defects escalate.  
Those signals guide **Evidence Review** through tighter AQL, CMM checks, and SPC requirements.  
Confirmed failures become **case records** in NCR/CAPA, and **Verification & Monitoring** confirms whether corrective actions actually reduce risk over time.
""")

def risk_register(df):
    view = filtered_df(df)
    st.markdown(section("Risk Signals Register"), unsafe_allow_html=True)
    st.caption(f"Showing {len(view)} of {len(df)} failure modes")

    show_cols = [
        "fmea_id","component","function","failure_mode","failure_effect",
        "severity","occurrence","detection","rpn","risk_band",
        "recommended_action","action_owner","target_completion_date",
        "revised_rpn","status"
    ]
    ranked_view = view[show_cols].sort_values("rpn", ascending=False)
    st.dataframe(ranked_view, use_container_width=True, hide_index=True)

    if not ranked_view.empty:
        st.markdown(section("Investigate Selected Risk Signal"), unsafe_allow_html=True)
        selected_id = st.selectbox(
            "Choose a risk signal",
            ranked_view["fmea_id"].tolist(),
            format_func=lambda x: f"FMEA-{x} — {ranked_view.loc[ranked_view['fmea_id'] == x, 'failure_mode'].iloc[0]}",
            key="risk_signal_case_selector",
        )
        row = ranked_view[ranked_view["fmea_id"] == selected_id].iloc[0]
        st.markdown(investigation_case_card(row), unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        if c1.button("Create Active Risk Case", use_container_width=True):
            set_active_risk_case(row)
            st.success("Active Quality Detective case created from this FMEA signal.")
        if c2.button("Review Inspection Evidence", use_container_width=True):
            set_active_risk_case(row)
            st.session_state["target_page"] = "2. Inspection & Verification"
            st.rerun()
        if c3.button("Monitor in Analytics", use_container_width=True):
            set_active_risk_case(row)
            st.session_state["target_page"] = "4. Quality Analytics Dashboard"
            st.rerun()

    st.download_button(
        "Download Filtered Risk Signals Register",
        data=view.drop(columns=[c for c in ["risk_band","rpn_reduction","rpn_reduction_pct","residual_band"] if c in view.columns]).to_csv(index=False).encode(),
        file_name="filtered_propulsion_fmea.csv",
        mime="text/csv",
        use_container_width=True,
    )

def prioritization(df):
    st.markdown(section("Risk Signal Prioritization"), unsafe_allow_html=True)

    top = df.sort_values("rpn", ascending=False).head(10).copy()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("Top Investigation Priorities"), unsafe_allow_html=True)
        fig = px.bar(top.sort_values("rpn"), x="rpn", y="failure_mode", orientation="h", hover_data=["component","severity","occurrence","detection"])
        fig.add_vline(x=HIGH_RPN, line_dash="dot", annotation_text="High")
        fig.update_layout(xaxis_title="RPN", yaxis_title="")
        st.plotly_chart(style_fig(fig, 420), use_container_width=True)

    with col2:
        st.markdown(section("Risk Pareto"), unsafe_allow_html=True)
        pareto = df.sort_values("rpn", ascending=False).copy()
        pareto["cum_rpn_pct"] = pareto["rpn"].cumsum() / pareto["rpn"].sum() * 100
        p10 = pareto.head(15)
        fig2 = go.Figure()
        fig2.add_bar(x=p10["failure_mode"], y=p10["rpn"], name="RPN")
        fig2.add_trace(go.Scatter(x=p10["failure_mode"], y=p10["cum_rpn_pct"], mode="lines+markers", name="Cumulative %", yaxis="y2"))
        fig2.update_layout(yaxis=dict(title="RPN"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0,100]), xaxis_tickangle=-45)
        st.plotly_chart(style_fig(fig2, 420), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(section("Severity × Occurrence Heatmap"), unsafe_allow_html=True)
        heat = df.pivot_table(index="severity", columns="occurrence", values="rpn", aggfunc="count", fill_value=0)
        fig3 = px.imshow(heat, text_auto=True, aspect="auto", labels=dict(x="Occurrence", y="Severity", color="Count"))
        st.plotly_chart(style_fig(fig3, 350), use_container_width=True)

    with col4:
        st.markdown(section("Before vs After RPN"), unsafe_allow_html=True)
        fig4 = px.scatter(df, x="rpn", y="revised_rpn", size="severity", color="component", hover_name="failure_mode")
        fig4.add_shape(type="line", x0=0, y0=0, x1=max(df["rpn"].max(), 1), y1=max(df["rpn"].max(), 1), line=dict(dash="dot"))
        fig4.update_layout(xaxis_title="Current RPN", yaxis_title="Revised RPN")
        st.plotly_chart(style_fig(fig4, 350), use_container_width=True)

def mitigation_planner(df):
    st.markdown(section("Mitigation Actions"), unsafe_allow_html=True)

    open_actions = df[df["status"] != "Complete"].copy()
    overdue = pd.to_datetime(open_actions["target_completion_date"], errors="coerce").dt.date < date.today()
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi_card("Total Actions", len(df), sub="All FMEA actions"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Complete", int((df["status"]=="Complete").sum()), "green"), unsafe_allow_html=True)
    c3.markdown(kpi_card("In Progress", int((df["status"]=="In Progress").sum()), "amber"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Overdue", int(overdue.sum()), "red" if overdue.sum() else "green"), unsafe_allow_html=True)

    st.markdown(section("Open Mitigation Backlog"), unsafe_allow_html=True)
    show = open_actions[[
        "fmea_id","component","failure_mode","rpn","recommended_action",
        "action_owner","target_completion_date","status","revised_rpn","rpn_reduction_pct"
    ]].sort_values(["status","rpn"], ascending=[True, False])
    st.dataframe(show, use_container_width=True, hide_index=True)

    selected_id = st.selectbox("Update action status", df.sort_values("rpn", ascending=False)["fmea_id"].tolist(), format_func=lambda x: f"{x} — {df.loc[df['fmea_id']==x, 'failure_mode'].iloc[0]}")
    row = df[df["fmea_id"] == selected_id].iloc[0]
    with st.form("update_fmea_action"):
        new_status = st.selectbox("Status", ["Open","In Progress","Complete"], index=["Open","In Progress","Complete"].index(row["status"]) if row["status"] in ["Open","In Progress","Complete"] else 0)
        new_owner = st.text_input("Owner", row["action_owner"])
        new_date = st.text_input("Target completion date", str(row["target_completion_date"]))
        new_action = st.text_area("Recommended action", row["recommended_action"])
        submit = st.form_submit_button("Save Mitigation Update")
    if submit:
        df.loc[df["fmea_id"] == selected_id, ["status","action_owner","target_completion_date","recommended_action"]] = [new_status, new_owner, new_date, new_action]
        save_fmea(df)
        make_reports(load_fmea())
        st.success("Mitigation updated and FMEA reports regenerated.")
        st.rerun()

def integration(df):
    st.markdown(section("Evidence Chain: Inspection + NCR/CAPA Link"), unsafe_allow_html=True)

    inspection_triggers = df[(df["severity"] >= 7) & (df["occurrence"] >= 4)].copy()
    bracket = df[df["component"].str.contains("Motor Mount Bracket", case=False, na=False)].copy()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(section("Inspection Evidence Triggers"), unsafe_allow_html=True)
        st.markdown("""
High S×O risk signals should drive stronger evidence collection: tighter sampling, CMM verification, and SPC monitoring.
""")
        st.dataframe(
            inspection_triggers[["fmea_id","component","failure_mode","severity","occurrence","detection","rpn","recommended_action"]].sort_values("rpn", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.markdown(section("GD&T/CMM Evidence Links"), unsafe_allow_html=True)
        st.markdown("""
Motor Mount Bracket risk signals connect directly to Inspection Workbench CMM/GD&T evidence.
""")
        st.dataframe(
            bracket[["fmea_id","failure_mode","failure_effect","potential_cause","rpn","recommended_action","status"]].sort_values("rpn", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown(section("Suggested Evidence Collection Plan from FMEA"), unsafe_allow_html=True)
    suggestions = []
    for _, r in bracket.iterrows():
        fm = str(r["failure_mode"]).lower()
        if "hole position" in fm:
            feature = "HOLE_1_POSITION / HOLE_2_POSITION / HOLE_3_POSITION / HOLE_4_POSITION"
            check = "True position CMM inspection + SPC on CNC fixture"
        elif "flatness" in fm:
            feature = "MOUNTING_FACE_FLATNESS"
            check = "Flatness CMM check + stress relief process control"
        elif "crack" in fm:
            feature = "MOUNTING_FEATURE_VISUAL"
            check = "Visual + dye penetrant inspection"
        elif "material" in fm:
            feature = "MATERIAL_CERT / PMI"
            check = "100% PMI scan at receiving"
        else:
            feature = "BRACKET_FEATURE"
            check = "Enhanced receiving / in-process inspection"
        suggestions.append({
            "FMEA ID": r["fmea_id"],
            "Failure Mode": r["failure_mode"],
            "Inspection Feature": feature,
            "Control Plan Link": check,
            "Risk Driver": f"S={r['severity']}, O={r['occurrence']}, D={r['detection']}, RPN={r['rpn']}",
        })
    st.dataframe(pd.DataFrame(suggestions), use_container_width=True, hide_index=True)

    ncr_path = DATA_DIR / "draft_ncrs.csv"
    if ncr_path.exists():
        try:
            ncr_df = pd.read_csv(ncr_path)
            st.markdown(section("Current Inspection Evidence Available for Case Management"), unsafe_allow_html=True)
            st.info(f"{len(ncr_df)} draft NCR records are available from Inspection Workbench at data/draft_ncrs.csv.")
            st.dataframe(ncr_df.head(20), use_container_width=True, hide_index=True)
        except Exception:
            pass

def reports(df):
    st.markdown(section("Case Reports"), unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    if col1.button("Regenerate Reports", type="primary", use_container_width=True):
        make_reports(df)
        st.success("Reports regenerated in /reports.")

    for path, label in [(SUMMARY_REPORT, "Summary Report"), (TOP_10_REPORT, "Top 10 Risks"), (ACTIONS_REPORT, "Recommended Actions")]:
        st.markdown(section(label), unsafe_allow_html=True)
        if path.exists():
            content = path.read_text()
            st.download_button(f"Download {label}", data=content, file_name=path.name, mime="text/markdown", use_container_width=True)
            with st.expander(f"Preview {label}"):
                st.markdown(content)
        else:
            st.warning(f"{path.name} not found. Click Regenerate Reports.")

    if FMEA_XLSX.exists():
        st.download_button("Download FMEA Excel Workbook", data=FMEA_XLSX.read_bytes(), file_name="propulsion_fmea.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

def render():
    apply_styles()
    st.markdown(page_header("1. Risk Intelligence Center", "Quality Detective workspace for investigating known failure modes, risk signals, mitigation actions, and downstream inspection controls."), unsafe_allow_html=True)
    st.markdown("---")

    df = load_fmea()
    if df.empty:
        st.warning("propulsion_fmea.csv not found in data/. Add the FMEA CSV or run the generator.")
        return

    active_case = st.session_state.get("active_quality_case")
    if active_case:
        st.markdown(
            alert(
                f"<b>Active Quality Detective Case:</b> {active_case.get('issue', 'Unknown issue')} "
                f"| Source: {active_case.get('source', '—')} "
                f"| Component: {active_case.get('component', '—')} "
                f"| RPN: {active_case.get('rpn', '—')}",
                "blue",
            ),
            unsafe_allow_html=True,
        )

    tabs = st.tabs([
        "Investigation Overview",
        "Risk Signals",
        "Prioritization",
        "Mitigation Actions",
        "Evidence Chain",
        "Case Reports",
    ])

    with tabs[0]:
        overview(df)
    with tabs[1]:
        risk_register(df)
    with tabs[2]:
        prioritization(df)
    with tabs[3]:
        mitigation_planner(df)
    with tabs[4]:
        integration(df)
    with tabs[5]:
        reports(df)
