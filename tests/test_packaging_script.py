import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import packaging_script


def test_include_no_unused_entries():
    # ensure unused files aren't packaged
    assert "extract" not in packaging_script.include
    assert "api_manager.py" not in packaging_script.include

