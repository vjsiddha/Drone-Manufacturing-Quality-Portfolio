"""
shared_styles.py
Shared design system for all Streamlit apps in this portfolio.
Import with: from shared_styles import apply_styles, kpi_card, badge, insight, section
"""

# ── Colour tokens ──────────────────────────────────────────────────────────
C = {
    "bg":        "#08090a",
    "surface":   "#0f1117",
    "surface2":  "#161b22",
    "border":    "#1e2530",
    "border2":   "#2a3140",
    "text":      "#e2e8f0",
    "muted":     "#64748b",
    "subtle":    "#94a3b8",
    "red":       "#e05252",
    "amber":     "#c9952a",
    "green":     "#3d9e6b",
    "blue":      "#4a7fa5",
    "plot_bg":   "#08090a",
    "grid":      "#1a2030",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', system-ui, sans-serif;
    background-color: {C['bg']};
    color: {C['text']};
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: {C['surface']};
    border-right: 1px solid {C['border']};
}}
section[data-testid="stSidebar"] .stRadio label {{
    font-size: 13px;
    color: {C['subtle']};
    padding: 6px 0;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.3px;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    color: {C['text']};
}}

/* ── KPI card ── */
.kpi {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-top: 2px solid {C['border2']};
    border-radius: 4px;
    padding: 20px 24px;
}}
.kpi-label {{
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: {C['muted']};
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 8px;
}}
.kpi-value {{
    font-size: 28px;
    font-weight: 500;
    color: {C['text']};
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
}}
.kpi-value.red   {{ color: {C['red']}; }}
.kpi-value.green {{ color: {C['green']}; }}
.kpi-value.amber {{ color: {C['amber']}; }}
.kpi-sub {{
    font-size: 11px;
    color: {C['muted']};
    margin-top: 6px;
    font-family: 'JetBrains Mono', monospace;
}}

/* ── Section header ── */
.section {{
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: {C['muted']};
    font-family: 'JetBrains Mono', monospace;
    border-bottom: 1px solid {C['border']};
    padding-bottom: 8px;
    margin: 24px 0 16px;
}}

/* ── Status badge ── */
.badge {{
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
    padding: 3px 8px;
    border-radius: 2px;
}}
.badge-pass    {{ background: rgba(61,158,107,0.12); color: {C['green']}; border: 1px solid rgba(61,158,107,0.3); }}
.badge-fail    {{ background: rgba(224,82,82,0.12);  color: {C['red']};   border: 1px solid rgba(224,82,82,0.3); }}
.badge-amber   {{ background: rgba(201,149,42,0.12); color: {C['amber']}; border: 1px solid rgba(201,149,42,0.3); }}
.badge-neutral {{ background: rgba(100,116,139,0.12); color: {C['subtle']}; border: 1px solid rgba(100,116,139,0.3); }}

/* ── Alert / insight strip ── */
.alert {{
    border-radius: 3px;
    padding: 12px 16px;
    font-size: 13px;
    color: {C['text']};
    margin-bottom: 10px;
    line-height: 1.5;
    font-family: 'Inter', sans-serif;
    border-left: 3px solid {C['border2']};
    background: {C['surface']};
}}
.alert-red   {{ border-left-color: {C['red']};   background: rgba(224,82,82,0.06); }}
.alert-green {{ border-left-color: {C['green']}; background: rgba(61,158,107,0.06); }}
.alert-amber {{ border-left-color: {C['amber']}; background: rgba(201,149,42,0.06); }}
.alert-blue  {{ border-left-color: {C['blue']};  background: rgba(74,127,165,0.06); }}

/* ── Page title ── */
.page-title {{
    font-size: 20px;
    font-weight: 500;
    color: {C['text']};
    letter-spacing: -0.3px;
    margin-bottom: 2px;
}}
.page-sub {{
    font-size: 13px;
    color: {C['muted']};
    margin-bottom: 24px;
    font-family: 'JetBrains Mono', monospace;
}}

/* ── Divider ── */
.divider {{
    border: none;
    border-top: 1px solid {C['border']};
    margin: 20px 0;
}}

/* ── Dataframe overrides ── */
div[data-testid="stDataFrame"] {{
    border: 1px solid {C['border']};
    border-radius: 4px;
}}

/* ── Streamlit default cleanup ── */
.stButton button {{
    background: {C['surface2']};
    border: 1px solid {C['border2']};
    color: {C['text']};
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.5px;
    border-radius: 3px;
}}
.stButton button:hover {{
    border-color: {C['blue']};
    color: {C['text']};
}}
div[data-testid="stSidebarNav"] {{ display: none; }}
</style>
"""

PLOT_DEFAULTS = dict(
    template="plotly_dark",
    paper_bgcolor=C["plot_bg"],
    plot_bgcolor=C["plot_bg"],
    font=dict(family="JetBrains Mono", size=11, color=C["subtle"]),
    margin=dict(l=16, r=16, t=32, b=16),
    xaxis=dict(gridcolor=C["grid"], zerolinecolor=C["grid"], linecolor=C["border"]),
    yaxis=dict(gridcolor=C["grid"], zerolinecolor=C["grid"], linecolor=C["border"]),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(size=11)),
)


def apply_styles():
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)


def style_fig(fig, height=320):
    fig.update_layout(**PLOT_DEFAULTS, height=height)
    return fig


def kpi_card(label, value, color="", sub=""):
    return f"""<div class="kpi">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {color}">{value}</div>
        {"" if not sub else f'<div class="kpi-sub">{sub}</div>'}
    </div>"""


def badge(text, variant="neutral"):
    return f'<span class="badge badge-{variant}">{text}</span>'


def alert(text, variant="blue"):
    return f'<div class="alert alert-{variant}">{text}</div>'


def section(text):
    return f'<div class="section">{text}</div>'


def page_header(title, sub=""):
    sub_html = f'<div class="page-sub">{sub}</div>' if sub else ""
    return f'<div class="page-title">{title}</div>{sub_html}'