#!/usr/bin/env python3
"""
调试流式响应的详细测试脚本

专门用于调试流式响应过早结束的问题
"""

import requests
import json
import time
import sys
from urllib3.exceptions import ProtocolError
from requests.exceptions import ChunkedEncodingError

def test_stream_with_debug():
    """带详细调试信息的流式测试"""
    print("🔧 流式响应调试测试")
    print("=" * 40)
    
    # 1. 测试基本连接
    print("🌐 测试基本连接...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ 基本连接成功: {response.status_code}")
    except Exception as e:
        print(f"❌ 基本连接失败: {e}")
        return
    
    # 2. 启动分析任务
    payload = {
        "video_file_id": 4,
        "template_id": None,
        "tag_group_ids": [],
        "custom_prompt": "测试调试信息",
        "ai_config_id": 1
    }
    
    print("\n🚀 启动分析任务...")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/video-analysis/start",
            json=payload,
            timeout=10
        )
        
        print(f"启动响应状态: {response.status_code}")
        print(f"启动响应内容: {response.text[:200]}")
        
        if response.status_code != 200:
            print(f"❌ 启动失败")
            return
        
        data = response.json()
        analysis_id = data.get('data', {}).get('analysis_id')
        print(f"✅ 分析启动成功: ID {analysis_id}")
        
    except Exception as e:
        print(f"❌ 启动异常: {e}")
        return
    
    # 3. 测试流式响应 - 使用更底层的方法
    print(f"\n📡 测试流式响应 (分析ID: {analysis_id})...")
    stream_url = f"http://localhost:8000/api/v1/video-analysis/{analysis_id}/stream"
    
    try:
        # 使用stream=True和更详细的配置
        response = requests.get(
            stream_url, 
            stream=True, 
            timeout=None,  # 不设置超时
            headers={
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }
        )
        
        print(f"流式响应状态: {response.status_code}")
        print(f"流式响应头: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ 流式连接失败")
            print(f"错误内容: {response.text}")
            return
        
        print("✅ 流式连接成功")
        
        # 使用更底层的方法读取数据
        chunk_count = 0
        total_data = ""
        
        try:
            # 逐字节读取，避免chunked encoding问题
            for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                if chunk:
                    total_data += chunk
                    
                    # 检查是否有完整的行
                    while '\n' in total_data:
                        line, total_data = total_data.split('\n', 1)
                        
                        if line.strip():
                            chunk_count += 1
                            print(f"📦 接收到数据块 #{chunk_count}: {line[:100]}{'...' if len(line) > 100 else ''}")
                            
                            # 解析SSE数据
                            if line.startswith('data: '):
                                data_str = line[6:]
                                
                                if data_str.strip() == '[DONE]':
                                    print("🏁 流式结束")
                                    return
                                
                                try:
                                    data = json.loads(data_str)
                                    event_type = data.get('type', 'unknown')
                                    
                                    print(f"   事件类型: {event_type}")
                                    
                                    if event_type == 'progress':
                                        progress = data.get('progress', 0)
                                        metadata = data.get('metadata', {})
                                        print(f"   进度: {progress}%")
                                        
                                        # 详细检查调试信息
                                        debug_fields = [
                                            'api_call_time', 'api_response_time', 'api_duration',
                                            'model_name', 'api_provider', 'request_id',
                                            'prompt_tokens', 'completion_tokens', 'total_tokens',
                                            'debug_info'
                                        ]
                                        
                                        found_fields = []
                                        for field in debug_fields:
                                            if field in metadata and metadata[field] is not None:
                                                found_fields.append(f"{field}={metadata[field]}")
                                        
                                        if found_fields:
                                            print(f"   🐛 调试信息: {'; '.join(found_fields[:3])}")
                                            if 'debug_info' in metadata and metadata['debug_info']:
                                                debug_info = metadata['debug_info']
                                                if isinstance(debug_info, dict):
                                                    status = debug_info.get('status', 'N/A')
                                                    print(f"   🔍 调试状态: {status}")
                                        else:
                                            print(f"   ⚠️ 无调试信息")
                                    
                                    elif event_type == 'content':
                                        content = data.get('content', '')
                                        print(f"   内容: {len(content)} 字符")
                                    
                                    elif event_type == 'complete':
                                        print(f"   ✅ 完成")
                                        return
                                    
                                    elif event_type == 'error':
                                        error_msg = data.get('content', 'Unknown error')
                                        print(f"   ❌ 错误: {error_msg}")
                                        return
                                
                                except json.JSONDecodeError as e:
                                    print(f"   ⚠️ JSON解析失败: {e}")
                                    print(f"   原始数据: {data_str}")
                        
                        # 限制测试
                        if chunk_count >= 30:
                            print(f"⏰ 达到测试限制，停止接收")
                            return
        
        except (ProtocolError, ChunkedEncodingError) as e:
            print(f"❌ 协议错误: {e}")
            print(f"已接收数据块: {chunk_count}")
            if total_data:
                print(f"缓冲区剩余数据: {total_data[:200]}")
        
        except Exception as e:
            print(f"❌ 读取异常: {e}")
            print(f"异常类型: {type(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"\n📊 测试总结:")
        print(f"  - 接收数据块: {chunk_count}")
        
    except Exception as e:
        print(f"❌ 流式测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stream_with_debug()