import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import version

def test_version():
    assert version.VERSION == "25.0.0"
