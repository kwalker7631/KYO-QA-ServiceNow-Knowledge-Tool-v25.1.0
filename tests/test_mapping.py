import sys
import types
import importlib
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# ruff: noqa: E402

# Stub external dependencies if missing
for mod in ('pandas', 'fitz'):
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

if 'dateutil' not in sys.modules:
    dateutil = types.ModuleType('dateutil')
    sys.modules['dateutil'] = dateutil
if 'dateutil.relativedelta' not in sys.modules:
    rd = types.ModuleType('dateutil.relativedelta')
    class _RD:
        def __init__(self, **kw):
            pass
    rd.relativedelta = _RD
    sys.modules['dateutil.relativedelta'] = rd

processing_engine = importlib.import_module('processing_engine')
from config import HEADER_MAPPING


def test_mapping_contains_required_headers():
    sample = {
        'author': 'Alice',
        'models': 'ModelX',
        'subject': 'Test Subject',
        'needs_review': True,
        'published_date': '2020-01-01',
    }
    result = processing_engine.map_to_servicenow_format(sample, 'file.pdf')
    # Ensure every header exists in result
    for header in HEADER_MAPPING.values():
        assert header in result

    assert result[HEADER_MAPPING['short_description']] == 'Test Subject'
    assert result[HEADER_MAPPING['models']] == 'ModelX'
    assert result[HEADER_MAPPING['processing_status']] == 'Needs Review'


