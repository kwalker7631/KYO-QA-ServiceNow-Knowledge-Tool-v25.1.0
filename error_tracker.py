import os
import logging

from sentry_sdk import init
from sentry_sdk.integrations.logging import LoggingIntegration, EventHandler

_initialized = False
_handler: logging.Handler | None = None


def init_error_tracker() -> bool:
    """Initialize Sentry error tracking if a DSN is provided."""
    global _initialized, _handler
    if _initialized:
        return True
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return False
    sentry_logging = LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR)
    init(dsn=dsn, integrations=[sentry_logging])
    _handler = EventHandler(level=logging.ERROR)
    _initialized = True
    return True


def get_handler() -> logging.Handler | None:
    """Return the Sentry logging handler if initialized."""
    return _handler
