from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"

def render():
    st.title("4. Quality Analytics Dashboard")

    production_path = DATA_DIR / "production_records.csv"
    inspection_path = DATA_DIR / "inspection_records.csv"
    supplier_path = DATA_DIR / "suppliers.csv"
    spc_path = DATA_DIR / "spc_measurements.csv"

    if production_path.exists():
        prod = pd.read_csv(production_path)

        st.subheader("Production KPIs")

        total_completed = prod["units_completed"].sum()
        total_passed = prod["units_passed_first_time"].sum()
        total_scrap = prod["units_scrapped"].sum()
        total_rework = prod["units_reworked"].sum()

        fpy = total_passed / total_completed if total_completed else 0
        scrap_rate = total_scrap / total_completed if total_completed else 0
        rework_rate = total_rework / total_completed if total_completed else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("First Pass Yield", f"{fpy:.1%}")
        c2.metric("Scrap Rate", f"{scrap_rate:.1%}")
        c3.metric("Rework Rate", f"{rework_rate:.1%}")

        if "station_name" in prod.columns:
            st.subheader("FPY by Station")
            station = prod.groupby("station_name").agg(
                units_completed=("units_completed", "sum"),
                units_passed_first_time=("units_passed_first_time", "sum")
            ).reset_index()
            station["fpy"] = station["units_passed_first_time"] / station["units_completed"]
            st.plotly_chart(px.bar(station, x="station_name", y="fpy"), use_container_width=True)

    if inspection_path.exists():
        insp = pd.read_csv(inspection_path)

        st.subheader("Defect Pareto")
        if "defect_type" in insp.columns:
            defects = insp["defect_type"].value_counts().head(10).reset_index()
            defects.columns = ["defect_type", "count"]
            st.plotly_chart(px.bar(defects, x="defect_type", y="count"), use_container_width=True)

    if spc_path.exists():
        st.subheader("SPC Monitoring")
        spc = pd.read_csv(spc_path)
        st.dataframe(spc.head(100), use_container_width=True)

        numeric_cols = spc.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            selected = st.selectbox("Select SPC measurement column", numeric_cols)
            mean = spc[selected].mean()
            std = spc[selected].std()
            ucl = mean + 3 * std
            lcl = mean - 3 * std

            st.metric("Mean", f"{mean:.4f}")
            st.metric("UCL", f"{ucl:.4f}")
            st.metric("LCL", f"{lcl:.4f}")

            fig = px.line(spc.reset_index(), x="index", y=selected)
            fig.add_hline(y=mean)
            fig.add_hline(y=ucl)
            fig.add_hline(y=lcl)
            st.plotly_chart(fig, use_container_width=True)