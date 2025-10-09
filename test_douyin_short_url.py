#!/usr/bin/env python3
"""
测试抖音短链接解析功能
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.platform_adapters import DouyinAdapter
from app.services.video_parsing_service import VideoParsingService

async def test_douyin_short_url():
    """测试抖音短链接解析"""
    
    # 测试URL
    test_url = "https://v.douyin.com/MnlXfSNdXOQ/"
    
    print(f"测试URL: {test_url}")
    print("=" * 50)
    
    # 1. 测试平台适配器
    print("1. 测试DouyinAdapter:")
    adapter = DouyinAdapter()
    
    # 验证URL
    is_valid = adapter.validate_url(test_url)
    print(f"   URL验证: {is_valid}")
    
    # 提取视频ID
    try:
        video_id = adapter.extract_video_id(test_url)
        print(f"   提取的视频ID: {video_id}")
    except Exception as e:
        print(f"   提取视频ID失败: {e}")
    
    print()
    
    # 2. 测试视频解析服务
    print("2. 测试VideoParsingService:")
    parsing_service = VideoParsingService()
    
    try:
        video_info = await parsing_service.parse_video_info(test_url, minimal=False)
        print(f"   解析成功!")
        print(f"   平台: {video_info.get('platform')}")
        print(f"   视频ID: {video_info.get('video_id')}")
        print(f"   标题: {video_info.get('title')}")
        print(f"   作者: {video_info.get('author', {}).get('name')}")
        print(f"   时长: {video_info.get('duration')}")
        print(f"   播放量: {video_info.get('statistics', {}).get('play_count')}")
        
    except Exception as e:
        print(f"   解析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_douyin_short_url())