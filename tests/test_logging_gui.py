import sys
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import logging
try:
    from logging_utils import setup_logger, QtWidgetHandler
except ImportError:
    from logging_utils import setup_logger

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
