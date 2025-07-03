import json
from pathlib import Path


class TextRedirector:
    """Simple stdout redirector used in tests."""

    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass


PDF_TXT_DIR = Path("PDF_TXT")
CACHE_DIR = Path(".cache")


class KyoQAToolApp:
    """Minimal stub of the main application for tests."""

    def __init__(self):
        self.last_run_info = {}

    def _collect_review_pdfs(self):
        pdfs = []
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
                pdf_path = info.get("pdf_path")
                if pdf_path:
                    txt_path = PDF_TXT_DIR / Path(pdf_path).with_suffix(".txt").name
                    if txt_path.exists():
                        pdfs.append(pdf_path)
            except Exception:
                continue
        return pdfs
