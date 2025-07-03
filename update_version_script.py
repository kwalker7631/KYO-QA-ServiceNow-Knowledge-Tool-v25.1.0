# update_all_to_v25_1_1.py
# One-time script to update all version references from v25.1.0 to v25.1.1

import re
from pathlib import Path
from datetime import datetime

new_version = "25.1.1"

# Files to update with version number changes
FILES_TO_UPDATE = [
    "kyo_qa_tool_app.py",
    "ocr_utils.py", 
    "data_harvesters.py", 
    "file_utils.py", 
    "processing_engine.py", 
    "run.py",
    "start_tool.py",
    "custom_patterns.py",
    "update_version.py",
    "README.md",
    "CHANGELOG.md",
    "START.bat"
]

def update_version_in_file(file_path, old_version="25.1.0", new_version="25.1.1"):
    """Update version strings in a file."""
    path = Path(file_path)
    if not path.exists():
        print(f"⚠️ File not found: {file_path}")
        return False
    
    try:
        content = path.read_text(encoding='utf-8')
        
        # Update raw version number
        updated_content = content.replace(old_version, new_version)
        
        # Update version header in Python files
        if file_path.endswith('.py'):
            version_header_pattern = re.compile(r'# Version: .*?\n')
            if version_header_pattern.search(updated_content):
                updated_content = version_header_pattern.sub(f'# Version: {new_version}\n', updated_content)
                # Update last modified date if it exists
                date_header_pattern = re.compile(r'# Last modified: .*?\n')
                if date_header_pattern.search(updated_content):
                    updated_content = date_header_pattern.sub(f'# Last modified: {datetime.now().strftime("%Y-%m-%d")}\n', updated_content)
        
        # Write updated content back to file
        path.write_text(updated_content, encoding='utf-8')
        print(f"✅ Updated version in {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

# Update version.py first
with open('version.py', 'w', encoding='utf-8') as f:
    f.write(f'''# version.py
VERSION = "{new_version}"

def get_version():
    return VERSION
''')
print("✅ Updated version.py")

# Update all other files
for file in FILES_TO_UPDATE:
    update_version_in_file(file)

print("\n✅ Version update complete! All files now reference v25.1.1")
