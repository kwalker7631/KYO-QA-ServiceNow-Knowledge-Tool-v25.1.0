"""Convenience wrapper to expose AI extraction helpers.

This module re-exports select functions so they can be imported from a single
location. ``bulletproof_extraction`` is now included from :mod:`extract.common`
for easy access.
"""

from data_harvesters import ai_extract, harvest_metadata
from extract.common import bulletproof_extraction

__all__ = ["ai_extract", "bulletproof_extraction", "harvest_metadata"]
