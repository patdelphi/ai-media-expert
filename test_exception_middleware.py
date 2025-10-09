"""测试异常处理中间件

验证异常处理中间件是否正常工作。
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from fastapi.testclient import TestClient
from app.app import app
import traceback

def test_exception_middleware():
    """测试异常处理中间件"""
    client = TestClient(app)
    
    try:
        print("测试健康检查端点...")
        response = client.get("/health")
        print(f"Health - 状态码: {response.status_code}")
        print(f"Health - 响应: {response.json()}")
        print()
        
        print("测试根端点...")
        response = client.get("/")
        print(f"Root - 状态码: {response.status_code}")
        print(f"Root - 响应: {response.json()}")
        print()
        
        print("测试视频列表端点...")
        response = client.get("/api/v1/videos/")
        print(f"Videos - 状态码: {response.status_code}")
        print(f"Videos - 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Videos - 响应数据: {len(data)} 个视频")
        else:
            print(f"Videos - 错误响应: {response.text}")
            
    except Exception as e:
        print(f"异常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_exception_middleware()