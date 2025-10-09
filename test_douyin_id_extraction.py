#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试抖音视频ID提取功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.utils import AwemeIdFetcher

async def test_douyin_id_extraction():
    """测试抖音视频ID提取"""
    
    test_urls = [
        "https://v.douyin.com/MnlXfSNdXOQ/",  # 用户提供的短链接
        "https://www.iesdouyin.com/share/video/7549821013878426889/",  # 重定向后的完整链接
        "https://www.douyin.com/video/7549821013878426889",  # 标准格式
    ]
    
    print("=== 测试抖音视频ID提取 ===")
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n测试 {i}: {url}")
        try:
            aweme_id = await AwemeIdFetcher.get_aweme_id(url)
            print(f"✅ 提取成功: {aweme_id}")
        except Exception as e:
            print(f"❌ 提取失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_douyin_id_extraction())