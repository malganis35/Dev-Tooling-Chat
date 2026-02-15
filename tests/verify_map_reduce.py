import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path relative to this script
# tests/ is one level deep, so we go up one level to root, then into src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
sys.path.append(src_path)

from dev_tooling_chat import utils

def test_chunking_and_map_reduce():
    print("Testing parse_gitingest_content...")
    # Simulate gitingest output
    # IMPORTANT: Ensure the mock content has enough tokens or the assert for chunks might fail if max_tokens is huge.
    # But here we pass max_tokens=10 explicitly to create_chunks.
    
    content = """
========================================
File: src/file1.py
========================================
def foo():
    pass

========================================
File: src/file2.py
========================================
class Bar:
    def baz(self):
        return "hello"
"""
    # Replace the visual separator with the regex-compatible one (20+ equals)
    content = content.replace("========================================", "="*40)
    
    files = utils.parse_gitingest_content(content)
    print(f"Found {len(files)} files.")
    for f in files:
        print(f" - {f['path']} ({f['tokens']} tokens)")
        
    assert len(files) == 2, "Should find 2 files"
    assert files[0]["path"] == "src/file1.py"
    assert files[1]["path"] == "src/file2.py"
    
    print("\nTesting create_chunks...")
    # Create a scenario where files need to be split into chunks
    # Let's force a small chunk size
    chunks = utils.create_chunks(files, max_tokens=10) 
    print(f"Created {len(chunks)} chunks with max_tokens=10")
    for i, c in enumerate(chunks):
        print(f"Chunk {i+1} length: {len(c)} chars")
    
    assert len(chunks) == 2, f"Should be 2 chunks, got {len(chunks)}"
    
    print("\nTesting analyze_code_content logic (Map-Reduce)...")
    
    # Mock call_groq_llm
    with patch("dev_tooling_chat.utils.call_groq_llm") as mock_llm:
        mock_llm.return_value = {
            "content": "Mocked Response", 
            "usage": {"total_tokens": 100}, 
            "elapsed_seconds": 1.0
        }
        
        # Trigger Map-Reduce by forcing huge content
        # We can just mock estimate_tokens to return a huge number
        with patch("dev_tooling_chat.utils.estimate_tokens") as mock_est:
            mock_est.return_value = 50000 # > THRESHOLD
            
            # We also need parse_gitingest_content to return something valid
            # so create_chunks doesn't return empty list
            with patch("dev_tooling_chat.utils.parse_gitingest_content") as mock_parse:
                mock_parse.return_value = files # reusing our small files
                
                utils.analyze_code_content(
                    api_key="dummy",
                    model="dummy",
                    prompt_template="Analyze this.",
                    code_content=content,
                    repo_url="http://github.com/test/repo",
                    status_callback=lambda msg: print(f"CB: {msg}")
                )
                
                print(f"LLM called {mock_llm.call_count} times")
                assert mock_llm.call_count >= 2
                
    print("\n✅ Verification Successful!")

if __name__ == "__main__":
    test_chunking_and_map_reduce()
