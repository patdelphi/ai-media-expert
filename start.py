#!/usr/bin/env python3
"""AI新媒体专家系统启动脚本

自动检查环境配置，初始化数据库，并启动应用服务。
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入数据库管理器
try:
    from app.core.db_manager import ensure_database_ready
    from app.core.config import settings
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保已安装所有依赖: pip install -r requirements.txt")
    sys.exit(1)


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
    
    def check_environment(self):
        """检查环境配置"""
        print("🔍 检查环境配置...")
        
        # 检查.env文件
        env_file = Path(".env")
        if not env_file.exists():
            print("❌ 未找到.env配置文件")
            print("请复制.env.example为.env并配置相关参数")
            return False
        
        print("✅ 环境配置检查通过")
        return True
    
    def setup_database(self):
        """设置数据库"""
        print("🗄️  检查数据库配置...")
        
        try:
            if ensure_database_ready():
                print("✅ 数据库配置完成")
                return True
            else:
                print("❌ 数据库配置失败")
                return False
        except Exception as e:
            print(f"❌ 数据库配置错误: {e}")
            logger.exception("数据库配置失败")
            return False
    
    def start_backend(self):
        """启动后端服务"""
        print("🚀 启动后端服务...")
        
        try:
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "app.app:app", 
                "--host", settings.host,
                "--port", str(settings.port),
                "--reload"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes['backend'] = process
            print(f"✅ 后端服务已启动 (PID: {process.pid})")
            print(f"   访问地址: http://{settings.host}:{settings.port}")
            
            return True
            
        except Exception as e:
            print(f"❌ 启动后端服务失败: {e}")
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
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes['celery'] = process
            print(f"✅ Celery工作进程已启动 (PID: {process.pid})")
            
            return True
            
        except Exception as e:
            print(f"❌ 启动Celery工作进程失败: {e}")
            return False
    
    def start_gradio(self):
        """启动Gradio界面"""
        print("🎨 启动Gradio界面...")
        
        try:
            gradio_script = project_root / "app" / "ui" / "main_ui.py"
            if not gradio_script.exists():
                print("⚠️  Gradio界面脚本不存在，跳过启动")
                return True
            
            cmd = [sys.executable, str(gradio_script)]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes['gradio'] = process
            print(f"✅ Gradio界面已启动 (PID: {process.pid})")
            print("   访问地址: http://localhost:7860")
            
            return True
            
        except Exception as e:
            print(f"❌ 启动Gradio界面失败: {e}")
            return False
    
    def monitor_processes(self):
        """监控进程状态"""
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    print(f"⚠️  {name} 进程已退出 (退出码: {process.returncode})")
                    if process.returncode != 0:
                        print(f"❌ {name} 进程异常退出")
            
            time.sleep(5)
    
    def stop_all(self):
        """停止所有服务"""
        print("\n🛑 正在停止所有服务...")
        self.running = False
        
        for name, process in self.processes.items():
            try:
                print(f"停止 {name} 服务...")
                process.terminate()
                
                # 等待进程结束
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"强制终止 {name} 服务...")
                    process.kill()
                    process.wait()
                
                print(f"✅ {name} 服务已停止")
                
            except Exception as e:
                print(f"❌ 停止 {name} 服务失败: {e}")
        
        print("🎯 所有服务已停止")
    
    def start_all(self):
        """启动所有服务"""
        print("🎯 AI新媒体专家系统启动中...")
        
        # 1. 检查环境
        if not self.check_environment():
            return False
        
        # 2. 设置数据库
        if not self.setup_database():
            return False
        
        # 3. 启动服务
        services_to_start = []
        
        # 询问用户要启动哪些服务
        print("\n请选择要启动的服务:")
        
        try:
            backend_choice = input("启动后端API服务? (Y/n): ").lower()
        except EOFError:
            backend_choice = 'y'
        
        if backend_choice != 'n':
            services_to_start.append('backend')
        
        try:
            celery_choice = input("启动Celery工作进程? (Y/n): ").lower()
        except EOFError:
            celery_choice = 'y'
        
        if celery_choice != 'n':
            services_to_start.append('celery')
        
        try:
            gradio_choice = input("启动Gradio界面? (y/N): ").lower()
        except EOFError:
            gradio_choice = 'n'
        
        if gradio_choice == 'y':
            services_to_start.append('gradio')
        
        # 启动选定的服务
        success_count = 0
        
        if 'backend' in services_to_start:
            if self.start_backend():
                success_count += 1
            time.sleep(2)  # 等待后端启动
        
        if 'celery' in services_to_start:
            if self.start_celery():
                success_count += 1
            time.sleep(2)
        
        if 'gradio' in services_to_start:
            if self.start_gradio():
                success_count += 1
        
        if success_count == len(services_to_start):
            print(f"\n🎉 成功启动 {success_count} 个服务!")
            print("\n📋 服务状态:")
            for name, process in self.processes.items():
                print(f"  {name}: 运行中 (PID: {process.pid})")
            
            print("\n💡 使用说明:")
            if 'backend' in services_to_start:
                print(f"  - API文档: http://{settings.host}:{settings.port}/docs")
                print(f"  - 管理后台: http://{settings.host}:{settings.port}/admin")
            if 'gradio' in services_to_start:
                print("  - Gradio界面: http://localhost:7860")
            
            print("\n按 Ctrl+C 停止所有服务")
            
            self.running = True
            
            # 启动监控线程
            with ThreadPoolExecutor(max_workers=1) as executor:
                monitor_future = executor.submit(self.monitor_processes)
                
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
            print(f"\n❌ 部分服务启动失败 ({success_count}/{len(services_to_start)})")
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
    signal.signal(signal.SIGTERM, signal_handler)
    
    manager = ServiceManager()
    
    try:
        success = manager.start_all()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        logger.exception("应用启动失败")
        sys.exit(1)


if __name__ == "__main__":
    main()