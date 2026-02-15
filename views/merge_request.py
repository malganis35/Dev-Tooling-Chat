"""Page 3 — Merge Request Description.

Uses the prompt from ``prompts/mr_assistant.txt`` to auto-generate a complete
MR description from a git diff.
"""

import tempfile

import streamlit as st
from loguru import logger

from dev_tooling_chat.utils import (
    call_groq_llm,
    clone_repo,
    estimate_tokens,
    get_branches,
    git_diff,
    load_prompt,
    render_response_actions,
)


def render() -> None:
    """Render the Merge Request Description page."""
    logger.info("Rendering Merge Request Description page")

    # Styled page header
    st.markdown(
        """
        <div class="page-header">
            <div class="icon-badge">🔀</div>
            <div class="header-text">
                <h1>Merge Request Description</h1>
                <p>Auto-generate a structured MR description from a git diff between two branches.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Reset button ─────────────────────────────────────────────────────────
    if st.button("🔄 Reset", key="mr_reset_btn", help="Clear all results and start over"):
        for key in list(st.session_state.keys()):
            if key.startswith("mr_"):
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

    prompt = load_prompt("mr_assistant.txt")

    # ── Input method ─────────────────────────────────────────────────────────
    input_method = st.radio(
        "How would you like to provide the diff?",
        options=["📄 Upload a diff .txt file", "🔗 GitHub repository URL"],
        horizontal=True,
        key="mr_input_method",
    )

    diff_content: str | None = None

    if input_method == "📄 Upload a diff .txt file":
        uploaded_file = st.file_uploader(
            "Upload your diff as a .txt file",
            type=["txt"],
            key="mr_file_uploader",
        )
        if uploaded_file is not None:
            diff_content = uploaded_file.read().decode("utf-8")
            logger.info("Diff file uploaded: '{}' ({} chars)", uploaded_file.name, len(diff_content))
            st.success(f"✅ File loaded — **{uploaded_file.name}**")
            with st.expander("📄 Preview uploaded diff", expanded=False):
                st.code(diff_content[:3000] + ("..." if len(diff_content) > 3000 else ""), language="diff")

        if diff_content and st.button("🚀 Generate MR Description", key="mr_run_file_btn"):
                model = st.session_state.get("groq_model", "openai/gpt-oss-120b")
                logger.info("Generating MR description from uploaded file with model='{}'", model)
                with st.status("Generating MR description…", expanded=True) as status:
                    st.write(f"🤖 Sending diff to **{model}** (~{estimate_tokens(diff_content):,} tokens)…")
                    result = call_groq_llm(api_key, model, prompt, diff_content)
                    st.session_state["mr_response"] = result["content"]
                    usage = result["usage"]
                    st.write(
                        f"✅ Generated in **{result['elapsed_seconds']}s** — "
                        f"{usage['prompt_tokens']:,} prompt + {usage['completion_tokens']:,} completion tokens"
                    )
                    status.update(
                        label=(
                            f"Description ready ✅ — {result['elapsed_seconds']}s · "
                            f"{usage['total_tokens']:,} tokens used"
                        ),
                        state="complete",
                        expanded=False,
                    )

    else:
        # Inline URL + button
        url_col, btn_col = st.columns([3, 1], vertical_alignment="bottom")
        with url_col:
            github_url = st.text_input(
                "Enter a public GitHub repository URL",
                placeholder="https://github.com/user/repo",
                key="mr_github_url",
            )
        with btn_col:
            fetch_clicked = st.button("📥 Fetch branches", key="mr_fetch_btn", use_container_width=True)

        # Clear cached results when the URL changes
        if github_url and github_url != st.session_state.get("mr_last_url"):
            for key in ("mr_repo_path", "mr_branches", "mr_response"):
                st.session_state.pop(key, None)

        # Step 1 — Clone and list branches
        if github_url and fetch_clicked:
            logger.info("Fetching branches for URL: {}", github_url)
            # Clear any previous response before re-fetching
            st.session_state.pop("mr_response", None)
            with st.status("Fetching branches…", expanded=True) as status:
                try:
                    repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
                    st.write(f"📥 Cloning **{repo_name}**…")
                    tmp_dir = tempfile.mkdtemp()
                    local_path = clone_repo(github_url, tmp_dir)
                    st.write("✅ Repository cloned")
                    st.write("🔍 Listing remote branches…")
                    branches = get_branches(local_path)
                    st.session_state["mr_repo_path"] = local_path
                    st.session_state["mr_branches"] = branches
                    st.session_state["mr_last_url"] = github_url
                    logger.success("Found {} branches", len(branches))
                    st.write(f"✅ Found **{len(branches)} branches**: {', '.join(branches[:10])}{'...' if len(branches) > 10 else ''}")
                    status.update(
                        label=f"{len(branches)} branches found ✅ — {repo_name}",
                        state="complete",
                        expanded=False,
                    )
                except Exception as e:
                    logger.error("Failed to fetch branches for '{}': {}", github_url, e)
                    status.update(label="Error ❌", state="error")
                    st.error(f"❌ Error: {e}")
                    return

        # Step 2 — Select branches
        if "mr_branches" in st.session_state:
            branches = st.session_state["mr_branches"]
            col1, col2 = st.columns(2)
            with col1:
                source_branch = st.selectbox(
                    "Source branch (feature)",
                    options=branches,
                    key="mr_source_branch",
                )
            with col2:
                target_branch = st.selectbox(
                    "Target branch (main/develop)",
                    options=branches,
                    key="mr_target_branch",
                )

            # Step 3 — Generate diff and analyze
            if st.button("🚀 Generate MR Description", key="mr_run_github_btn"):
                repo_path = st.session_state["mr_repo_path"]
                logger.info("Generating MR description: {} → {}", source_branch, target_branch)
                with st.status("Computing diff and generating description…", expanded=True) as status:
                    try:
                        st.write(f"🔄 Computing diff: `{source_branch}` → `{target_branch}`…")
                        diff_text = git_diff(repo_path, source_branch, target_branch)
                        if not diff_text.strip():
                            logger.warning("No diff found between '{}' and '{}'", source_branch, target_branch)
                            status.update(label="No differences found", state="error")
                            st.warning("⚠️ No differences found between the selected branches.")
                            return

                        diff_lines = diff_text.count("\n")
                        diff_tokens = estimate_tokens(diff_text)
                        st.write(
                            f"✅ Diff computed — **{diff_lines:,} lines** · ~{diff_tokens:,} tokens"
                        )

                        with st.expander("📄 Preview diff", expanded=False):
                            st.code(diff_text[:3000] + ("..." if len(diff_text) > 3000 else ""), language="diff")

                        model = st.session_state.get("groq_model", "openai/gpt-oss-120b")
                        st.write(f"🤖 Sending to **{model}** (~{diff_tokens:,} tokens)…")
                        result = call_groq_llm(
                            api_key,
                            model,
                            prompt,
                            diff_text,
                        )
                        st.session_state["mr_response"] = result["content"]
                        usage = result["usage"]
                        st.write(
                            f"✅ Generated in **{result['elapsed_seconds']}s** — "
                            f"{usage['prompt_tokens']:,} prompt + {usage['completion_tokens']:,} completion tokens"
                        )
                        status.update(
                            label=(
                                f"Description ready ✅ — {result['elapsed_seconds']}s · "
                                f"{usage['total_tokens']:,} tokens used"
                            ),
                            state="complete",
                            expanded=False,
                        )
                    except Exception as e:
                        logger.error("MR description generation failed: {}", e)
                        status.update(label="Error ❌", state="error")
                        st.error(f"❌ Error: {e}")
                        return

    # ── Display result ───────────────────────────────────────────────────────
    if "mr_response" in st.session_state:
        st.markdown("---")
        st.subheader("📋 Merge Request Description")
        st.markdown(st.session_state["mr_response"])
        render_response_actions(st.session_state["mr_response"], "mr")
