import sys
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import run

def test_run_version_constant():
    assert run.VERSION == "v25.0.1"
