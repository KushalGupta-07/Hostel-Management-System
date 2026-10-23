@echo off
title Hostel Management System (HMS)
color 0b

echo ========================================================
echo        HOSTEL MANAGEMENT SYSTEM (HMS)
echo   Connected to MySQL: hostal_management (User: root)
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in system PATH.
    echo Please install Python 3.9+ and try again.
    pause
    exit /b
)

echo [*] Initializing database and synchronizing room occupancy...
python db.py
if %errorlevel% neq 0 (
    echo [WARNING] Database init reported an error. Please verify MySQL Server is running.
)

echo.
echo [*] Starting Hostel Management System web server...
echo [*] URL: http://127.0.0.1:5000
echo.

start "" "http://127.0.0.1:5000"

python app.py

pause
