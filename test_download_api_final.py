#!/usr/bin/env python3
"""最终下载API测试脚本

测试下载API的完整功能，包括创建任务和获取任务列表
"""

import requests
import json
from app.core.security import create_access_token
from datetime import timedelta

def test_download_api_with_requests():
    """使用requests库测试下载API"""
    
    # 创建有效的JWT token
    token = create_access_token(subject="1", expires_delta=timedelta(hours=24))
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "http://localhost:8000/api/v1/download"
    
    print("=== 下载API测试 ===")
    print(f"Token: {token[:50]}...")
    
    # 测试数据
    test_data = {
        "url": "https://www.douyin.com/video/test123",
        "quality": "720p",
        "format_preference": "mp4",
        "audio_only": False,
        "priority": "normal"
    }
    
    # 1. 测试创建下载任务
    print("\n1. 测试创建下载任务...")
    try:
        response = requests.post(f"{base_url}/tasks", json=test_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            task_data = response.json()
            print("✅ 创建任务成功")
            task_id = task_data.get("data", {}).get("id")
            print(f"任务ID: {task_id}")
        else:
            print("❌ 创建任务失败")
            return
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 2. 测试获取任务列表
    print("\n2. 测试获取任务列表...")
    try:
        response = requests.get(f"{base_url}/tasks", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            tasks_data = response.json()
            print("✅ 获取任务列表成功")
            total = tasks_data.get("data", {}).get("total", 0)
            print(f"总任务数: {total}")
        else:
            print("❌ 获取任务列表失败")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 3. 测试获取单个任务详情（如果有任务ID）
    if 'task_id' in locals() and task_id:
        print(f"\n3. 测试获取任务详情 (ID: {task_id})...")
        try:
            response = requests.get(f"{base_url}/tasks/{task_id}", headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            
            if response.status_code == 200:
                print("✅ 获取任务详情成功")
            else:
                print("❌ 获取任务详情失败")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_download_api_with_requests()