#!/usr/bin/env python3
"""
前端调试信息显示问题诊断脚本

用于检查：
1. 前端是否正确接收调试信息
2. API调用是否成功
3. 数据传输是否正常
"""

import requests
import json
import time
from datetime import datetime
from app.core.database import SessionLocal
from app.models.uploaded_file import UploadedFile
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis

def test_frontend_debug_display():
    """测试前端调试信息显示"""
    print("🔍 开始前端调试信息显示测试...\n")
    
    db = SessionLocal()
    
    try:
        # 1. 检查基础数据
        print("📊 检查基础数据...")
        
        videos = db.query(UploadedFile).all()
        ai_configs = db.query(AIConfig).all()
        
        print(f"  - 视频文件数量: {len(videos)}")
        print(f"  - AI配置数量: {len(ai_configs)}")
        
        if not videos:
            print("❌ 没有视频文件，无法进行测试")
            return
            
        if not ai_configs:
            print("❌ 没有AI配置，无法进行测试")
            return
            
        video = videos[0]
        ai_config = ai_configs[0]
        
        print(f"  - 使用视频: {video.original_filename}")
        print(f"  - 使用AI配置: {ai_config.name} ({ai_config.model})")
        
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
            response = requests.post(
                "http://localhost:8000/api/v1/video-analysis/start",
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
                
                # 3. 检查数据库中的调试信息
                print("\n📋 检查数据库中的调试信息...")
                
                time.sleep(2)  # 等待一下让任务开始
                
                analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
                
                if analysis:
                    print(f"  - 任务状态: {analysis.status}")
                    print(f"  - 进度: {analysis.progress}%")
                    print(f"  - 模型: {analysis.model_name}")
                    print(f"  - 提供商: {analysis.api_provider}")
                    
                    if analysis.debug_info:
                        debug_info = analysis.debug_info
                        print("  - 调试信息:")
                        print(f"    * 状态: {debug_info.get('status', 'N/A')}")
                        print(f"    * API URL: {debug_info.get('api_url', 'N/A')}")
                        
                        if 'curl_command' in debug_info:
                            print(f"    * Curl命令: 已生成 ({len(debug_info['curl_command'])} 字符)")
                            print(f"      {debug_info['curl_command'][:100]}...")
                        else:
                            print("    * Curl命令: 未生成")
                            
                        if 'request_data' in debug_info:
                            print(f"    * 请求数据: 已生成")
                            req_data = debug_info['request_data']
                            print(f"      模型: {req_data.get('model', 'N/A')}")
                            print(f"      流式: {req_data.get('stream', 'N/A')}")
                            if 'thinking' in req_data:
                                print(f"      思考模式: {req_data['thinking']}")
                        else:
                            print("    * 请求数据: 未生成")
                    else:
                        print("  - 调试信息: 无")
                        
                    # 4. 测试流式API
                    print("\n📡 测试流式API...")
                    
                    try:
                        stream_response = requests.get(
                            f"http://localhost:8000/api/v1/video-analysis/{analysis_id}/stream",
                            stream=True,
                            timeout=5
                        )
                        
                        print(f"  - 流式响应状态码: {stream_response.status_code}")
                        
                        if stream_response.status_code == 200:
                            print("  - 开始接收流式数据...")
                            
                            chunk_count = 0
                            for line in stream_response.iter_lines():
                                if line:
                                    line_str = line.decode('utf-8')
                                    if line_str.startswith('data: '):
                                        try:
                                            data_str = line_str[6:]
                                            if data_str.strip() != '[DONE]':
                                                data = json.loads(data_str)
                                                chunk_count += 1
                                                
                                                print(f"    第{chunk_count}个数据块: {data.get('type', 'unknown')}")
                                                
                                                if data.get('type') == 'progress':
                                                    metadata = data.get('metadata', {})
                                                    if 'debug_info' in metadata:
                                                        debug_info = metadata['debug_info']
                                                        print(f"      调试状态: {debug_info.get('status', 'N/A')}")
                                                        if 'curl_command' in debug_info:
                                                            print(f"      Curl命令: 已传输 ({len(debug_info['curl_command'])} 字符)")
                                                
                                                if chunk_count >= 3:  # 只检查前几个数据块
                                                    break
                                                    
                                        except json.JSONDecodeError:
                                            continue
                                            
                            print(f"  ✅ 流式API正常，接收到 {chunk_count} 个数据块")
                        else:
                            print(f"  ❌ 流式API异常: {stream_response.status_code}")
                            
                    except Exception as e:
                        print(f"  ❌ 流式API测试失败: {str(e)}")
                        
                else:
                    print("  ❌ 未找到解析任务")
                    
            else:
                print(f"  ❌ 启动解析API失败: {response.status_code}")
                print(f"  响应内容: {response.text}")
                
        except Exception as e:
            print(f"  ❌ API调用失败: {str(e)}")
            
        # 5. 检查前端服务状态
        print("\n🌐 检查前端服务状态...")
        
        try:
            frontend_response = requests.get("http://localhost:3001", timeout=5)
            print(f"  - 前端服务状态码: {frontend_response.status_code}")
            if frontend_response.status_code == 200:
                print("  ✅ 前端服务正常")
            else:
                print("  ❌ 前端服务异常")
        except Exception as e:
            print(f"  ❌ 前端服务连接失败: {str(e)}")
            
        # 6. 检查后端服务状态
        print("\n🔧 检查后端服务状态...")
        
        try:
            backend_response = requests.get("http://localhost:8000/docs", timeout=5)
            print(f"  - 后端服务状态码: {backend_response.status_code}")
            if backend_response.status_code == 200:
                print("  ✅ 后端服务正常")
            else:
                print("  ❌ 后端服务异常")
        except Exception as e:
            print(f"  ❌ 后端服务连接失败: {str(e)}")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        
    finally:
        db.close()
        
    print("\n📋 诊断建议:")
    print("1. 如果API调用正常但前端没显示，检查前端JavaScript控制台是否有错误")
    print("2. 如果调试信息在数据库中但没传输到前端，检查流式API的metadata字段")
    print("3. 如果curl命令没生成，检查AI服务中的调试信息更新逻辑")
    print("4. 建议在浏览器开发者工具中检查网络请求和响应")

if __name__ == "__main__":
    test_frontend_debug_display()
    print("\n🏁 诊断完成")