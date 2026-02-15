# 🛠️ Dev Tooling Chat

**AI-powered code analysis assistant** built with [Streamlit](https://streamlit.io/) and the [Groq API](https://groq.com/).  
Upload a `.txt` file or point at a public GitHub repository and get instant, structured feedback — from recruitment-grade audits to senior-level code reviews and auto-generated merge request descriptions.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🔍 Audit & Diagnostic** | Evaluate a GitHub repository against a **10-point professional audit grid** used by technical recruiters. |
| **📝 Senior Code Review** | Get a comprehensive Python code review with **weighted scoring**, strengths, weaknesses and actionable recommendations. |
| **🔀 Merge Request Description** | Auto-generate a **complete, structured MR description** from a git diff between two branches. |

Every feature supports two input methods:

- **📄 File upload** — paste or export your code / diff as a `.txt` file.
- **🔗 GitHub URL** — provide a public repository URL; the app clones the repo and processes it automatically (via [gitingest](https://github.com/cyclotruc/gitingest)).

All AI responses can be **copied to clipboard** or **downloaded as `.txt`** with one click.

---

## 🗂️ Project Structure

```
dev_tooling_chat/
├── app.py                          # Streamlit entry point & page routing
├── views/
│   ├── __init__.py
│   ├── audit_diagnostic.py         # 🔍 Audit & Diagnostic page
│   ├── code_review.py              # 📝 Senior Code Review page
│   └── merge_request.py            # 🔀 Merge Request Description page
├── src/
│   └── dev_tooling_chat/
│       ├── __init__.py
│       └── utils.py                # Shared utilities (LLM, Git, UI helpers)
├── prompts/
│   ├── repo_recrutement.txt        # System prompt for Audit & Diagnostic
│   ├── code_audit.txt              # System prompt for Code Review
│   └── mr_assistant.txt            # System prompt for MR Description
├── Makefile                        # Common dev commands
├── pyproject.toml                  # Project metadata & dependencies
├── uv.lock                        # Lockfile (uv)
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | ≥ 3.12 |
| [uv](https://docs.astral.sh/uv/) | latest recommended |
| Git | any recent version |
| A [Groq API key](https://console.groq.com/keys) | free tier is fine |

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/dev_tooling_chat.git
cd dev_tooling_chat

# Create a virtual environment and install dependencies
uv sync
```

### Running the App

```bash
uv run streamlit run app.py
```

The application will open in your browser at **http://localhost:8501**.

### Make Targets

The project includes a `Makefile` for common tasks:

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies via `uv sync` |
| `make run` | Start the Streamlit app |
| `make run-dev` | Start with auto-reload & debug logging |
| `make lint` | Run the ruff linter |
| `make lint-fix` | Run ruff with auto-fix |
| `make format` | Format code with ruff |
| `make check` | Run all code quality checks (lint + format) |
| `make typecheck` | Run mypy type checking |
| `make build` | Build the distribution package |
| `make clean` | Remove caches and build artifacts |
| `make help` | Show all available targets |

---

## 🔧 Usage

1. **Enter your Groq API key** in the sidebar (starts with `gsk_...`).
2. **Select an AI model** from the dropdown — only text-generation models are listed.
3. **Pick a feature** from the sidebar navigation:
   - **Audit & Diagnostic** — upload code or provide a GitHub URL to run a recruitment audit.
   - **Senior Code Review** — upload code or provide a GitHub URL for a detailed code quality review.
   - **Merge Request Description** — upload a diff file, or provide a GitHub URL, select source/target branches, and generate a structured MR description.
4. **Review the AI response**, then use the **📋 Copy** or **📥 Download** buttons.

---

## 🧩 Architecture

```
┌──────────────────────────────────────┐
│              Streamlit UI            │
│         (app.py + views/)            │
├──────────────────────────────────────┤
│         dev_tooling_chat.utils       │
│  ┌───────────┬──────────┬──────────┐ │
│  │ LLM layer │ Git      │ UI       │ │
│  │ (Groq API)│ helpers  │ helpers  │ │
│  └───────────┴──────────┴──────────┘ │
├──────────────────────────────────────┤
│           prompts/*.txt              │
│     (system prompts per feature)     │
└──────────────────────────────────────┘
```

- **`app.py`** — Configures the Streamlit page, renders the sidebar (API key input, model selector, navigation), and routes to the appropriate view.
- **`views/`** — Each feature is a self-contained module exposing a `render()` function.
- **`src/dev_tooling_chat/utils.py`** — Shared logic split into three sections:
  - **LLM** — `fetch_groq_models()` and `call_groq_llm()` for interacting with the Groq chat API.
  - **Git helpers** — `clone_repo()`, `clone_and_ingest()`, `get_branches()`, `git_diff()` for repository operations.
  - **UI helpers** — `load_prompt()` and `render_response_actions()` (copy + download buttons).
- **`prompts/`** — Plain-text system prompts injected into the LLM call for each feature.

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| [streamlit](https://pypi.org/project/streamlit/) ≥ 1.40 | Web UI framework |
| [groq](https://pypi.org/project/groq/) ≥ 0.15 | Groq API Python client |
| [gitpython](https://pypi.org/project/GitPython/) ≥ 3.1 | Git operations (clone, diff, branches) |
| [requests](https://pypi.org/project/requests/) ≥ 2.31 | HTTP calls to the Groq models endpoint |

> **Runtime tool:** The *Audit & Diagnostic* and *Code Review* features also invoke [`gitingest`](https://github.com/cyclotruc/gitingest) via `uv run --with gitingest gitingest .` to digest a cloned repository into a single text file.

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/my-feature`.
3. Commit your changes: `git commit -m "feat: add my feature"`.
4. Push to the branch: `git push origin feat/my-feature`.
5. Open a Pull Request.

---

## 📄 License

This project does not currently specify a license. Please contact the author before reusing.

---

## 👤 Author

**Cao Tri DO** — [caotri.do88@gmail.com](mailto:caotri.do88@gmail.com)
