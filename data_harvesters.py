# data_harvesters.py
import os
import re
import pandas as pd
import logging

# Local module imports
from config import (
    MODEL_PATTERNS,
    PART_NUMBER_PATTERNS,
    SERIAL_NUMBER_PATTERNS,
    QA_NUMBER_PATTERNS,
    DOCUMENT_TYPE_PATTERNS,
    DOCUMENT_TITLE_PATTERNS,
    REVISION_PATTERNS,
    LANGUAGE_PATTERNS,
    EXCLUSION_PATTERNS,
    UNWANTED_AUTHORS,
    STANDARDIZATION_RULES
)
import logging_utils

# --- FIX: Use the correct function name `setup_logger` ---
# This was the cause of the AttributeError.
logger = logging_utils.setup_logger("harvesters")

def harvest_all_data(text, qa_number):
    """
    Harvests all specified data points from the given text.
    """
    data = {
        'qa_number': qa_number,
        'models': harvest_data(text, MODEL_PATTERNS),
        'part_numbers': harvest_data(text, PART_NUMBER_PATTERNS),
        'serial_numbers': harvest_data(text, SERIAL_NUMBER_PATTERNS),
        'document_type': harvest_data(text, DOCUMENT_TYPE_PATTERNS, max_capture=1),
        'document_title': harvest_data(text, DOCUMENT_TITLE_PATTERNS, max_capture=1),
        'revision': harvest_data(text, REVISION_PATTERNS, max_capture=1),
        'language': harvest_data(text, LANGUAGE_PATTERNS, max_capture=1)
    }
    return data

def harvest_data(text, patterns, max_capture=None):
    """
    Generic function to find data in text based on a list of regex patterns.
    """
    results = []
    for pattern in patterns:
        try:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # If the pattern uses capturing groups, the result might be a tuple
                if isinstance(match, tuple):
                    # Find the first non-empty group
                    actual_match = next((item for item in match if item), None)
                else:
                    actual_match = match

                if actual_match and actual_match.strip():
                    results.append(standardize_data(actual_match.strip()))
        except re.error as e:
            logger.error(f"Regex error with pattern '{pattern}': {e}")
            
    # Remove duplicates and items in the exclusion list
    unique_results = sorted(list(set(results)))
    filtered_results = [res for res in unique_results if not any(re.search(ex, res, re.IGNORECASE) for ex in EXCLUSION_PATTERNS)]

    if max_capture:
        return filtered_results[0] if filtered_results else None
        
    return filtered_results

def standardize_data(value):
    """
    Applies standardization rules to the captured data.
    """
    for rule, replacement in STANDARDIZATION_RULES.items():
        value = re.sub(rule, replacement, value, flags=re.IGNORECASE)
    return value

def harvest_author(text):
    """
    Specifically harvests the author from the text, excluding unwanted names.
    """
    # This is a placeholder for a more sophisticated author harvesting logic
    # For now, it might just return a default or be left empty.
    return "Unknown"
