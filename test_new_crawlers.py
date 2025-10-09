#!/usr/bin/env python3
"""测试新的爬虫功能

验证集成的Douyin_TikTok_Download_API爬虫组件是否正常工作。
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.hybrid.hybrid_crawler import HybridCrawler
from app.services.platform_adapters import get_platform_adapter
from app.services.video_parsing_service import VideoParsingService
from app.core.app_logging import download_logger


async def test_hybrid_crawler():
    """测试HybridCrawler"""
    print("🚀 测试HybridCrawler")
    print("=" * 50)
    
    crawler = HybridCrawler()
    
    # 测试URL列表
    test_urls = [
        "https://www.douyin.com/video/7123456789",
        "https://www.tiktok.com/@user/video/7123456789",
        "https://v.douyin.com/test123",
    ]
    
    for url in test_urls:
        print(f"\n=== 测试URL: {url} ===")
        try:
            result = await crawler.hybrid_parsing_single_video(url, minimal=True)
            print(f"✅ 解析成功:")
            print(f"   平台: {result.get('platform', 'unknown')}")
            print(f"   标题: {result.get('title', 'unknown')}")
            print(f"   类型: {result.get('type', 'unknown')}")
            print(f"   作者: {result.get('author', {}).get('nickname', 'unknown')}")
        except Exception as e:
            print(f"❌ 解析失败: {e}")


async def test_platform_adapters():
    """测试平台适配器"""
    print("\n🔧 测试平台适配器")
    print("=" * 50)
    
    test_urls = [
        "https://www.douyin.com/video/7123456789",
        "https://www.tiktok.com/@user/video/7123456789",
        "https://www.bilibili.com/video/BV1234567890",
    ]
    
    for url in test_urls:
        print(f"\n=== 测试URL: {url} ===")
        try:
            adapter = get_platform_adapter(url)
            if adapter:
                print(f"✅ 找到适配器: {adapter.__class__.__name__}")
                print(f"   平台名称: {adapter.get_platform_name()}")
                print(f"   显示名称: {adapter.get_display_name()}")
                
                # 测试视频ID提取
                video_id = adapter.extract_video_id(url)
                print(f"   视频ID: {video_id or 'unknown'}")
                
                # 如果适配器有解析方法，测试解析
                if hasattr(adapter, 'parse_video_info'):
                    try:
                        info = await adapter.parse_video_info(url)
                        print(f"   解析结果: {info.get('title', 'unknown')}")
                    except Exception as parse_error:
                        print(f"   解析失败: {parse_error}")
            else:
                print(f"❌ 未找到适配器")
        except Exception as e:
            print(f"❌ 适配器测试失败: {e}")


async def test_video_parsing_service():
    """测试视频解析服务"""
    print("\n📹 测试视频解析服务")
    print("=" * 50)
    
    service = VideoParsingService()
    
    test_urls = [
        "https://www.douyin.com/video/7123456789",
        "https://www.tiktok.com/@user/video/7123456789",
    ]
    
    for url in test_urls:
        print(f"\n=== 测试URL: {url} ===")
        try:
            result = await service.parse_video_info(url, minimal=True)
            print(f"✅ 解析成功:")
            print(f"   平台: {result.get('platform', 'unknown')}")
            print(f"   标题: {result.get('title', 'unknown')}")
            print(f"   视频ID: {result.get('video_id', 'unknown')}")
            print(f"   作者: {result.get('author', {}).get('name', 'unknown')}")
        except Exception as e:
            print(f"❌ 解析失败: {e}")


def test_imports():
    """测试模块导入"""
    print("📦 测试模块导入")
    print("=" * 50)
    
    modules_to_test = [
        ('app.crawlers.hybrid.hybrid_crawler', 'HybridCrawler'),
        ('app.crawlers.base_crawler', 'BaseCrawler'),
        ('app.crawlers.douyin.web.web_crawler', 'DouyinWebCrawler'),
        ('app.crawlers.tiktok.web.web_crawler', 'TikTokWebCrawler'),
        ('app.crawlers.utils.utils', 'extract_valid_urls'),
    ]
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {e}")


async def main():
    """主测试函数"""
    print("🎬 新爬虫功能测试")
    print("=" * 50)
    
    # 测试模块导入
    test_imports()
    
    # 测试HybridCrawler
    await test_hybrid_crawler()
    
    # 测试平台适配器
    await test_platform_adapters()
    
    # 测试视频解析服务
    await test_video_parsing_service()
    
    print("\n" + "=" * 50)
    print("📊 测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())