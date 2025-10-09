#!/usr/bin/env python3
"""
Redis服务启动脚本

用于在开发环境中启动Redis服务，支持多种启动方式。
"""

import os
import sys
import subprocess
import time
import socket
from pathlib import Path


def check_redis_running(host='localhost', port=6379):
    """检查Redis是否正在运行"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def start_redis_windows():
    """在Windows上启动Redis"""
    print("🔍 检查Redis是否已运行...")
    if check_redis_running():
        print("✅ Redis已在运行")
        return True
    
    print("🚀 尝试启动Redis...")
    
    # 方法1: 尝试使用WSL启动Redis
    try:
        print("📝 尝试使用WSL启动Redis...")
        subprocess.run(['wsl', 'redis-server', '--daemonize', 'yes'], 
                      check=True, capture_output=True)
        time.sleep(2)
        if check_redis_running():
            print("✅ Redis通过WSL启动成功")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  WSL方式启动失败")
    
    # 方法2: 尝试使用Docker Desktop启动Redis
    try:
        print("📝 尝试使用Docker启动Redis...")
        # 先检查是否有现有的redis容器
        try:
            subprocess.run(['docker', 'stop', 'redis'], 
                          capture_output=True, timeout=10)
            subprocess.run(['docker', 'rm', 'redis'], 
                          capture_output=True, timeout=10)
        except:
            pass
        
        # 启动新的Redis容器
        subprocess.run([
            'docker', 'run', '-d', 
            '--name', 'redis',
            '-p', '6379:6379',
            'redis:6-alpine'
        ], check=True, capture_output=True, timeout=30)
        
        time.sleep(3)
        if check_redis_running():
            print("✅ Redis通过Docker启动成功")
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Docker方式启动失败")
    
    # 方法3: 提示用户手动安装Redis
    print("❌ 无法自动启动Redis")
    print("\n💡 请手动启动Redis服务:")
    print("   方式1: 安装Redis for Windows")
    print("   方式2: 使用Docker Desktop启动Redis容器")
    print("   方式3: 使用WSL安装并启动Redis")
    print("\n📖 详细说明:")
    print("   - Redis for Windows: https://github.com/microsoftarchive/redis/releases")
    print("   - Docker命令: docker run -d --name redis -p 6379:6379 redis:6-alpine")
    print("   - WSL命令: sudo apt install redis-server && redis-server --daemonize yes")
    
    return False


def main():
    """主函数"""
    print("🔧 Redis服务启动器")
    print("=" * 50)
    
    if sys.platform.startswith('win'):
        success = start_redis_windows()
    else:
        # Linux/macOS系统
        print("🐧 检测到Linux/macOS系统")
        try:
            subprocess.run(['redis-server', '--daemonize', 'yes'], check=True)
            time.sleep(2)
            success = check_redis_running()
            if success:
                print("✅ Redis启动成功")
            else:
                print("❌ Redis启动失败")
        except FileNotFoundError:
            print("❌ 未找到redis-server命令，请先安装Redis")
            success = False
    
    if success:
        print("\n🎉 Redis服务已就绪!")
        print(f"   连接地址: redis://localhost:6379")
        print(f"   状态检查: {'✅ 正常' if check_redis_running() else '❌ 异常'}")
    else:
        print("\n❌ Redis服务启动失败")
        sys.exit(1)


if __name__ == "__main__":
    main()