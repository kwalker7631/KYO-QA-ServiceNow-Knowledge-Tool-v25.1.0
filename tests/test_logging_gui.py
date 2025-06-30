import sys
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import logging
from logging_utils import setup_logger, QtWidgetHandler

class DummyTextEdit:
    def __init__(self):
        self.messages = []
    def append(self, msg):
        self.messages.append(msg)

def test_gui_handler_appends_messages():
    widget = DummyTextEdit()
    logger = setup_logger('gui_test', log_widget=widget)
    logger.setLevel(logging.INFO)
    logger.info('hello world')
    assert any('hello world' in m for m in widget.messages)
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        if isinstance(h, QtWidgetHandler):
            root_logger.removeHandler(h)

def test_no_widget_has_no_qt_handler():
    setup_logger('plain_test')
    assert not any(isinstance(h, QtWidgetHandler) for h in logging.getLogger().handlers)
