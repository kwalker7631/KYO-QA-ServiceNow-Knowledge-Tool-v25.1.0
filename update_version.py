# update_version.py
# Version: 26.0.0
# Last modified: 2025-07-03
# Utility to update version numbers across all relevant files

import re
from pathlib import Path
from datetime import datetime
import sys

# --- Configuration ---
# Add any new files that contain the version number to this list.
FILES_TO_UPDATE = [
    "start_tool.py",
    "error_tracker.py",
    "README.md",
    "CHANGELOG.md",
    "run.py",
    # kyo_qa_tool_app.py now imports directly from version.py, so it doesn't need to be here.
]

def get_current_version():
    """Reads the version from the single source of truth: version.py"""
    version_file = Path("version.py").read_text(encoding='utf-8')
    match = re.search(r"VERSION\s*=\s*['\"]([^'\"]+)['\"]", version_file)
    if not match:
        raise RuntimeError("Could not find version in version.py")
    return match.group(1)

def update_files(new_version):
    """Updates the version number in the specified list of files."""
    print(f"Updating files to version: v{new_version}\n")
    
    # Pattern to find 'v' followed by an old version number, e.g., v24.0.6
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
            
            # Count occurrences before replacement to know how many were replaced
            original_count = len(version_pattern.findall(content))
            new_content = version_pattern.sub(new_version_string, content)
            # Count occurrences after replacement
            new_count = len(version_pattern.findall(new_content))
            # Calculate number of replacements
            num_replacements = original_count - new_count + len(version_pattern.findall(new_content))

            if num_replacements > 0:
                file_path.write_text(new_content, encoding='utf-8')
                print(f"✅ Updated {filename}: {num_replacements} replacements")
            else:
                print(f"ℹ️  No version string found to update in {filename}")
        except Exception as e:
            print(f"❌ Error updating {filename}: {e}")

def update_version_in_all_py_files(new_version):
    """Updates version headers in all Python files."""
    for py_file in Path('.').glob('*.py'):
        if py_file.name == 'version.py':
            continue  # Skip the main version file
            
        try:
            content = py_file.read_text(encoding='utf-8')
            # Check if file already has a version header
            version_header_pattern = re.compile(r'# Version: .*?\n')
            if version_header_pattern.search(content):
                # Update existing version header
                updated_content = version_header_pattern.sub(f'# Version: {new_version}\n', content)
                # Update last modified date if it exists
                date_header_pattern = re.compile(r'# Last modified: .*?\n')
                if date_header_pattern.search(updated_content):
                    updated_content = date_header_pattern.sub(f'# Last modified: {datetime.now().strftime("%Y-%m-%d")}\n', updated_content)
            else:
                # Add version header at the top of the file, after any shebang or encoding lines
                if content.startswith('#!') or content.startswith('# -*- coding'):
                    lines = content.splitlines()
                    first_non_special = next((i for i, line in enumerate(lines) if not (line.startswith('#!') or line.startswith('# -*- coding'))), 1)
                    lines.insert(first_non_special, f'# Version: {new_version}')
                    lines.insert(first_non_special+1, f'# Last modified: {datetime.now().strftime("%Y-%m-%d")}')
                    updated_content = '\n'.join(lines)
                else:
                    header = f'# Version: {new_version}\n# Last modified: {datetime.now().strftime("%Y-%m-%d")}\n'
                    updated_content = header + content
                    
            py_file.write_text(updated_content, encoding='utf-8')
            print(f"✅ Added/updated version header in {py_file.name}")
        except Exception as e:
            print(f"❌ Error updating version in {py_file.name}: {e}")

if __name__ == "__main__":
    try:
        if len(sys.argv) == 3:
            # If two arguments provided, update from old_version to new_version
            old_version = sys.argv[1]
            new_version = sys.argv[2]
            
            # Update version.py file
            version_file = Path("version.py")
            version_content = version_file.read_text(encoding='utf-8')
            updated_content = re.sub(r'VERSION\s*=\s*["\'].*?["\']', f'VERSION = "{new_version}"', version_content)
            version_file.write_text(updated_content, encoding='utf-8')
            print(f"Updated version.py from {old_version} to {new_version}")
            
            # Update all files that reference the version
            update_files(new_version)
            update_version_in_all_py_files(new_version)
        else:
            # Just use current version to update all files for consistency
            current_version = get_current_version()
            print(f"Current version set in version.py: {current_version}")
            update_files(current_version)
            update_version_in_all_py_files(current_version)
            
        print("\nVersioning update complete!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
