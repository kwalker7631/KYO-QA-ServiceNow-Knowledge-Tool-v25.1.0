from pathlib import Path

FILES = ["logging_utils.py", "config.py", "custom_exceptions.py"]

def test_files_end_with_single_newline():
    repo_root = Path(__file__).resolve().parents[1]
    for name in FILES:
        with open(repo_root / name, 'rb') as f:
            data = f.read()
            assert data.endswith(b"\n"), f"{name} does not end with newline"
            assert not data.endswith(b"\n\n"), f"{name} ends with extra newlines"
