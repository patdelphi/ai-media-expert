#!/usr/bin/env python3
"""AI新媒体专家系统 - 自动启动脚本

功能：非交互式自动启动所有前后端服务
- 后端API服务 (FastAPI + Uvicorn)
- Celery工作进程 (后台任务处理)
- 前端开发服务器 (React + Vite)
"""

import os
import sys
import time
import signal
import subprocess
import threading
import platform
from pathlib import Path
import logging
import json
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
LOGS_DIR = PROJECT_ROOT / "logs"

class AutoServiceManager:
    """自动服务管理器 - 非交互式启动所有服务"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志目录"""
        LOGS_DIR.mkdir(exist_ok=True)
        print(f"📁 日志目录: {LOGS_DIR}")
    
    def check_environment(self):
        """检查运行环境"""
        print("🔍 检查运行环境...")
        
        # 检查Python版本
        if sys.version_info < (3, 9):
            print(f"❌ Python版本过低: {sys.version}")
            print("请安装Python 3.9+")
            return False
        
        # 检查.env文件
        env_file = PROJECT_ROOT / ".env"
        if not env_file.exists():
            print("❌ 未找到.env配置文件")
            print("请复制.env.example为.env并配置相关参数")
            return False
        
        # 检查Node.js
        try:
            result = subprocess.run(["node", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print("❌ Node.js未安装或不可用")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Node.js未安装或不可用")
            return False
        
        print("✅ 环境检查通过")
        return True
    
    def install_dependencies(self):
        """安装依赖"""
        print("📦 检查并安装依赖...")
        
        # 安装后端依赖
        try:
            print("  检查后端依赖...")
            result = subprocess.run([sys.executable, "-c", "import fastapi"], 
                                  capture_output=True, timeout=10)
            if result.returncode != 0:
                print("  安装后端依赖...")
                subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                             check=True, cwd=PROJECT_ROOT)
        except subprocess.CalledProcessError:
            print("❌ 后端依赖安装失败")
            return False
        
        # 安装前端依赖
        try:
            print("  检查前端依赖...")
            if not (FRONTEND_DIR / "node_modules").exists():
                print("  安装前端依赖...")
                subprocess.run(["npm", "install"], 
                             check=True, cwd=FRONTEND_DIR)
        except subprocess.CalledProcessError:
            print("❌ 前端依赖安装失败")
            return False
        
        print("✅ 依赖检查完成")
        return True
    
    def init_database(self):
        """初始化数据库"""
        print("🗄️  初始化数据库...")
        
        try:
            # 导入并运行数据库初始化
            sys.path.insert(0, str(PROJECT_ROOT))
            from app.core.db_manager import ensure_database_ready
            
            if ensure_database_ready():
                print("✅ 数据库初始化完成")
                return True
            else:
                print("❌ 数据库初始化失败")
                return False
                
        except Exception as e:
            print(f"❌ 数据库初始化错误: {e}")
            logger.exception("数据库初始化失败")
            return False
    
    def start_backend(self):
        """启动后端API服务"""
        print("🚀 启动后端API服务...")
        
        try:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.app:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ]
            
            log_file = LOGS_DIR / "backend.log"
            with open(log_file, "w", encoding="utf-8") as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=PROJECT_ROOT
                )
            
            self.processes['backend'] = process
            print(f"✅ 后端API服务已启动 (PID: {process.pid})")
            print(f"   访问地址: http://localhost:8000")
            print(f"   日志文件: {log_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 启动后端API服务失败: {e}")
            return False
    
    def start_celery(self):
        """启动Celery工作进程"""
        print("⚡ 启动Celery工作进程...")
        
        try:
            cmd = [
                sys.executable, "-m", "celery",
                "-A", "app.tasks.celery_app",
                "worker",
                "--loglevel=info"
            ]
            
            log_file = LOGS_DIR / "celery.log"
            with open(log_file, "w", encoding="utf-8") as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=PROJECT_ROOT
                )
            
            self.processes['celery'] = process
            print(f"✅ Celery工作进程已启动 (PID: {process.pid})")
            print(f"   日志文件: {log_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 启动Celery工作进程失败: {e}")
            return False
    
    def start_frontend(self):
        """启动前端开发服务器"""
        print("🎨 启动前端开发服务器...")
        
        try:
            # Windows 环境下需要使用 shell=True 或指定完整路径
            if platform.system() == "Windows":
                cmd = ["npm.cmd", "run", "dev"]
            else:
                cmd = ["npm", "run", "dev"]
            
            log_file = LOGS_DIR / "frontend.log"
            with open(log_file, "w", encoding="utf-8") as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=FRONTEND_DIR,
                    shell=True if platform.system() == "Windows" else False
                )
            
            self.processes['frontend'] = process
            print(f"✅ 前端开发服务器已启动 (PID: {process.pid})")
            print(f"   访问地址: http://localhost:3000")
            print(f"   日志文件: {log_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 启动前端开发服务器失败: {e}")
            return False
    
    def check_services_health(self):
        """检查服务健康状态"""
        print("🔍 检查服务状态...")
        
        # 等待服务启动
        time.sleep(5)
        
        # 检查后端服务
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ 后端API服务运行正常")
            else:
                print("⚠️  后端API服务响应异常")
        except requests.RequestException:
            print("⚠️  后端API服务可能未完全启动")
        
        # 检查前端服务
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("✅ 前端开发服务器运行正常")
            else:
                print("⚠️  前端开发服务器响应异常")
        except requests.RequestException:
            print("⚠️  前端开发服务器可能未完全启动")
    
    def monitor_processes(self):
        """监控进程状态"""
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    print(f"⚠️  {name} 进程已退出 (退出码: {process.returncode})")
                    if process.returncode != 0:
                        print(f"❌ {name} 进程异常退出，请检查日志")
            
            time.sleep(10)
    
    def stop_all(self):
        """停止所有服务"""
        print("\n🛑 正在停止所有服务...")
        self.running = False
        
        for name, process in self.processes.items():
            try:
                print(f"  停止 {name} 服务...")
                process.terminate()
                
                # 等待进程结束
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"  强制终止 {name} 服务...")
                    process.kill()
                    process.wait()
                
                print(f"  ✅ {name} 服务已停止")
                
            except Exception as e:
                print(f"  ❌ 停止 {name} 服务失败: {e}")
        
        print("🎯 所有服务已停止")
    
    def start_all(self):
        """自动启动所有服务"""
        print("=" * 50)
        print("    AI新媒体专家系统 - 自动启动器")
        print("=" * 50)
        print()
        
        # 1. 检查环境
        if not self.check_environment():
            return False
        
        # 2. 安装依赖
        if not self.install_dependencies():
            return False
        
        # 3. 初始化数据库
        if not self.init_database():
            return False
        
        # 4. 启动所有服务
        print("\n🚀 启动所有服务...")
        
        services = [
            ('backend', self.start_backend),
            ('celery', self.start_celery),
            ('frontend', self.start_frontend)
        ]
        
        success_count = 0
        for name, start_func in services:
            if start_func():
                success_count += 1
                time.sleep(2)  # 等待服务启动
            else:
                print(f"❌ {name} 服务启动失败")
        
        if success_count == len(services):
            print(f"\n🎉 成功启动 {success_count} 个服务!")
            
            # 检查服务健康状态
            self.check_services_health()
            
            print("\n" + "=" * 50)
            print("           🎉 所有服务启动完成！")
            print("=" * 50)
            print()
            print("📋 服务访问地址：")
            print("  • 后端API:     http://localhost:8000")
            print("  • API文档:     http://localhost:8000/docs")
            print("  • 前端界面:    http://localhost:3000")
            print("  • 管理后台:    http://localhost:8000/admin")
            print()
            print("📁 日志文件位置：")
            print(f"  • 后端日志:    {LOGS_DIR}/backend.log")
            print(f"  • Celery日志:  {LOGS_DIR}/celery.log")
            print(f"  • 前端日志:    {LOGS_DIR}/frontend.log")
            print()
            print("💡 使用说明：")
            print("  • 所有服务已在后台运行")
            print("  • 按 Ctrl+C 停止所有服务")
            print("  • 或运行 stop_all_services.bat 停止服务")
            print()
            
            self.running = True
            
            # 启动监控线程
            monitor_thread = threading.Thread(target=self.monitor_processes)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            try:
                # 等待用户中断
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                self.stop_all()
            
            return True
        else:
            print(f"\n❌ 部分服务启动失败 ({success_count}/{len(services)})")
            self.stop_all()
            return False


def signal_handler(signum, frame):
    """信号处理器"""
    print("\n\n收到停止信号，正在关闭服务...")
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    manager = AutoServiceManager()
    
    try:
        success = manager.start_all()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        logger.exception("应用启动失败")
        sys.exit(1)


if __name__ == "__main__":
    main()