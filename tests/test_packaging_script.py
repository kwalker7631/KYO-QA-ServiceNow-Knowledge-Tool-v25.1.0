import importlib
import packaging_script
from version import VERSION as APP_VERSION

def test_zip_filename_contains_current_version():
    importlib.reload(packaging_script)
    assert packaging_script.current_version == APP_VERSION
    assert packaging_script.out_zip.name.startswith(f"KYO_QA_Knowledge_Tool_{APP_VERSION}")
