"""Page 2 — Code Review.

Uses the prompt from ``prompts/code_audit.txt`` to perform a comprehensive
Python code quality audit with weighted scoring.
"""

import streamlit as st
from dev_tooling_chat.utils import call_groq_llm, clone_and_ingest, load_prompt, render_response_actions


def render() -> None:
    st.title("📝 Code Review")
    st.markdown(
        "Get a **comprehensive Python code review** with weighted scoring, "
        "strengths, weaknesses and actionable recommendations."
    )
    st.markdown("---")

    # Check API key
    api_key = st.session_state.get("groq_api_key")
    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar first.")
        return

    prompt = load_prompt("code_audit.txt")

    # ── Input method ─────────────────────────────────────────────────────────
    input_method = st.radio(
        "How would you like to provide your code?",
        options=["📄 Upload a .txt file", "🔗 GitHub repository URL"],
        horizontal=True,
        key="code_audit_input_method",
    )

    code_content: str | None = None

    if input_method == "📄 Upload a .txt file":
        uploaded_file = st.file_uploader(
            "Upload your code as a .txt file",
            type=["txt"],
            key="code_audit_file_uploader",
        )
        if uploaded_file is not None:
            code_content = uploaded_file.read().decode("utf-8")
            with st.expander("📄 Preview uploaded content", expanded=False):
                st.code(code_content[:3000] + ("..." if len(code_content) > 3000 else ""))
    else:
        github_url = st.text_input(
            "Enter a public GitHub repository URL",
            placeholder="https://github.com/user/repo",
            key="code_audit_github_url",
        )
        if github_url and st.button("🚀 Clone & Analyze", key="code_audit_clone_btn"):
            with st.spinner("Cloning repository and running gitingest…"):
                try:
                    code_content = clone_and_ingest(github_url)
                    st.session_state["code_audit_code_content"] = code_content
                    st.success("Repository ingested successfully! ✅")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    return

        # Retrieve stored content if already cloned
        if "code_audit_code_content" in st.session_state:
            code_content = st.session_state["code_audit_code_content"]

    # ── Analysis ─────────────────────────────────────────────────────────────
    model = st.session_state.get("groq_model", "openai/gpt-oss-120b")

    if code_content and input_method == "📄 Upload a .txt file":
        run = st.button("🚀 Run Audit", key="code_audit_run_btn")
    else:
        run = False

    if run or (code_content and "code_audit_response" not in st.session_state and input_method != "📄 Upload a .txt file"):
        with st.spinner("🤖 Analyzing with Groq LLM…"):
            response = call_groq_llm(api_key, model, prompt, code_content)
            st.session_state["code_audit_response"] = response

    if "code_audit_response" in st.session_state:
        st.markdown("---")
        st.subheader("📊 Code Review Result")
        st.markdown(st.session_state["code_audit_response"])
        render_response_actions(st.session_state["code_audit_response"], "code_audit")
