import sys
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from ai_extractor import bulletproof_extraction


def test_qa_number_patterns():
    cases = [
        ("Ref. No. AB-1234 (E11)", "AB-1234", "E11"),
        ("AB-5678 (E22)", "AB-5678", "E22"),
        ("Ref. No. XY-9876 (E33)", "XY-9876", "E33"),
        ("E123-AB-4567", "E123-AB-4567", "E123"),
        ("ZZ-2024 (E55)", "ZZ-2024", "E55"),
    ]
    for text, full, short in cases:
        sample = f"{text}\nModel:\nTASKalfa 2550ci"
        result = bulletproof_extraction(sample, "file.pdf")
        assert result["full_qa_number"] == full
        assert result.get("short_qa_number") == short
        assert result["models"] == "TASKalfa 2550ci"


def test_model_patterns():
    cases = [
        (
            "Ref. No. AA-1111 (E11)\nModel:\nTASKalfa 3005i\nECOSYS M3040",
            "TASKalfa 3005i ECOSYS M3040",
        ),
        (
            "Ref. No. AA-2222 (E12)\nSome info TASKalfa 1230i present",
            "TASKalfa 1230i present",
        ),
    ]
    for text, models in cases:
        result = bulletproof_extraction(text, "file.pdf")
        assert result["models"] == models

