#!/usr/bin/env python3
"""
测试抖音完整请求头
"""

import sys
import os
import asyncio
import httpx
from urllib.parse import urlencode

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler
from app.crawlers.douyin.web.utils import BogusManager
from app.crawlers.douyin.web.endpoints import DouyinAPIEndpoints
from app.crawlers.douyin.web.models import PostDetail

async def test_douyin_with_full_headers():
    """使用完整的抖音请求头测试"""
    
    video_id = "7549821013878426889"
    
    print(f"测试抖音完整请求头")
    print("=" * 50)
    print(f"视频ID: {video_id}")
    
    # 1. 获取抖音爬虫的完整请求头
    print("\n1. 获取抖音爬虫的完整请求头...")
    
    try:
        crawler = DouyinWebCrawler()
        kwargs = await crawler.get_douyin_headers()
        
        print(f"   请求头数量: {len(kwargs['headers'])}")
        print(f"   代理设置: {kwargs.get('proxies', '无代理')}")
        
        # 显示关键请求头
        key_headers = ['User-Agent', 'Cookie', 'Referer', 'Accept']
        for key in key_headers:
            if key in kwargs['headers']:
                value = kwargs['headers'][key]
                if key == 'Cookie' and len(value) > 100:
                    value = value[:100] + "..."
                print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"   ❌ 获取请求头失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 生成A-Bogus签名
    print("\n2. 生成A-Bogus签名...")
    
    try:
        # 创建参数
        params = PostDetail(aweme_id=video_id)
        params_dict = params.model_dump()
        params_dict["msToken"] = ''
        
        # 生成A-Bogus
        a_bogus = BogusManager.ab_model_2_endpoint(params_dict, kwargs['headers']['User-Agent'])
        
        print(f"   A-Bogus: {a_bogus[:50]}...")
        
        # 构建完整URL
        endpoint = f"{DouyinAPIEndpoints.POST_DETAIL}?{urlencode(params_dict)}&a_bogus={a_bogus}"
        
    except Exception as e:
        print(f"   ❌ A-Bogus生成失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 使用完整请求头测试API
    print("\n3. 使用完整请求头测试API...")
    
    # 处理代理设置
    proxies = kwargs.get('proxies')
    client_kwargs = {'timeout': 30.0}
    if proxies:
        client_kwargs['proxies'] = proxies
    
    async with httpx.AsyncClient(**client_kwargs) as client:
        try:
            response = await client.get(endpoint, headers=kwargs['headers'])
            print(f"   状态码: {response.status_code}")
            print(f"   响应长度: {len(response.text)}")
            
            if response.status_code == 200 and len(response.text) > 10:
                print(f"   响应内容前200字符: {response.text[:200]}")
                
                # 尝试解析JSON
                try:
                    data = response.json()
                    print(f"   ✅ JSON解析成功")
                    
                    # 检查响应结构
                    if 'aweme_detail' in data:
                        aweme_detail = data['aweme_detail']
                        print(f"   ✅ 找到aweme_detail")
                        print(f"   视频标题: {aweme_detail.get('desc', 'N/A')}")
                        print(f"   作者昵称: {aweme_detail.get('author', {}).get('nickname', 'N/A')}")
                        print(f"   播放数量: {aweme_detail.get('statistics', {}).get('play_count', 'N/A')}")
                    elif 'status_code' in data:
                        print(f"   状态码: {data.get('status_code')}")
                        print(f"   状态消息: {data.get('status_msg', 'N/A')}")
                    else:
                        print(f"   响应包含字段: {list(data.keys())}")
                        
                except Exception as json_e:
                    print(f"   ❌ JSON解析失败: {json_e}")
            else:
                print("   ⚠️  响应异常")
                if response.status_code != 200:
                    print(f"   响应内容: {response.text[:500]}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
    
    # 4. 测试使用爬虫的fetch_one_video方法
    print("\n4. 测试使用爬虫的fetch_one_video方法...")
    
    try:
        result = await crawler.fetch_one_video(video_id)
        print(f"   ✅ 爬虫方法调用成功")
        
        if isinstance(result, dict):
            if 'aweme_detail' in result:
                aweme_detail = result['aweme_detail']
                print(f"   视频标题: {aweme_detail.get('desc', 'N/A')}")
                print(f"   作者昵称: {aweme_detail.get('author', {}).get('nickname', 'N/A')}")
            elif 'status_code' in result:
                print(f"   状态码: {result.get('status_code')}")
                print(f"   状态消息: {result.get('status_msg', 'N/A')}")
            else:
                print(f"   响应包含字段: {list(result.keys())}")
        else:
            print(f"   响应类型: {type(result)}")
            
    except Exception as e:
        print(f"   ❌ 爬虫方法调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_douyin_with_full_headers())