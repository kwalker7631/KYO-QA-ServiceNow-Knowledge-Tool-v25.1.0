import queue
import sys
import types

# Stub heavy dependencies to import kyo_qa_tool_app without installing them
openpyxl_stub = types.ModuleType('openpyxl')
openpyxl_stub.styles = types.ModuleType('openpyxl.styles')
openpyxl_stub.utils = types.ModuleType('openpyxl.utils')
openpyxl_stub.styles.PatternFill = object
openpyxl_stub.utils.get_column_letter = lambda x: 'A'
sys.modules.setdefault('openpyxl', openpyxl_stub)
sys.modules.setdefault('openpyxl.styles', openpyxl_stub.styles)
sys.modules.setdefault('openpyxl.utils', openpyxl_stub.utils)
sys.modules.setdefault('fitz', types.ModuleType('fitz'))
sys.modules.setdefault('cv2', types.ModuleType('cv2'))
sys.modules.setdefault('numpy', types.ModuleType('numpy'))
sys.modules.setdefault('pytesseract', types.ModuleType('pytesseract'))

from kyo_qa_tool_app import TextRedirector  # noqa: E402


def test_text_redirector_write():
    q = queue.Queue()
    tr = TextRedirector(q)
    tr.write("hello")
    assert q.get_nowait() == "hello"
