import queue
import sys
import types
from tests.openpyxl_stub import ensure_openpyxl_stub
import zipfile
from pathlib import Path
import pytest

# ruff: noqa: E402

# Stub dependencies not available in the test environment
fake_ocr_utils = types.ModuleType("ocr_utils")
fake_ocr_utils.extract_text_from_pdf = lambda p: ""
fake_ocr_utils._is_ocr_needed = lambda p: False
sys.modules["ocr_utils"] = fake_ocr_utils
ensure_openpyxl_stub()

import processing_engine  # noqa: E402


def test_process_single_pdf_ocr_failed(tmp_path, monkeypatch):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")
    processing_engine.CACHE_DIR = tmp_path / ".cache"
    processing_engine.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    processing_engine.PDF_TXT_DIR = tmp_path / "PDF_TXT"
    processing_engine.PDF_TXT_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(processing_engine, "extract_text_from_pdf", lambda p: "")
    monkeypatch.setattr(processing_engine, "_is_ocr_needed", lambda p: True)
    q = queue.Queue()
    result = processing_engine.process_single_pdf(pdf, q)
    msgs = []
    while not q.empty():
        msgs.append(q.get())
    assert result["status"] == "Fail"
    assert not any(m.get("type") == "review_item" for m in msgs)


def test_process_folder_invalid_path():
    with pytest.raises(FileNotFoundError):
        processing_engine.process_folder(
            "does/not/exist",
            "base.xlsx",
            None,
            None,
            None,
            None,
            lambda: False,
        )


def test_process_folder_calls_execute_job(monkeypatch, tmp_path):
    called = {}

    def fake_execute(job, *a):
        called.update(job)

    monkeypatch.setattr(processing_engine, "_execute_job", fake_execute)
    folder = tmp_path / "docs"
    folder.mkdir()
    excel = tmp_path / "base.xlsx"
    excel.write_text("x")

    processing_engine.process_folder(
        folder,
        excel,
        None,
        None,
        None,
        None,
        lambda: False,
    )

    assert called["input_path"] == folder
    assert called["excel_path"] == excel


def test_process_zip_archive_bad_zip(tmp_path):
    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_text("not a zip")
    with pytest.raises(zipfile.BadZipFile):
        processing_engine.process_zip_archive(
            bad_zip,
            "base.xlsx",
            None,
            None,
            None,
            None,
            lambda: False,
        )


def test_process_zip_archive_calls_process_folder(monkeypatch, tmp_path):
    pdf = tmp_path / "file.pdf"
    pdf.write_text("x")
    zip_path = tmp_path / "docs.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(pdf, pdf.name)

    called = {}

    def fake_process_folder(path, excel, *a):
        called["folder"] = Path(path)
        called["excel"] = excel

    monkeypatch.setattr(processing_engine, "process_folder", fake_process_folder)
    excel = tmp_path / "base.xlsx"
    excel.write_text("x")

    processing_engine.process_zip_archive(
        zip_path,
        excel,
        None,
        None,
        None,
        None,
        lambda: False,
    )

    assert isinstance(called["folder"], Path)
    assert called["excel"] == excel
