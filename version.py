# version.py
# This is the single source of truth for the application's version number.
"""Central application version."""

# Canonical version for the tool
VERSION = "v25.0.1"


def get_version() -> str:
    """Return the current application version."""
    return VERSION
