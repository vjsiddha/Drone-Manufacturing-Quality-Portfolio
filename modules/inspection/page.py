from pathlib import Path
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"

def render():
    st.title("2. Inspection & Verification")

    results_path = DATA_DIR / "inspection_results.csv"
    draft_ncr_path = DATA_DIR / "draft_ncrs.csv"

    if results_path.exists():
        st.subheader("Inspection Results")
        df = pd.read_csv(results_path)
        st.dataframe(df, use_container_width=True)

        if "result" in df.columns:
            st.metric("Failed Features", (df["result"] == "FAIL").sum())
            st.metric("Passed Features", (df["result"] == "PASS").sum())
    else:
        st.warning("inspection_results.csv not found in data/.")

    if draft_ncr_path.exists():
        st.subheader("Draft NCRs Generated")
        ncr_df = pd.read_csv(draft_ncr_path)
        st.dataframe(ncr_df, use_container_width=True)
        st.metric("Draft NCR Count", len(ncr_df))