# custom_patterns.py
# This file stores user-defined regex patterns.

MODEL_PATTERNS = [
    r"\\bDP\\b",
    r"\\bM\\d+idn\\b",
    r"\\bM\\d+idnf\\b",
    r"\\bDevice Manager\\b",
    r"\\bVi\\d+\\b",
    r"\\bKM-\\d+\\b",
    r"\\bFS-\\d+DN\\b",
    r"\\bP\\d+dn\\b",
    r"\\bM\\d+dn\\b",
    r"\\bM\\d+cdn\\b",
    r"\\bM\\d+cidn\\b",
    r"\\bP\\d+cdn\\b",
    r"\\bFS-C\\d+(?:MFP\+?|DN)\\b",
]

QA_NUMBER_PATTERNS = [
    r"\\bFS-C\\d+(?:MFP\+?|DN)\\b",
]
