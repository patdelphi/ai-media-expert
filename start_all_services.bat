@echo off
setlocal
chcp 65001 >nul
:: Program: delegate startup to the Python supervisor in ONE console window.

echo ========================================
echo    AI Media Expert - Service Starter
echo ========================================
echo.

echo [1/4] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.9+ and add it to PATH.
    pause
    exit /b 1
)
echo OK: Python environment is ready.

echo.
echo [2/4] Checking Node.js environment...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH.
    echo Please install Node.js 16+ and add it to PATH.
    pause
    exit /b 1
)
echo OK: Node.js environment is ready.

echo.
echo [3/4] Checking config file...
if not exist ".env" (
    echo ERROR: ".env" was not found.
    echo Please copy ".env.example" to ".env" and fill in required settings.
    pause
    exit /b 1
)
echo OK: Config file check passed.

echo.
echo [4/4] Starting Python supervisor...
echo.
python "start_auto.py"
set EXIT_CODE=%ERRORLEVEL%

echo.
echo Supervisor exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
