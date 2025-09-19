#!/usr/bin/env python3
"""
测试完整视频解析流程的脚本
"""

import requests
import json
import time
from app.core.database import SessionLocal
from app.models.uploaded_file import UploadedFile
from app.models.video import AIConfig

def test_full_analysis():
    """测试完整的视频解析流程"""
    db = SessionLocal()
    
    try:
        # 获取第一个视频文件和AI配置
        video = db.query(UploadedFile).first()
        ai_config = db.query(AIConfig).first()
        
        if not video:
            print("❌ 没有找到视频文件")
            return
            
        if not ai_config:
            print("❌ 没有找到AI配置")
            return
            
        print(f"📹 使用视频: {video.original_filename}")
        print(f"🤖 使用AI配置: {ai_config.name}")
        
        # 启动解析
        print("\n🚀 启动视频解析...")
        
        payload = {
            "video_file_id": video.id,
            "template_id": None,
            "tag_group_ids": [],
            "custom_prompt": "请分析这个视频的内容，包括视觉元素、音频特征和整体质量。",
            "ai_config_id": ai_config.id
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/video-analysis/start",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ 启动解析失败: {response.status_code}")
            print(response.text)
            return
            
        result = response.json()
        analysis_id = result["data"]["analysis_id"]
        
        print(f"✅ 解析任务已启动，ID: {analysis_id}")
        
        # 监听流式结果
        print("\n📡 开始监听流式结果...")
        
        from sseclient import SSEClient
        
        stream_url = f"http://localhost:8000/api/v1/video-analysis/{analysis_id}/stream"
        response = requests.get(stream_url, stream=True)
        
        client = SSEClient(response)
        
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    print(f"📦 收到事件: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'progress':
                        progress = data.get('progress', 0)
                        metadata = data.get('metadata', {})
                        print(f"   进度: {progress}%")
                        
                        if metadata.get('debug_info'):
                            debug_info = metadata['debug_info']
                            print(f"   调试状态: {debug_info.get('status', 'N/A')}")
                            if debug_info.get('curl_command'):
                                print(f"   Curl命令: 已生成 ({len(debug_info['curl_command'])} 字符)")
                            if debug_info.get('current_total_tokens'):
                                print(f"   当前Token: {debug_info['current_total_tokens']}")
                    
                    elif data.get('type') == 'content':
                        content = data.get('content', '')
                        print(f"   内容长度: {len(content)} 字符")
                    
                    elif data.get('type') == 'complete':
                        print("✅ 解析完成!")
                        break
                        
                    elif data.get('type') == 'error':
                        print(f"❌ 解析失败: {data.get('content', 'Unknown error')}")
                        break
                        
                except json.JSONDecodeError:
                    print(f"⚠️  无法解析事件数据: {event.data}")
                    
        # 获取最终结果
        print("\n📋 获取最终结果...")
        
        final_response = requests.get(
            f"http://localhost:8000/api/v1/video-analysis/{analysis_id}"
        )
        
        if final_response.status_code == 200:
            final_data = final_response.json()
            analysis = final_data["data"]
            
            print(f"状态: {analysis['status']}")
            print(f"进度: {analysis['progress']}%")
            
            if analysis.get('debug_info'):
                debug_info = analysis['debug_info']
                print("\n🔍 调试信息:")
                print(f"  - API状态: {debug_info.get('status', 'N/A')}")
                print(f"  - API URL: {debug_info.get('api_url', 'N/A')}")
                if debug_info.get('curl_command'):
                    print(f"  - Curl命令: 已生成 ({len(debug_info['curl_command'])} 字符)")
                    print(f"    {debug_info['curl_command'][:100]}...")
                print(f"  - 总Token: {analysis.get('total_tokens', 0)}")
            
            if analysis.get('analysis_result'):
                result_text = analysis['analysis_result']
                print(f"\n📄 结果预览: {result_text[:200]}...")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 开始完整视频解析流程测试...\n")
    test_full_analysis()
    print("\n🏁 测试完成")