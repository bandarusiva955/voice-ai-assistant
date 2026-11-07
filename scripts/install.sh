#!/bin/bash
# One-click setup for macOS / Linux
set -e
cd "$(dirname "$0")/.."
command -v python3 >/dev/null || { echo "Python 3.10+ is required"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
