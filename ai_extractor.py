"""Convenience wrapper to expose AI extraction helpers."""

from data_harvesters import harvest_all_data as ai_extract, harvest_author as harvest_metadata

# Create a fallback for bulletproof_extraction
def bulletproof_extraction(text, patterns=None):
    """Fallback implementation for bulletproof extraction."""
    import re
    results = []
    if patterns:
        for pattern in patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                results.extend(matches)
            except re.error:
                pass
    return results

# Try to import from extract.common, fall back to local implementation
try:
    from extract.common import bulletproof_extraction
except ImportError:
    pass  # Use the fallback implementation above

__all__ = ["ai_extract", "bulletproof_extraction", "harvest_metadata"]