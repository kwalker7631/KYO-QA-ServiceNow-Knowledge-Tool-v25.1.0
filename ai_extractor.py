"""Extraction entry points for QA knowledge tool."""

def ai_extract(text: str, pdf_path):
    """Proxy to :func:`data_harvesters.ai_extract`. Any caller can monkeypatch
    ``data_harvesters.harvest_metadata`` before invoking this helper to adjust
    metadata extraction."""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = QAApp()
    win.show()
    sys.exit(app.exec())
