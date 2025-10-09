#!/usr/bin/env python3
"""直接测试下载API的脚本

绕过中间件直接测试API端点功能
"""

import asyncio
from fastapi.testclient import TestClient
from app.app import fastapi_app
from app.core.security import create_access_token
from datetime import timedelta

def test_download_api():
    """测试下载API端点"""
    client = TestClient(fastapi_app)
    
    # 创建有效的JWT token
    token = create_access_token(subject="1", expires_delta=timedelta(hours=24))
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试数据
    test_data = {
        "url": "https://www.douyin.com/video/test",
        "quality": "720p",
        "format_preference": "mp4",
        "audio_only": False,
        "priority": "normal"
    }
    
    print("Testing download API...")
    print(f"Token: {token}")
    
    # 测试POST /api/v1/download/tasks
    try:
        response = client.post("/api/v1/download/tasks", json=test_data, headers=headers)
        print(f"POST /api/v1/download/tasks")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"POST request failed: {e}")
    
    # 测试GET /api/v1/download/tasks
    try:
        response = client.get("/api/v1/download/tasks", headers=headers)
        print(f"\nGET /api/v1/download/tasks")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"GET request failed: {e}")

if __name__ == "__main__":
    test_download_api()