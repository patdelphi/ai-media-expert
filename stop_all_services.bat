@echo off
setlocal
chcp 65001 >nul
:: Program: stop backend API, Celery worker and frontend dev server.

echo ========================================
echo    AI Media Expert - Service Stopper
echo ========================================
echo.

color 0C

echo Stopping all services...
echo.

echo Stopping backend API service...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8000"') do (
    taskkill /f /pid %%i >nul 2>&1
)

echo Stopping Celery worker...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'celery' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

echo Stopping frontend development server...
taskkill /f /im "node.exe" /fi "COMMANDLINE eq *vite*" >nul 2>&1
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":5173"') do (
    taskkill /f /pid %%i >nul 2>&1
)

echo Stopping Redis service...
taskkill /f /im "redis-server.exe" >nul 2>&1
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":6379"') do (
    taskkill /f /pid %%i >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo          All services stopped
echo ========================================
echo.
echo Stopped services:
echo   Backend API service  (port 8000)
echo   Celery worker
echo   Frontend server      (port 5173)
echo   Redis service        (port 6379)
echo.
echo Notes:
echo   Related processes were terminated.
echo   Port usage was cleaned up.
echo   You can run "start_all_services.bat" to start services again.
echo.

echo Press any key to exit...
pause >nul
