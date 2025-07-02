import importlib
import sys


def test_bulletproof_extraction_fallback(monkeypatch):
    # Ensure the optional extract package is not available
    monkeypatch.setitem(sys.modules, "extract.common", None)
    ai_extractor = importlib.import_module("ai_extractor")
    importlib.reload(ai_extractor)
    text = "The quick brown fox jumps over the lazy dog"
    patterns = [r"quick\s+brown\s+(\w+)", r"(lazy\s+dog)"]
    result = ai_extractor.bulletproof_extraction(text, patterns)
    assert "fox" in result
    assert "lazy dog" in result
