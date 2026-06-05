from pathlib import Path
import streamlit as st

from modules.ncr_capa.database import init_db, get_all_ncrs, get_all_capas

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"

def render():
    st.title("3. NCR / CAPA Management")

    init_db()

    ncr_df = get_all_ncrs()
    capa_df = get_all_capas()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total NCRs", len(ncr_df))
        if "status" in ncr_df.columns:
            st.dataframe(ncr_df["status"].value_counts().reset_index(), use_container_width=True)

    with col2:
        st.metric("Total CAPAs", len(capa_df))
        if "closure_status" in capa_df.columns:
            st.dataframe(capa_df["closure_status"].value_counts().reset_index(), use_container_width=True)

    st.subheader("NCR Records")
    st.dataframe(ncr_df, use_container_width=True)

    st.subheader("CAPA Records")
    st.dataframe(capa_df, use_container_width=True)