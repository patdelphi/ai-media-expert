#!/usr/bin/env python3
"""API调试脚本

用于测试API端点并获取详细错误信息。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.app import app

def test_videos_endpoint():
    """测试视频端点"""
    client = TestClient(app)
    
    try:
        response = client.get("/api/v1/videos/")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code != 200:
            print("API调用失败")
            return False
        
        print("API调用成功")
        return True
        
    except Exception as e:
        print(f"调用异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试API端点...")
    success = test_videos_endpoint()
    sys.exit(0 if success else 1)