#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试抖音爬虫 - 使用最新视频链接
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler

async def test_latest_videos():
    """测试最新的抖音视频链接"""
    crawler = DouyinWebCrawler()
    
    # 使用一些最新的抖音视频链接进行测试
    test_urls = [
        "https://v.douyin.com/iJsyDxeJ/",  # 短链接
        "https://www.douyin.com/video/7447875551779024160",  # 长链接
        # 可以添加更多测试链接
    ]
    
    for url in test_urls:
        print(f"\n=== 测试链接: {url} ===")
        try:
            # 1. 测试获取视频ID
            print("1. 获取视频ID...")
            video_id = await crawler.get_aweme_id(url)
            print(f"视频ID: {video_id}")
            
            if video_id:
                # 2. 测试获取视频详情
                print("2. 获取视频详情...")
                video_data = await crawler.fetch_one_video(video_id)
                
                if video_data:
                    print("✅ 视频数据获取成功")
                    print(f"视频标题: {video_data.get('desc', 'N/A')}")
                    print(f"作者: {video_data.get('author', {}).get('nickname', 'N/A')}")
                    print(f"点赞数: {video_data.get('statistics', {}).get('digg_count', 'N/A')}")
                    print(f"评论数: {video_data.get('statistics', {}).get('comment_count', 'N/A')}")
                    print(f"分享数: {video_data.get('statistics', {}).get('share_count', 'N/A')}")
                else:
                    print("❌ 视频数据为空")
            else:
                print("❌ 无法获取视频ID")
                
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_latest_videos())