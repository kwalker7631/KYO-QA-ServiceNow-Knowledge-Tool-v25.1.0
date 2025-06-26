import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from processing_engine import map_to_servicenow_format
from config import HEADER_MAPPING
from excel_generator import ExcelWriter
from openpyxl import load_workbook


def test_map_to_servicenow_format_keys():
    sample = {
        "author": "Jane",
        "short_description": "Example",
        "models": "Model A",
    }
    result = map_to_servicenow_format(sample, "file.pdf")
    assert set(HEADER_MAPPING.values()).issubset(result.keys())
    assert result[HEADER_MAPPING["file_name"]] == "file.pdf"
    assert result[HEADER_MAPPING["author"]] == "Jane"


def test_excel_writer_save_creates_file(tmp_path):
    filepath = tmp_path / "out.xlsx"
    headers = ["Col1", "Col2"]
    writer = ExcelWriter(filepath, headers)
    writer.add_row({"Col1": "A", "Col2": "B"})
    writer.save()
    assert filepath.exists()
    wb = load_workbook(filepath)
    sheet = wb.active
    assert sheet["A1"].font.bold
