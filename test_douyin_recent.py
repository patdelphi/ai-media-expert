#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新的抖音视频链接
"""

import sys
import os
import asyncio
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler
from app.crawlers.hybrid.hybrid_crawler import HybridCrawler

async def test_recent_douyin_videos():
    """测试更新的抖音视频"""
    
    # 使用更新的测试链接
    test_urls = [
        "https://www.douyin.com/video/7449123456789012345",  # 示例ID
        "https://v.douyin.com/iJsyDxeJ/",  # 短链接
    ]
    
    print("=== 测试更新的抖音视频 ===")
    crawler = DouyinWebCrawler()
    
    # 首先测试短链接解析
    short_url = "https://v.douyin.com/iJsyDxeJ/"
    print(f"\n测试短链接解析: {short_url}")
    
    try:
        video_id = await crawler.get_aweme_id(short_url)
        print(f"解析出的视频ID: {video_id}")
        
        if video_id:
            # 测试获取视频详情
            result = await crawler.fetch_one_video(video_id)
            print(f"API响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result and result.get('aweme_detail'):
                detail = result['aweme_detail']
                print(f"✅ 成功获取视频详情")
                print(f"视频标题: {detail.get('desc', 'N/A')}")
                print(f"作者: {detail.get('author', {}).get('nickname', 'N/A')}")
            else:
                print(f"❌ 视频详情为空")
                if result and 'filter_detail' in result:
                    filter_info = result['filter_detail']
                    print(f"过滤原因: {filter_info.get('filter_reason', 'N/A')}")
                    print(f"详细信息: {filter_info.get('detail_msg', 'N/A')}")
        else:
            print("❌ 无法解析视频ID")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    # 测试一些常见的抖音视频ID格式
    print(f"\n=== 测试不同的视频ID格式 ===")
    test_ids = [
        "7449000000000000000",  # 19位数字
        "7450000000000000000",  # 另一个19位数字
    ]
    
    for test_id in test_ids:
        print(f"\n测试视频ID: {test_id}")
        try:
            result = await crawler.fetch_one_video(test_id)
            if result and result.get('aweme_detail'):
                print(f"✅ 视频ID {test_id} 有效")
                detail = result['aweme_detail']
                print(f"标题: {detail.get('desc', 'N/A')[:50]}...")
            else:
                print(f"❌ 视频ID {test_id} 无效或被过滤")
                if result and 'filter_detail' in result:
                    print(f"过滤原因: {result['filter_detail'].get('filter_reason', 'N/A')}")
        except Exception as e:
            print(f"❌ 测试ID {test_id} 失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_recent_douyin_videos())