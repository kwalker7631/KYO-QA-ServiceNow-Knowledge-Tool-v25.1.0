# data_harvesters.py
import re
import importlib
from config import (
    MODEL_PATTERNS as DEFAULT_MODEL_PATTERNS,
    QA_NUMBER_PATTERNS as DEFAULT_QA_PATTERNS,
    EXCLUSION_PATTERNS,
    UNWANTED_AUTHORS,
    STANDARDIZATION_RULES,
)

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
        for p in patterns:
            for match in re.findall(p, content, re.IGNORECASE):
                #==============================================================
                # --- BUG FIX: Changed to use the correct function name ---
                #==============================================================
                if not is_excluded(match): models.add(clean_model_string(match))
                #==============================================================
                # --- END OF BUG FIX ---
                #==============================================================
    return sorted(list(models))

# --- UPDATED FUNCTION ---
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
# --- END OF UPDATE ---

def harvest_all_data(text: str, filename: str) -> dict:
    """The main harvester function that aggregates all data."""
    models_str = ", ".join(harvest_models(text, filename)) or "Not Found"
    # --- UPDATED FUNCTION CALL ---
    author_str = harvest_author(text)
    return {"models": models_str, "author": author_str}
    # --- END OF UPDATE ---