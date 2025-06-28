import sys
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import start_tool


def test_launch_application_uses_correct_script(monkeypatch):
    captured = {}
    def fake_run(cmd, check):
        captured['cmd'] = cmd
        return 0
    monkeypatch.setattr(start_tool, 'subprocess', type('S', (), {'run': fake_run}))
    monkeypatch.setattr('builtins.print', lambda *a, **k: None)
    start_tool.launch_application()
    assert 'kyo_qa_tool_app.py' in captured['cmd']


def test_main_block_contains_launch_call():
    src = Path(start_tool.__file__).read_text()
    assert 'if __name__ == "__main__"' in src
    assert '\nmain\n' not in src
    start = src.index('if __name__ == "__main__"')
    assert 'launch_application()' in src[start:]
