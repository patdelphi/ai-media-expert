#!/usr/bin/env python3
"""
测试抖音Cookie有效性
"""

import sys
import os
import asyncio
import httpx

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_douyin_cookie():
    """测试抖音Cookie有效性"""
    
    # 从配置文件读取Cookie
    import yaml
    config_path = "app/crawlers/douyin/web/config.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    headers = config['TokenManager']['douyin']['headers']
    
    print("测试抖音Cookie有效性")
    print("=" * 50)
    print(f"User-Agent: {headers['User-Agent']}")
    print(f"Cookie长度: {len(headers['Cookie'])}")
    print()
    
    # 测试访问抖音主页
    test_urls = [
        "https://www.douyin.com/",
        "https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7549821013878426889",
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, url in enumerate(test_urls, 1):
            print(f"{i}. 测试URL: {url}")
            
            try:
                response = await client.get(url, headers=headers)
                print(f"   状态码: {response.status_code}")
                print(f"   响应长度: {len(response.text)}")
                
                # 检查是否被重定向到验证页面
                if "验证" in response.text or "captcha" in response.text.lower():
                    print("   ❌ Cookie可能已失效，需要验证")
                elif response.status_code == 200 and len(response.text) > 1000:
                    print("   ✅ Cookie可能有效")
                else:
                    print("   ⚠️  响应异常，需要检查")
                
                # 打印前200字符
                print(f"   响应内容前200字符: {response.text[:200]}")
                
            except Exception as e:
                print(f"   ❌ 请求失败: {e}")
            
            print()

if __name__ == "__main__":
    asyncio.run(test_douyin_cookie())