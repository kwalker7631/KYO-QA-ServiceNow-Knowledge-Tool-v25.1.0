import sys
import types
from pathlib import Path

# Ensure repo root is on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

try:
    import openpyxl  # type: ignore
except ModuleNotFoundError:
    openpyxl = types.ModuleType('openpyxl')
    styles = types.ModuleType('styles')
    styles.PatternFill = object
    styles.Alignment = object
    utils = types.ModuleType('utils')
    utils.get_column_letter = lambda x: x
    openpyxl.styles = styles
    openpyxl.utils = utils
    openpyxl.Workbook = object
    sys.modules['openpyxl'] = openpyxl
    sys.modules['openpyxl.styles'] = styles
    sys.modules['openpyxl.utils'] = utils

import cli_runner


def test_cli_main_calls_ensure_folders(monkeypatch, tmp_path):
    called = {}

    def fake_ensure():
        called['called'] = True

    monkeypatch.setattr(cli_runner, 'ensure_folders', fake_ensure)
    monkeypatch.setattr(cli_runner, 'process_folder', lambda *a, **k: None)
    monkeypatch.setattr(cli_runner, 'process_zip_archive', lambda *a, **k: None)
    monkeypatch.setattr('builtins.print', lambda *a, **k: None)

    excel = tmp_path / 'base.xlsx'
    excel.write_text('x')

    argv = [
        'cli_runner',
        '--folder', str(tmp_path),
        '--excel', str(excel)
    ]
    monkeypatch.setattr(sys, 'argv', argv)

    cli_runner.main()

    assert called.get('called')
