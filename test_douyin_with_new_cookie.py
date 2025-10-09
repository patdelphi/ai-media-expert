#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试使用新Cookie的抖音视频解析功能
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler
from app.crawlers.hybrid.hybrid_crawler import HybridCrawler

async def test_douyin_with_new_cookie():
    """测试使用新Cookie的抖音视频解析"""
    
    # 测试链接
    test_urls = [
        "https://v.douyin.com/iJsyDxeJ/",  # 短链接
        "https://www.douyin.com/video/7447875551779024160"  # 长链接
    ]
    
    print("=== 测试抖音Web爬虫 ===")
    crawler = DouyinWebCrawler()
    
    for url in test_urls:
        print(f"\n测试链接: {url}")
        try:
            # 测试获取视频ID
            video_id = await crawler.get_aweme_id(url)
            print(f"视频ID: {video_id}")
            
            if video_id:
                # 测试获取视频详情
                result = await crawler.fetch_one_video(video_id)
                if result and 'aweme_detail' in result:
                    detail = result['aweme_detail']
                    print(f"视频标题: {detail.get('desc', '无标题')}")
                    print(f"作者: {detail.get('author', {}).get('nickname', '未知')}")
                    print(f"点赞数: {detail.get('statistics', {}).get('digg_count', 0)}")
                    print("✅ 获取视频详情成功")
                else:
                    print("❌ 获取视频详情失败")
            else:
                print("❌ 获取视频ID失败")
                
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
    
    print("\n=== 测试混合爬虫 ===")
    hybrid_crawler = HybridCrawler()
    
    for url in test_urls:
        print(f"\n测试链接: {url}")
        try:
            # 测试完整数据解析
            result = await hybrid_crawler.hybrid_parsing_single_video(url, minimal=False)
            if result:
                print(f"视频标题: {result.get('desc', '无标题')}")
                print(f"作者: {result.get('author', {}).get('nickname', '未知')}")
                print(f"点赞数: {result.get('statistics', {}).get('digg_count', 0)}")
                print("✅ 混合爬虫解析成功")
            else:
                print("❌ 混合爬虫解析失败")
                
        except Exception as e:
            print(f"❌ 混合爬虫测试失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_douyin_with_new_cookie())