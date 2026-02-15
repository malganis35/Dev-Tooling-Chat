"""Page 2 — Code Review.

Uses the prompt from ``prompts/code_audit.txt`` to perform a comprehensive
Python code quality audit with weighted scoring.
"""

import streamlit as st
from loguru import logger
from dev_tooling_chat.utils import call_groq_llm, clone_and_ingest, estimate_tokens, load_prompt, render_response_actions


def render() -> None:
    logger.info("Rendering Code Review page")

    # Styled page header
    st.markdown(
        """
        <div class="page-header">
            <div class="icon-badge">📝</div>
            <div class="header-text">
                <h1>Senior Code Review</h1>
                <p>Comprehensive Python code review with weighted scoring and actionable recommendations.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Reset button ─────────────────────────────────────────────────────────
    if st.button("🔄 Reset", key="code_audit_reset_btn", help="Clear all results and start over"):
        for key in list(st.session_state.keys()):
            if key.startswith("code_audit_"):
                del st.session_state[key]
        st.rerun()

    # Check API key
    api_key = st.session_state.get("groq_api_key")
    if not api_key:
        logger.warning("No API key found in session state")
        st.markdown(
            '<div class="dtc-alert">'
            '<span class="alert-icon">🔑</span>'
            "<span>Please enter your <strong>Groq API key</strong> in the sidebar to enable AI features.</span>"
            "</div>",
            unsafe_allow_html=True,
        )
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
            logger.info("File uploaded: '{}' ({} chars)", uploaded_file.name, len(code_content))
            st.success(f"✅ File loaded — **{uploaded_file.name}**")
            with st.expander("📄 Preview uploaded content", expanded=False):
                st.code(code_content[:3000] + ("..." if len(code_content) > 3000 else ""))
    else:
        # Inline URL + button
        url_col, btn_col = st.columns([3, 1], vertical_alignment="bottom")
        with url_col:
            github_url = st.text_input(
                "Enter a public GitHub repository URL",
                placeholder="https://github.com/user/repo",
                key="code_audit_github_url",
            )
        with btn_col:
            clone_clicked = st.button("🚀 Clone & Analyze", key="code_audit_clone_btn", use_container_width=True)

        # Clear cached results when the URL changes
        if github_url and github_url != st.session_state.get("code_audit_last_url"):
            for key in ("code_audit_code_content", "code_audit_response"):
                st.session_state.pop(key, None)

        if github_url and clone_clicked:
            logger.info("User requested clone & ingest for URL: {}", github_url)
            # Clear any previous response before re-analyzing
            st.session_state.pop("code_audit_response", None)
            with st.status("Cloning and analyzing repository…", expanded=True) as status:
                try:
                    result = clone_and_ingest(github_url, status_callback=st.write)
                    code_content = result["content"]
                    st.session_state["code_audit_code_content"] = code_content
                    st.session_state["code_audit_last_url"] = github_url
                    logger.success("Repository ingested successfully ({} chars)", len(code_content))
                    status.update(
                        label=(
                            f"Repository ready ✅ — ~{result['token_estimate']:,} tokens · "
                            f"{result['line_count']:,} lines · {result['elapsed_seconds']}s"
                        ),
                        state="complete",
                        expanded=False,
                    )
                except Exception as e:
                    logger.error("Clone & ingest failed for '{}': {}", github_url, e)
                    status.update(label="Error ❌", state="error")
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

    if run or (
        code_content and "code_audit_response" not in st.session_state and input_method != "📄 Upload a .txt file"
    ):
        logger.info("Running code review with model='{}'", model)
        input_tokens = estimate_tokens(code_content)
        with st.status("Running AI code review…", expanded=True) as status:
            st.write(f"🤖 Sending to **{model}** (~{input_tokens:,} tokens)…")
            result = call_groq_llm(api_key, model, prompt, code_content)
            st.session_state["code_audit_response"] = result["content"]
            usage = result["usage"]
            st.write(
                f"✅ Generated in **{result['elapsed_seconds']}s** — "
                f"{usage['prompt_tokens']:,} prompt + {usage['completion_tokens']:,} completion tokens"
            )
            status.update(
                label=(
                    f"Review complete ✅ — {result['elapsed_seconds']}s · "
                    f"{usage['total_tokens']:,} tokens used"
                ),
                state="complete",
                expanded=False,
            )

    if "code_audit_response" in st.session_state:
        st.markdown("---")
        st.subheader("📊 Code Review Result")
        st.markdown(st.session_state["code_audit_response"])
        render_response_actions(st.session_state["code_audit_response"], "code_audit")
