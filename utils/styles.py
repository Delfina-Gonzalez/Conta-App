"""Shared styling and UI utility functions."""

import streamlit as st


APP_STYLE = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap');

/* ── Root tokens ── */
:root {
    --bg:        #0F1117;
    --surface:   #1A1D27;
    --surface2:  #22263A;
    --border:    #2D3150;
    --accent:    #6C7BFF;
    --accent2:   #A78BFA;
    --green:     #34D399;
    --red:       #F87171;
    --amber:     #FBBF24;
    --text:      #E8EAF6;
    --text-muted:#8892B0;
    --font-body: 'Inter', sans-serif;
    --font-disp: 'DM Serif Display', serif;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: var(--font-body);
    background-color: var(--bg);
    color: var(--text);
}
.stApp { background-color: var(--bg); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: var(--text-muted) !important;
    font-size: 0.875rem;
    font-weight: 500;
    letter-spacing: 0.02em;
}

/* ── Headers ── */
h1 {
    font-family: var(--font-disp) !important;
    font-size: 2rem !important;
    color: var(--text) !important;
    letter-spacing: -0.02em;
}
h2 {
    font-family: var(--font-body) !important;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    color: var(--accent2) !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 1.5rem !important;
}
h3 {
    font-family: var(--font-body) !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.card-accent {
    border-left: 3px solid var(--accent);
}
.card-green  { border-left: 3px solid var(--green); }
.card-red    { border-left: 3px solid var(--red); }
.card-amber  { border-left: 3px solid var(--amber); }

/* ── KPI tiles ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.kpi {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.kpi-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}
.kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1;
}
.kpi-sub {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
}

/* ── Tables ── */
.stDataFrame, [data-testid="stTable"] {
    border-radius: 8px;
    overflow: hidden;
}
.stDataFrame thead tr th {
    background: var(--surface2) !important;
    color: var(--text-muted) !important;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div,
.stTextArea > div > div > textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-family: var(--font-body) !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(108,123,255,.2) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: blue !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.45rem 1.2rem !important;
    transition: opacity .10s, transform .1s !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}

/* ── Alerts ── */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 8px !important;
}

/* ── Dividers ── */
hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.5rem 0;
}

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-activo      { background:#1E3A5F; color:#60A5FA; }
.badge-pasivo      { background:#3B1F1F; color:#F87171; }
.badge-patrimonio  { background:#1F3B2D; color:#34D399; }
.badge-r_positivo  { background:#1C3D2C; color:#6EE7B7; }
.badge-r_negativo  { background:#3B2A1A; color:#FBBF24; }
.badge-corriente   { background:#2A2A3A; color:#A78BFA; }
.badge-no_corriente{ background:#1E2A3A; color:#93C5FD; }

/* ── Ledger table ── */
.ledger-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    font-variant-numeric: tabular-nums;
}
.ledger-table th {
    background: var(--surface2);
    color: var(--text-muted);
    font-size: 0.7rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border);
}
.ledger-table td {
    padding: 7px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
}
.ledger-table tr:last-child td { border-bottom: none; }
.ledger-table .num { text-align: right; font-family: 'Inter', monospace; }
.ledger-table .total-row td {
    font-weight: 700;
    background: var(--surface2);
    color: var(--accent2);
}
.ledger-table .saldo-row td {
    font-weight: 700;
    color: var(--green);
    font-size: 0.9rem;
}

/* ── Statement table ── */
.stmt-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}
.stmt-table th {
    background: var(--surface2);
    color: var(--text-muted);
    font-size: 0.7rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 8px 14px;
    border-bottom: 1px solid var(--border);
}
.stmt-table td { padding: 7px 14px; border-bottom: 1px solid rgba(45,49,80,.5); }
.stmt-table .section-header td {
    font-weight: 700;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent2);
    background: var(--surface2);
    padding-top: 10px;
}
.stmt-table .total-row td {
    font-weight: 700;
    background: var(--surface2);
    border-top: 1px solid var(--border);
}
.stmt-table .subtotal-row td {
    font-weight: 600;
    color: var(--text-muted);
    border-top: 1px solid var(--border);
}
.stmt-table .grand-total td {
    font-weight: 800;
    font-size: 1rem;
    color: var(--accent2);
    background: var(--surface2);
    border-top: 2px solid var(--accent);
}
.num-col { text-align: right !important; font-variant-numeric: tabular-nums; }
.positive { color: var(--green) !important; }
.negative { color: var(--red) !important; }

/* ── Hint box ── */
.hint-box {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent2);
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    font-size: 0.83rem;
    color: var(--text-muted);
    line-height: 1.6;
    margin-top: 0.5rem;
}
.hint-box strong { color: var(--accent2); }

/* ── Page title ── */
.page-title {
    margin-bottom: 0.25rem;
}
.page-subtitle {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
}
</style>
"""


def apply_style():
    st.markdown(APP_STYLE, unsafe_allow_html=True)


def fmt_money(value: float, prefix: str = "$") -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}{prefix} {abs(value):,.2f}"


def badge(tipo: str) -> str:
    labels = {
        "activo": "Activo",
        "pasivo": "Pasivo",
        "patrimonio": "Patrimonio",
        "r_positivo": "R. Positivo",
        "r_negativo": "R. Negativo",
        "corriente": "Corriente",
        "no_corriente": "No Corriente",
    }
    label = labels.get(tipo, tipo)
    return f'<span class="badge badge-{tipo}">{label}</span>'


def page_header(title: str, subtitle: str = ""):
    st.markdown(f'<h1 class="page-title">{title}</h1>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)


def divider():
    st.markdown("<hr>", unsafe_allow_html=True)
