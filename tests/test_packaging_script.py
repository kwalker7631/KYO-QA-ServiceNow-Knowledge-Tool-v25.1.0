import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import packaging_script
from version import get_version

def test_out_zip_contains_version():
    version = get_version()
    assert version in packaging_script.out_zip.name

def test_no_hardcoded_version_constant():
    # Ensure packaging_script defines VERSION using get_version
    assert hasattr(packaging_script, 'VERSION')
    assert packaging_script.VERSION == get_version()
