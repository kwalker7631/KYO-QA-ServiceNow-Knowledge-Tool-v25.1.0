# data_harvesters.py
# Version: 25.1.0
# Last modified: 2025-07-02
# Functions for extracting model numbers, QA numbers, and metadata from text

import re
import importlib
import functools
from pathlib import Path
from config import (
    MODEL_PATTERNS as DEFAULT_MODEL_PATTERNS,
    QA_NUMBER_PATTERNS as DEFAULT_QA_PATTERNS,
    EXCLUSION_PATTERNS,
    UNWANTED_AUTHORS,
    STANDARDIZATION_RULES,
)

@functools.lru_cache(maxsize=100)
def get_compiled_pattern(pattern_str):
    """Compile and cache regex patterns for better performance."""
    return re.compile(pattern_str, re.IGNORECASE)

def get_combined_patterns(pattern_name: str, default_patterns: list) -> list:
    """Safely loads and combines default and custom patterns."""
    custom_patterns = []
    try:
        custom_mod = importlib.import_module("custom_patterns")
        importlib.reload(custom_mod)
        custom_patterns = getattr(custom_mod, pattern_name, [])
    except (ImportError, SyntaxError):
        pass
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
    
    for content in [text, filename.replace("_", " ")]:
        for pattern_str in patterns:
            pattern = get_compiled_pattern(pattern_str)
            for match in pattern.findall(content):
                if not is_excluded(match):
                    models.add(clean_model_string(match))
    return sorted(list(models))

def harvest_author(text: str) -> str:
    """
    Finds the author and returns an empty string if it's an unwanted name.
    
    Args:
        text: The text to search for author information
        
    Returns:
        str: Author name or empty string if not found or unwanted
    """
    # Search for a line that looks like "Author: John Doe"
    match = re.search(r"^Author:\s*(.*)", text, re.MULTILINE | re.IGNORECASE)
    if match:
        author = match.group(1).strip()
        # Ensure the found author is not in the unwanted list
        if author not in UNWANTED_AUTHORS:
            return author
    return "" # Return empty string if no author is found or if it's unwanted

def harvest_qa_number(text: str) -> str:
    """
    Extracts QA numbers from text using combined patterns.
    
    Args:
        text: The text to search for QA numbers
        
    Returns:
        str: Found QA number or empty string
    """
    patterns = get_combined_patterns("QA_NUMBER_PATTERNS", DEFAULT_QA_PATTERNS)
    for pattern_str in patterns:
        pattern = get_compiled_pattern(pattern_str)
        match = pattern.search(text)
        if match:
            return match.group(0).strip()
    return ""

def harvest_all_data(text: str, filename: str) -> dict:
    """
    The main harvester function that aggregates all data.
    
    Args:
        text: The text to extract data from
        filename: The filename to extract additional info from
        
    Returns:
        dict: Dictionary with all extracted data
    """
    models_list = harvest_models(text, filename)
    models_str = ", ".join(models_list) if models_list else "Not Found"
    qa_number = harvest_qa_number(text)
    author_str = harvest_author(text)
    
    return {
        "models": models_str, 
        "author": author_str,
        "qa_number": qa_number
    }

# Backward-compatibility functions
def harvest_models_from_text(text: str) -> set:
    """Legacy function to maintain backward compatibility."""
    return set(harvest_models(text, ""))

def harvest_models_from_filename(filename: str) -> set:
    """Legacy function to maintain backward compatibility."""
    return set(harvest_models("", filename))

def bulletproof_extraction(text: str, filename: str) -> dict:
    """Backward-compatible wrapper for comprehensive extraction."""
    return harvest_all_data(text, Path(filename).name if hasattr(filename, "name") else filename)
