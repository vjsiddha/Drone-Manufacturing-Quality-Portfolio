
"""
Root Streamlit app for AeroQMS — Quality Detective investigation platform.

Run from repo root:
    streamlit run app.py --server.address 0.0.0.0 --server.port 8502
"""

from pathlib import Path
from datetime import date
import importlib

import pandas as pd
import streamlit as st

try:
    from shared_styles import apply_styles, kpi_card, alert, section, page_header, badge, C
except Exception:
    C = {
        "bg": "#08090a", "surface": "#0f1117", "surface2": "#161b22",
        "border": "#1e2530", "border2": "#2a3140", "text": "#e2e8f0",
        "muted": "#64748b", "subtle": "#94a3b8", "red": "#e05252",
        "amber": "#c9952a", "green": "#3d9e6b", "blue": "#4a7fa5",
    }
    def apply_styles(): return None
    def kpi_card(label, value, color="", sub=""):
        color_map = {"green": C["green"], "red": C["red"], "amber": C["amber"], "blue": C["blue"]}
        val_color = color_map.get(color, C["text"])
        return f"<div style='background:{C['surface']};border:1px solid {C['border']};border-radius:8px;padding:16px;'><div style='font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:{C['muted']}'>{label}</div><div style='font-size:28px;font-weight:700;color:{val_color};margin:6px 0'>{value}</div><div style='font-size:12px;color:{C['muted']}'>{sub}</div></div>"
    def alert(text, variant="blue"):
        color = {"red": C["red"], "amber": C["amber"], "green": C["green"], "blue": C["blue"]}.get(variant, C["blue"])
        return f"<div style='background:{C['surface']};border-left:4px solid {color};padding:12px 14px;border-radius:6px;color:{C['subtle']}'>{text}</div>"
    def section(text):
        return f"<div style='font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:{C['blue']};border-bottom:1px solid {C['border']};padding-bottom:8px;margin:22px 0 14px'>{text}</div>"
    def page_header(title, sub=""):
        return f"<div style='font-size:26px;font-weight:700;color:{C['text']}'>{title}</div><div style='color:{C['muted']}'>{sub}</div>"
    def badge(text, variant="neutral"): return f"<span>{text}</span>"


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="AeroQMS | Quality Detective",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = [
    "Home",
    "1. Risk Intelligence / FMEA",
    "2. Evidence Review / Inspection",
    "3. Case Management / NCR-CAPA",
    "4. Verification & Monitoring",
]

if "target_page" not in st.session_state:
    st.session_state["target_page"] = "Home"

def _go(page_name, action_hint=None):
    """
    Route from homepage action buttons to the selected module.
    Uses target_page instead of the radio widget key so Streamlit does not throw
    session_state modification errors.
    """
    st.session_state["target_page"] = page_name
    if action_hint:
        st.session_state["workflow_action_hint"] = action_hint
    st.rerun()

def _read_csv(name: str, parse_dates=None) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, parse_dates=parse_dates)
    except Exception:
        return pd.read_csv(path)

@st.cache_data(show_spinner=False)
def load_home_data():
    fmea = _read_csv("propulsion_fmea.csv")
    inspection = _read_csv("inspection_results.csv")
    draft_ncrs = _read_csv("draft_ncrs.csv")
    production = _read_csv("production_records.csv", parse_dates=["date"])
    inspection_records = _read_csv("inspection_records.csv", parse_dates=["date"])
    spc = _read_csv("spc_measurements.csv", parse_dates=["date"])
    ncr = pd.DataFrame()
    capa = pd.DataFrame()
    try:
        from modules.ncr_capa.database import init_db, get_all_ncrs, get_all_capas
        init_db()
        ncr = get_all_ncrs()
        capa = get_all_capas()
    except Exception:
        ncr = _read_csv("ncr_records.csv", parse_dates=["date_opened", "date_closed"])
    return fmea, inspection, draft_ncrs, production, inspection_records, ncr, capa, spc

def pct(num, den):
    try:
        den = float(den); num = float(num)
    except Exception:
        return 0.0
    return 0.0 if den == 0 else num / den * 100

def safe_count(df, condition=None):
    if df.empty: return 0
    if condition is None: return len(df)
    try: return int(condition(df).sum())
    except Exception: return 0

def metric_color(value, good, warn, lower_is_better=False):
    if lower_is_better:
        return "green" if value <= good else "amber" if value <= warn else "red"
    return "green" if value >= good else "amber" if value >= warn else "red"

