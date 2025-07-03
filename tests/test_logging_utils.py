import logging
import importlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
import types


def test_setup_logger_to_console_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "LOGS_DIR", tmp_path)

    import logging_utils
    importlib.reload(logging_utils)

    monkeypatch.setattr(logging_utils, "SESSION_LOG_FILE", tmp_path / "session.log")

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    initial_streams = sum(
        1
        for h in root_logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    )

    logging_utils.setup_logger("test")
    after = sum(
        1
        for h in root_logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    )

    assert after >= initial_streams + 1


def test_setup_logger_initializes_sentry(monkeypatch, tmp_path):
    called = []
    fake_sdk = type(
        "Fake",
        (),
        {
            "Hub": type("Hub", (), {"current": type("cur", (), {"client": None})()}),
            "init": lambda dsn=None: called.append(dsn),
            "capture_exception": lambda exc: called.append("cap")
        },
    )
    monkeypatch.setenv("SENTRY_DSN", "xyz")
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sdk)
    monkeypatch.setitem(sys.modules, "openpyxl", types.ModuleType("openpyxl"))
    monkeypatch.setattr(config, "LOGS_DIR", tmp_path)
    logging.getLogger().handlers.clear()
    import logging_utils
    import importlib
    importlib.reload(logging_utils)
    monkeypatch.setattr(logging_utils, "SESSION_LOG_FILE", tmp_path / "file.log")
    logger = logging_utils.setup_logger("t")
    assert "xyz" in called

