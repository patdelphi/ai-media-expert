#!/usr/bin/env python3
"""
ngrok隧道启动脚本

用于快速启动ngrok隧道服务，为GLM-4.5V等视频理解模型提供公网访问能力。
"""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

def check_ngrok_installed():
    """检查ngrok是否已安装"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ngrok已安装: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def install_ngrok():
    """安装ngrok"""
    print("📦 正在安装ngrok...")
    try:
        # 使用npm安装ngrok
        result = subprocess.run(['npm', 'install', '-g', 'ngrok'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok安装成功")
            return True
        else:
            print(f"❌ ngrok安装失败: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ 未找到npm，请先安装Node.js")
        return False

def start_ngrok_tunnel(port=8000):
    """启动ngrok隧道"""
    print(f"🚀 启动ngrok隧道，端口: {port}")
    
    # 启动ngrok进程
    process = subprocess.Popen(
        ['ngrok', 'http', str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待ngrok启动
    print("⏳ 等待ngrok启动...")
    time.sleep(3)
    
    # 获取ngrok状态
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        if response.status_code == 200:
            tunnels = response.json()['tunnels']
            if tunnels:
                public_url = tunnels[0]['public_url']
                print(f"\n🎉 ngrok隧道启动成功！")
                print(f"📍 本地地址: http://localhost:{port}")
                print(f"🌐 公网地址: {public_url}")
                print(f"📊 管理界面: http://localhost:4040")
                
                # 更新.env文件
                update_env_file(public_url)
                
                return public_url, process
            else:
                print("❌ 未找到活跃的隧道")
                return None, process
        else:
            print(f"❌ 无法获取ngrok状态: {response.status_code}")
            return None, process
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到ngrok API，请检查ngrok是否正常启动")
        return None, process
    except Exception as e:
        print(f"❌ 获取ngrok状态时出错: {str(e)}")
        return None, process

def update_env_file(ngrok_url):
    """更新.env文件中的NGROK_URL"""
    env_file = Path('.env')
    env_example_file = Path('.env.example')
    
    # 如果.env文件不存在，从.env.example复制
    if not env_file.exists() and env_example_file.exists():
        print("📝 创建.env文件...")
        with open(env_example_file, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    if env_file.exists():
        # 读取现有内容
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 更新或添加NGROK_URL
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('NGROK_URL=') or line.startswith('# NGROK_URL='):
                lines[i] = f'NGROK_URL={ngrok_url}\n'
                updated = True
                break
        
        if not updated:
            # 如果没有找到NGROK_URL行，添加到文件末尾
            lines.append(f'\n# ngrok公网地址\nNGROK_URL={ngrok_url}\n')
        
        # 写回文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ 已更新.env文件: NGROK_URL={ngrok_url}")
    else:
        print("⚠️  未找到.env文件，请手动设置NGROK_URL环境变量")

def main():
    """主函数"""
    print("🎬 ngrok隧道启动工具")
    print("=" * 50)
    
    # 检查ngrok是否安装
    if not check_ngrok_installed():
        print("❌ ngrok未安装")
        install_choice = input("是否自动安装ngrok? (y/n): ")
        if install_choice.lower() == 'y':
            if not install_ngrok():
                print("❌ 安装失败，请手动安装ngrok")
                print("💡 安装方法: npm install -g ngrok")
                sys.exit(1)
        else:
            print("💡 请手动安装ngrok: npm install -g ngrok")
            sys.exit(1)
    
    # 获取端口号
    port = 8000
    port_input = input(f"请输入后端服务端口 (默认: {port}): ")
    if port_input.strip():
        try:
            port = int(port_input)
        except ValueError:
            print("❌ 端口号无效，使用默认端口8000")
    
    # 启动ngrok隧道
    public_url, process = start_ngrok_tunnel(port)
    
    if public_url:
        print("\n📋 使用说明：")
        print("1. 确保后端服务运行在指定端口")
        print("2. 重启后端服务以加载新的环境变量")
        print("3. 使用GLM-4.5V模型进行视频分析")
        print("4. 按Ctrl+C停止ngrok隧道")
        
        try:
            # 保持进程运行
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 正在停止ngrok隧道...")
            process.terminate()
            process.wait()
            print("✅ ngrok隧道已停止")
    else:
        print("❌ ngrok隧道启动失败")
        if process:
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()