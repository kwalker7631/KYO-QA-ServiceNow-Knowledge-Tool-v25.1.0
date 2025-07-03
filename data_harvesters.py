# data_harvesters.py
import logging
import pandas as pd
import re

logger = logging.getLogger(__name__)
KNOWLEDGE_BASE_FIELDS = ['number', 'short_description', 'kb_knowledge_base']

class DataHarvester:
    def harvest_from_excel(self, file_path):
        try:
            # More adaptable: Try to find a relevant sheet name
            xls = pd.ExcelFile(file_path)
            sheet_name_to_use = 'Page 1' # Default
            for name in xls.sheet_names:
                if 'knowledge' in name.lower() or 'kb' in name.lower():
                    sheet_name_to_use = name
                    break
            df = pd.read_excel(xls, sheet_name=sheet_name_to_use)
            # Standardize column names (e.g., 'Number' -> 'number')
            df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Failed to harvest data from Excel file '{file_path}': {e}")
            return []
    
    def harvest_from_text(self, text_content):
        if text_content:
            return [{'number': 'TXT_001', 'short_description': 'Content from PDF', 'article_body': text_content[:500] + '...'}]
        return []

# Model extraction patterns
MODEL_PATTERNS = [
    r'\b(?:model|models|product)\s*(?:name|number|no|#|:)?\s*[:-]?\s*([A-Z0-9]+-[A-Z0-9]+(?:-[A-Z0-9]+)*)',
    r'\b([A-Z]{2,4}-[A-Z0-9]{3,5}(?:-[A-Z0-9]+)*)\b',
    r'\b(TA[SX]-[A-Z0-9]{4,})\b',
    r'\b(FS-[A-Z0-9]{4,})\b',
    r'\b(ECOSYS [A-Z0-9]{4,})\b',
    r'\b(TASKalfa [0-9]{4,}[a-z]*i?)\b',
    # Add any other model patterns here
]

# QA Number patterns
QA_NUMBER_PATTERNS = [
    r'\bQA[-\s]?#?[-\s]?([0-9]{5,6})\b',
    r'\bQA[-\s]?([0-9]{5,6})\b',
    r'\b(QA[0-9]{5,6})\b',
    # Add any other QA number patterns here
]

def bulletproof_extraction(text_content, filename=None):
    """
    Extract models and other metadata from document text using regex patterns.
    This is the function that was missing and caused the import error.
    
    Args:
        text_content: The text extracted from a PDF
        filename: Original filename for reference
        
    Returns:
        dict: Extracted data including models, qa numbers, etc.
    """
    if not text_content or not isinstance(text_content, str):
        return {"models": "Not Found", "author": "", "short_description": filename or "Unknown"}
    
    # Attempt to find all models mentioned in the text
    all_models = []
    for pattern in MODEL_PATTERNS:
        matches = re.finditer(pattern, text_content, re.IGNORECASE)
        for match in matches:
            model = match.group(1).strip()
            if model and model not in all_models and len(model) >= 4:  # Minimum length check
                all_models.append(model)
    
    # Look for QA number references
    qa_number = ""
    full_qa_number = ""
    for pattern in QA_NUMBER_PATTERNS:
        matches = re.finditer(pattern, text_content, re.IGNORECASE)
        for match in matches:
            if match.group(1).isdigit():
                qa_number = match.group(1)
                full_qa_number = match.group(0)
                break
            else:
                full_qa_number = match.group(0)
                qa_number = ''.join(filter(str.isdigit, full_qa_number))
            if qa_number:
                break
        if qa_number:
            break
    
    # Extract potential author name (simple heuristic)
    author = ""
    author_pattern = r'(?:Author|Written by|Prepared by|Created by)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'
    author_match = re.search(author_pattern, text_content)
    if author_match:
        author = author_match.group(1)
    
    # Create a short description from filename or first meaningful line
    short_description = filename or "Unknown File"
    if len(text_content) > 10:
        first_lines = text_content.split('\n')[:5]
        for line in first_lines:
            clean_line = line.strip()
            if clean_line and len(clean_line) > 15 and not clean_line.startswith('Page '):
                short_description = clean_line[:100]
                break
    
    return {
        "models": ", ".join(all_models) if all_models else "Not Found",
        "author": author,
        "short_description": short_description,
        "full_qa_number": full_qa_number,
        "qa_number": qa_number
    }