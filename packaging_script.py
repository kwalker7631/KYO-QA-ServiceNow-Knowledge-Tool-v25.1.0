# KYO QA Packaging Script
import zipfile
from datetime import datetime
from pathlib import Path
from version import get_version

# Paths
project_root = Path(__file__).parent
output_dir = project_root / "dist"
output_dir.mkdir(exist_ok=True)

# Metadata
current_version = get_version()
ts = datetime.now().strftime("%Y%m%d_%H%M")
out_zip = output_dir / f"KYO_QA_Knowledge_Tool_{current_version}_{ts}.zip"

# Files and folders to include
include = [
    "run.py",
    "cli_runner.py",
    "kyo_qa_tool_app.py",
    "excel_generator.py",
    "processing_engine.py",
    "ai_extractor.py",
    "data_harvesters.py",
    "file_utils.py",
    "logging_utils.py",
    "ocr_utils.py",
    "custom_exceptions.py",
    "config.py",
    "version.py",
    "README.md",
    "requirements.txt",
    "Sample_Set",
    "extract",
    "tests",
]

# Zip it up
def zip_project():
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for entry in include:
            path = project_root / entry
            if path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file():
                        arcname = file.relative_to(project_root)
                        zipf.write(file, arcname)
            elif path.is_file():
                zipf.write(path, path.name)

    print(f"\n✅ Packaged to {out_zip}\n")

if __name__ == '__main__':
    zip_project()
