@echo off
chcp 65001 >nul
echo 🎬 启动ngrok隧道服务
echo ================================

REM 检查Python是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 运行ngrok启动脚本
python scripts\start_ngrok.py

echo.
echo 按任意键退出...
pause >nul