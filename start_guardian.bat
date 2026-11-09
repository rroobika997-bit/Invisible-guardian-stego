@echo off
title The Invisible Guardian
cd /d "%~dp0"

echo ===============================================
echo   The Invisible Guardian - starting up...
echo ===============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    echo Please install Python from https://python.org and try again.
    pause
    exit /b 1
)

echo Installing/checking required packages (this is quick if already installed)...
pip install --quiet -r requirements.txt

echo.
echo Starting the server in a new window (keep it open while you use the app)...
start "Invisible Guardian Server" cmd /k "cd /d "%~dp0" && python run.py"

echo Waiting a few seconds for the server to start...
timeout /t 4 /nobreak >nul

start "" http://127.0.0.1:5000

echo.
echo Done. The app should now be open in your browser.
echo The server window stays open in the background - closing it stops the app.
pause
