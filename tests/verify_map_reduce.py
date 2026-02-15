"""Verify the map-reduce chunking logic."""

import sys
import os
from unittest.mock import patch

# Add src to path relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

from dev_tooling_chat import utils


def test_chunking_and_map_reduce():
    print("Testing parse_gitingest_content...")

    # Simulate REAL gitingest output format:
    #   ====…====
    #   File: path
    #   ====…====
    #   <content>
    sep = "=" * 48

    content = f"""
{sep}
Directory: my_project
{sep}

├── src/
│   ├── file1.py
│   └── file2.py

{sep}
File: src/file1.py
{sep}
def foo():
    pass

{sep}
File: src/file2.py
{sep}
class Bar:
    def baz(self):
        return "hello"
"""

    files = utils.parse_gitingest_content(content)
    print(f"Found {len(files)} files.")
    for f in files:
        print(f"  - {f['path']} ({f['tokens']} tokens, {len(f['content'])} chars)")

    assert len(files) == 2, f"Expected 2 files, got {len(files)}"
    assert files[0]["path"] == "src/file1.py"
    assert files[1]["path"] == "src/file2.py"
    assert "def foo" in files[0]["content"]
    assert "class Bar" in files[1]["content"]

    print("\nTesting create_chunks...")
    # Force a tiny chunk size to trigger splitting
    chunks = utils.create_chunks(files, max_tokens=10)
    print(f"Created {len(chunks)} chunks with max_tokens=10")
    for i, c in enumerate(chunks):
        print(f"  Chunk {i+1}: {len(c)} chars")

    assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"

    print("\nTesting analyze_code_content logic (Map-Reduce)...")

    with patch("dev_tooling_chat.utils.call_groq_llm") as mock_llm:
        mock_llm.return_value = {
            "content": "Mocked Response",
            "usage": {"prompt_tokens": 50, "completion_tokens": 50, "total_tokens": 100},
            "elapsed_seconds": 1.0,
        }

        # Force the threshold to trigger map-reduce
        with patch("dev_tooling_chat.utils.estimate_tokens") as mock_est:
            mock_est.return_value = 50000  # > TOKEN_THRESHOLD

            with patch("dev_tooling_chat.utils.parse_gitingest_content") as mock_parse:
                mock_parse.return_value = files

                result = utils.analyze_code_content(
                    api_key="dummy",
                    model="dummy",
                    prompt_template="Analyze this.",
                    code_content=content,
                    repo_url="http://github.com/test/repo",
                    status_callback=lambda msg: print(f"  CB: {msg}"),
                )

                print(f"\nLLM called {mock_llm.call_count} times (expected >= 2)")
                assert mock_llm.call_count >= 2, f"Expected >= 2 LLM calls, got {mock_llm.call_count}"

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_chunking_and_map_reduce()
