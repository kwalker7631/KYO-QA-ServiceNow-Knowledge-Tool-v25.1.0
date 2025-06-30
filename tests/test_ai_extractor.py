import importlib
import types
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_bulletproof_import():
    # Prepare dummy extract.common module
    extract_mod = types.ModuleType("extract")
    common_mod = types.ModuleType("extract.common")

    def bulletproof_extraction():
        return "dummy"

    common_mod.bulletproof_extraction = bulletproof_extraction
    extract_mod.common = common_mod

    sys.modules["extract"] = extract_mod
    sys.modules["extract.common"] = common_mod

    # Stub data_harvesters with minimal API
    dh = types.ModuleType("data_harvesters")

    def ai_extract():
        return None

    def harvest_metadata():
        return None

    dh.ai_extract = ai_extract
    dh.harvest_metadata = harvest_metadata
    sys.modules["data_harvesters"] = dh

    ai_ext = importlib.reload(importlib.import_module("ai_extractor"))
    assert ai_ext.bulletproof_extraction() == "dummy"
    assert "bulletproof_extraction" in ai_ext.__all__

    # Cleanup
    del sys.modules["extract.common"]
    del sys.modules["extract"]
    del sys.modules["data_harvesters"]
    del sys.modules["ai_extractor"]

