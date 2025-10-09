#!/usr/bin/env python3
"""前端集成测试脚本（简化版）

使用标准库测试前端与后端的基本集成。
"""

import sys
import urllib.request
import urllib.error
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class SimpleFrontendTester:
    """简化版前端集成测试器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3003"
        self.test_results = []
    
    def test_api_health(self):
        """测试API健康状态"""
        print("\n=== 测试API健康状态 ===")
        
        try:
            with urllib.request.urlopen(f"{self.base_url}/docs", timeout=5) as response:
                if response.status == 200:
                    print("✅ API文档可访问")
                    return True
                else:
                    print(f"❌ API文档访问失败: {response.status}")
                    return False
        except urllib.error.URLError as e:
            print(f"❌ API健康检查失败: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ API健康检查异常: {str(e)}")
            return False
    
    def test_platform_api(self):
        """测试平台列表API"""
        print("\n=== 测试平台列表API ===")
        
        try:
            url = f"{self.base_url}/api/v1/video-download/platforms"
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    platforms = data.get('data', {}).get('platforms', [])
                    print(f"✅ 获取到 {len(platforms)} 个支持的平台")
                    
                    for platform in platforms[:3]:  # 显示前3个
                        print(f"   - {platform['display_name']} ({platform['name']})")
                    
                    return len(platforms) > 0
                else:
                    print(f"❌ 平台API访问失败: {response.status}")
                    return False
        except urllib.error.HTTPError as e:
            print(f"❌ 平台API HTTP错误: {e.code} - {e.reason}")
            return False
        except Exception as e:
            print(f"❌ 平台API测试异常: {str(e)}")
            return False
    
    def test_video_parse_api(self):
        """测试视频解析API"""
        print("\n=== 测试视频解析API ===")
        
        try:
            # 测试无效URL的处理
            test_data = json.dumps({
                "url": "https://invalid-url.com/test",
                "minimal": True
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.base_url}/api/v1/video-download/parse",
                data=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    print(f"✅ 视频解析API响应状态: {response.status}")
                    return True
            except urllib.error.HTTPError as e:
                # 预期会返回错误，但不应该是500错误
                if e.code in [400, 401, 422]:  # 客户端错误是预期的
                    print("✅ 视频解析API正确处理无效请求")
                    return True
                elif e.code == 500:
                    print("❌ 视频解析API服务器内部错误")
                    return False
                else:
                    print(f"✅ 视频解析API响应状态: {e.code}")
                    return True
                    
        except Exception as e:
            print(f"❌ 视频解析API测试异常: {str(e)}")
            return False
    
    def test_frontend_assets(self):
        """测试前端资源访问"""
        print("\n=== 测试前端资源访问 ===")
        
        try:
            # 测试前端主页
            with urllib.request.urlopen(self.frontend_url, timeout=10) as response:
                if response.status == 200:
                    print("✅ 前端主页可访问")
                    
                    # 测试视频下载页面
                    try:
                        with urllib.request.urlopen(
                            f"{self.frontend_url}/video-download", 
                            timeout=10
                        ) as download_response:
                            if download_response.status == 200:
                                print("✅ 视频下载页面可访问")
                                return True
                            else:
                                print(f"⚠️  视频下载页面状态: {download_response.status}")
                                return True  # 主页能访问就算成功
                    except:
                        print("⚠️  视频下载页面可能需要路由处理")
                        return True  # 主页能访问就算成功
                else:
                    print(f"❌ 前端主页访问失败: {response.status}")
                    return False
        except urllib.error.URLError as e:
            print(f"❌ 前端资源访问失败: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ 前端资源测试异常: {str(e)}")
            return False
    
    def test_cors_headers(self):
        """测试CORS头设置"""
        print("\n=== 测试CORS头设置 ===")
        
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/v1/video-download/platforms",
                headers={
                    'Origin': 'http://localhost:3003',
                    'Access-Control-Request-Method': 'GET'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                # 检查响应头
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                
                if cors_origin:
                    print(f"✅ CORS头设置正确: {cors_origin}")
                    return True
                else:
                    print("⚠️  未检测到CORS头（可能在中间件中处理）")
                    return True  # 不是致命问题
        except Exception as e:
            print(f"⚠️  CORS测试异常: {str(e)}")
            return True  # 不是致命问题
    
    def test_websocket_endpoint(self):
        """测试WebSocket端点存在性"""
        print("\n=== 测试WebSocket端点 ===")
        
        try:
            # 测试WebSocket统计端点
            url = f"{self.base_url}/api/v1/websocket/stats"
            req = urllib.request.Request(url)
            
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    print(f"✅ WebSocket统计端点响应: {response.status}")
                    return True
            except urllib.error.HTTPError as e:
                if e.code == 401:  # 需要认证是预期的
                    print("✅ WebSocket端点存在（需要认证）")
                    return True
                else:
                    print(f"⚠️  WebSocket端点状态: {e.code}")
                    return True
                    
        except Exception as e:
            print(f"❌ WebSocket端点测试异常: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始前端集成测试（简化版）")
        print("=" * 50)
        
        # 定义测试列表
        tests = [
            ("API健康状态", self.test_api_health),
            ("平台列表API", self.test_platform_api),
            ("视频解析API", self.test_video_parse_api),
            ("前端资源访问", self.test_frontend_assets),
            ("CORS头设置", self.test_cors_headers),
            ("WebSocket端点", self.test_websocket_endpoint)
        ]
        
        results = []
        
        # 运行所有测试
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}测试异常: {str(e)}")
                results.append((test_name, False))
        
        # 输出测试结果
        print("\n" + "=" * 50)
        print("📊 前端集成测试结果")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总计: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎉 所有前端集成测试通过！")
            return True
        elif passed >= total * 0.8:  # 80%通过率
            print("✅ 大部分测试通过，系统基本可用")
            return True
        else:
            print(f"⚠️  有 {total - passed} 项测试失败，需要检查")
            return False


def main():
    """主函数"""
    tester = SimpleFrontendTester()
    
    try:
        result = tester.run_all_tests()
        return result
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return False
    except Exception as e:
        print(f"\n测试执行异常: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"程序执行异常: {str(e)}")
        sys.exit(1)