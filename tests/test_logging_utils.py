import logging

import logging_utils


def test_setup_logger_to_console_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_utils, "LOG_DIR", tmp_path)
    monkeypatch.setattr(logging_utils, "SESSION_LOG_FILE", tmp_path / "session.log")

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    initial_streams = sum(
        1
        for h in root_logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    )

    logging_utils.setup_logger("no_console")
    after_no_console = sum(
        1
        for h in root_logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    )

    root_logger.handlers.clear()

    logging_utils.setup_logger("with_console", to_console=True)
    after_console = sum(
        1
        for h in root_logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    )

    assert after_no_console == initial_streams
    assert after_console >= after_no_console + 1

