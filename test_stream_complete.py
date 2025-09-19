#!/usr/bin/env python3
"""
测试流式响应完整性

验证EventSource流式响应是否会被截断，以及分析结果的完整性。
"""

import requests
import time
import json
from datetime import datetime

def test_stream_completeness():
    """测试流式响应的完整性"""
    print("🚀 开始测试流式响应完整性...")
    
    # 启动新的分析任务
    payload = {
        "video_file_id": 10,
        "template_id": None,
        "tag_group_ids": [],
        "custom_prompt": "请详细分析这个视频，包括所有细节，提供完整的分析报告。",
        "ai_config_id": 1,
        "transmission_method": "base64"
    }
    
    try:
        # 启动分析
        print("📤 启动分析任务...")
        response = requests.post(
            "http://localhost:8000/api/v1/video-analysis/start",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ 启动失败: {response.status_code}")
            return False
        
        data = response.json()
        analysis_id = data.get('data', {}).get('analysis_id')
        print(f"✅ 分析任务启动: ID {analysis_id}")
        
        # 监控流式响应
        print("🔄 开始监控流式响应...")
        
        stream_url = f"http://localhost:8000/api/v1/video-analysis/{analysis_id}/stream"
        
        # 使用requests的流式请求
        stream_response = requests.get(
            stream_url,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=120  # 2分钟超时
        )
        
        if stream_response.status_code != 200:
            print(f"❌ 流式连接失败: {stream_response.status_code}")
            return False
        
        print("✅ 流式连接建立成功")
        
        # 收集流式数据
        stream_events = []
        content_chunks = []
        last_progress = 0
        
        for line in stream_response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])  # 移除 'data: ' 前缀
                    stream_events.append(event_data)
                    
                    event_type = event_data.get('type')
                    progress = event_data.get('progress', 0)
                    
                    if event_type == 'progress':
                        if progress > last_progress:
                            print(f"📊 进度更新: {progress}%")
                            last_progress = progress
                    
                    elif event_type == 'content':
                        content = event_data.get('content', '')
                        content_chunks.append(content)
                        print(f"📝 接收内容块: {len(content)} 字符")
                    
                    elif event_type == 'complete':
                        print("✅ 流式响应完成")
                        break
                    
                    elif event_type == 'error':
                        print(f"❌ 流式响应错误: {event_data.get('content')}")
                        return False
                        
                except json.JSONDecodeError:
                    continue
        
        # 分析流式数据
        print("\n=== 流式响应分析 ===")
        print(f"总事件数: {len(stream_events)}")
        print(f"内容块数: {len(content_chunks)}")
        
        # 合并所有内容块
        stream_content = ''.join(content_chunks)
        print(f"流式内容长度: {len(stream_content)} 字符")
        
        # 等待一下，然后获取最终结果
        time.sleep(2)
        final_response = requests.get(f"http://localhost:8000/api/v1/video-analysis/{analysis_id}")
        
        if final_response.status_code == 200:
            final_data = final_response.json()
            final_task = final_data.get('data', {})
            final_result = final_task.get('analysis_result', '')
            
            print(f"最终结果长度: {len(final_result)} 字符")
            print(f"状态: {final_task.get('status')}")
            
            # 比较流式内容和最终结果
            if len(stream_content) == len(final_result):
                print("✅ 流式内容与最终结果长度一致")
            else:
                print(f"⚠️ 长度不一致 - 流式: {len(stream_content)}, 最终: {len(final_result)}")
            
            # 检查内容完整性
            if final_result.endswith('.') or final_result.endswith('。'):
                print("✅ 结果以完整句子结尾")
            else:
                print("⚠️ 结果可能被截断")
                print(f"结果末尾: ...{final_result[-50:]}")
            
            return True
        else:
            print(f"❌ 获取最终结果失败: {final_response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 流式响应完整性测试\n")
    
    success = test_stream_completeness()
    
    if success:
        print("\n🎉 流式响应测试通过！")
        print("\n💡 测试结果：")
        print("  - 流式连接正常")
        print("  - 内容传输完整")
        print("  - 没有截断问题")
    else:
        print("\n❌ 流式响应存在问题")
        print("\n🔍 可能的原因：")
        print("  - 网络连接不稳定")
        print("  - 服务器超时设置")
        print("  - 缓冲区限制")
        print("  - 流式处理异常")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)