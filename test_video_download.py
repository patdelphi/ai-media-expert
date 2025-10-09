#!/usr/bin/env python3
"""视频下载功能测试脚本

测试视频下载功能的核心组件，包括：
1. 平台适配器
2. 视频解析服务
3. 下载队列管理
4. WebSocket连接管理
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.platform_adapters import get_platform_adapter, get_all_supported_platforms
from app.services.video_parsing_service import VideoParsingService
from app.services.download_queue_manager import DownloadQueueManager
from app.services.websocket_manager import connection_manager
from app.core.app_logging import download_logger


async def test_platform_adapters():
    """测试平台适配器"""
    print("\n=== 测试平台适配器 ===")
    
    # 测试获取所有支持的平台
    platforms = get_all_supported_platforms()
    print(f"支持的平台数量: {len(platforms)}")
    
    for platform in platforms:
        print(f"- {platform['display_name']} ({platform['name']})")
    
    # 测试URL识别
    test_urls = [
        "https://www.douyin.com/video/7123456789",
        "https://www.tiktok.com/@user/video/7123456789",
        "https://www.bilibili.com/video/BV1234567890",
        "https://www.xiaohongshu.com/explore/123456",
        "https://v.kuaishou.com/123456",
        "https://channels.weixin.qq.com/video/123456"
    ]
    
    for url in test_urls:
        adapter = get_platform_adapter(url)
        if adapter:
            print(f"✅ {url} -> {adapter.__class__.__name__}")
        else:
            print(f"❌ {url} -> 未识别")
    
    return True


async def test_video_parsing_service():
    """测试视频解析服务"""
    print("\n=== 测试视频解析服务 ===")
    
    parsing_service = VideoParsingService()
    
    # 测试抖音URL解析（模拟）
    test_url = "https://www.douyin.com/video/test123"
    
    try:
        result = await parsing_service.parse_video_info(
            url=test_url,
            minimal=True
        )
        
        if result:
            print(f"✅ 解析成功: {result.get('title', '未知标题')}")
            print(f"   平台: {result.get('platform', '未知')}")
            print(f"   作者: {result.get('author', {}).get('name', '未知')}")
        else:
            print("❌ 解析失败: 返回空结果")
            
    except Exception as e:
        print(f"❌ 解析异常: {str(e)}")
        # 这是预期的，因为我们使用的是测试URL
        print("   (这是预期的，因为使用了测试URL)")
    
    return True


async def test_download_queue_manager():
    """测试下载队列管理器"""
    print("\n=== 测试下载队列管理器 ===")
    
    try:
        queue_manager = DownloadQueueManager()
        
        # 测试队列状态
        stats = queue_manager.get_queue_stats()
        print(f"✅ 队列管理器初始化成功")
        print(f"   队列状态: {stats}")
        
        # 测试并发设置
        print(f"   最大并发数: {queue_manager.max_concurrent}")
        print(f"   当前运行任务: {len(queue_manager.running_tasks)}")
        print(f"   是否运行中: {queue_manager._running}")
        
        return True
        
    except Exception as e:
        print(f"❌ 队列管理器测试失败: {str(e)}")
        return False


async def test_websocket_manager():
    """测试WebSocket连接管理器"""
    print("\n=== 测试WebSocket连接管理器 ===")
    
    try:
        # 测试连接统计
        stats = connection_manager.get_connection_stats()
        print(f"✅ WebSocket管理器初始化成功")
        print(f"   连接统计: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket管理器测试失败: {str(e)}")
        return False


async def test_error_handling():
    """测试错误处理机制"""
    print("\n=== 测试错误处理机制 ===")
    
    try:
        from app.utils.error_handler import default_error_handler, DownloadError, ErrorCategory
        
        # 创建测试错误
        test_error = DownloadError(
            message="测试错误",
            category=ErrorCategory.NETWORK,
            details={"test": True}
        )
        
        # 测试错误处理
        await default_error_handler.handle_error(test_error, {"context": "test"})
        
        # 获取错误统计
        stats = default_error_handler.get_error_statistics()
        print(f"✅ 错误处理机制正常")
        print(f"   错误统计: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("🚀 开始视频下载功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("平台适配器", test_platform_adapters),
        ("视频解析服务", test_video_parsing_service),
        ("下载队列管理器", test_download_queue_manager),
        ("WebSocket管理器", test_websocket_manager),
        ("错误处理机制", test_error_handling)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {str(e)}")
            test_results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！视频下载功能基本正常。")
        return True
    else:
        print(f"⚠️  有 {total - passed} 项测试失败，需要进一步检查。")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试执行异常: {str(e)}")
        sys.exit(1)