def compute_home_metrics():
    fmea, inspection, draft_ncrs, production, inspection_records, ncr, capa, spc = load_home_data()
    high_rpn = safe_count(fmea, lambda d: pd.to_numeric(d["rpn"], errors="coerce") >= 150) if "rpn" in fmea.columns else 0
    avg_rpn = f"{pd.to_numeric(fmea['rpn'], errors='coerce').mean():.1f}" if not fmea.empty and "rpn" in fmea.columns else "N/A"
    failed_features = safe_count(inspection, lambda d: d["result"].astype(str).str.upper() == "FAIL") if "result" in inspection.columns else 0
    total_features = len(inspection) if not inspection.empty else 0
    inspection_pass_rate = pct(total_features - failed_features, total_features)
    open_ncr = safe_count(ncr, lambda d: d["status"].astype(str) != "Closed") if "status" in ncr.columns else 0
    critical_ncr = safe_count(ncr, lambda d: d["severity"].astype(str) == "Critical") if "severity" in ncr.columns else 0
    open_capa = 0
    overdue_capa = 0
    if not capa.empty:
        status_col = "closure_status" if "closure_status" in capa.columns else "status" if "status" in capa.columns else None
        if status_col:
            open_capa = int((capa[status_col].astype(str) != "Closed").sum())
        if "due_date" in capa.columns and status_col:
            due = pd.to_datetime(capa["due_date"], errors="coerce").dt.date
            overdue_capa = int(((due < date.today()) & (capa[status_col].astype(str) != "Closed")).sum())
    fpy = 0.0
    if not production.empty and {"units_passed_first_time", "units_completed"}.issubset(production.columns):
        fpy = pct(production["units_passed_first_time"].sum(), production["units_completed"].sum())
    defect_rate = 0.0
    if not inspection_records.empty and {"quantity_failed", "quantity_inspected"}.issubset(inspection_records.columns):
        defect_rate = pct(inspection_records["quantity_failed"].sum(), inspection_records["quantity_inspected"].sum())
    elif total_features:
        defect_rate = pct(failed_features, total_features)
    out_of_spec = 0.0
    if not spc.empty and "out_of_spec" in spc.columns:
        out_of_spec = float(pd.to_numeric(spc["out_of_spec"], errors="coerce").fillna(0).mean() * 100)
    return {
        "fmea": fmea, "inspection": inspection, "draft_ncrs": draft_ncrs, "production": production,
        "inspection_records": inspection_records, "ncr": ncr, "capa": capa, "spc": spc,
        "high_rpn": high_rpn, "avg_rpn": avg_rpn, "failed_features": failed_features,
        "total_features": total_features, "inspection_pass_rate": inspection_pass_rate,
        "open_ncr": open_ncr, "critical_ncr": critical_ncr, "open_capa": open_capa,
        "overdue_capa": overdue_capa, "fpy": fpy, "defect_rate": defect_rate, "out_of_spec": out_of_spec,
    }

