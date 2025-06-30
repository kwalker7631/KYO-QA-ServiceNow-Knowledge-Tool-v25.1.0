import sys
import types
import queue
import threading
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import kyo_qa_tool_app


def test_start_processing_import(monkeypatch):
    dummy_mod = types.SimpleNamespace(
        run_processing_job=lambda job, q, ev: q.put("done")
    )
    monkeypatch.setitem(sys.modules, "processing_engine", dummy_mod)

    dummy_app = types.SimpleNamespace(
        is_processing=False,
        pause_event=threading.Event(),
        response_queue=queue.Queue(),
        cancel_event=threading.Event(),
        update_ui_for_processing_start=lambda: None,
        log_message=lambda *a, **k: None,
    )

    class DummyThread:
        def __init__(self, target, args, daemon=True):
            self.target = target
            self.args = args
        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(kyo_qa_tool_app.threading, "Thread", DummyThread)

    bound = kyo_qa_tool_app.KyoQAToolApp.start_processing.__get__(dummy_app, kyo_qa_tool_app.KyoQAToolApp)
    bound(job_request={"excel_path": "f.xlsx", "input_path": ["a.pdf"]})
    assert dummy_app.response_queue.get() == "done"
