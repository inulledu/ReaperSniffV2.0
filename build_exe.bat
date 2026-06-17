@echo off
REM ============================================================
REM   ReaperSniff - one-click Windows .exe builder
REM   Run this on a Windows machine with Python 3.10+ installed.
REM ============================================================
setlocal

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found in PATH. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/4] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo [3/4] Building ReaperSniff.exe (this can take a few minutes)...
pyinstaller --noconfirm reapersniff.spec

echo [4/4] Done!
echo.
echo   Your app is here:  dist\ReaperSniff\ReaperSniff.exe
echo.
echo   For full per-process bandwidth + UDP P2P detection:
echo     - Install Npcap  : https://npcap.com/#download  (check "WinPcap API-compatible")
echo     - Run ReaperSniff as Administrator and tick "Npcap deep mode".
echo.
pause
