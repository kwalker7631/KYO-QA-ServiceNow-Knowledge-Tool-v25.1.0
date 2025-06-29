# update_version.py
import re
from pathlib import Path

# --- Configuration ---
# Add any new files that contain the version number to this list.
FILES_TO_UPDATE = [
    "start_tool.py",
    "kyo_qa_tool_app.py",
    "README.md",
    # Add other files like CHANGELOG.md if needed
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
    print(f"Updating files to version: {new_version}\n")
    
    # Pattern to find 'v' followed by an old version number, e.g., v24.0.6
    # This is flexible and will match different version numbers.
    version_pattern = re.compile(r'(v)\d+\.\d+\.\d+')

    for filename in FILES_TO_UPDATE:
        file_path = Path(filename)
        if not file_path.exists():
            print(f"⚠️  Skipping: {filename} (not found)")
            continue
        
        content = file_path.read_text(encoding='utf-8')
        
        # Replace old version with new one using the pattern
        new_content, num_replacements = version_pattern.sub(f'v{new_version}', content)

        if num_replacements > 0:
            file_path.write_text(new_content, encoding='utf-8')
            print(f"✅ Updated {filename}")
        else:
            print(f"ℹ️  No version string found to update in {filename}")

if __name__ == "__main__":
    try:
        version = get_current_version()
        print(f"Found current version in version.py: {version}")
        update_files(version)
        print("\nVersioning update complete!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")