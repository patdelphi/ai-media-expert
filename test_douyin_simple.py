#!/usr/bin/env python3
"""
简单的抖音视频解析测试
使用基础的HTTP请求，不依赖复杂的签名验证
"""

import sys
import os
import asyncio
import httpx
import re
from urllib.parse import urlparse, parse_qs

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.utils import AwemeIdFetcher

async def test_simple_douyin_parsing():
    """简单的抖音视频解析测试"""
    
    test_url = "https://v.douyin.com/iJsyDJAj/"
    
    print(f"简单的抖音视频解析测试")
    print("=" * 50)
    print(f"测试URL: {test_url}")
    
    # 1. 解析短链接获取视频ID
    print("\n1. 解析短链接获取视频ID...")
    
    try:
        aweme_id_fetcher = AwemeIdFetcher()
        video_id = await aweme_id_fetcher.get_aweme_id(test_url)
        print(f"   ✅ 视频ID: {video_id}")
        
    except Exception as e:
        print(f"   ❌ 视频ID解析失败: {e}")
        return
    
    # 2. 尝试使用简单的API端点
    print("\n2. 尝试使用简单的API端点...")
    
    # 基础请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # 测试不同的API端点
    api_endpoints = [
        f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}",
        f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}",
        f"https://www.douyin.com/video/{video_id}",  # 网页版
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, endpoint in enumerate(api_endpoints, 1):
            print(f"\n   {i}. 测试端点: {endpoint[:80]}...")
            
            try:
                response = await client.get(endpoint, headers=headers, follow_redirects=True)
                print(f"      状态码: {response.status_code}")
                print(f"      响应长度: {len(response.text)}")
                
                if response.status_code == 200:
                    content = response.text
                    
                    # 检查是否包含视频信息
                    if video_id in content:
                        print(f"      ✅ 响应包含视频ID")
                        
                        # 尝试提取视频标题
                        title_patterns = [
                            r'"desc":"([^"]+)"',
                            r'<title>([^<]+)</title>',
                            r'"title":"([^"]+)"',
                        ]
                        
                        for pattern in title_patterns:
                            match = re.search(pattern, content)
                            if match:
                                title = match.group(1)
                                print(f"      视频标题: {title}")
                                break
                        
                        # 尝试提取作者信息
                        author_patterns = [
                            r'"nickname":"([^"]+)"',
                            r'"author":"([^"]+)"',
                        ]
                        
                        for pattern in author_patterns:
                            match = re.search(pattern, content)
                            if match:
                                author = match.group(1)
                                print(f"      作者昵称: {author}")
                                break
                        
                        # 尝试提取视频URL
                        video_patterns = [
                            r'"play_addr":\{"uri":"[^"]+","url_list":\["([^"]+)"',
                            r'"video_url":"([^"]+)"',
                        ]
                        
                        for pattern in video_patterns:
                            match = re.search(pattern, content)
                            if match:
                                video_url = match.group(1)
                                print(f"      视频地址: {video_url[:100]}...")
                                break
                        
                        # 如果是JSON响应，尝试解析
                        if 'application/json' in response.headers.get('content-type', ''):
                            try:
                                data = response.json()
                                print(f"      ✅ JSON解析成功")
                                print(f"      JSON字段: {list(data.keys())}")
                            except:
                                print(f"      ❌ JSON解析失败")
                        
                        print(f"      响应内容前200字符: {content[:200]}")
                        
                    else:
                        print(f"      ⚠️  响应不包含视频ID")
                        if len(content) < 1000:
                            print(f"      响应内容: {content}")
                        else:
                            print(f"      响应内容前500字符: {content[:500]}")
                else:
                    print(f"      ❌ 请求失败")
                    print(f"      响应内容: {response.text[:200]}")
                    
            except Exception as e:
                print(f"      ❌ 请求异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_douyin_parsing())