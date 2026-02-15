"""Dev Tooling Assistant — Streamlit Application.

A visual interface for AI-powered code analysis tools using the Groq API.
"""

import streamlit as st
from loguru import logger

from dev_tooling_chat.styles import inject_global_css
from dev_tooling_chat.utils import fetch_groq_models

logger.info("Starting Dev Tooling Assistant application")

st.set_page_config(
    page_title="Dev Tooling Assistant",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject global CSS design system ──────────────────────────────────────────
inject_global_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Branded header
    st.markdown(
        """
        <div class="sidebar-brand">
            <img src="https://i.postimg.cc/T1gjvpMg/logo-astrodata-v2.png"
                 width="100" style="border-radius:16px; margin-bottom:0.2rem;" />
            <h2>Dev Tooling Assistant</h2>
            <p>AI-powered dev assistant</p>
        </div>
        <hr class="brand-divider" />
        """,
        unsafe_allow_html=True,
    )

    # Navigation
    st.markdown(
        '<p style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; '
        'color:#94a3b8; font-weight:600; margin-bottom:0.3rem;">Navigation</p>',
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navigate to",
        options=[
            "🏠 Home",
            "🔍 Audit & Diagnostic",
            "📝 Senior Code Review",
            "🔀 Merge Request Description",
        ],
        label_visibility="collapsed",
        key="nav_radio",
    )

    st.markdown('<hr class="brand-divider" />', unsafe_allow_html=True)

    # API key input
    st.markdown(
        '<p style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; '
        'color:#94a3b8; font-weight:600; margin-bottom:0.3rem;">Settings</p>',
        unsafe_allow_html=True,
    )
    api_key = st.text_input(
        "🔑 Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Enter your Groq API key to enable the AI features.",
    )
    if api_key:
        st.session_state["groq_api_key"] = api_key
        logger.info("Groq API key provided by user")
        st.success("API key saved ✅")
    st.markdown(
        '<a href="https://console.groq.com/keys" target="_blank" '
        'style="font-size:0.8rem; color:#667eea; text-decoration:none;">'
        '🔗 Do not have a Groq API key? Get one here →</a>',
        unsafe_allow_html=True,
    )

    # Model selector (only visible once the API key is provided)
    if st.session_state.get("groq_api_key"):
        try:
            models = fetch_groq_models(st.session_state["groq_api_key"])
            default_idx = models.index("openai/gpt-oss-120b") if "openai/gpt-oss-120b" in models else 0
            selected_model = st.selectbox(
                "🤖 Model",
                options=models,
                index=default_idx,
                help="Choose which Groq model to use for analysis.",
            )
            st.session_state["groq_model"] = selected_model
            logger.info("Model selected: {}", selected_model)
        except Exception as e:
            logger.error("Failed to fetch models: {}", e)
            st.error(f"Could not fetch models: {e}")

    # Footer
    st.markdown(
        """
        <div style="position:fixed; bottom:1rem; padding:0.5rem 1rem;
                    font-size:0.72rem; color:#64748b;">
            Built with ❤️ using Streamlit & Groq
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Page routing ─────────────────────────────────────────────────────────────
logger.info("Navigating to page: {}", page)

if page == "🏠 Home":
    # Hero section
    st.markdown(
        """
        <div class="hero">
            <span class="hero-badge">✨ AI-Powered Developer Tools</span>
            <h1>Dev Tooling Assistant</h1>
            <p>Analyze and audit your code in seconds
               with the power of AI</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Getting started alert
    st.markdown(
        """
        <div class="dtc-alert">
            <span class="alert-icon">💡</span>
            <span><strong>Getting started:</strong> enter your Groq API key in the sidebar,
            then select a feature below.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    # Feature cards
    st.markdown(
        """
        <div class="card-grid">
            <div class="feature-card">
                <span class="card-icon">🔍</span>
                <h3>Audit &amp; Diagnostic</h3>
                <p>Evaluate a GitHub repository against a <strong>10-point professional
                audit grid</strong> used by technical recruiters.</p>
                <span class="card-tag">Recruitment</span>
            </div>
            <div class="feature-card">
                <span class="card-icon">📝</span>
                <h3>Senior Code Review</h3>
                <p>Get a <strong>comprehensive Python code review</strong> with weighted scoring,
                strengths, weaknesses and actionable recommendations.</p>
                <span class="card-tag">Quality</span>
            </div>
            <div class="feature-card">
                <span class="card-icon">🔀</span>
                <h3>Merge Request</h3>
                <p>Auto-generate a <strong>complete, structured MR description</strong>
                from a git diff between two branches.</p>
                <span class="card-tag">Automation</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Helper to navigate to a page
    def _go_to(page_name: str) -> None:
        st.session_state["nav_radio"] = page_name

    # Navigation buttons below the cards
    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.button(
            "Open Audit →", key="go_audit", on_click=_go_to, args=("🔍 Audit & Diagnostic",), use_container_width=True
        )
    with col2:
        st.button(
            "Open Review →", key="go_review", on_click=_go_to, args=("📝 Senior Code Review",), use_container_width=True
        )
    with col3:
        st.button(
            "Open MR →", key="go_mr", on_click=_go_to, args=("🔀 Merge Request Description",), use_container_width=True
        )


elif page == "🔍 Audit & Diagnostic":
    from views.audit_diagnostic import render

    render()

elif page == "📝 Senior Code Review":
    from views.code_review import render

    render()

elif page == "🔀 Merge Request Description":
    from views.merge_request import render

    render()
