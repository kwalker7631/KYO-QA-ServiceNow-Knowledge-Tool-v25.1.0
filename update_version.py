# update_version.py
import re
from pathlib import Path
from datetime import datetime
import sys

# --- Configuration ---
# Add any new files that contain the version number to this list.
FILES_TO_UPDATE = [
    "start_tool.py",
    "README.md",
    "CHANGELOG.md",
    # kyo_qa_tool_app.py now imports directly from version.py, so it doesn't need to be here.
]

def get_current_version():
    """Reads the version from the single source of truth: version.py"""
    version_file = Path("version.py").read_text()
    match = re.search(r"VERSION\s*=\s*['\"]([^'\"]+)['\"]", version_file)
    if not match:
        raise RuntimeError("Could not find version in version.py")
    return match.group(1)

def update_files(new_version):
    """Updates the version number in the specified list of files."""
    print(f"Updating files to version: v{new_version}\n")
    
    # This pattern is now more flexible. It finds a 'v' followed by digits, dots, etc.
    # This will match old versions like 'v25.0.1' and update them correctly.
    version_pattern = re.compile(r'(v)\d+\.\d+\.\d+')

    for filename in FILES_TO_UPDATE:
        file_path = Path(filename)
        if not file_path.exists():
            print(f"⚠️  Skipping: {filename} (not found)")
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Create the new version string with a 'v' prefix for display
            new_version_string = f'v{new_version}'
            
            new_content, num_replacements = version_pattern.sub(new_version_string, content)

            if num_replacements > 0:
                file_path.write_text(new_content, encoding='utf-8')
                print(f"✅ Updated {filename}")
            else:
                print(f"ℹ️  No version string found to update in {filename}")
        except Exception as e:
            print(f"❌ Error updating {filename}: {e}")

if __name__ == "__main__":
    try:
        current_version = get_current_version()
        print(f"Current version set in version.py: {current_version}")
        update_files(current_version)
        print("\nVersioning update complete!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
