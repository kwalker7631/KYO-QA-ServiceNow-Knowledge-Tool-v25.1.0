# run_state.py
# Version: 26.0.0
# Last modified: 2025-07-03
import json
from config import CACHE_DIR

STATE_FILE = CACHE_DIR / 'run_state.json'


def get_run_count() -> int:
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return int(data.get('run_count', 0))
    except Exception:
        return 0


def increment_run_count() -> int:
    count = get_run_count() + 1
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'run_count': count}, f)
    except Exception:
        pass
    return count

