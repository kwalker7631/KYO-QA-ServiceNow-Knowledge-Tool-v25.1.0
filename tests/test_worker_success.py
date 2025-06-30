import types
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from kyo_qa_tool_app import Worker


def test_worker_runs_job(monkeypatch):
    called = {}
    def fake_job(info, q, ev):
        called['info'] = info
    monkeypatch.setitem(sys.modules, 'processing_engine', types.SimpleNamespace(run_processing_job=fake_job))

    result = []
    w = Worker('in', 'excel.xlsx')
    w.finished = types.SimpleNamespace(emit=lambda m: result.append(m))
    w.run()

    assert called['info']['excel_path'] == 'excel.xlsx'
    assert result == ['Complete']
