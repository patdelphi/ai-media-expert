"""调试videos API路由

直接测试videos API路由，查看具体错误信息。
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from fastapi.testclient import TestClient
from app.app import app
import traceback

def test_videos_api():
    """测试videos API"""
    client = TestClient(app)
    
    try:
        print("测试 /api/v1/videos/ 端点...")
        response = client.get("/api/v1/videos/")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {data}")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"异常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_videos_api()