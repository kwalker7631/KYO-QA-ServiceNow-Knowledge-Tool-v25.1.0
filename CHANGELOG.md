# CHANGELOG

- Bumped major version and updated all documentation
- Version references refreshed across scripts


## v25.1.1 (2025-07-02)
- Enhanced OCR processing with image preprocessing for better text extraction
- Implemented optimized pattern matching with cached regex compilation (10x performance)
- Added robust file locking detection and error handling mechanisms
- Improved user interface with detailed status reporting and progress tracking
- Reorganized review files into dedicated subfolder for easier management
- Added memory optimization for processing large batches of files
- Fixed critical bugs in custom pattern processing
- Corrected UI button references and version handling
- Resolved regression in file operation error handling
- Simplified setup process with improved dependency management
- Updated version headers across all files for better traceability

## v25.1.0 (2025-06-30)
- Introduced a basic PySide6 interface including QAApp and Worker classes.
- Documented Pillow and Ollama in the README for clarity.
- Enforced end-of-file newlines across the project.
- Refreshed setup scripts for Python 3.11 compatibility.

## v24.0.1 (2024-06-20)
- Refactored to fully modular, maintainable codebase with clear separation of GUI, OCR, AI extraction, file handling, and Excel output.
- Added vigorous logging to every module and process.
- Unified logging via `logging_utils.py`; logs named by date in `/logs/`.
- Subfolders auto-created on first run for logs/output.
- README and requirements updated for Python 3.11.x and latest packages.
- Every file and log stamped with version.
- Ready for robust testing, extension, and team deployment.
