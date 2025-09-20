@echo off
chcp 65001 >nul
:: AI新媒体专家系统 - 停止所有服务脚本
:: 功能：停止所有正在运行的前后端服务

echo ========================================
echo    AI新媒体专家系统 - 服务停止器  
echo ========================================
echo.

:: 设置颜色
color 0C

echo 🛑 正在停止所有服务...
echo.

:: 停止后端API服务 (uvicorn)
echo 停止后端API服务...
taskkill /f /im "python.exe" /fi "WINDOWTITLE eq AI媒体专家-后端API*" >nul 2>&1
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "uvicorn"') do (
    taskkill /f /pid %%i >nul 2>&1
)

:: 停止Celery工作进程
echo 停止Celery工作进程...
taskkill /f /im "python.exe" /fi "WINDOWTITLE eq AI媒体专家-Celery*" >nul 2>&1
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "celery"') do (
    taskkill /f /pid %%i >nul 2>&1
)

:: 停止前端开发服务器 (Node.js/Vite)
echo 停止前端开发服务器...
taskkill /f /im "cmd.exe" /fi "WINDOWTITLE eq AI媒体专家-前端*" >nul 2>&1
taskkill /f /im "node.exe" /fi "COMMANDLINE eq *vite*" >nul 2>&1
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo csv ^| findstr "vite"') do (
    taskkill /f /pid %%i >nul 2>&1
)

:: 停止可能的Redis进程
echo 停止Redis服务...
taskkill /f /im "redis-server.exe" >nul 2>&1

:: 清理端口占用
echo 清理端口占用...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8000"') do (
    taskkill /f /pid %%i >nul 2>&1
)
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":5173"') do (
    taskkill /f /pid %%i >nul 2>&1
)
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":6379"') do (
    taskkill /f /pid %%i >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo           ✅ 所有服务已停止！
echo ========================================
echo.
echo 📋 已停止的服务：
echo   • 后端API服务 (端口 8000)
echo   • Celery工作进程  
echo   • 前端开发服务器 (端口 5173)
echo   • Redis服务 (端口 6379)
echo.
echo 💡 提示：
echo   • 所有相关进程已被终止
echo   • 端口占用已清理
echo   • 可以重新运行 start_all_services.bat 启动服务
echo.

echo 按任意键退出...
pause >nul