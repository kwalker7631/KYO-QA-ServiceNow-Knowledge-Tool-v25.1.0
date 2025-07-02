from pathlib import Path
import run


def test_ensure_pip_installed(monkeypatch):
    called = {}
    def fake_check_call(cmd, stdout=None, stderr=None):
        called['cmd'] = cmd
    monkeypatch.setattr(run.subprocess, 'check_call', fake_check_call)
    assert run.ensure_pip(Path('py'))
    assert called['cmd'][1:] == ['-m', 'pip', '--version']


def test_ensure_pip_bootstrap(monkeypatch):
    def raise_error(*a, **k):
        raise FileNotFoundError
    monkeypatch.setattr(run.subprocess, 'check_call', raise_error)
    called = {}
    def fake_spinner(cmd, msg):
        called['cmd'] = cmd
        return True
    monkeypatch.setattr(run, 'run_command_with_spinner', fake_spinner)
    assert run.ensure_pip(Path('py'))
    assert 'ensurepip' in called['cmd']
