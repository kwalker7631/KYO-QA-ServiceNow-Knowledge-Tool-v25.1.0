import logging
import importlib
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import config


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

