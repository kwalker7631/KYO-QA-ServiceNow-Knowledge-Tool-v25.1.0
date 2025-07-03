import logging
import importlib
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import config


def test_sentry_handler_added(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "LOGS_DIR", tmp_path)
    monkeypatch.setenv("SENTRY_DSN", "http://example.com/123")

    import logging_utils
    importlib.reload(logging_utils)
    monkeypatch.setattr(logging_utils, "SESSION_LOG_FILE", tmp_path / "session.log")

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    logging_utils.setup_logger("test")

    assert any(h.__class__.__name__ == "EventHandler" for h in root_logger.handlers)


def test_sentry_handler_not_added(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "LOGS_DIR", tmp_path)
    monkeypatch.delenv("SENTRY_DSN", raising=False)

    import logging_utils
    importlib.reload(logging_utils)
    monkeypatch.setattr(logging_utils, "SESSION_LOG_FILE", tmp_path / "session.log")

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    logging_utils.setup_logger("test")

    assert not any(h.__class__.__name__ == "EventHandler" for h in root_logger.handlers)
