# KYO QA ServiceNow Custom Exceptions
from version import VERSION

class QAExtractionError(Exception):
    """Raised when QA data extraction fails"""
    pass

class FileProcessingError(Exception):
    """Raised when file processing fails"""
    pass

class ExcelGenerationError(Exception):
    """Raised when Excel generation fails"""
    pass

class OCRError(Exception):
    """Raised when OCR text extraction fails"""
    pass

class ZipExtractionError(Exception):
    """Raised when ZIP extraction fails"""
    pass

class ConfigurationError(Exception):
    """Raised when a configuration error occurs"""
    pass

# --- NEW UTILITY EXCEPTION ---
class FileLockError(Exception):
    """Raised when a file is locked and cannot be written to."""
    pass