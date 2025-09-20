@echo off
chcp 65001 >nul
:: AI新媒体专家系统 - 自动启动所有服务脚本
:: 功能：非交互式启动后端API、Celery工作进程和前端开发服务器

echo ========================================
echo    AI新媒体专家系统 - 服务启动器
echo ========================================
echo.

:: 设置颜色
color 0A

:: 检查Python环境
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请安装Python 3.9+并添加到系统PATH
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

:: 检查Node.js环境
echo.
echo [2/6] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装或未添加到PATH
    echo 请安装Node.js 16+并添加到系统PATH
    pause
    exit /b 1
)
echo ✅ Node.js环境检查通过

:: 检查.env配置文件
echo.
echo [3/6] 检查配置文件...
if not exist ".env" (
    echo ❌ 未找到.env配置文件
    echo 请复制.env.example为.env并配置相关参数
    pause
    exit /b 1
)
echo ✅ 配置文件检查通过

:: 安装后端依赖
echo.
echo [4/6] 检查后端依赖...
pip list | findstr "fastapi" >nul 2>&1
if errorlevel 1 (
    echo 正在安装后端依赖...
    pip install -e .
    if errorlevel 1 (
        echo ❌ 后端依赖安装失败
        pause
        exit /b 1
    )
)
echo ✅ 后端依赖检查通过

:: 安装前端依赖
echo.
echo [5/6] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo 正在安装前端依赖...
    npm install
    if errorlevel 1 (
        echo ❌ 前端依赖安装失败
        cd ..
        pause
        exit /b 1
    )
)
cd ..
echo ✅ 前端依赖检查通过

:: 启动所有服务
echo.
echo [6/6] 启动所有服务...
echo.

:: 创建日志目录
if not exist "logs" mkdir logs

:: 启动后端服务（非交互模式）
echo 🚀 启动后端API服务...
start "AI媒体专家-后端API" /min cmd /c "python -c \"import sys; sys.path.insert(0, '.'); from app.core.db_manager import ensure_database_ready; ensure_database_ready()\" && python -m uvicorn app.app:app --host 0.0.0.0 --port 8000 --reload > logs\backend.log 2>&1"

:: 等待后端启动
timeout /t 5 /nobreak >nul

:: 启动Celery工作进程
echo ⚡ 启动Celery工作进程...
start "AI媒体专家-Celery" /min cmd /c "python -m celery -A app.tasks.celery_app worker --loglevel=info > logs\celery.log 2>&1"

:: 等待Celery启动
timeout /t 3 /nobreak >nul

:: 启动前端开发服务器
echo 🎨 启动前端开发服务器...
start "AI媒体专家-前端" /min cmd /k "cd frontend && npm run dev > ..\logs\frontend.log 2>&1"

:: 等待前端启动
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo           🎉 所有服务启动完成！
echo ========================================
echo.
echo 📋 服务访问地址：
echo   • 后端API:     http://localhost:8000
echo   • API文档:     http://localhost:8000/docs  
echo   • 前端界面:    http://localhost:5173
echo   • 管理后台:    http://localhost:8000/admin
echo.
echo 📁 日志文件位置：
echo   • 后端日志:    logs\backend.log
echo   • Celery日志:  logs\celery.log  
echo   • 前端日志:    logs\frontend.log
echo.
echo 💡 使用说明：
echo   • 所有服务已在后台运行
echo   • 关闭此窗口不会停止服务
echo   • 要停止服务请运行: stop_all_services.bat
echo   • 或手动关闭对应的命令行窗口
echo.

:: 检查服务状态
echo 🔍 检查服务状态...
timeout /t 2 /nobreak >nul

:: 检查后端服务
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  后端服务可能未完全启动，请稍等片刻
) else (
    echo ✅ 后端服务运行正常
)

:: 检查前端服务  
curl -s http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  前端服务可能未完全启动，请稍等片刻
) else (
    echo ✅ 前端服务运行正常
)

echo.
echo 按任意键打开前端界面...
pause >nul

:: 打开前端界面
start http://localhost:5173

echo.
echo 服务启动完成！按任意键退出...
pause >nul