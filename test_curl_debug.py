#!/usr/bin/env python3
"""
使用requests库测试API端点
模拟curl请求行为
"""

import requests
import json
import traceback

def test_with_requests():
    """使用requests测试API"""
    try:
        print("测试 /health 端点...")
        response = requests.get('http://localhost:8000/health')
        print(f"Health - 状态码: {response.status_code}")
        print(f"Health - 响应: {response.text}")
        print()
        
        print("测试 / 根端点...")
        response = requests.get('http://localhost:8000/')
        print(f"Root - 状态码: {response.status_code}")
        print(f"Root - 响应: {response.text}")
        print()
        
        print("测试 /api/v1/videos/ 端点...")
        response = requests.get('http://localhost:8000/api/v1/videos/')
        print(f"Videos - 状态码: {response.status_code}")
        print(f"Videos - 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Videos - 数据类型: {type(data)}")
                if isinstance(data, list):
                    print(f"Videos - 视频数量: {len(data)}")
                else:
                    print(f"Videos - 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except Exception as e:
                print(f"Videos - JSON解析失败: {e}")
                print(f"Videos - 原始响应: {response.text}")
        else:
            print(f"Videos - 错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_with_requests()