#!/bin/bash
# Simple setup script for KYO QA ServiceNow Knowledge Tool
# Creates a Python virtual environment and installs dependencies
set -e
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"
python3 -m venv venv
"$repo_root/venv/bin/pip" install -r requirements.txt