def workflow_card(title, stage, description, primary_action, page_name, accent="blue"):
    color = C.get(accent, C.get("blue", "#4a7fa5"))
    st.markdown(
        f"""
        <div style="background:{C['surface']};border:1px solid {C['border']};border-top:3px solid {color};
                    border-radius:8px;padding:18px 18px 16px;min-height:188px;">
            <div style="font-size:10px;letter-spacing:1.8px;text-transform:uppercase;color:{C['muted']};
                        font-family:'JetBrains Mono',monospace;margin-bottom:8px">{stage}</div>
            <div style="font-size:18px;font-weight:650;color:{C['text']};margin-bottom:10px">{title}</div>
            <div style="font-size:13px;line-height:1.55;color:{C['subtle']};min-height:66px">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(primary_action, key=f"launch_{page_name}_{title}", use_container_width=True):
        _go(page_name, title)

def investigation_step(number, title, detail, page_name, button_label):
    st.markdown(
        f"""
        <div style="background:{C['surface']};border:1px solid {C['border']};
                    border-radius:8px;padding:14px 16px;margin-bottom:10px;">
            <div style="font-size:10px;letter-spacing:1.8px;text-transform:uppercase;color:{C['muted']};
                        font-family:'JetBrains Mono',monospace;margin-bottom:6px">Step {number}</div>
            <div style="font-size:15px;font-weight:650;color:{C['text']};margin-bottom:4px">{title}</div>
            <div style="font-size:12px;line-height:1.45;color:{C['subtle']};margin-bottom:10px">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(button_label, key=f"case_step_{number}_{page_name}", use_container_width=True):
        _go(page_name, title)


def case_file_card(case_id, issue_type, issue_detail, priority, target_title):
    variant = "red" if priority == "Critical" else "amber" if priority == "High" else "blue"
    st.markdown(
        alert(
            f"""
            <b>Active Case File:</b> {case_id}<br>
            <b>Issue Type:</b> {issue_type}<br>
            <b>Concern:</b> {issue_detail or 'No specific concern entered yet'}<br>
            <b>Priority:</b> {priority}<br>
            <b>Recommended Starting Point:</b> {target_title}
            """,
            variant,
        ),
        unsafe_allow_html=True,
    )


def home_page():
    data = compute_home_metrics()

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, rgba(74,127,165,0.16), rgba(201,149,42,0.08));
                    border:1px solid {C['border']};border-radius:12px;padding:30px 32px;margin-bottom:20px;">
            <div style="font-size:11px;letter-spacing:2.2px;text-transform:uppercase;color:{C['blue']};
                        font-family:'JetBrains Mono',monospace;margin-bottom:10px">
                Quality Engineering Investigation Assistant
            </div>
            <div style="font-size:40px;font-weight:780;color:{C['text']};letter-spacing:-1px;margin-bottom:10px">
                AeroQMS Quality Detective
            </div>
            <div style="font-size:15px;color:{C['subtle']};line-height:1.65;max-width:1050px">
                Investigate manufacturing quality issues from first signal to verified corrective action.
                Connect risk clues, inspection evidence, NCR/CAPA case work, and SPC verification in one guided workflow.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(kpi_card("Risk Clues", data["high_rpn"], "red" if data["high_rpn"] else "green", f"Avg RPN {data['avg_rpn']}"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Evidence Pass Rate", f"{data['inspection_pass_rate']:.1f}%", metric_color(data["inspection_pass_rate"], 95, 85), f"{data['failed_features']} failed features"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Draft Cases", len(data["draft_ncrs"]), "amber" if len(data["draft_ncrs"]) else "green", "Ready for NCR import"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Open Cases", data["open_ncr"], metric_color(data["open_ncr"], 20, 50, True), f"{data['critical_ncr']} critical"), unsafe_allow_html=True)
    c5.markdown(kpi_card("Open CAPAs", data["open_capa"], metric_color(data["open_capa"], 10, 25, True), f"{data['overdue_capa']} overdue"), unsafe_allow_html=True)
    c6.markdown(kpi_card("Process Health", f"{data['fpy']:.1f}%", metric_color(data["fpy"], 90, 80), f"Defect {data['defect_rate']:.2f}%"), unsafe_allow_html=True)

    st.markdown(section("Open a Quality Investigation"), unsafe_allow_html=True)
    left, right = st.columns([1.05, 1])
    with left:
        issue_type = st.selectbox(
            "What quality issue are you investigating?",
            [
                "Potential risk before production",
                "Measured part failed inspection",
                "Non-conformance needs investigation",
                "Supplier performance issue",
                "Process drift or SPC instability",
                "Overall quality health review",
            ],
        )
        issue_detail = st.text_input(
            "Describe the signal, part, lot, supplier, feature, or process",
            placeholder="Example: MMB-001 hole position failures on LOT-203 from SUP-003",
        )
        priority = st.select_slider("Case priority", options=["Low", "Medium", "High", "Critical"], value="High")

    with right:
        route_map = {
            "Potential risk before production": (
                "Risk Intelligence",
                "Start with FMEA risk clues, RPN ranking, potential causes, and mitigation controls.",
                "1. Risk Intelligence / FMEA",
            ),
            "Measured part failed inspection": (
                "Evidence Review",
                "Start with GD&T evidence, true-position math, failed features, reports, and draft NCRs.",
                "2. Evidence Review / Inspection",
            ),
            "Non-conformance needs investigation": (
                "Case Management",
                "Start with NCR intake, containment, RCA, CAPA creation, 5-Why, Fishbone, and 8D.",
                "3. Case Management / NCR-CAPA",
            ),
            "Supplier performance issue": (
                "Case Management",
                "Start with supplier-linked NCRs, repeated defect signals, and supplier feedback reports.",
                "3. Case Management / NCR-CAPA",
            ),
            "Process drift or SPC instability": (
                "Verification & Monitoring",
                "Start with SPC charts, Cp/Cpk, FPY, defect trends, supplier scorecards, and improvement backlog.",
                "4. Verification & Monitoring",
            ),
            "Overall quality health review": (
                "Verification & Monitoring",
                "Start with executive quality signals, lifecycle performance, and continuous improvement status.",
                "4. Verification & Monitoring",
            ),
        }
        target_title, target_desc, target_page = route_map[issue_type]
        case_seed = issue_detail.strip() or issue_type
        case_id = "CASE-" + str(abs(hash(case_seed)) % 100000).zfill(5)
        case_file_card(case_id, issue_type, issue_detail, priority, target_title)
        st.markdown(alert(f"<b>Recommended next move:</b> {target_desc}", "blue"), unsafe_allow_html=True)
        if st.button("Start Investigation", type="primary", use_container_width=True):
            st.session_state["active_case"] = {
                "case_id": case_id,
                "issue_type": issue_type,
                "issue_detail": issue_detail,
                "priority": priority,
                "recommended_module": target_title,
            }
            _go(target_page, f"{case_id} — {target_title}")

    st.markdown(section("Recommended Investigation Path"), unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        investigation_step(
            "01",
            "Risk Clues",
            "Check known failure modes, RPN severity, likely causes, and mitigations.",
            "1. Risk Intelligence / FMEA",
            "Review Risks",
        )
    with s2:
        investigation_step(
            "02",
            "Evidence Review",
            "Verify inspection evidence, true-position failures, margins, and feature-level data.",
            "2. Evidence Review / Inspection",
            "Review Evidence",
        )
    with s3:
        investigation_step(
            "03",
            "Case File",
            "Create or import NCRs and document containment, disposition, and ownership.",
            "3. Case Management / NCR-CAPA",
            "Open Case Mgmt",
        )
    with s4:
        investigation_step(
            "04",
            "Root Cause",
            "Run 5-Why, Fishbone, CAPA planning, and generate 8D reports.",
            "3. Case Management / NCR-CAPA",
            "Run RCA / CAPA",
        )
    with s5:
        investigation_step(
            "05",
            "Verify Fix",
            "Use SPC, FPY, defect trends, and process capability to confirm effectiveness.",
            "4. Verification & Monitoring",
            "Verify in SPC",
        )

    st.markdown(section("Investigation Modules"), unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        workflow_card("Risk Intelligence", "01 / Prevention", "Find risk clues in FMEA: high RPNs, potential causes, recommended mitigations, and open actions.", "Open Risk Clues", "1. Risk Intelligence / FMEA", "amber")
    with m2:
        workflow_card("Evidence Review", "02 / Detection", "Analyze GD&T inspection evidence, true-position calculations, failed features, and draft NCR generation.", "Review Evidence", "2. Evidence Review / Inspection", "blue")
    with m3:
        workflow_card("Case Management", "03 / Correction", "Manage NCRs, CAPAs, 5-Why/Fishbone RCA, supplier feedback, and 8D reporting.", "Open Case Files", "3. Case Management / NCR-CAPA", "red")
    with m4:
        workflow_card("Verification & Monitoring", "04 / Verification", "Monitor FPY, defects, SPC control charts, Cp/Cpk, and CAPA effectiveness.", "Verify Process Health", "4. Verification & Monitoring", "green")

    st.markdown(section("Active Quality Signals"), unsafe_allow_html=True)
    alerts = []
    if data["high_rpn"] > 0:
        alerts.append(("red", f"<b>Risk signal:</b> {data['high_rpn']} high-RPN FMEA items may need mitigation."))
    if data["failed_features"] > 0:
        alerts.append(("amber", f"<b>Evidence signal:</b> {data['failed_features']} failed GD&T inspection features detected."))
    if len(data["draft_ncrs"]) > 0:
        alerts.append(("amber", f"<b>Case intake signal:</b> {len(data['draft_ncrs'])} draft NCRs are ready to import."))
    if data["open_ncr"] > 0:
        alerts.append(("red" if data["critical_ncr"] else "amber", f"<b>Case workload signal:</b> {data['open_ncr']} open NCRs, including {data['critical_ncr']} critical."))
    if data["overdue_capa"] > 0:
        alerts.append(("red", f"<b>Action signal:</b> {data['overdue_capa']} CAPAs are overdue and need effectiveness follow-up."))
    if data["out_of_spec"] > 0:
        alerts.append(("amber", f"<b>Process signal:</b> SPC shows {data['out_of_spec']:.2f}% out-of-spec measurements."))
    if not alerts:
        st.markdown(alert("No urgent quality investigation signals detected. Review monitoring for routine process health.", "green"), unsafe_allow_html=True)
    else:
        for variant, text in alerts[:6]:
            st.markdown(alert(text, variant), unsafe_allow_html=True)

    st.markdown(section("Case Evidence Map"), unsafe_allow_html=True)
    flow_rows = [
        {"Investigation Area": "Risk Clues", "Evidence Source": "FMEA S/O/D scoring", "Current Signal": f"{data['high_rpn']} high-risk items", "Next Move": "Prioritize controls"},
        {"Investigation Area": "Inspection Evidence", "Evidence Source": "GD&T measurements", "Current Signal": f"{data['failed_features']} failed features", "Next Move": "Generate or review NCRs"},
        {"Investigation Area": "Case Management", "Evidence Source": "NCR/CAPA records", "Current Signal": f"{data['open_ncr']} open NCRs / {data['open_capa']} open CAPAs", "Next Move": "Contain, investigate, correct"},
        {"Investigation Area": "Verification", "Evidence Source": "Production + SPC data", "Current Signal": f"{data['fpy']:.1f}% FPY / {data['defect_rate']:.2f}% defect rate", "Next Move": "Verify effectiveness"},
    ]
    st.dataframe(pd.DataFrame(flow_rows), use_container_width=True, hide_index=True)

    st.markdown(section("Quick Investigation Actions"), unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    if q1.button("Investigate Top Risks", use_container_width=True):
        _go("1. Risk Intelligence / FMEA", "Top Risk Investigation")
    if q2.button("Investigate Inspection Failures", use_container_width=True):
        _go("2. Evidence Review / Inspection", "Inspection Evidence Review")
    if q3.button("Investigate Open Cases", use_container_width=True):
        _go("3. Case Management / NCR-CAPA", "Open Case Review")
    if q4.button("Investigate Process Health", use_container_width=True):
        _go("4. Verification & Monitoring", "SPC / Process Health Review")

def load_module_page(module_name: str, display_name: str):
    try:
        module = importlib.import_module(module_name)
        for function_name in ["render", "main", "app", "page"]:
            if hasattr(module, function_name):
                getattr(module, function_name)()
                return
        st.error(f"{display_name} was imported, but no render/main/app/page function was found.")
        st.info(f"Add one function named `render()` to `{module_name}.py`.")
    except Exception as e:
        st.error(f"Could not load {display_name}.")
        st.exception(e)

def main():
    apply_styles()

    # Single source of truth for routing.
    # Do NOT use key="page" on the radio, because homepage buttons need to update
    # navigation programmatically.
    if "target_page" not in st.session_state:
        st.session_state["target_page"] = "Home"

    st.sidebar.markdown(
        f"""
        <div style="padding:18px 0 10px">
            <div style="font-size:22px;font-weight:750;color:{C['text']};margin-bottom:4px">AeroQMS</div>
            <div style="font-size:11px;letter-spacing:1.7px;text-transform:uppercase;color:{C['muted']};
                        font-family:'JetBrains Mono',monospace">Quality Detective</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_page = st.session_state.get("target_page", "Home")
    current_index = PAGES.index(current_page) if current_page in PAGES else 0

    page = st.sidebar.radio(
        "Navigate",
        PAGES,
        index=current_index,
    )

    # Keep sidebar clicks and homepage button routing synchronized.
    st.session_state["target_page"] = page

    st.sidebar.divider()
    st.sidebar.caption("Quality investigation assistant")

    # Optional context banner after a homepage workflow button routes the user.
    action_hint = st.session_state.pop("workflow_action_hint", None)
    if action_hint and page != "Home":
        st.markdown(
            alert(
                f"Opened workflow: <b>{action_hint}</b>. Continue from the relevant tab/action in this module.",
                "blue",
            ),
            unsafe_allow_html=True,
        )

    if page == "Home":
        home_page()
    elif page == "1. Risk Intelligence / FMEA":
        load_module_page("modules.fmea.page", "Risk Intelligence / FMEA")
    elif page == "2. Evidence Review / Inspection":
        load_module_page("modules.inspection.page", "Evidence Review / Inspection")
    elif page == "3. Case Management / NCR-CAPA":
        load_module_page("modules.ncr_capa.page", "Case Management / NCR-CAPA")
    elif page == "4. Verification & Monitoring":
        load_module_page("modules.dashboard.page", "Verification & Monitoring")


if __name__ == "__main__":
    main()
