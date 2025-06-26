import sys
from pathlib import Path
import importlib
from types import ModuleType

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub heavy optional modules so imports don't fail
if 'openpyxl' not in sys.modules:
    xl = ModuleType('openpyxl')
    styles = ModuleType('openpyxl.styles')
    class _Dummy:
        def __init__(self, *a, **k):
            pass
    styles.Alignment = _Dummy
    styles.Font = _Dummy
    styles.PatternFill = _Dummy
    xl.styles = styles
    sys.modules['openpyxl'] = xl
    sys.modules['openpyxl.styles'] = styles

sys.modules.setdefault('fitz', ModuleType('fitz'))

MODULES = [
    "ai_extractor",
    "custom_exceptions",
    "excel_generator",
    "file_utils",
    "ocr_utils",
    "processing_engine",
]

def test_modules_importable():
    for name in MODULES:
        mod = importlib.import_module(name)
        assert mod is not None
