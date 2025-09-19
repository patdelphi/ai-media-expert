#!/usr/bin/env python3
"""
简化的流式响应测试脚本

专门测试视频分析的流式响应是否正常工作
"""

import requests
import json
import time

def test_simple_stream():
    """简单的流式响应测试"""
    print("🧪 简化流式响应测试")
    print("=" * 30)
    
    # 1. 启动分析任务
    payload = {
        "video_file_id": 4,  # 使用已知的视频ID
        "template_id": None,
        "tag_group_ids": [],
        "custom_prompt": "简单测试",
        "ai_config_id": 1  # 使用已知的AI配置ID
    }
    
    print("🚀 启动分析任务...")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/video-analysis/start",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 启动失败: {response.status_code}")
            print(f"响应: {response.text}")
            return
        
        data = response.json()
        analysis_id = data.get('data', {}).get('analysis_id')
        print(f"✅ 分析启动成功: ID {analysis_id}")
        
    except Exception as e:
        print(f"❌ 启动异常: {e}")
        return
    
    # 2. 测试流式响应
    print(f"\n📡 测试流式响应...")
    stream_url = f"http://localhost:8000/api/v1/video-analysis/{analysis_id}/stream"
    
    try:
        # 使用更长的超时时间
        response = requests.get(stream_url, stream=True, timeout=60)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ 流式连接失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        print("✅ 流式连接成功，开始接收数据...")
        
        chunk_count = 0
        start_time = time.time()
        
        # 逐行读取流式数据
        for line_bytes in response.iter_lines():
            if line_bytes:
                line = line_bytes.decode('utf-8')
                chunk_count += 1
                elapsed = time.time() - start_time
                
                print(f"[{elapsed:.1f}s] 块 #{chunk_count}: {line[:100]}{'...' if len(line) > 100 else ''}")
                
                # 解析SSE数据
                if line.startswith('data: '):
                    data_str = line[6:]
                    
                    if data_str.strip() == '[DONE]':
                        print("🏁 流式结束")
                        break
                    
                    try:
                        data = json.loads(data_str)
                        event_type = data.get('type', 'unknown')
                        
                        print(f"   事件类型: {event_type}")
                        
                        if event_type == 'progress':
                            progress = data.get('progress', 0)
                            metadata = data.get('metadata', {})
                            print(f"   进度: {progress}%")
                            
                            # 检查调试信息
                            debug_keys = [k for k, v in metadata.items() if v is not None]
                            if debug_keys:
                                print(f"   调试字段: {debug_keys[:5]}")
                            else:
                                print(f"   ⚠️ 无调试信息")
                        
                        elif event_type == 'content':
                            content = data.get('content', '')
                            print(f"   内容: {len(content)} 字符")
                        
                        elif event_type == 'complete':
                            print(f"   ✅ 完成")
                            break
                        
                        elif event_type == 'error':
                            error_msg = data.get('content', 'Unknown error')
                            print(f"   ❌ 错误: {error_msg}")
                            break
                    
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️ JSON解析失败: {e}")
                        print(f"   原始数据: {data_str}")
                
                # 限制测试时间和数据量
                if elapsed > 30 or chunk_count > 50:
                    print(f"⏰ 测试超时或达到限制，停止接收")
                    break
        
        print(f"\n📊 测试总结:")
        print(f"  - 接收数据块: {chunk_count}")
        print(f"  - 总耗时: {elapsed:.1f}秒")
        
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接错误")
    except Exception as e:
        print(f"❌ 流式测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_stream()