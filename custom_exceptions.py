# custom_exceptions.py - Custom exception classes for KYO QA Tool

class KYOQAToolError(Exception):
    """Base exception for all KYO QA Tool errors."""
    pass

class FileLockError(KYOQAToolError):
    """Raised when a file is locked by another process."""
    pass

class ExcelGenerationError(KYOQAToolError):
    """Raised when Excel file generation fails."""
    pass

class PDFExtractionError(KYOQAToolError):
    """Raised when PDF text extraction fails."""
    pass

class PatternMatchError(KYOQAToolError):
    """Raised when pattern matching fails."""
    pass

class ConfigurationError(KYOQAToolError):
    """Raised when there's a configuration issue."""
    pass