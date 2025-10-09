#!/usr/bin/env python3
"""
测试抖音A-Bogus签名生成
"""

import sys
import os
import asyncio
import httpx
from urllib.parse import urlencode

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.utils import BogusManager
from app.crawlers.douyin.web.endpoints import DouyinAPIEndpoints
from app.crawlers.douyin.web.models import PostDetail

async def test_douyin_abogus():
    """测试抖音A-Bogus签名生成"""
    
    video_id = "7549821013878426889"
    
    print(f"测试抖音A-Bogus签名生成")
    print("=" * 50)
    print(f"视频ID: {video_id}")
    
    # 1. 生成A-Bogus签名
    print("\n1. 生成A-Bogus签名...")
    
    try:
        # 创建参数
        params = PostDetail(aweme_id=video_id)
        params_dict = params.dict()
        params_dict["msToken"] = ''
        
        print(f"   参数: {params_dict}")
        
        # 生成A-Bogus
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        a_bogus = BogusManager.ab_model_2_endpoint(params_dict, user_agent)
        
        print(f"   A-Bogus: {a_bogus}")
        
        # 构建完整URL
        endpoint = f"{DouyinAPIEndpoints.POST_DETAIL}?{urlencode(params_dict)}&a_bogus={a_bogus}"
        print(f"   完整URL: {endpoint}")
        
    except Exception as e:
        print(f"   ❌ A-Bogus生成失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 测试API请求
    print("\n2. 测试API请求...")
    
    headers = {
        'User-Agent': user_agent,
        'Referer': 'https://www.douyin.com/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(endpoint, headers=headers)
            print(f"   状态码: {response.status_code}")
            print(f"   响应长度: {len(response.text)}")
            
            if response.status_code == 200 and len(response.text) > 10:
                print(f"   响应内容前500字符: {response.text[:500]}")
                
                # 尝试解析JSON
                try:
                    data = response.json()
                    print(f"   ✅ JSON解析成功")
                    
                    # 检查响应结构
                    if 'aweme_detail' in data:
                        aweme_detail = data['aweme_detail']
                        print(f"   ✅ 找到aweme_detail")
                        print(f"   视频标题: {aweme_detail.get('desc', 'N/A')}")
                        print(f"   作者昵称: {aweme_detail.get('author', {}).get('nickname', 'N/A')}")
                        print(f"   播放数量: {aweme_detail.get('statistics', {}).get('play_count', 'N/A')}")
                    elif 'status_code' in data:
                        print(f"   状态码: {data.get('status_code')}")
                        print(f"   状态消息: {data.get('status_msg', 'N/A')}")
                    else:
                        print(f"   响应包含字段: {list(data.keys())}")
                        
                except Exception as json_e:
                    print(f"   ❌ JSON解析失败: {json_e}")
            else:
                print("   ⚠️  响应异常")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_douyin_abogus())