#!/usr/bin/env python3
"""
直接测试API端点脚本
用于调试API内部错误
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from fastapi.testclient import TestClient
from app.app import fastapi_app
import traceback
import json

def test_videos_endpoint():
    """测试视频列表端点"""
    try:
        client = TestClient(fastapi_app)
        
        print("测试 /api/v1/videos/ 端点...")
        response = client.get('/api/v1/videos/')
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应数据类型: {type(data)}")
                if isinstance(data, list):
                    print(f"视频数量: {len(data)}")
                    if data:
                        print(f"第一个视频: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
                else:
                    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except Exception as e:
                print(f"解析JSON失败: {e}")
                print(f"原始响应: {response.text}")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_videos_endpoint()