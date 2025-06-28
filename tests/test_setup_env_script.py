from pathlib import Path


def test_setup_env_script_exists():
    script = Path(__file__).resolve().parents[1] / "scripts" / "setup_env.sh"
    assert script.exists(), "setup_env.sh script should exist"

