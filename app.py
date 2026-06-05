"""
Root Streamlit app for the integrated Drone Manufacturing Quality Lifecycle System.

Run from repo root:
    streamlit run app.py --server.address 0.0.0.0 --server.port 8502
"""

from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


st.set_page_config(
    page_title="Drone Manufacturing Quality Lifecycle",
    page_icon="🛠️",
    layout="wide",
)


def home_page():
    st.title("Drone Manufacturing Quality Lifecycle System")

    st.markdown(
        """
        This system connects the major stages of a manufacturing quality lifecycle:

        **Risk Assessment → Inspection → NCR/CAPA → Analytics & SPC**

        The goal is to show how quality data flows from early risk identification,
        through inspection failures, into corrective action workflows, and finally
        into quality performance monitoring.
        """
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.subheader("1. Risk Assessment")
        st.markdown(
            """
            **FMEA**

            Identifies potential propulsion system failure modes before production.
            """
        )

    with col2:
        st.subheader("2. Inspection")
        st.markdown(
            """
            **GD&T Verification**

            Evaluates measured part data against engineering requirements.
            """
        )

    with col3:
        st.subheader("3. NCR / CAPA")
        st.markdown(
            """
            **Quality Management**

            Converts failures into NCRs, RCA, CAPA, and 8D reports.
            """
        )

    with col4:
        st.subheader("4. Analytics")
        st.markdown(
            """
            **Dashboard + SPC**

            Tracks quality KPIs, supplier performance, and process stability.
            """
        )

    st.divider()

    st.subheader("End-to-End Flow")

    st.code(
        """
FMEA identifies potential risk
        ↓
GD&T inspection detects actual defect
        ↓
Draft NCR is generated
        ↓
NCR/CAPA system manages investigation and corrective action
        ↓
Dashboard and SPC monitor whether quality improved
        """,
        language="text",
    )

    st.subheader("Shared System Data")

    data_files = sorted([p.name for p in DATA_DIR.glob("*")])

    if data_files:
        st.write("Files currently available in `data/`:")
        st.dataframe({"file": data_files}, use_container_width=True)
    else:
        st.warning("No files found in the shared `data/` folder yet.")


def load_module_page(module_name: str, display_name: str):
    """
    Imports and runs a module page safely.
    Each module should expose one of these:
        - render()
        - main()
        - app()
        - page()
    """

    try:
        module = __import__(module_name, fromlist=[""])

        for function_name in ["render", "main", "app", "page"]:
            if hasattr(module, function_name):
                getattr(module, function_name)()
                return

        st.error(
            f"{display_name} was imported, but no render/main/app/page function was found."
        )
        st.info(
            f"Add one function named `render()` to `{module_name}.py`."
        )

    except Exception as e:
        st.error(f"Could not load {display_name}.")
        st.exception(e)


def main():
    st.sidebar.title("Quality Lifecycle")

    page = st.sidebar.radio(
        "Navigate",
        [
            "Home",
            "1. Risk Assessment / FMEA",
            "2. Inspection & Verification",
            "3. NCR / CAPA Management",
            "4. Quality Analytics Dashboard",
        ],
    )

    st.sidebar.divider()
    st.sidebar.caption("Integrated Quality Lifecycle System")

    if page == "Home":
        home_page()

    elif page == "1. Risk Assessment / FMEA":
        load_module_page(
            "modules.fmea.page",
            "Risk Assessment / FMEA",
        )

    elif page == "2. Inspection & Verification":
        load_module_page(
            "modules.inspection.page",
            "Inspection & Verification",
        )

    elif page == "3. NCR / CAPA Management":
        load_module_page(
            "modules.ncr_capa.page",
            "NCR / CAPA Management",
        )

    elif page == "4. Quality Analytics Dashboard":
        load_module_page(
            "modules.dashboard.page",
            "Quality Analytics Dashboard",
        )


if __name__ == "__main__":
    main()