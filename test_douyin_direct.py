#!/usr/bin/env python3
"""
直接测试抖音视频解析，不依赖Cookie
"""

import sys
import os
import asyncio
import httpx
import re

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_douyin_direct():
    """直接测试抖音视频解析"""
    
    # 测试短链接
    short_url = "https://v.douyin.com/MnlXfSNdXOQ/"
    
    print(f"测试抖音短链接解析: {short_url}")
    print("=" * 50)
    
    # 1. 先解析短链接获取真实URL
    print("1. 解析短链接...")
    
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        }
    ) as client:
        try:
            response = await client.get(short_url)
            real_url = str(response.url)
            print(f"   真实URL: {real_url}")
            
            # 提取视频ID
            video_id_match = re.search(r'/video/(\d+)', real_url)
            if video_id_match:
                video_id = video_id_match.group(1)
                print(f"   视频ID: {video_id}")
            else:
                print("   ❌ 无法提取视频ID")
                return
            
        except Exception as e:
            print(f"   ❌ 解析短链接失败: {e}")
            return
    
    print()
    
    # 2. 尝试不同的API端点
    api_endpoints = [
        f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}",
        f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Referer': 'https://www.douyin.com/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, endpoint in enumerate(api_endpoints, 2):
            print(f"{i}. 测试API端点: {endpoint}")
            
            try:
                response = await client.get(endpoint, headers=headers)
                print(f"   状态码: {response.status_code}")
                print(f"   响应长度: {len(response.text)}")
                
                if response.status_code == 200 and len(response.text) > 10:
                    print(f"   响应内容前500字符: {response.text[:500]}")
                    
                    # 尝试解析JSON
                    try:
                        data = response.json()
                        print(f"   ✅ JSON解析成功，包含 {len(data)} 个字段")
                        if 'aweme_detail' in data:
                            print("   ✅ 找到aweme_detail字段")
                        elif 'item_list' in data:
                            print("   ✅ 找到item_list字段")
                    except:
                        print("   ❌ JSON解析失败")
                else:
                    print("   ⚠️  响应异常")
                
            except Exception as e:
                print(f"   ❌ 请求失败: {e}")
            
            print()

if __name__ == "__main__":
    asyncio.run(test_douyin_direct())