import sys
from pathlib import Path
import re

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import DATE_PATTERNS, APP_SOFTWARE_PATTERNS


def test_date_patterns_match_common_format():
    sample = 'Published: 2025-06-26'
    assert any(re.search(p, sample) for p in DATE_PATTERNS)


def test_app_software_patterns_keyword_and_version():
    text = 'This software bulletin covers app version 1.2.3.'
    assert re.search(APP_SOFTWARE_PATTERNS["keywords"], text, re.IGNORECASE)
    assert re.search(APP_SOFTWARE_PATTERNS["version"], text, re.IGNORECASE)
