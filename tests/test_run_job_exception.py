import types
import queue
import kyo_qa_tool_app


def test_run_job_wrapper_handles_exception(monkeypatch):
    dummy = types.SimpleNamespace(response_queue=queue.Queue(), cancel_event=None)
    method = kyo_qa_tool_app.KyoQAToolApp.run_job_with_error_handling.__get__(dummy, type(dummy))

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(kyo_qa_tool_app, "run_processing_job", boom)
    calls = {}
    monkeypatch.setattr(kyo_qa_tool_app.logging_utils, "log_exception", lambda *a, **k: calls.setdefault("log", True))
    monkeypatch.setattr(kyo_qa_tool_app.messagebox, "showerror", lambda *a, **k: calls.setdefault("dlg", True))

    method({})

    assert calls.get("log")
    assert calls.get("dlg")
    msg = dummy.response_queue.get_nowait()
    assert msg["type"] == "finish"
