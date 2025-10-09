#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试抖音爬虫 - 使用用户提供的新链接
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler
from app.crawlers.hybrid.hybrid_crawler import HybridCrawler

async def test_new_douyin_link():
    """测试用户提供的新抖音链接"""
    
    # 用户提供的链接
    test_url = "https://v.douyin.com/h-N_QCNQJs0/"
    
    print(f"=== 测试新抖音链接 ===")
    print(f"链接: {test_url}")
    print(f"描述: 南京免费博物馆，收藏六百年人间烟火与匠心温度")
    
    # 测试1: DouyinWebCrawler
    print(f"\n--- 测试 DouyinWebCrawler ---")
    try:
        crawler = DouyinWebCrawler()
        
        # 获取视频ID
        print("1. 获取视频ID...")
        video_id = await crawler.get_aweme_id(test_url)
        print(f"视频ID: {video_id}")
        
        if video_id:
            # 获取视频详情
            print("2. 获取视频详情...")
            video_data = await crawler.fetch_one_video(video_id)
            
            if video_data:
                print("✅ DouyinWebCrawler 测试成功")
                print(f"视频标题: {video_data.get('desc', 'N/A')}")
                print(f"作者: {video_data.get('author', {}).get('nickname', 'N/A')}")
                print(f"点赞数: {video_data.get('statistics', {}).get('digg_count', 'N/A')}")
                print(f"评论数: {video_data.get('statistics', {}).get('comment_count', 'N/A')}")
                print(f"分享数: {video_data.get('statistics', {}).get('share_count', 'N/A')}")
                print(f"播放数: {video_data.get('statistics', {}).get('play_count', 'N/A')}")
            else:
                print("❌ 视频数据为空")
        else:
            print("❌ 无法获取视频ID")
            
    except Exception as e:
        print(f"❌ DouyinWebCrawler 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试2: HybridCrawler
    print(f"\n--- 测试 HybridCrawler ---")
    try:
        hybrid_crawler = HybridCrawler()
        
        print("使用混合爬虫解析视频...")
        result = await hybrid_crawler.hybrid_parsing_single_video(test_url, minimal=False)
        
        if result:
            print("✅ HybridCrawler 测试成功")
            print(f"视频标题: {result.get('desc', 'N/A')}")
            print(f"作者: {result.get('author', {}).get('nickname', 'N/A')}")
            print(f"点赞数: {result.get('statistics', {}).get('digg_count', 'N/A')}")
            print(f"评论数: {result.get('statistics', {}).get('comment_count', 'N/A')}")
            print(f"分享数: {result.get('statistics', {}).get('share_count', 'N/A')}")
            print(f"播放数: {result.get('statistics', {}).get('play_count', 'N/A')}")
            
            # 检查视频下载链接
            video_urls = result.get('video', {}).get('play_addr', {}).get('url_list', [])
            if video_urls:
                print(f"视频下载链接数量: {len(video_urls)}")
                print(f"第一个下载链接: {video_urls[0][:100]}..." if video_urls[0] else "无")
            else:
                print("❌ 未找到视频下载链接")
        else:
            print("❌ HybridCrawler 返回空结果")
            
    except Exception as e:
        print(f"❌ HybridCrawler 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_new_douyin_link())