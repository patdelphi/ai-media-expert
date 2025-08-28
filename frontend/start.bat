@echo off
echo Starting AI Media Expert Frontend...
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
    echo.
)

echo Starting development server...
npm run dev

pause