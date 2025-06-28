from pathlib import Path

REQUIRED_PACKAGES = {"PyMuPDF", "Pillow", "python-dateutil", "ollama"}

def test_new_requirements_present():
    req_file = Path(__file__).resolve().parents[1] / "requirements.txt"
    content = req_file.read_text()
    missing = [pkg for pkg in REQUIRED_PACKAGES if pkg not in content]
    assert not missing, f"Missing packages in requirements.txt: {missing}"
