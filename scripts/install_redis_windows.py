#!/usr/bin/env python3
"""
Windows Redis安装脚本

自动下载并安装Redis for Windows。
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path


def download_redis_windows():
    """下载Redis for Windows"""
    redis_url = "https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.zip"
    redis_dir = Path("redis-windows")
    redis_zip = "redis-windows.zip"
    
    print("📥 下载Redis for Windows...")
    
    try:
        # 下载Redis
        urllib.request.urlretrieve(redis_url, redis_zip)
        print("✅ Redis下载完成")
        
        # 解压Redis
        with zipfile.ZipFile(redis_zip, 'r') as zip_ref:
            zip_ref.extractall(redis_dir)
        print("✅ Redis解压完成")
        
        # 清理下载文件
        os.remove(redis_zip)
        
        return redis_dir
        
    except Exception as e:
        print(f"❌ 下载Redis失败: {e}")
        return None


def install_redis_service(redis_dir):
    """安装Redis服务"""
    redis_exe = redis_dir / "redis-server.exe"
    
    if not redis_exe.exists():
        print("❌ 未找到redis-server.exe")
        return False
    
    try:
        # 安装Redis服务
        print("🔧 安装Redis服务...")
        subprocess.run([
            str(redis_exe),
            "--service-install",
            "--service-name", "Redis",
            "--port", "6379"
        ], check=True)
        
        # 启动Redis服务
        print("🚀 启动Redis服务...")
        subprocess.run([
            str(redis_exe),
            "--service-start",
            "--service-name", "Redis"
        ], check=True)
        
        print("✅ Redis服务安装并启动成功")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Redis服务安装失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 Redis Windows安装器")
    print("=" * 50)
    
    if not sys.platform.startswith('win'):
        print("❌ 此脚本仅适用于Windows系统")
        sys.exit(1)
    
    # 检查是否以管理员身份运行
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("⚠️  建议以管理员身份运行此脚本以安装系统服务")
    except:
        pass
    
    # 下载并安装Redis
    redis_dir = download_redis_windows()
    if not redis_dir:
        sys.exit(1)
    
    # 尝试安装服务
    if install_redis_service(redis_dir):
        print("\n🎉 Redis安装完成!")
        print("   服务名称: Redis")
        print("   端口: 6379")
        print("   配置文件: redis.windows.conf")
    else:
        print("\n⚠️  服务安装失败，但可以手动启动Redis:")
        redis_exe = redis_dir / "redis-server.exe"
        print(f"   手动启动: {redis_exe}")
    
    print(f"\n📁 Redis安装目录: {redis_dir.absolute()}")


if __name__ == "__main__":
    main()