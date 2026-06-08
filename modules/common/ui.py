import streamlit as st


def product_header(title: str, subtitle: str = ""):
    st.markdown(f"# {title}")
    if subtitle:
        st.markdown(f"#### {subtitle}")
    st.divider()


def metric_card(label: str, value, help_text: str = None):
    st.metric(label=label, value=value, help=help_text)


def status_badge(label: str, status: str):
    status = str(status).lower()

    if status in ["good", "closed", "pass", "stable", "low"]:
        color = "#DCFCE7"
        text = "#166534"
    elif status in ["warning", "medium", "mrb review", "open"]:
        color = "#FEF9C3"
        text = "#854D0E"
    else:
        color = "#FEE2E2"
        text = "#991B1B"

    st.markdown(
        f"""
        <span style="
            background-color:{color};
            color:{text};
            padding:6px 10px;
            border-radius:8px;
            font-weight:600;
            font-size:0.85rem;
        ">
            {label}
        </span>
        """,
        unsafe_allow_html=True,
    )


def lifecycle_flow():
    st.code(
        """
Risk Assessment
      ↓
Inspection & Verification
      ↓
NCR / CAPA Management
      ↓
Quality Analytics + SPC
      ↓
Continuous Improvement
        """,
        language="text",
    )