import sys
from pathlib import Path
import types

# ruff: noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub heavy dependencies for import
openpyxl_stub = types.ModuleType("openpyxl")
openpyxl_stub.load_workbook = lambda *a, **k: None
openpyxl_stub.styles = types.ModuleType("openpyxl.styles")
openpyxl_stub.styles.PatternFill = lambda **kw: None
openpyxl_stub.styles.Alignment = lambda **kw: None
openpyxl_stub.utils = types.ModuleType("openpyxl.utils")
openpyxl_stub.utils.get_column_letter = lambda x: "A"
openpyxl_stub.utils.exceptions = types.ModuleType("openpyxl.utils.exceptions")
openpyxl_stub.utils.exceptions.InvalidFileException = Exception
sys.modules.setdefault("openpyxl", openpyxl_stub)
sys.modules.setdefault("openpyxl.styles", openpyxl_stub.styles)
sys.modules.setdefault("openpyxl.utils", openpyxl_stub.utils)
sys.modules.setdefault("openpyxl.utils.exceptions", openpyxl_stub.utils.exceptions)

sys.modules.setdefault("fitz", types.ModuleType("fitz"))
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
pytesseract_mod = types.ModuleType("pytesseract")
pytesseract_mod.image_to_string = lambda *a, **k: ""
sys.modules.setdefault("pytesseract", pytesseract_mod)

import cli_runner


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

