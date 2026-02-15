"""Page 1 — Audit & Diagnostic.

Uses the prompt from ``prompts/repo_recrutement.txt`` to evaluate a code
repository against a professional recruitment audit grid.
"""

import streamlit as st
from loguru import logger
from dev_tooling_chat.utils import call_groq_llm, clone_and_ingest, load_prompt, render_response_actions


def render() -> None:
    logger.info("Rendering Audit & Diagnostic page")
    st.title("🔍 Audit & Diagnostic")
    st.markdown(
        "Evaluate a code repository against a **10-point professional audit grid** "
        "used by technical recruiters."
    )
    st.markdown("---")

    # Check API key
    api_key = st.session_state.get("groq_api_key")
    if not api_key:
        logger.warning("No API key found in session state")
        st.warning("⚠️ Please enter your Groq API key in the sidebar first.")
        return

    prompt = load_prompt("repo_recrutement.txt")

    # ── Input method ─────────────────────────────────────────────────────────
    input_method = st.radio(
        "How would you like to provide your code?",
        options=["📄 Upload a .txt file", "🔗 GitHub repository URL"],
        horizontal=True,
        key="audit_input_method",
    )

    code_content: str | None = None

    if input_method == "📄 Upload a .txt file":
        uploaded_file = st.file_uploader(
            "Upload your code as a .txt file",
            type=["txt"],
            key="audit_file_uploader",
        )
        if uploaded_file is not None:
            code_content = uploaded_file.read().decode("utf-8")
            logger.info("File uploaded: '{}' ({} chars)", uploaded_file.name, len(code_content))
            with st.expander("📄 Preview uploaded content", expanded=False):
                st.code(code_content[:3000] + ("..." if len(code_content) > 3000 else ""))
    else:
        github_url = st.text_input(
            "Enter a public GitHub repository URL",
            placeholder="https://github.com/user/repo",
            key="audit_github_url",
        )
        if github_url and st.button("🚀 Clone & Analyze", key="audit_clone_btn"):
            logger.info("User requested clone & ingest for URL: {}", github_url)
            with st.spinner("Cloning repository and running gitingest…"):
                try:
                    code_content = clone_and_ingest(github_url)
                    st.session_state["audit_code_content"] = code_content
                    logger.success("Repository ingested successfully ({} chars)", len(code_content))
                    st.success("Repository ingested successfully! ✅")
                except Exception as e:
                    logger.error("Clone & ingest failed for '{}': {}", github_url, e)
                    st.error(f"❌ Error: {e}")
                    return

        # Retrieve stored content if already cloned
        if "audit_code_content" in st.session_state:
            code_content = st.session_state["audit_code_content"]

    # ── Analysis ─────────────────────────────────────────────────────────────
    model = st.session_state.get("groq_model", "openai/gpt-oss-120b")

    if code_content and input_method == "📄 Upload a .txt file":
        run = st.button("🚀 Run Audit", key="audit_run_btn")
    else:
        run = False

    if run or (code_content and "audit_response" not in st.session_state and input_method != "📄 Upload a .txt file"):
        logger.info("Running audit analysis with model='{}'", model)
        with st.spinner("🤖 Analyzing with Groq LLM…"):
            response = call_groq_llm(api_key, model, prompt.format(model_name=model), code_content)
            st.session_state["audit_response"] = response

    if "audit_response" in st.session_state:
        st.markdown("---")
        st.subheader("📊 Audit Result")
        st.markdown(st.session_state["audit_response"])
        render_response_actions(st.session_state["audit_response"], "audit")
