import os
from tempfile import TemporaryDirectory
import pytest

from excel_generator import ExcelWriter, NEEDS_REVIEW_FILL, FAILED_FILL


def test_excel_writer_row_colors():
    with TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'out.xlsx')
        headers = ['processing_status', 'Title']
        writer = ExcelWriter(path, headers)
        writer.add_row({'processing_status': 'Needs Review', 'Title': 'One'})
        writer.add_row({'processing_status': 'Failed', 'Title': 'Two'})
        writer.save()

        import openpyxl
        wb = openpyxl.load_workbook(path)
        ws = wb.active
        # Row colors should match status
        assert ws['A2'].fill.start_color.rgb == NEEDS_REVIEW_FILL.start_color.rgb
        assert ws['A3'].fill.start_color.rgb == FAILED_FILL.start_color.rgb
