@echo off
REM One-click setup for Windows: creates a virtual env, installs packages, starts the assistant.
cd /d "%~dp0\.."
python --version >nul 2>&1 || (echo Python 3.10+ is required: https://python.org & pause & exit /b 1)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || (echo Install failed & pause & exit /b 1)
python main.py
