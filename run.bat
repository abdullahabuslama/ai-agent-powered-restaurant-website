@echo off
REM ===========================================================================
REM  Restaurant Chatbot - One-Click Launcher (Windows)
REM  Just double-click this file. It sets everything up the first time,
REM  then opens the website in your browser.
REM ===========================================================================
chcp 65001 >nul 2>&1
title Restaurant Chatbot
cd /d "%~dp0"

echo.
echo ============================================================
echo    Starting your Restaurant Assistant website...
echo ============================================================
echo.

REM --- Check Python is installed ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python is not installed on this computer.
    echo.
    echo     Please install Python 3.10 or newer from:
    echo     https://www.python.org/downloads/
    echo     During setup, tick the box "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

REM --- Create the virtual environment on first run ---
if not exist ".venv" (
    echo [*] First-time setup: preparing the environment...
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"

REM --- Install / update dependencies ---
echo [*] Installing required packages... (first run may take a minute)
python -m pip install --upgrade pip >nul
pip install -r requirements.txt

REM --- Launch the app ---
echo.
echo [OK] Opening the website in your browser...
echo      To stop the website later, just close this window.
echo.
streamlit run app.py

pause
