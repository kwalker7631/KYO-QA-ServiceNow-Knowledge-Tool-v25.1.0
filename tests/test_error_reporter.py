from pathlib import Path
from error_reporter import extract_snippet


def test_extract_snippet(tmp_path):
    f = tmp_path / "demo.py"
    f.write_text("a\nb\nc\n")
    snippet = extract_snippet(str(f), 2, context=1)
    assert "2: b" in snippet
