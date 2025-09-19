#!/usr/bin/env python3
"""
本地API测试脚本

直接测试本地API，绕过代理问题
"""

import requests
import json
import os
from app.core.database import SessionLocal
from app.models.uploaded_file import UploadedFile
from app.models.video import AIConfig

def test_local_api():
    """测试本地API"""
    print("🧪 开始本地API测试...\n")
    
    # 设置环境变量，禁用代理
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    if 'HTTP_PROXY' in os.environ:
        del os.environ['HTTP_PROXY']
    if 'HTTPS_PROXY' in os.environ:
        del os.environ['HTTPS_PROXY']
    
    db = SessionLocal()
    
    try:
        # 获取测试数据
        video = db.query(UploadedFile).first()
        ai_config = db.query(AIConfig).first()
        
        if not video or not ai_config:
            print("❌ 缺少测试数据")
            return
            
        print(f"📹 视频: {video.original_filename}")
        print(f"🤖 AI配置: {ai_config.name}")
        
        # 1. 测试后端健康检查
        print("\n🔧 测试后端健康检查...")
        
        try:
            # 使用session禁用代理
            session = requests.Session()
            session.trust_env = False  # 禁用环境变量代理
            
            health_response = session.get("http://127.0.0.1:8000/", timeout=5)
            print(f"  - 健康检查状态码: {health_response.status_code}")
            
            if health_response.status_code == 200:
                print("  ✅ 后端服务正常")
            else:
                print("  ❌ 后端服务异常")
                return
                
        except Exception as e:
            print(f"  ❌ 后端连接失败: {str(e)}")
            return
            
        # 2. 测试启动解析API
        print("\n🚀 测试启动解析API...")
        
        start_payload = {
            "video_file_id": video.id,
            "template_id": None,
            "tag_group_ids": [],
            "custom_prompt": "请分析这个视频的内容。",
            "ai_config_id": ai_config.id
        }
        
        try:
            response = session.post(
                "http://127.0.0.1:8000/api/v1/video-analysis/start",
                json=start_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"  - 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                analysis_id = result["data"]["analysis_id"]
                print(f"  - 解析任务ID: {analysis_id}")
                print("  ✅ 启动解析API正常")
                
                # 3. 测试获取解析结果API
                print("\n📋 测试获取解析结果API...")
                
                import time
                time.sleep(3)  # 等待任务开始
                
                result_response = session.get(
                    f"http://127.0.0.1:8000/api/v1/video-analysis/{analysis_id}",
                    timeout=5
                )
                
                print(f"  - 结果API状态码: {result_response.status_code}")
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    analysis_data = result_data["data"]
                    
                    print(f"  - 任务状态: {analysis_data['status']}")
                    print(f"  - 进度: {analysis_data['progress']}%")
                    
                    if analysis_data.get('debug_info'):
                        debug_info = analysis_data['debug_info']
                        print("  - 调试信息:")
                        print(f"    * 状态: {debug_info.get('status', 'N/A')}")
                        print(f"    * API URL: {debug_info.get('api_url', 'N/A')}")
                        
                        if 'curl_command' in debug_info:
                            print(f"    * Curl命令: 已生成 ({len(debug_info['curl_command'])} 字符)")
                            print(f"      {debug_info['curl_command'][:150]}...")
                        else:
                            print("    * Curl命令: 未生成")
                            
                        if 'request_data' in debug_info:
                            req_data = debug_info['request_data']
                            print(f"    * 请求格式: {req_data.get('model', 'N/A')}")
                            if 'thinking' in req_data:
                                print(f"    * 思考模式: 已启用")
                        else:
                            print("    * 请求数据: 未生成")
                    else:
                        print("  - 调试信息: 无")
                        
                    print("  ✅ 获取解析结果API正常")
                else:
                    print(f"  ❌ 获取解析结果API异常: {result_response.status_code}")
                    
                # 4. 测试流式API（简单测试）
                print("\n📡 测试流式API...")
                
                try:
                    stream_response = session.get(
                        f"http://127.0.0.1:8000/api/v1/video-analysis/{analysis_id}/stream",
                        stream=True,
                        timeout=5
                    )
                    
                    print(f"  - 流式API状态码: {stream_response.status_code}")
                    
                    if stream_response.status_code == 200:
                        print("  ✅ 流式API连接正常")
                        
                        # 读取前几行数据
                        line_count = 0
                        for line in stream_response.iter_lines():
                            if line:
                                line_str = line.decode('utf-8')
                                if line_str.startswith('data: '):
                                    line_count += 1
                                    print(f"    第{line_count}行: {line_str[:80]}...")
                                    
                                    if line_count >= 3:  # 只读前3行
                                        break
                    else:
                        print(f"  ❌ 流式API异常: {stream_response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ 流式API测试失败: {str(e)}")
                    
            else:
                print(f"  ❌ 启动解析API失败: {response.status_code}")
                print(f"  响应内容: {response.text[:200]}...")
                
        except Exception as e:
            print(f"  ❌ API调用失败: {str(e)}")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        
    finally:
        db.close()
        
    print("\n📋 测试总结:")
    print("- 如果API调用正常，问题可能在前端JavaScript")
    print("- 如果调试信息存在但前端没显示，检查前端数据处理逻辑")
    print("- 建议检查浏览器开发者工具的控制台和网络面板")

if __name__ == "__main__":
    test_local_api()
    print("\n🏁 测试完成")