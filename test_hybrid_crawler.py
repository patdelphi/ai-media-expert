#!/usr/bin/env python3
"""
测试HybridCrawler解析抖音视频
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.hybrid.hybrid_crawler import HybridCrawler

async def test_hybrid_crawler():
    """测试HybridCrawler解析抖音视频"""
    
    # 测试URL列表
    test_urls = [
        "https://v.douyin.com/iJsyDJAj/",  # 短链接
        "https://www.douyin.com/video/7549821013878426889",  # 长链接
    ]
    
    print(f"测试HybridCrawler解析抖音视频")
    print("=" * 50)
    
    crawler = HybridCrawler()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{i}. 测试URL: {url}")
        print("-" * 30)
        
        try:
            # 测试完整数据解析
            print("   解析完整数据...")
            result = await crawler.hybrid_parsing_single_video(url, minimal=False)
            
            if isinstance(result, dict):
                print(f"   ✅ 解析成功")
                print(f"   数据类型: {type(result)}")
                print(f"   数据字段: {list(result.keys())}")
                
                # 显示关键信息
                if 'desc' in result:
                    print(f"   视频标题: {result.get('desc', 'N/A')}")
                if 'author' in result:
                    author = result.get('author', {})
                    print(f"   作者昵称: {author.get('nickname', 'N/A')}")
                if 'statistics' in result:
                    stats = result.get('statistics', {})
                    print(f"   播放数量: {stats.get('play_count', 'N/A')}")
                    print(f"   点赞数量: {stats.get('digg_count', 'N/A')}")
                if 'video' in result:
                    video = result.get('video', {})
                    if 'play_addr' in video:
                        play_addr = video.get('play_addr', {})
                        url_list = play_addr.get('url_list', [])
                        if url_list:
                            print(f"   视频地址: {url_list[0][:100]}...")
                            
            else:
                print(f"   ⚠️  返回数据类型异常: {type(result)}")
                print(f"   数据内容: {str(result)[:200]}")
                
        except Exception as e:
            print(f"   ❌ 完整数据解析失败: {e}")
            import traceback
            traceback.print_exc()
            
        try:
            # 测试最小数据解析
            print("   解析最小数据...")
            result = await crawler.hybrid_parsing_single_video(url, minimal=True)
            
            if isinstance(result, dict):
                print(f"   ✅ 最小数据解析成功")
                print(f"   数据字段: {list(result.keys())}")
                
                # 显示关键信息
                for key in ['type', 'platform', 'aweme_id', 'title', 'author']:
                    if key in result:
                        print(f"   {key}: {result[key]}")
                        
            else:
                print(f"   ⚠️  最小数据类型异常: {type(result)}")
                
        except Exception as e:
            print(f"   ❌ 最小数据解析失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_hybrid_crawler())