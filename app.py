"""Dev Tooling Chat — Streamlit Application.

A visual interface for AI-powered code analysis tools using the Groq API.
"""

import streamlit as st
from dev_tooling_chat.utils import fetch_groq_models

st.set_page_config(
    page_title="Dev Tooling Chat",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/code.png",
        width=64,
    )
    st.title("Dev Tooling Chat")
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
        st.success("API key saved ✅")

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
        except Exception as e:
            st.error(f"Could not fetch models: {e}")

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
    )

# ── Page routing ─────────────────────────────────────────────────────────────
if page == "🏠 Home":
    st.title("🛠️ Dev Tooling Chat")
    st.markdown(
        """
        Welcome to **Dev Tooling Chat** — your AI-powered code analysis assistant.

        ### Available features

        | # | Feature | Description |
        |---|---------|-------------|
        | 1 | **🔍 Audit & Diagnostic** | Evaluate a GitHub repository against a professional recruitment audit grid (10 criteria). |
        | 2 | **📝 Senior Code Review** | Get a full Python code review with weighted scoring, strengths, weaknesses and actionable recommendations. |
        | 3 | **🔀 Merge Request Description** | Auto-generate a complete, structured MR description from a git diff. |

        ### Getting started

        1. Enter your **Groq API key** in the sidebar.
        2. Select a feature from the navigation menu.
        3. Upload a `.txt` file **or** provide a public GitHub URL.
        4. Get your AI-generated analysis! 🚀
        """
    )
    st.info(
        "💡 **Tip:** Each feature lets you **copy** or **download** the AI response.",
        icon="ℹ️",
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
