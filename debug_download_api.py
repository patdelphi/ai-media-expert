#!/usr/bin/env python3
"""调试下载API脚本

测试下载API端点的连通性和功能。"""

import requests
import json
from datetime import datetime, timedelta

# 生成测试用的JWT token
def generate_test_token():
    # 从app.core.security导入token生成函数
    try:
        from app.core.security import create_access_token
        from datetime import timedelta
        # 创建测试用户的token，使用正确的参数格式
        token = create_access_token(
            subject="1",  # 用户ID为1
            expires_delta=timedelta(hours=24)
        )
        return token
    except Exception as e:
        print(f"生成token失败: {e}")
        # 备用方案：使用简单的token
        import jwt
        payload = {
            'sub': '1',  # 用户ID
            'exp': datetime.utcnow() + timedelta(hours=24)  # 24小时后过期
        }
        secret_key = "your-secret-key-here"
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token

def test_download_api():
    """测试下载API端点"""
    base_url = "http://localhost:8000"
    
    # 生成JWT token
    print("生成JWT token...")
    try:
        token = generate_test_token()
        print(f"Token生成成功: {token[:50]}...")
    except Exception as e:
        print(f"Token生成失败: {e}")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试1: 健康检查
    print("\n=== 测试健康检查端点 ===")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试2: 下载任务创建 (正确路径)
    print("\n=== 测试 /api/v1/video-download/download 端点 ===")
    download_data = {
        "url": "https://www.douyin.com/video/test123",
        "quality": "720p",
        "format_preference": "mp4",
        "audio_only": False,
        "priority": 1
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/video-download/download",
            headers=headers,
            json=download_data
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试3: 获取下载任务列表
    print("\n=== 测试获取下载任务列表 ===")
    try:
        response = requests.get(
            f"{base_url}/api/v1/video-download/tasks",
            headers=headers
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试4: 解析视频URL (使用真实抖音链接)
    print("\n=== 测试解析视频URL ===")
    parse_data = {
        "url": "https://v.douyin.com/MnlXfSNdXOQ/"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/video-download/parse",
            headers=headers,
            json=parse_data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"解析结果: {response.json()}")
        else:
            print(f"解析失败: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试5: 下载视频 (使用真实抖音链接)
    print("\n=== 测试下载视频 ===")
    download_data_real = {
        "url": "https://v.douyin.com/MnlXfSNdXOQ/",
        "quality": "high",
        "format_preference": "mp4",
        "audio_only": False,
        "priority": 1
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/video-download/download",
            headers=headers,
            json=download_data_real
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"下载任务创建成功: {result}")
            if 'task_id' in result:
                print(f"任务ID: {result['task_id']}")
        else:
            print(f"下载失败: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_download_api()