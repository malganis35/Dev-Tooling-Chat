"""Shared utilities for Dev Tooling Assistant."""

import os
import re
import subprocess
import tempfile
import time
from collections.abc import Callable

import requests
import streamlit as st
from git import Repo
from groq import Groq
from loguru import logger

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

_NON_TEXT_GENERATION_KEYWORDS = {"whisper", "tts", "playai", "distil"}


def _is_text_generation_model(model_id: str) -> bool:
    """Return True if *model_id* looks like a text-generation (chat) model."""
    lower = model_id.lower()
    return not any(kw in lower for kw in _NON_TEXT_GENERATION_KEYWORDS)


def fetch_groq_models(api_key: str) -> list[str]:
    """Fetch the list of available text-generation model IDs from the Groq API."""
    logger.info("Fetching available Groq models…")
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    all_models = [m["id"] for m in data.get("data", [])]
    text_models = sorted([m for m in all_models if _is_text_generation_model(m)])
    logger.info("Fetched {} models total, {} text-generation models retained", len(all_models), len(text_models))
    logger.debug("Text-generation models: {}", text_models)
    return text_models


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in *text* (~4 chars per token)."""
    return max(1, len(text) // 4)


def call_groq_llm(api_key: str, model: str, system_prompt: str, user_content: str) -> dict:
    """Send *system_prompt* + *user_content* to the Groq chat API.

    Returns a dict with the reply and usage metadata.
    """
    logger.info("Calling Groq LLM with model={}", model)
    logger.debug(
        "System prompt length: {} chars | User content length: {} chars", len(system_prompt), len(user_content)
    )
    client = Groq(api_key=api_key)
    start = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=8192,
        )
        elapsed = round(time.time() - start, 1)
        reply = response.choices[0].message.content
        usage = response.usage
        logger.success("Groq LLM response received ({} chars, {:.1f}s)", len(reply), elapsed)
        return {
            "content": reply,
            "model": model,
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            },
            "elapsed_seconds": elapsed,
        }
    except Exception as e:
        logger.error("Groq LLM call failed: {}", e)
        raise


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def clone_repo(github_url: str, dest_dir: str) -> str:
    """Clone a public GitHub repo into *dest_dir* and return the local path."""
    repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
    local_path = os.path.join(dest_dir, repo_name)
    logger.info("Cloning repo '{}' into '{}'…", github_url, local_path)
    try:
        Repo.clone_from(github_url, local_path)
        logger.success("Repository cloned successfully to '{}'", local_path)
    except Exception as e:
        logger.error("Failed to clone repository '{}': {}", github_url, e)
        raise
    return local_path


def clone_and_ingest(github_url: str, status_callback: Callable | None = None) -> dict:
    """Clone a public GitHub repo and run ``gitingest`` on it.

    Returns a dict with the digest content and useful metadata.

    Parameters
    ----------
    github_url : str
        Public GitHub URL to clone.
    status_callback : callable, optional
        Called with ``(message: str)`` to report intermediate progress.

    Returns
    -------
    dict
        Keys: content, token_estimate, char_count, line_count, file_count,
        repo_name, elapsed_seconds.

    """
    # Patterns to exclude from ingestion – these files are heavy and have no
    # value for a code audit, but would blow up the token count and trigger
    # Groq rate-limit errors (HTTP 413).
    exclude_patterns = ",".join(
        [
            "uv.lock",
            "poetry.lock",
            "package-lock.json",
            "yarn.lock",
            "*.docx",
            "*.pdf",
            "*.xlsx",
            "*.pptx",
            "*.bin",
            "*.exe",
            "*.zip",
            "*.tar.gz",
            "*.png",
            "*.jpg",
            "*.jpeg",
            "*.gif",
            "*.svg",
            "*.woff",
            "*.woff2",
            "*.ttf",
            "*.eot",
        ]
    )

    def _report(msg: str) -> None:
        if status_callback:
            status_callback(msg)

    repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
    logger.info("Starting clone & ingest for '{}'", github_url)
    start = time.time()

    with tempfile.TemporaryDirectory() as tmp:
        _report("📥 Cloning repository…")
        local_path = clone_repo(github_url, tmp)
        _report("✅ Repository cloned")

        _report("🔄 Running gitingest — extracting source code…")
        logger.info("Running gitingest on '{}' (excluding: {})…", local_path, exclude_patterns)
        result = subprocess.run(
            [
                "uv",
                "run",
                "--with",
                "gitingest",
                "gitingest",
                ".",
                "--exclude-pattern",
                exclude_patterns,
            ],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.debug("gitingest stdout: {}", result.stdout[:500] if result.stdout else "(empty)")
        if result.stderr:
            logger.debug("gitingest stderr: {}", result.stderr[:500])

        digest_path = os.path.join(local_path, "digest.txt")
        logger.info("Reading digest file at '{}'", digest_path)
        with open(digest_path, encoding="utf-8") as f:
            content = f.read()

        # ----------------------------------------------------------
        # Supplement: gitingest silently excludes dotfiles (.gitignore,
        # .env, .python-version, etc.).  We scan the repo root for
        # common dotfiles and append them to the digest so the LLM
        # can evaluate their presence/content.
        # ----------------------------------------------------------
        _DOTFILES_TO_CHECK = [
            ".gitignore",
            ".env",
            ".env.example",
            ".python-version",
            ".flake8",
            ".editorconfig",
            ".pre-commit-config.yaml",
            ".gitattributes",
            ".dockerignore",
            ".nvmrc",
            ".tool-versions",
        ]
        separator = "=" * 48
        dotfile_supplement = ""
        for dotfile in _DOTFILES_TO_CHECK:
            dotfile_path = os.path.join(local_path, dotfile)
            if os.path.isfile(dotfile_path):
                try:
                    with open(dotfile_path, encoding="utf-8", errors="replace") as df:
                        dotfile_content = df.read()
                    dotfile_supplement += f"\n{separator}\nFile: {dotfile}\n{separator}\n{dotfile_content}\n"
                    logger.info("Supplemented digest with dotfile: {}", dotfile)
                except Exception as exc:
                    logger.warning("Could not read dotfile '{}': {}", dotfile, exc)

        # Also check for CI/CD config directories
        github_workflows = os.path.join(local_path, ".github", "workflows")
        if os.path.isdir(github_workflows):
            for wf_file in os.listdir(github_workflows):
                wf_path = os.path.join(github_workflows, wf_file)
                if os.path.isfile(wf_path):
                    try:
                        with open(wf_path, encoding="utf-8", errors="replace") as wf:
                            wf_content = wf.read()
                        dotfile_supplement += (
                            f"\n{separator}\nFile: .github/workflows/{wf_file}\n{separator}\n{wf_content}\n"
                        )
                        logger.info("Supplemented digest with workflow: .github/workflows/{}", wf_file)
                    except Exception as exc:
                        logger.warning("Could not read workflow file '{}': {}", wf_path, exc)

        if dotfile_supplement:
            content += dotfile_supplement
            logger.info("Dotfile supplement added ({} chars)", len(dotfile_supplement))

        elapsed = round(time.time() - start, 1)

        # Compute metadata
        char_count = len(content)
        line_count = content.count("\n")
        token_est = estimate_tokens(content)
        # Count files listed in the digest (gitingest marks files with
        # patterns like "File: path/to/file" or similar header lines)
        file_count = len(re.findall(r"^={4,}$", content, re.MULTILINE)) // 2 or (
            content.count("File: ") or line_count // 50
        )

        logger.success(
            "Digest loaded: {} chars, ~{} tokens, ~{} files, {:.1f}s",
            char_count,
            token_est,
            file_count,
            elapsed,
        )

        _report(
            f"✅ Ingestion complete — **~{token_est:,} tokens** · "
            f"{line_count:,} lines · {char_count:,} chars · {elapsed}s"
        )

        return {
            "content": content,
            "token_estimate": token_est,
            "char_count": char_count,
            "line_count": line_count,
            "file_count": file_count,
            "repo_name": repo_name,
            "elapsed_seconds": elapsed,
        }


def get_branches(repo_path: str) -> list[str]:
    """Return a list of remote branch names for the repo at *repo_path*."""
    logger.info("Fetching remote branches for '{}'…", repo_path)
    repo = Repo(repo_path)
    branches = [ref.remote_head for ref in repo.remotes.origin.refs]
    logger.info("Found {} branches: {}", len(branches), branches)
    return branches


def git_diff(repo_path: str, source_branch: str, target_branch: str) -> str:
    """Return the diff between *source_branch* and *target_branch*."""
    logger.info("Computing diff: origin/{} → origin/{}", target_branch, source_branch)
    repo = Repo(repo_path)
    diff = repo.git.diff(f"origin/{target_branch}", f"origin/{source_branch}")
    logger.info("Diff computed: {} chars", len(diff))
    return diff


def parse_gitingest_content(content: str) -> list[dict]:
    """Parse *content* (output from gitingest) into a list of file dicts.

    gitingest output format:

        ================================================================
        File: src/main.py
        ================================================================
        <file content here>

        ================================================================
        File: src/utils.py
        ================================================================
        <file content here>

    Each file header is sandwiched between two separator lines (``====…``).
    When we ``re.split`` by the separator, file headers and their content
    end up in **alternating** chunks that must be paired together.
    """
    separator_pattern = r"^={20,}$"
    raw_chunks = re.split(separator_pattern, content, flags=re.MULTILINE)

    # Strip all chunks once and filter out empty ones, keeping indices
    stripped = [(i, c.strip()) for i, c in enumerate(raw_chunks) if c.strip()]

    files = []
    skip_next = False

    for idx, (pos, chunk) in enumerate(stripped):
        if skip_next:
            skip_next = False
            continue

        lines = chunk.splitlines()
        first_line = lines[0].strip() if lines else ""

        # Detect a "File: <path>" or "FILE: <path>" header chunk (case-insensitive)
        first_line_lower = first_line.lower()
        if first_line_lower.startswith("file: "):
            # Extract path after "file: " (preserving original casing of the path)
            path = first_line[len("file: ") :].strip()

            # The CONTENT is the NEXT chunk (after the closing separator)
            if idx + 1 < len(stripped):
                _, next_chunk = stripped[idx + 1]
                # Make sure the next chunk is not another "File:" header
                next_first = next_chunk.splitlines()[0].strip() if next_chunk else ""
                if not next_first.lower().startswith("file: "):
                    file_content = next_chunk
                    skip_next = True
                else:
                    # Next chunk is another File header → this file is empty
                    file_content = ""
            else:
                file_content = ""

            files.append(
                {
                    "path": path,
                    "content": file_content,
                    "tokens": estimate_tokens(file_content) if file_content else 0,
                }
            )
        elif first_line_lower.startswith("directory:") or "files analyzed:" in chunk.lower():
            # Preamble / summary — skip
            logger.debug("Skipping preamble chunk: '{}'", first_line[:60])
            continue
        else:
            # Orphan content chunk (shouldn't happen with correct pairing)
            logger.debug("Orphan chunk (pos {}): '{}'", pos, first_line[:60])

    # FALLBACK: if parsing found nothing, treat the whole content as one file
    if not files and content.strip():
        logger.warning("parse_gitingest_content found 0 files. Falling back to single-file mode.")
        files.append(
            {
                "path": "entire_repo_digest.txt",
                "content": content,
                "tokens": estimate_tokens(content),
            }
        )

    total_tokens = sum(f["tokens"] for f in files)
    logger.info("Parsed {} files from digest. Total input tokens (est): {}", len(files), total_tokens)
    return files


def create_chunks(files: list[dict], max_tokens: int = 6000) -> list[str]:
    """Group *files* into text chunks, each roughly under *max_tokens*.

    If a single file is larger than *max_tokens*, it is split into multiple chunks.
    """
    chunks = []
    current_chunk_files = []
    current_chunk_tokens = 0

    def _flush_current_chunk() -> None:
        nonlocal current_chunk_files, current_chunk_tokens
        if current_chunk_files:
            text = "\n\n".join(current_chunk_files)
            chunks.append(text)
            current_chunk_files = []
            current_chunk_tokens = 0

    for f in files:
        f_tokens = f["tokens"]

        # CASE 1: File fits in the current chunk?
        if current_chunk_tokens + f_tokens <= max_tokens:
            entry = f"File: {f['path']}\n====================\n{f['content']}"
            current_chunk_files.append(entry)
            current_chunk_tokens += f_tokens
            continue

        # CASE 2: File is huge (larger than max_tokens) or just won't fit current chunk?

        # First, if we have a current chunk, flush it to start fresh
        if current_chunk_files:
            _flush_current_chunk()

        # Now, is the file ITSELF larger than max_tokens?
        if f_tokens > max_tokens:
            # We need to split this file
            logger.info("File '{}' is too large ({} tokens). Splitting...", f["path"], f_tokens)
            lines = f["content"].splitlines()

            # Accumulate lines for this file parts
            part_lines = []
            part_tokens = 0
            part_idx = 1

            # Header tokens approximation
            header = f"File: {f['path']} (Part {part_idx})\n====================\n"
            header_tokens = estimate_tokens(header)

            for line in lines:
                line_tokens = estimate_tokens(line) + 1  # +1 for newline

                if part_tokens + line_tokens + header_tokens > max_tokens:
                    # Flush this part
                    full_text = header + "\n".join(part_lines)
                    chunks.append(full_text)

                    # Reset for next part
                    part_idx += 1
                    part_lines = []
                    part_tokens = 0
                    header = f"File: {f['path']} (Part {part_idx})\n====================\n"
                    header_tokens = estimate_tokens(header)

                part_lines.append(line)
                part_tokens += line_tokens

            # Flush existing part
            if part_lines:
                full_text = header + "\n".join(part_lines)
                chunks.append(full_text)

        else:
            # File fits in a fresh chunk (we flushed above)
            entry = f"File: {f['path']}\n====================\n{f['content']}"
            current_chunk_files.append(entry)
            current_chunk_tokens = f_tokens

    # Flush any remaining
    _flush_current_chunk()

    logger.info("Created {} chunks from {} files.", len(chunks), len(files))
    return chunks


def map_reduce_analysis(
    api_key: str,
    model: str,
    prompt_template: str,
    chunks: list[str],
    repo_url: str,
    status_callback: Callable | None = None,
) -> dict:
    """Perform a Map-Reduce analysis on *chunks*."""

    def _report(msg: str) -> None:
        if status_callback:
            status_callback(msg)

    # 1. MAP PHASE
    partial_results = []
    total_chunks = len(chunks)

    for i, chunk in enumerate(chunks, 1):
        _report(f"Analyzing chunk {i}/{total_chunks}...")

        # Create a specific prompt for the chunk
        map_prompt = (
            f"You are analyzing PART {i} of {total_chunks} of the repository {repo_url}.\n\n"
            f"{prompt_template}\n\n"
            "INSTRUCTIONS FOR PARTIAL ANALYSIS:\n"
            "- Identify key findings in THIS chunk only.\n"
            "- Be concise but specific.\n"
            "- If you see partial implementations, note them.\n"
            "- DO NOT generate the final fully formatted report yet; provide a structured summary of observations."
        )

        try:
            # We must adhere to the rate limit per chunk too.
            result = call_groq_llm(api_key, model, map_prompt, chunk)
            partial_results.append(result["content"])
        except Exception as e:
            logger.error(f"Failed to analyze chunk {i}: {e}")
            partial_results.append(f"[Error analyzing chunk {i}: {e}]")

    # 2. REDUCE PHASE
    _report("Synthesizing final report...")

    combined_findings = "\n\n=== PARTIAL FINDING ===\n".join(partial_results)

    reduce_prompt = (
        f"You have analyzed the repository {repo_url} in {total_chunks} parts. "
        "Below are the partial findings from each part. "
        "Synthesize these into a SINGLE, COHERENT final report following the original audit grid format exactly.\n\n"
        f"ORIGINAL AUDIT GRID PROMPT:\n{prompt_template}\n\n"
        "PARTIAL FINDINGS TO SYNTHESIZE:\n"
        f"{combined_findings}"
    )

    reduce_system_msg = (
        f"You are a Lead Tech Auditor. Synthesize the provided partial findings into a final report for {repo_url}."
    )

    final_result = call_groq_llm(api_key, model, reduce_system_msg, reduce_prompt)

    return final_result


def analyze_code_content(
    api_key: str,
    model: str,
    prompt_template: str,
    code_content: str,
    repo_url: str,
    status_callback: Callable | None = None,
) -> dict:
    """Intelligent analysis that switches to Map-Reduce if content is too large."""
    # 1. Check size
    total_tokens = estimate_tokens(code_content)

    # Threshold: Groq's free tier/on-demand often has 8k TPM limits for large models (like Llama 3 70b or Mixtral).
    # We set a conservative threshold to trigger chunking early.
    TOKEN_THRESHOLD = 6000

    if total_tokens < TOKEN_THRESHOLD:
        # Standard Single-Pass
        if status_callback:
            status_callback(f"Running standard analysis (~{total_tokens} tokens)...")

        llm_content = f"GitHub Repository URL: {repo_url}\n\n{code_content}"
        return call_groq_llm(api_key, model, prompt_template.format(model_name=model, repo_url=repo_url), llm_content)
    else:
        # Map-Reduce Strategy
        if status_callback:
            status_callback(f"Large repository detected (~{total_tokens} tokens). Switching to Map-Reduce strategy...")

        files = parse_gitingest_content(code_content)
        # Chunk size also needs to be safe for TPM (input tokens)
        effective_max = 6000
        chunks = create_chunks(files, max_tokens=effective_max)

        if status_callback:
            status_callback(f"Parsed {len(files)} files. Split into {len(chunks)} chunks (max {effective_max} toks).")

        return map_reduce_analysis(
            api_key,
            model,
            prompt_template.format(model_name=model, repo_url=repo_url),
            chunks,
            repo_url,
            status_callback,
        )


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def load_prompt(filename: str) -> str:
    """Load a prompt file from the ``prompts/`` directory."""
    from pathlib import Path

    logger.info("Loading prompt file '{}'…", filename)
    # resolve() ensures an absolute path even on Streamlit Cloud
    project_root = Path(__file__).resolve().parent.parent.parent
    prompts_dir = project_root / "prompts"
    prompt_path = prompts_dir / filename
    content = prompt_path.read_text(encoding="utf-8")
    logger.success("Prompt '{}' loaded ({} chars)", filename, len(content))
    return content


def render_response_actions(response_text: str, key_prefix: str) -> None:
    """Render a copy-to-clipboard button and a download button for *response_text*."""
    import base64

    import streamlit.components.v1 as components

    logger.debug("Rendering response actions for key_prefix='{}'", key_prefix)

    b64_text = base64.b64encode(response_text.encode()).decode()

    copy_button_html = f"""
    <button id="copy-btn-{key_prefix}"
        onclick="
            navigator.clipboard.writeText(decodeURIComponent(atob('{b64_text}')
                .split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')))
            .then(() => {{
                const btn = document.getElementById('copy-btn-{key_prefix}');
                btn.textContent = 'Copied ✅';
                btn.style.background = '#2ea043';
                setTimeout(() => {{
                    btn.textContent = '📋 Copy response';
                    btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                }}, 2000);
            }});
        "
        style="
            padding: 0.55rem 1.4rem;
            font-size: 0.92rem;
            font-weight: 600;
            color: white;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            letter-spacing: 0.01em;
            box-shadow: 0 2px 8px rgba(102,126,234,0.20);
        "
        onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(102,126,234,0.35)'"
        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(102,126,234,0.20)'"
    >📋 Copy response</button>
    """

    col1, col2 = st.columns([1, 1])
    with col1:
        components.html(copy_button_html, height=50)
    with col2:
        st.download_button(
            label="📥 Download as .txt",
            data=response_text,
            file_name="response.txt",
            mime="text/plain",
            key=f"{key_prefix}_download",
        )
