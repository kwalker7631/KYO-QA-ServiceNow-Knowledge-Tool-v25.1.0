# data_harvesters.py
# Version: 26.0.0 (Repaired)
# Last modified: 2025-07-03
# Extracts specific data points from raw text using regex patterns.

import re
import importlib

# --- Application Modules ---
# Imports settings from the central config file.
from config import (
    MODEL_PATTERNS as DEFAULT_MODEL_PATTERNS,
    QA_NUMBER_PATTERNS as DEFAULT_QA_PATTERNS,
    EXCLUSION_PATTERNS,
    UNWANTED_AUTHORS,
    STANDARDIZATION_RULES,
)
import logging_utils

logger = logging_utils.setup_logger("harvesters")

def get_combined_patterns(pattern_name: str, default_patterns: list) -> list:
    """
    Safely loads patterns from custom_patterns.py and combines them with
    the default patterns from config.py, giving precedence to custom ones.
    """
    custom_patterns = []
    try:
        # Reload the module to get the latest changes without restarting the app
        custom_mod = importlib.import_module("custom_patterns")
        importlib.reload(custom_mod)
        custom_patterns = getattr(custom_mod, pattern_name, [])
    except (ImportError, SyntaxError):
        # This is expected if the user hasn't created a custom_patterns.py file
        pass
    # Combine lists, ensuring custom patterns come first
    return custom_patterns + [p for p in default_patterns if p not in custom_patterns]

def is_excluded(text: str) -> bool:
    """Checks if a string contains any of the unwanted exclusion patterns."""
    return any(p.lower() in text.lower() for p in EXCLUSION_PATTERNS)

def clean_model_string(model_str: str) -> str:
    """Applies standardization rules to a found model string."""
    for rule, replacement in STANDARDIZATION_RULES.items():
        model_str = model_str.replace(rule, replacement)
    return model_str.strip()

def harvest_models(text: str, filename: str) -> list:
    """Finds all unique models from text and filename, respecting exclusions."""
    models = set()
    patterns = get_combined_patterns("MODEL_PATTERNS", DEFAULT_MODEL_PATTERNS)
    
    # Search both the document text and the filename itself for patterns
    for content in [text, filename.replace("_", " ")]:
        for p in patterns:
            try:
                for match in re.findall(p, content, re.IGNORECASE):
                    if not is_excluded(match):
                        models.add(clean_model_string(match))
            except re.error as e:
                logger.warning(f"Invalid regex pattern skipped: '{p}'. Error: {e}")

    return sorted(list(models))

def harvest_author(text: str) -> str:
    """Finds the author and returns an empty string if it's an unwanted name."""
    # Search for a line that looks like "Author: John Doe"
    match = re.search(r"^Author:\s*(.*)", text, re.MULTILINE | re.IGNORECASE)
    if match:
        author = match.group(1).strip()
        # Ensure the found author is not in the unwanted list
        if author not in UNWANTED_AUTHORS:
            return author
    return "" # Return empty string if no author is found or if it's unwanted

def harvest_all_data(text: str, filename: str) -> dict:
    """
    REPAIRED: This is the main harvester function that the processing engine
    calls. It aggregates all the extracted data into a single dictionary.
    """
    models_list = harvest_models(text, filename)
    models_str = ", ".join(models_list) if models_list else "Not Found"
    author_str = harvest_author(text)
    
    logger.info(f"Harvested from '{filename}': {len(models_list)} models, Author: '{author_str or 'N/A'}'")
    
    return {"models": models_str, "author": author_str}
