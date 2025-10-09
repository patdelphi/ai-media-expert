#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试抖音视频数据获取功能
"""

import asyncio
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler

async def test_douyin_video_fetch():
    """测试抖音视频数据获取"""
    
    aweme_id = "7549821013878426889"  # 从短链接提取的视频ID
    
    print(f"=== 测试抖音视频数据获取 ===")
    print(f"视频ID: {aweme_id}")
    
    try:
        crawler = DouyinWebCrawler()
        video_data = await crawler.fetch_one_video(aweme_id)
        
        if video_data and 'aweme_detail' in video_data:
            aweme_detail = video_data['aweme_detail']
            print(f"✅ 视频数据获取成功")
            print(f"标题: {aweme_detail.get('desc', 'N/A')}")
            print(f"作者: {aweme_detail.get('author', {}).get('nickname', 'N/A')}")
            print(f"视频类型: {aweme_detail.get('aweme_type', 'N/A')}")
            print(f"创建时间: {aweme_detail.get('create_time', 'N/A')}")
            
            # 检查视频URL
            video_info = aweme_detail.get('video', {})
            if video_info:
                play_addr = video_info.get('play_addr', {})
                if play_addr and 'url_list' in play_addr:
                    print(f"视频URL数量: {len(play_addr['url_list'])}")
                    print(f"第一个视频URL: {play_addr['url_list'][0] if play_addr['url_list'] else 'N/A'}")
                else:
                    print("❌ 未找到视频播放地址")
            else:
                print("❌ 未找到视频信息")
        else:
            print(f"❌ 视频数据获取失败: 响应格式不正确")
            print(f"响应内容: {json.dumps(video_data, indent=2, ensure_ascii=False)}")
            
    except Exception as e:
        print(f"❌ 视频数据获取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_douyin_video_fetch())