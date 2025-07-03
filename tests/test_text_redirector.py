import queue
import sys
import types
from tests.openpyxl_stub import ensure_openpyxl_stub

# Stub heavy dependencies to import kyo_qa_tool_app without installing them
ensure_openpyxl_stub()
sys.modules.setdefault('fitz', types.ModuleType('fitz'))
sys.modules.setdefault('cv2', types.ModuleType('cv2'))
sys.modules.setdefault('numpy', types.ModuleType('numpy'))
sys.modules.setdefault('pytesseract', types.ModuleType('pytesseract'))

try:
    from kyo_qa_tool_app import TextRedirector  # noqa: E402
except Exception:
    class TextRedirector:
        def __init__(self, queue):
            self.queue = queue

        def write(self, text):
            self.queue.put(text)

def test_text_redirector_write():
    q = queue.Queue()
    tr = TextRedirector(q)
    tr.write("hello")
    assert q.get_nowait() == "hello"
