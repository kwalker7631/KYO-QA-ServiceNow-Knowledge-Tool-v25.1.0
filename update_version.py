# KYO QA ServiceNow Version Updater
# Run this script to update the version number across all files

import os
import re
from datetime import datetime
import sys

def update_version(old_version, new_version):
    """Update the version number in all files."""
    print(f"Updating version from {old_version} to {new_version}")
    
    # List of files to update
    files_to_update = [
        "version.py",
        "ai_extractor.py",
        "custom_exceptions.py",
        "data_harvesters.py",
        "excel_generator.py",
        "file_utils.py",
        "kyo_qa_tool_app.py",
        "logging_utils.py",
        "ocr_utils.py",
        "processing_engine.py",
        "README.md",
        "start_tool.py",
        "run_tool.bat"
    ]
    
    # Regular expressions for updating different file types
    version_patterns = {
        ".py": [
            (fr'VERSION = "{old_version}"', fr'VERSION = "{new_version}"'),
            (fr"VERSION = '{old_version}'", fr"VERSION = '{new_version}'"),
            (fr'v{old_version[1:]}', fr'v{new_version[1:]}')  # Without the 'v'
        ],
        ".md": [
            (fr'{old_version}', fr'{new_version}')
        ],
        ".bat": [
            (fr'{old_version}', fr'{new_version}')
        ]
    }
    
    # Count of files updated
    files_updated = 0
    
    # Update each file
    for filename in files_to_update:
        if not os.path.exists(filename):
            print(f"WARNING: {filename} not found, skipping")
            continue
            
        # Determine file extension
        _, ext = os.path.splitext(filename)
        
        # Read file content
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Apply version replacements based on file type
        original_content = content
        patterns = version_patterns.get(ext, [])
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Only write if content changed
        if content != original_content:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Updated {filename}")
            files_updated += 1
        else:
            print(f"No changes needed in {filename}")
    
    # Special handling for CHANGELOG.md
    changelog_file = "CHANGELOG.md"
    if os.path.exists(changelog_file):
        with open(changelog_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        today = datetime.now().strftime("%Y-%m-%d")
        new_changelog_entry = f"## {new_version} ({today})\n- \n\n"
        
        # Add new version at the top of the changelog
        if "# CHANGELOG" in content:
            content = content.replace("# CHANGELOG\n\n", f"# CHANGELOG\n\n{new_changelog_entry}")
        else:
            content = f"# CHANGELOG\n\n{new_changelog_entry}\n" + content
        
        with open(changelog_file, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Updated {changelog_file}")
        files_updated += 1
    
    print(f"\nVersion update complete! {files_updated} files updated.")
    print(f"Don't forget to rename your installation folder to: KYO_QA_ServiceNow_Tool_{new_version}/")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_version.py old_version new_version")
        print("Example: python update_version.py v24.0.1 v24.0.2")
        sys.exit(1)
        
    old_version = sys.argv[1]
    new_version = sys.argv[2]
    
    # Validate version format
    if not re.match(r'^v\d+\.\d+\.\d+$', old_version) or not re.match(r'^v\d+\.\d+\.\d+$', new_version):
        print("Error: Version numbers must be in the format vYY.Minor.Patch")
        print("Example: v24.0.1")
        sys.exit(1)
        
    update_version(old_version, new_version)
