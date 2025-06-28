import sys
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from version import VERSION, get_version

def test_get_version():
    assert get_version() == VERSION == "v25.0.1"


def test_no_main_attr():
    import version
    assert not hasattr(version, "main")
