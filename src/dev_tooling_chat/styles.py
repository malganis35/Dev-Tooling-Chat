"""Global CSS design system for Dev Tooling Assistant.

Call ``inject_global_css()`` once at app startup to apply the premium
dark-theme styling across all pages.
"""

import streamlit as st

# ── colour tokens ─────────────────────────────────────────────────────────────
_PRIMARY = "#667eea"
_SECONDARY = "#764ba2"
_BG_DARK = "#0f1117"
_BG_CARD = "#1a1c2e"
_BG_GLASS = "rgba(26, 28, 46, 0.7)"
_BORDER = "rgba(102, 126, 234, 0.15)"
_TEXT = "#e2e8f0"
_TEXT_MUTED = "#94a3b8"
_GRADIENT = f"linear-gradient(135deg, {_PRIMARY} 0%, {_SECONDARY} 100%)"
_SUCCESS = "#2ea043"
_ERROR = "#f85149"

_CSS = f"""
/* ── Google Fonts ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base ──────────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {_BG_CARD} 0%, {_BG_DARK} 100%) !important;
    border-right: 1px solid {_BORDER} !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
    padding: 0.55rem 1rem !important;
    border-radius: 10px !important;
    transition: all 0.25s ease !important;
    margin-bottom: 2px !important;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    background: rgba(102, 126, 234, 0.10) !important;
}}
section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {{
    background: rgba(102, 126, 234, 0.18) !important;
    border-left: 3px solid {_PRIMARY} !important;
}}

/* ── Logo / branding block ────────────────────────────────────────────────── */
.sidebar-brand {{
    text-align: center;
    padding: 1.2rem 0 0.6rem;
}}
.sidebar-brand h2 {{
    background: {_GRADIENT};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 1.45rem;
    margin: 0.5rem 0 0.15rem;
    letter-spacing: -0.02em;
}}
.sidebar-brand p {{
    color: {_TEXT_MUTED};
    font-size: 0.82rem;
    margin: 0;
}}
.brand-divider {{
    height: 2px;
    background: {_GRADIENT};
    border: none;
    border-radius: 2px;
    margin: 0.9rem 0;
    opacity: 0.5;
}}

/* ── Hero section ─────────────────────────────────────────────────────────── */
.hero {{
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    animation: fadeInUp 0.6s ease-out;
}}
.hero h1 {{
    font-size: 2.8rem;
    font-weight: 800;
    background: {_GRADIENT};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    letter-spacing: -0.03em;
}}
.hero p {{
    font-size: 1.15rem;
    color: {_TEXT_MUTED};
    max-width: 560px;
    margin: 0 auto 1.6rem;
    line-height: 1.6;
}}
.hero-badge {{
    display: inline-block;
    padding: 0.35rem 1rem;
    border-radius: 20px;
    background: rgba(102, 126, 234, 0.12);
    border: 1px solid rgba(102, 126, 234, 0.25);
    color: {_PRIMARY};
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}}

/* ── Feature cards ────────────────────────────────────────────────────────── */
.card-grid {{
    display: flex;
    gap: 1.2rem;
    margin: 1rem 0 1.2rem;
}}
.feature-card {{
    flex: 1;
    background: {_BG_GLASS};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid {_BORDER};
    border-radius: 16px;
    padding: 1.8rem 1.4rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.3s ease, box-shadow 0.35s ease, border-color 0.3s ease;
    display: flex;
    flex-direction: column;
}}
.feature-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: {_GRADIENT};
    border-radius: 16px 16px 0 0;
}}
.feature-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.18);
    border-color: rgba(102, 126, 234, 0.35);
}}
.feature-card .card-icon {{
    font-size: 2rem;
    margin-bottom: 0.8rem;
    display: inline-block;
    background: rgba(102, 126, 234, 0.10);
    border-radius: 12px;
    width: 52px;
    height: 52px;
    line-height: 52px;
    text-align: center;
}}
.feature-card h3 {{
    font-size: 1.1rem;
    font-weight: 700;
    color: {_TEXT};
    margin: 0 0 0.5rem;
    letter-spacing: -0.01em;
}}
.feature-card p {{
    font-size: 0.92rem;
    color: {_TEXT_MUTED};
    line-height: 1.55;
    flex: 1;
}}
.feature-card .card-tag {{
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 6px;
    background: rgba(102, 126, 234, 0.10);
    color: {_PRIMARY};
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}

/* ── Page header ──────────────────────────────────────────────────────────── */
.page-header {{
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.4rem;
    animation: fadeInUp 0.5s ease-out;
}}
.page-header .icon-badge {{
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: {_GRADIENT};
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    flex-shrink: 0;
}}
.page-header .header-text h1 {{
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.02em;
    color: {_TEXT};
}}
.page-header .header-text p {{
    font-size: 0.95rem;
    color: {_TEXT_MUTED};
    margin: 0.15rem 0 0;
    line-height: 1.4;
}}

/* ── Styled panel ─────────────────────────────────────────────────────────── */
.dtc-panel {{
    background: {_BG_GLASS};
    border: 1px solid {_BORDER};
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}}

/* ── Styled alert (replaces st.warning for API key) ───────────────────────── */
.dtc-alert {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.2rem;
    border-radius: 12px;
    border: 1px solid rgba(102, 126, 234, 0.25);
    background: rgba(102, 126, 234, 0.08);
    color: {_TEXT};
    font-size: 0.92rem;
    line-height: 1.5;
    animation: fadeInUp 0.4s ease-out;
}}
.dtc-alert .alert-icon {{
    font-size: 1.4rem;
    flex-shrink: 0;
}}

/* ── Buttons (Streamlit overrides) ────────────────────────────────────────── */
div.stButton > button {{
    background: {_GRADIENT} !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.4rem !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.01em !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.20) !important;
}}
div.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.35) !important;
}}
div.stButton > button:active {{
    transform: translateY(0) !important;
}}

/* ── Download button override ─────────────────────────────────────────────── */
div.stDownloadButton > button {{
    background: transparent !important;
    color: {_PRIMARY} !important;
    border: 1px solid rgba(102, 126, 234, 0.3) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}}
div.stDownloadButton > button:hover {{
    background: rgba(102, 126, 234, 0.08) !important;
    border-color: {_PRIMARY} !important;
}}

/* ── Text inputs & select boxes ───────────────────────────────────────────── */
div[data-baseweb="input"] > div {{
    background: rgba(15, 17, 23, 0.6) !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 10px !important;
    transition: border-color 0.3s ease !important;
}}
div[data-baseweb="input"] > div:focus-within {{
    border-color: {_PRIMARY} !important;
    box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.3) !important;
}}
div[data-baseweb="select"] > div {{
    background: rgba(15, 17, 23, 0.6) !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 10px !important;
}}

/* ── Expanders ────────────────────────────────────────────────────────────── */
details {{
    border: 1px solid {_BORDER} !important;
    border-radius: 12px !important;
    background: {_BG_GLASS} !important;
}}

/* ── Status widget ────────────────────────────────────────────────────────── */
div[data-testid="stStatusWidget"] {{
    border-radius: 12px !important;
}}

/* ── Scrollbar ────────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: transparent;
}}
::-webkit-scrollbar-thumb {{
    background: rgba(102, 126, 234, 0.25);
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: rgba(102, 126, 234, 0.45);
}}

/* ── Animations ───────────────────────────────────────────────────────────── */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(16px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 768px) {{
    .card-grid {{
        flex-direction: column;
    }}
    .hero h1 {{
        font-size: 2rem;
    }}
}}
"""


def inject_global_css() -> None:
    """Inject the global CSS design system into the Streamlit page.

    Must be called once, typically right after ``st.set_page_config()``.
    """
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)
