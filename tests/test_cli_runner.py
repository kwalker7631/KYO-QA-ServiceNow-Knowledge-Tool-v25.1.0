import sys
from pathlib import Path
import types
from tests.openpyxl_stub import ensure_openpyxl_stub

# ruff: noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub heavy dependencies for import
ensure_openpyxl_stub()
if 'PIL.Image' not in sys.modules:
    pil_image_stub = types.SimpleNamespace(open=lambda *a, **k: None)
    pil_stub = types.SimpleNamespace(Image=pil_image_stub)
    sys.modules.setdefault('PIL', pil_stub)
    sys.modules.setdefault('PIL.Image', pil_image_stub)

processing_stub = types.ModuleType("processing_engine")
processing_stub.process_folder = lambda *a, **k: None
processing_stub.process_zip_archive = lambda *a, **k: None
sys.modules.setdefault("processing_engine", processing_stub)

# Stub Pillow's Image module
pil_stub = types.ModuleType("PIL")
pil_stub.Image = types.SimpleNamespace(open=lambda *a, **k: None)
sys.modules.setdefault("PIL", pil_stub)
sys.modules.setdefault("fitz", types.ModuleType("fitz"))
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
pytesseract_mod = types.ModuleType("pytesseract")
pytesseract_mod.image_to_string = lambda *a, **k: ""
sys.modules.setdefault("pytesseract", pytesseract_mod)

import pytest

try:
    import cli_runner
except Exception:  # pragma: no cover - skip if dependencies missing
    pytest.skip("cli_runner unavailable", allow_module_level=True)


def test_main_runs(monkeypatch, tmp_path):
    folder_called = {}
    zip_called = {}

    def fake_process_folder(folder, excel, *a):
        folder_called['path'] = folder
        folder_called['excel'] = excel

    def fake_process_zip(zip_path, excel, *a):
        zip_called['path'] = zip_path
        zip_called['excel'] = excel

    monkeypatch.setattr(cli_runner, 'process_folder', fake_process_folder)
    monkeypatch.setattr(cli_runner, 'process_zip_archive', fake_process_zip)

    excel = tmp_path / "base.xlsx"
    excel.write_text("dummy")

    monkeypatch.setattr(sys, 'argv', ['cli_runner.py', '--folder', str(tmp_path), '--excel', str(excel)])
    cli_runner.main()
    assert folder_called

    zip_file = tmp_path / 'docs.zip'
    import zipfile
    with zipfile.ZipFile(zip_file, 'w'):
        pass
    new_excel = tmp_path / "base2.xlsx"
    new_excel.write_text("dummy")

    folder_called.clear()
    monkeypatch.setattr(sys, 'argv', ['cli_runner.py', '--zip', str(zip_file), '--excel', str(new_excel)])
    cli_runner.main()
    assert zip_called

