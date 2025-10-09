#!/usr/bin/env python3
"""
测试抖音API响应内容
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler
from app.crawlers.base_crawler import BaseCrawler

async def test_douyin_response():
    print("=== 测试抖音API响应内容 ===")
    
    aweme_id = "7549821013878426889"
    print(f"视频ID: {aweme_id}")
    
    try:
        crawler = DouyinWebCrawler()
        kwargs = await crawler.get_douyin_headers()
        
        # 创建基础爬虫
        proxies = kwargs.get("proxies")
        base_crawler = BaseCrawler(proxies=proxies, crawler_headers=kwargs["headers"])
        
        async with base_crawler as crawler_client:
            # 构建API端点
            endpoint = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={aweme_id}&aid=1128&version_name=23.5.0&device_platform=android&os_version=2333"
            
            print(f"请求URL: {endpoint}")
            
            # 获取原始响应
            response = await crawler_client.fetch_response(endpoint)
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容长度: {len(response.content)}")
            print(f"响应内容前500字符: {response.text[:500]}")
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    print("✅ JSON解析成功")
                    print(f"响应数据结构: {list(json_data.keys()) if isinstance(json_data, dict) else type(json_data)}")
                except Exception as e:
                    print(f"❌ JSON解析失败: {e}")
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_douyin_response())