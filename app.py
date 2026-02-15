"""Dev Tooling Chat — Streamlit Application.

A visual interface for AI-powered code analysis tools using the Groq API.
"""

import streamlit as st
from loguru import logger
from dev_tooling_chat.utils import fetch_groq_models

logger.info("Starting Dev Tooling Chat application")

st.set_page_config(
    page_title="Dev Tooling Chat",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(
            "https://i.postimg.cc/T1gjvpMg/logo-astrodata-v2.png",
            width=200,
        )
    st.title("Dev Tooling Chat")
    st.markdown("Your AI-powered code analysis assistant")
    st.markdown("---")

    # Navigation
    st.subheader("📂 Features")
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
    st.markdown("---")

    # API key input
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

    # Model selector (only visible once the API key is provided)
    if st.session_state.get("groq_api_key"):
        try:
            models = fetch_groq_models(st.session_state["groq_api_key"])
            default_idx = (
                models.index("openai/gpt-oss-120b")
                if "openai/gpt-oss-120b" in models
                else 0
            )
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

# ── Page routing ─────────────────────────────────────────────────────────────
logger.info("Navigating to page: {}", page)

if page == "🏠 Home":
    st.title("🛠️ Dev Tooling Chat")
    st.markdown(
        "Your **AI-powered code analysis assistant**. "
        "Select a feature from the sidebar to get started."
    )
    st.markdown("")

    # Helper to navigate to a page
    def _go_to(page_name: str) -> None:
        st.session_state["nav_radio"] = page_name

    st.info(
        "💡 **Getting started:** Enter your Groq API key in the sidebar, "
        "then select a feature.",
        icon="ℹ️",
    )

    st.markdown("")

    # Feature cards — HTML for guaranteed equal height
    st.markdown(
        """
        <div style="display:flex; gap:1rem; margin-bottom:1rem;">
            <div style="flex:1; border:1px solid #e0e0e0; border-radius:12px; padding:1.5rem; min-height:220px; display:flex; flex-direction:column;">
                <h3 style="margin-top:0;">🔍 Audit & Diagnostic</h3>
                <p style="flex:1;">Evaluate a GitHub repository against a <strong>10-point professional audit grid</strong> used by technical recruiters.</p>
                <p style="color:#888; font-size:0.85rem; margin-bottom:0;">Best for: recruitment evaluation</p>
            </div>
            <div style="flex:1; border:1px solid #e0e0e0; border-radius:12px; padding:1.5rem; min-height:220px; display:flex; flex-direction:column;">
                <h3 style="margin-top:0;">📝 Code Review</h3>
                <p style="flex:1;">Get a <strong>comprehensive Python code review</strong> with weighted scoring, strengths, weaknesses, and actionable recommendations.</p>
                <p style="color:#888; font-size:0.85rem; margin-bottom:0;">Best for: code quality improvement</p>
            </div>
            <div style="flex:1; border:1px solid #e0e0e0; border-radius:12px; padding:1.5rem; min-height:220px; display:flex; flex-direction:column;">
                <h3 style="margin-top:0;">🔀 Merge Request</h3>
                <p style="flex:1;">Auto-generate a <strong>complete, structured MR description</strong> from a git diff between two branches.</p>
                <p style="color:#888; font-size:0.85rem; margin-bottom:0;">Best for: pull request automation</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation buttons below the cards
    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.button("Open Audit →", key="go_audit", on_click=_go_to, args=("🔍 Audit & Diagnostic",), use_container_width=True)
    with col2:
        st.button("Open Review →", key="go_review", on_click=_go_to, args=("📝 Senior Code Review",), use_container_width=True)
    with col3:
        st.button("Open MR →", key="go_mr", on_click=_go_to, args=("🔀 Merge Request Description",), use_container_width=True)

    
elif page == "🔍 Audit & Diagnostic":
    from views.audit_diagnostic import render
    render()

elif page == "� Senior Code Review":
    from views.code_review import render
    render()

elif page == "🔀 Merge Request Description":
    from views.merge_request import render
    render()
