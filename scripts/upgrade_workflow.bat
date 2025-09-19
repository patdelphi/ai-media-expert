@echo off
REM Douyin_TikTok_Download_API 升级工作流脚本
REM 用于简化日常升级维护操作

setlocal enabledelayedexpansion

echo ========================================
echo Douyin_TikTok_Download_API 升级工具
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    pause
    exit /b 1
)

REM 激活虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call .venv\Scripts\activate.bat
)

:menu
echo 请选择操作:
echo 1. 检查上游更新
echo 2. 同步上游项目
echo 3. 预览整合变更
echo 4. 执行代码整合
echo 5. 运行兼容性测试
echo 6. 创建回滚点
echo 7. 查看版本历史
echo 8. 回滚到指定版本
echo 9. 完整升级流程
echo 0. 退出
echo.

set /p choice="请输入选择 (0-9): "

if "%choice%"=="1" goto check_updates
if "%choice%"=="2" goto sync_upstream
if "%choice%"=="3" goto preview_integration
if "%choice%"=="4" goto execute_integration
if "%choice%"=="5" goto run_tests
if "%choice%"=="6" goto create_rollback
if "%choice%"=="7" goto list_versions
if "%choice%"=="8" goto rollback_version
if "%choice%"=="9" goto full_upgrade
if "%choice%"=="0" goto exit
goto menu

:check_updates
echo.
echo 检查上游更新...
python scripts\sync_upstream.py --check
if errorlevel 1 (
    echo 检查更新失败
    pause
    goto menu
)
echo.
pause
goto menu

:sync_upstream
echo.
echo 同步上游项目...
python scripts\sync_upstream.py
if errorlevel 1 (
    echo 同步失败
    pause
    goto menu
)
echo 记录版本信息...
python scripts\version_manager.py --record
echo.
pause
goto menu

:preview_integration
echo.
echo 预览整合变更...
python scripts\integration_manager.py --dry-run
echo.
pause
goto menu

:execute_integration
echo.
echo 执行代码整合...
python scripts\integration_manager.py --integrate
if errorlevel 1 (
    echo 整合失败
    pause
    goto menu
)
echo.
pause
goto menu

:run_tests
echo.
echo 运行兼容性测试...
python scripts\version_manager.py --test
if errorlevel 1 (
    echo 测试失败，建议检查代码或回滚
    pause
    goto menu
)
echo 测试通过!
echo.
pause
goto menu

:create_rollback
echo.
set /p description="请输入回滚点描述: "
python scripts\version_manager.py --create-rollback-point "%description%"
echo.
pause
goto menu

:list_versions
echo.
echo 版本历史:
python scripts\version_manager.py --list
echo.
pause
goto menu

:rollback_version
echo.
echo 可用的回滚点:
python scripts\version_manager.py --list
echo.
set /p version_id="请输入要回滚的版本ID: "
if "%version_id%"=="" goto menu

echo 确认回滚到版本 %version_id%? (y/N)
set /p confirm=""
if /i not "%confirm%"=="y" goto menu

python scripts\version_manager.py --rollback %version_id%
if errorlevel 1 (
    echo 回滚失败
    pause
    goto menu
)
echo 回滚成功!
echo.
pause
goto menu

:full_upgrade
echo.
echo ========================================
echo 执行完整升级流程
echo ========================================
echo.

REM 1. 检查更新
echo 步骤 1/7: 检查上游更新...
python scripts\sync_upstream.py --check
if errorlevel 1 (
    echo 检查更新失败，终止升级流程
    pause
    goto menu
)

REM 2. 创建当前状态的回滚点
echo.
echo 步骤 2/7: 创建回滚点...
for /f "tokens=2 delims==" %%i in ('wmic OS Get localdatetime /value') do set datetime=%%i
set rollback_desc=升级前备份_%datetime:~0,8%_%datetime:~8,6%
python scripts\version_manager.py --create-rollback-point "%rollback_desc%"

REM 3. 同步上游
echo.
echo 步骤 3/7: 同步上游项目...
python scripts\sync_upstream.py --auto
if errorlevel 1 (
    echo 同步失败，终止升级流程
    pause
    goto menu
)

REM 4. 记录版本
echo.
echo 步骤 4/7: 记录版本信息...
python scripts\version_manager.py --record

REM 5. 预览整合
echo.
echo 步骤 5/7: 预览整合变更...
python scripts\integration_manager.py --dry-run

echo.
echo 确认继续整合? (y/N)
set /p confirm=""
if /i not "%confirm%"=="y" (
    echo 取消升级流程
    goto menu
)

REM 6. 执行整合
echo.
echo 步骤 6/7: 执行代码整合...
python scripts\integration_manager.py --integrate
if errorlevel 1 (
    echo 整合失败，建议回滚
    pause
    goto menu
)

REM 7. 运行测试
echo.
echo 步骤 7/7: 运行兼容性测试...
python scripts\version_manager.py --test
if errorlevel 1 (
    echo 测试失败，建议回滚到之前的版本
    pause
    goto menu
)

echo.
echo ========================================
echo 升级流程完成!
echo ========================================
echo.
echo 建议操作:
echo 1. 运行应用程序进行功能验证
echo 2. 如果发现问题，可以回滚到 "%rollback_desc%"
echo 3. 确认无问题后，提交代码变更
echo.
pause
goto menu

:exit
echo.
echo 感谢使用升级工具!
pause
exit /b 0