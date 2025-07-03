import sys
import types

# Provide lightweight stubs for heavy optional dependencies
openpyxl_stub = types.ModuleType("openpyxl")
openpyxl_stub.load_workbook = lambda *a, **k: None
openpyxl_stub.styles = types.ModuleType("openpyxl.styles")
openpyxl_stub.styles.PatternFill = lambda **kw: None
openpyxl_stub.styles.Alignment = object
openpyxl_stub.utils = types.ModuleType("openpyxl.utils")
openpyxl_stub.utils.get_column_letter = lambda x: "A"
openpyxl_stub.utils.exceptions = types.ModuleType("openpyxl.utils.exceptions")
openpyxl_stub.utils.exceptions.InvalidFileException = Exception
sys.modules.setdefault("openpyxl", openpyxl_stub)
sys.modules.setdefault("openpyxl.styles", openpyxl_stub.styles)
sys.modules.setdefault("openpyxl.utils", openpyxl_stub.utils)
sys.modules.setdefault("openpyxl.utils.exceptions", openpyxl_stub.utils.exceptions)

# Pillow stub
pil_stub = types.ModuleType("PIL")
image_stub = types.SimpleNamespace(open=lambda *a, **k: None)
pil_stub.Image = image_stub
sys.modules.setdefault("PIL", pil_stub)
sys.modules.setdefault("PIL.Image", pil_stub.Image)

# Other heavy libraries commonly imported
sys.modules.setdefault("fitz", types.ModuleType("fitz"))
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
pt_stub = types.ModuleType("pytesseract")
pt_stub.image_to_string = lambda *a, **k: ""
sys.modules.setdefault("pytesseract", pt_stub)

# Provide minimal logging_utils stubs if module missing
if "logging_utils" not in sys.modules:
    logging_utils_stub = types.ModuleType("logging_utils")
    import logging
    logging_utils_stub.setup_logger = lambda name=None, level=logging.INFO, **k: logging.getLogger(name)
    logging_utils_stub.log_info = lambda *a, **k: None
    logging_utils_stub.log_error = lambda *a, **k: None
    logging_utils_stub.log_warning = lambda *a, **k: None
    sys.modules["logging_utils"] = logging_utils_stub

# Stub sentry_sdk to avoid import errors during tests
import logging

sentry_stub = types.ModuleType("sentry_sdk")
sentry_stub.init = lambda *a, **k: None
logging_mod = types.ModuleType("sentry_sdk.integrations.logging")
class _EventHandler(logging.Handler):
    def __init__(self, *a, **k):
        super().__init__()

logging_mod.EventHandler = _EventHandler
logging_mod.LoggingIntegration = lambda *a, **k: None
sys.modules.setdefault("sentry_sdk", sentry_stub)
sys.modules.setdefault("sentry_sdk.integrations", types.ModuleType("sentry_sdk.integrations"))
sys.modules.setdefault("sentry_sdk.integrations.logging", logging_mod)
