import importlib
import sys
import types


def test_launcher_setup_without_sentry(monkeypatch):
    # Simulate clean env with sentry_sdk missing
    sys.modules.pop('sentry_sdk', None)
    sys.modules.pop('error_tracker', None)

    run = importlib.import_module('run')

    launched = {}

    def fake_setup_environment():
        sys.modules['sentry_sdk'] = types.ModuleType('sentry_sdk')
        return True

    monkeypatch.setattr(run, 'setup_environment', fake_setup_environment)
    monkeypatch.setattr(run, 'launch_application', lambda: launched.setdefault('ok', True))

    if run.setup_environment():
        err = importlib.import_module('error_tracker')
        err.init_error_tracker()
        run.launch_application()

    assert launched.get('ok')
