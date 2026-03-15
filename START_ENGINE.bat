@echo off
TITLE StreamGlide Media Downloader - Starter
COLOR 0B

:: Close any old running versions first
taskkill /F /IM python.exe /T >nul 2>&1

echo ======================================================
echo    STREAGLIDE AI - NEXT GEN MEDIA DOWNLOADER
echo ======================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python using the provided installer before running.
    echo Running Python Installer now...
    if exist "python-3.13.12-amd64.exe" (
        start /wait python-3.13.12-amd64.exe
        echo.
        echo [INFO] Please check "Add Python to PATH" during installation!
        echo [INFO] Restart this script after Python is installed.
    ) else (
        echo Please download and install Python from python.org.
    )
    pause
    exit /b
)

echo [1/3] Checking requirements...
:: Check if virtual environment exists; if not, create it
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

:: Activate the virtual environment
call .venv\Scripts\activate

:: Install/Upgrade dependencies
pip install -r requirements.txt --quiet --disable-pip-version-check

echo [2/3] Starting Local Backend Engine...
echo [3/3] Opening browser...
echo.
echo ======================================================
echo    KEEP THIS WINDOW OPEN WHILE USING THE DOWNLOADER
echo ======================================================
echo.

:: Run the app
python app.py

pause
