import sys
from pathlib import Path
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
openpyxl_stub = types.ModuleType("openpyxl")
styles_stub = types.ModuleType("openpyxl.styles")
utils_stub = types.ModuleType("openpyxl.utils")
setattr(styles_stub, "PatternFill", object)
setattr(styles_stub, "Alignment", object)
setattr(utils_stub, "get_column_letter", lambda x: str(x))
openpyxl_stub.styles = styles_stub
openpyxl_stub.utils = utils_stub
sys.modules.setdefault("openpyxl", openpyxl_stub)
sys.modules.setdefault("openpyxl.styles", styles_stub)
sys.modules.setdefault("openpyxl.utils", utils_stub)

ocr_stub = types.ModuleType("ocr_utils")
ocr_stub.extract_text_from_pdf = lambda x: ""
ocr_stub._is_ocr_needed = lambda x: False
sys.modules.setdefault("ocr_utils", ocr_stub)

import processing_engine
from unittest import mock

def test_process_folder_invokes_run(tmp_path):
    excel = tmp_path / "base.xlsx"
    excel.touch()
    called = {}

    def dummy_run(job_info, queue, cancel, pause):
        called['info'] = job_info

    with mock.patch('processing_engine.run_processing_job', dummy_run):
        processing_engine.process_folder(tmp_path, excel)
    assert called['info']['excel_path'] == excel
    assert called['info']['input_path'] == tmp_path


def test_process_zip_archive_invokes_run(tmp_path):
    excel = tmp_path / "base.xlsx"
    excel.touch()
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("pdf")
    zip_path = tmp_path / "docs.zip"
    import zipfile
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(pdf, pdf.name)

    called = {}

    def dummy_run(job_info, queue, cancel, pause):
        called['info'] = job_info

    with mock.patch('processing_engine.run_processing_job', dummy_run):
        processing_engine.process_zip_archive(zip_path, excel)

    assert called['info']['excel_path'] == excel



