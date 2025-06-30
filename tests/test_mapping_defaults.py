import importlib
from pathlib import Path
from config import HEADER_MAPPING

import processing_engine


def test_default_status_and_subject():
    sample = {'models': 'ModelA'}
    result = processing_engine.map_to_servicenow_format(sample, 'doc.pdf')
    assert result[HEADER_MAPPING['processing_status']] == 'Success'
    assert result[HEADER_MAPPING['short_description']] == 'doc.pdf'
