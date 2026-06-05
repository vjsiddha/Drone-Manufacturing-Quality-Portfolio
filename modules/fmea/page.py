from pathlib import Path
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"

def render():
    st.title("1. Risk Assessment / FMEA")

    fmea_path = DATA_DIR / "propulsion_fmea.csv"

    if not fmea_path.exists():
        st.warning("propulsion_fmea.csv not found in data/. Run the FMEA generator first.")
        return

    df = pd.read_csv(fmea_path)

    st.subheader("FMEA Overview")
    st.dataframe(df, use_container_width=True)

    if "rpn" in df.columns:
        st.subheader("Top 10 Risks by RPN")
        st.dataframe(df.sort_values("rpn", ascending=False).head(10), use_container_width=True)

    report_path = REPORTS_DIR / "fmea_summary_report.md"
    if report_path.exists():
        st.subheader("FMEA Summary Report")
        st.markdown(report_path.read_text())