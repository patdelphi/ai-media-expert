#!/usr/bin/env python3
"""AI新媒体专家系统启动脚本

提供便捷的启动方式和环境检查。
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python版本检查通过: {sys.version.split()[0]}")


def check_dependencies():
    """检查依赖包"""
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn', 
        'gradio': 'gradio', 
        'sqlalchemy': 'sqlalchemy',
        'celery': 'celery', 
        'redis': 'redis', 
        'yt-dlp': 'yt_dlp', 
        'opencv-python': 'cv2'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} (未安装)")
    
    if missing_packages:
        print(f"\n❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装依赖:")
        print("pip install -e .")
        return False
    
    return True


def check_environment():
    """检查环境配置"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ 未找到.env配置文件")
        print("请复制.env.example为.env并配置相关参数")
        return False
    
    print("✅ 环境配置文件存在")
    return True


def create_directories():
    """创建必要的目录"""
    directories = [
        "uploads", "downloads", "models", "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 目录创建: {directory}")


def check_redis():
    """检查Redis连接"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis连接正常")
        return True
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print("请确保Redis服务已启动")
        return False


def start_celery_worker():
    """启动Celery Worker"""
    print("🚀 启动Celery Worker...")
    
    cmd = [
        sys.executable, "-m", "celery", 
        "-A", "app.tasks.celery_app", 
        "worker", 
        "--loglevel=info",
        "--pool=solo" if os.name == 'nt' else "--pool=prefork"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待一下确保启动
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ Celery Worker启动成功")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Celery Worker启动失败")
            print(f"错误信息: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动Celery Worker失败: {e}")
        return None


def start_application():
    """启动主应用"""
    print("🚀 启动AI新媒体专家系统...")
    
    try:
        # 导入并启动应用
        from app.app import start_server
        start_server()
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    print("🎬 AI新媒体专家系统启动检查")
    print("=" * 50)
    
    # 环境检查
    print("\n📋 检查Python版本...")
    check_python_version()
    
    print("\n📦 检查依赖包...")
    if not check_dependencies():
        sys.exit(1)
    
    print("\n⚙️ 检查环境配置...")
    if not check_environment():
        sys.exit(1)
    
    print("\n📁 创建必要目录...")
    create_directories()
    
    print("\n🔗 检查Redis连接...")
    redis_ok = check_redis()
    
    if not redis_ok:
        print("\n⚠️ Redis未连接，某些功能可能无法正常使用")
        response = input("是否继续启动? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ 环境检查完成，准备启动应用")
    print("=" * 50)
    
    # 启动Celery Worker (如果Redis可用)
    celery_process = None
    if redis_ok:
        celery_process = start_celery_worker()
    
    try:
        # 启动主应用
        start_application()
    finally:
        # 清理Celery进程
        if celery_process:
            print("\n🛑 停止Celery Worker...")
            celery_process.terminate()
            celery_process.wait()


if __name__ == "__main__":
    main()