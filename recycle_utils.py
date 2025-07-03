# recycle_utils.py
# Simple recycling utilities for text preprocessing
import re

# Default recycling rules (pattern, replacement)
DEFAULT_RECYCLING_RULES = [
    # Example rule: normalize multiple spaces
    (r"\s{2,}", " "),
]

# Attempt to import user-defined rules
try:
    from custom_recycles import RECYCLING_RULES as CUSTOM_RECYCLING_RULES
except Exception:
    CUSTOM_RECYCLING_RULES = []

# Combine, giving precedence to custom rules
RECYCLING_RULES = CUSTOM_RECYCLING_RULES + [
    r for r in DEFAULT_RECYCLING_RULES if r not in CUSTOM_RECYCLING_RULES
]


def apply_recycles(text: str, rules=None) -> str:
    """Apply regex-based recycling rules to text."""
    if not text:
        return ""
    if rules is None:
        rules = RECYCLING_RULES
    for pattern, repl in rules:
        try:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        except re.error:
            # Skip invalid patterns but continue processing
            continue
    return text