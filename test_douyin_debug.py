#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试抖音API响应，查看详细信息
"""

import sys
import os
import asyncio
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler

async def debug_douyin_api():
    """调试抖音API响应"""
    
    print("=== 调试抖音API响应 ===")
    crawler = DouyinWebCrawler()
    
    # 测试长链接（直接包含视频ID）
    video_id = "7447875551779024160"
    print(f"测试视频ID: {video_id}")
    
    try:
        # 获取请求头
        kwargs = await crawler.get_douyin_headers()
        print(f"请求头: {json.dumps(kwargs['headers'], indent=2, ensure_ascii=False)}")
        
        # 直接调用API
        result = await crawler.fetch_one_video(video_id)
        print(f"API响应类型: {type(result)}")
        print(f"API响应内容: {result}")
        
        if result:
            print(f"响应字段: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict) and 'aweme_detail' in result:
                detail = result['aweme_detail']
                print(f"aweme_detail类型: {type(detail)}")
                if detail:
                    print(f"aweme_detail字段: {list(detail.keys()) if isinstance(detail, dict) else 'Not a dict'}")
                    if isinstance(detail, dict):
                        print(f"视频标题: {detail.get('desc', 'N/A')}")
                        print(f"作者信息: {detail.get('author', 'N/A')}")
                        print(f"统计信息: {detail.get('statistics', 'N/A')}")
                else:
                    print("aweme_detail为空")
            else:
                print("响应中没有aweme_detail字段")
        else:
            print("API返回空响应")
            
    except Exception as e:
        print(f"调试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_douyin_api())