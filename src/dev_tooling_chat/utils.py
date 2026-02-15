"""Shared utilities for Dev Tooling Chat."""

import os
import subprocess
import tempfile
import requests
import streamlit as st
from groq import Groq
from git import Repo


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
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return sorted([
        m["id"] for m in data.get("data", [])
        if _is_text_generation_model(m["id"])
    ])


def call_groq_llm(api_key: str, model: str, system_prompt: str, user_content: str) -> str:
    """Send *system_prompt* + *user_content* to the Groq chat API and return
    the assistant's reply as a string."""
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
        max_tokens=8192,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def clone_repo(github_url: str, dest_dir: str) -> str:
    """Clone a public GitHub repo into *dest_dir* and return the local path."""
    repo_name = github_url.rstrip("/").split("/")[-1].replace(".git", "")
    local_path = os.path.join(dest_dir, repo_name)
    Repo.clone_from(github_url, local_path)
    return local_path


def clone_and_ingest(github_url: str) -> str:
    """Clone a public GitHub repo, run ``gitingest`` on it and return the
    content of the generated ``digest.txt`` file."""
    # Patterns to exclude from ingestion – these files are heavy and have no
    # value for a code audit, but would blow up the token count and trigger
    # Groq rate-limit errors (HTTP 413).
    exclude_patterns = ",".join([
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
    ])

    with tempfile.TemporaryDirectory() as tmp:
        local_path = clone_repo(github_url, tmp)
        subprocess.run(
            [
                "uv", "run", "--with", "gitingest", "gitingest", ".",
                "--exclude-pattern", exclude_patterns,
            ],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True,
        )
        digest_path = os.path.join(local_path, "digest.txt")
        with open(digest_path, "r", encoding="utf-8") as f:
            return f.read()


def get_branches(repo_path: str) -> list[str]:
    """Return a list of remote branch names for the repo at *repo_path*."""
    repo = Repo(repo_path)
    return [ref.remote_head for ref in repo.remotes.origin.refs]


def git_diff(repo_path: str, source_branch: str, target_branch: str) -> str:
    """Return the diff between *source_branch* and *target_branch*."""
    repo = Repo(repo_path)
    return repo.git.diff(f"origin/{target_branch}", f"origin/{source_branch}")


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def load_prompt(filename: str) -> str:
    """Load a prompt file from the ``prompts/`` directory."""
    from pathlib import Path

    # resolve() ensures an absolute path even on Streamlit Cloud
    project_root = Path(__file__).resolve().parent.parent.parent
    prompts_dir = project_root / "prompts"
    return (prompts_dir / filename).read_text(encoding="utf-8")


def render_response_actions(response_text: str, key_prefix: str) -> None:
    """Render a copy-to-clipboard button and a download button for *response_text*."""
    import html as html_mod
    import streamlit.components.v1 as components

    escaped = html_mod.escape(response_text).replace("`", "\\`").replace("${", "\\${")

    copy_button_html = f"""
    <button id="copy-btn-{key_prefix}"
        onclick="
            navigator.clipboard.writeText(decodeURIComponent(atob('{__import__('base64').b64encode(response_text.encode()).decode()}')
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
            padding: 8px 20px;
            font-size: 14px;
            font-weight: 600;
            color: white;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-right: 8px;
        "
        onmouseover="this.style.opacity='0.85'"
        onmouseout="this.style.opacity='1'"
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
