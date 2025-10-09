#!/usr/bin/env python3
"""
诊断视频分析实时AI API调用信息显示问题

用于检查：
1. 后端是否正确发送调试信息
2. 流式响应是否包含完整的调试数据
3. 前端是否能正确接收和显示调试信息
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from app.core.database import SessionLocal
from app.models.uploaded_file import UploadedFile
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis

def check_backend_data():
    """检查后端数据状态"""
    print("🔍 检查后端数据状态...")
    
    db = SessionLocal()
    try:
        # 检查视频文件
        videos = db.query(UploadedFile).all()
        print(f"  📹 视频文件数量: {len(videos)}")
        
        if videos:
            video = videos[0]
            print(f"  📹 测试视频: {video.original_filename} (ID: {video.id})")
        
        # 检查AI配置
        ai_configs = db.query(AIConfig).all()
        print(f"  🤖 AI配置数量: {len(ai_configs)}")
        
        if ai_configs:
            ai_config = ai_configs[0]
            print(f"  🤖 测试AI配置: {ai_config.name} - {ai_config.model} (ID: {ai_config.id})")
        
        # 检查最近的分析记录
        analyses = db.query(VideoAnalysis).order_by(VideoAnalysis.created_at.desc()).limit(5).all()
        print(f"  📊 最近分析记录: {len(analyses)}")
        
        for i, analysis in enumerate(analyses):
            print(f"    {i+1}. ID:{analysis.id} 状态:{analysis.status} 进度:{analysis.progress}%")
            if analysis.debug_info:
                debug_keys = list(analysis.debug_info.keys()) if isinstance(analysis.debug_info, dict) else []
                print(f"       调试信息字段: {debug_keys[:5]}{'...' if len(debug_keys) > 5 else ''}")
            else:
                print(f"       调试信息: 无")
        
        return videos, ai_configs, analyses
        
    finally:
        db.close()

def test_api_endpoints():
    """测试API端点"""
    print("\n🌐 测试API端点...")
    
    base_url = "http://localhost:8000"
    
    # 测试基本连接
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"  ✅ 基本连接: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 基本连接失败: {e}")
        return False
    
    # 测试视频列表API
    try:
        response = requests.get(f"{base_url}/api/v1/videos", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 视频列表API: {len(data.get('data', []))} 个视频")
        else:
            print(f"  ❌ 视频列表API: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 视频列表API失败: {e}")
    
    # 测试AI配置API
    try:
        response = requests.get(f"{base_url}/api/v1/ai-configs", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ AI配置API: {len(data.get('data', []))} 个配置")
        else:
            print(f"  ❌ AI配置API: {response.status_code}")
    except Exception as e:
        print(f"  ❌ AI配置API失败: {e}")
    
    return True

def test_analysis_start(video_id, ai_config_id):
    """测试启动分析"""
    print(f"\n🚀 测试启动分析 (视频ID: {video_id}, AI配置ID: {ai_config_id})...")
    
    payload = {
        "video_file_id": video_id,
        "template_id": None,
        "tag_group_ids": [],
        "custom_prompt": "请简单分析这个视频的内容，用一句话描述即可。",
        "ai_config_id": ai_config_id
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/video-analysis/start",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            analysis_id = data.get('data', {}).get('analysis_id')
            print(f"  ✅ 分析启动成功: ID {analysis_id}")
            return analysis_id
        else:
            print(f"  ❌ 分析启动失败: {response.status_code}")
            print(f"     响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"  ❌ 分析启动异常: {e}")
        return None

def test_stream_response(analysis_id):
    """测试流式响应"""
    print(f"\n📡 测试流式响应 (分析ID: {analysis_id})...")
    
    stream_url = f"http://localhost:8000/api/v1/video-analysis/{analysis_id}/stream"
    
    try:
        response = requests.get(stream_url, stream=True, timeout=30)
        
        if response.status_code != 200:
            print(f"  ❌ 流式连接失败: {response.status_code}")
            return
        
        print(f"  ✅ 流式连接成功")
        
        chunk_count = 0
        debug_info_received = False
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                chunk_count += 1
                data_str = line[6:]
                
                if data_str.strip() == '[DONE]':
                    print(f"  🏁 流式结束")
                    break
                
                try:
                    data = json.loads(data_str)
                    event_type = data.get('type', 'unknown')
                    
                    print(f"  📦 事件 #{chunk_count}: {event_type}")
                    
                    if event_type == 'progress':
                        progress = data.get('progress', 0)
                        metadata = data.get('metadata', {})
                        print(f"     进度: {progress}%")
                        
                        # 检查调试信息
                        debug_fields = [
                            'api_call_time', 'api_response_time', 'api_duration',
                            'model_name', 'api_provider', 'request_id',
                            'prompt_tokens', 'completion_tokens', 'total_tokens',
                            'debug_info'
                        ]
                        
                        found_debug_fields = []
                        for field in debug_fields:
                            if field in metadata and metadata[field] is not None:
                                found_debug_fields.append(field)
                        
                        if found_debug_fields:
                            debug_info_received = True
                            print(f"     🐛 调试字段: {found_debug_fields}")
                            
                            # 显示关键调试信息
                            if 'debug_info' in metadata and metadata['debug_info']:
                                debug_info = metadata['debug_info']
                                if isinstance(debug_info, dict):
                                    status = debug_info.get('status', 'N/A')
                                    chunks_received = debug_info.get('chunks_received', 'N/A')
                                    print(f"     🔍 调试状态: {status}, 接收块数: {chunks_received}")
                        else:
                            print(f"     ⚠️ 未发现调试信息")
                    
                    elif event_type == 'content':
                        content = data.get('content', '')
                        print(f"     内容长度: {len(content)} 字符")
                    
                    elif event_type == 'complete':
                        print(f"     ✅ 分析完成")
                        break
                    
                    elif event_type == 'error':
                        error_msg = data.get('content', 'Unknown error')
                        print(f"     ❌ 错误: {error_msg}")
                        break
                
                except json.JSONDecodeError as e:
                    print(f"     ⚠️ JSON解析失败: {e}")
                
                # 限制测试时间
                if chunk_count >= 20:
                    print(f"  ⏰ 达到测试限制，停止监听")
                    break
        
        print(f"\n📊 流式测试总结:")
        print(f"  - 接收事件数: {chunk_count}")
        print(f"  - 调试信息接收: {'✅ 是' if debug_info_received else '❌ 否'}")
        
        return debug_info_received
        
    except Exception as e:
        print(f"  ❌ 流式测试异常: {e}")
        return False

def check_database_debug_info(analysis_id):
    """检查数据库中的调试信息"""
    print(f"\n🗄️ 检查数据库调试信息 (分析ID: {analysis_id})...")
    
    db = SessionLocal()
    try:
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
        
        if not analysis:
            print(f"  ❌ 未找到分析记录")
            return
        
        print(f"  📊 分析状态: {analysis.status}")
        print(f"  📊 进度: {analysis.progress}%")
        
        # 检查调试相关字段
        debug_fields = {
            'api_call_time': analysis.api_call_time,
            'api_response_time': analysis.api_response_time,
            'api_duration': analysis.api_duration,
            'model_name': analysis.model_name,
            'api_provider': analysis.api_provider,
            'request_id': analysis.request_id,
            'prompt_tokens': analysis.prompt_tokens,
            'completion_tokens': analysis.completion_tokens,
            'total_tokens': analysis.total_tokens,
            'debug_info': analysis.debug_info
        }
        
        print(f"  🐛 调试字段状态:")
        for field, value in debug_fields.items():
            if value is not None:
                if field == 'debug_info' and isinstance(value, dict):
                    keys = list(value.keys())[:5]
                    print(f"     ✅ {field}: {keys}{'...' if len(value) > 5 else ''}")
                else:
                    print(f"     ✅ {field}: {value}")
            else:
                print(f"     ❌ {field}: None")
        
    finally:
        db.close()

def main():
    """主测试流程"""
    print("🔧 视频分析实时调试信息诊断工具")
    print("=" * 50)
    
    # 1. 检查后端数据
    videos, ai_configs, analyses = check_backend_data()
    
    if not videos or not ai_configs:
        print("\n❌ 缺少必要的测试数据（视频文件或AI配置）")
        return
    
    # 2. 测试API端点
    if not test_api_endpoints():
        print("\n❌ API端点测试失败，请检查后端服务")
        return
    
    # 3. 启动新的分析任务
    video_id = videos[0].id
    ai_config_id = ai_configs[0].id
    
    analysis_id = test_analysis_start(video_id, ai_config_id)
    
    if not analysis_id:
        print("\n❌ 无法启动分析任务")
        return
    
    # 4. 测试流式响应
    debug_info_received = test_stream_response(analysis_id)
    
    # 5. 检查数据库中的调试信息
    time.sleep(2)  # 等待数据库更新
    check_database_debug_info(analysis_id)
    
    # 6. 总结
    print("\n" + "=" * 50)
    print("🎯 诊断总结:")
    
    if debug_info_received:
        print("  ✅ 后端正确发送调试信息")
        print("  💡 如果前端仍无法显示，请检查前端代码中的数据处理逻辑")
    else:
        print("  ❌ 后端未发送调试信息")
        print("  💡 问题可能在于:")
        print("     1. AI服务调用过程中调试信息更新失败")
        print("     2. 流式响应中调试信息字段缺失")
        print("     3. 数据库事务提交问题")
    
    print("\n🔍 建议检查:")
    print("  1. app/services/ai_service.py 中的调试信息更新逻辑")
    print("  2. app/api/v1/endpoints/video_analysis.py 中的流式响应逻辑")
    print("  3. 前端 VideoAnalysis.tsx 中的 currentDebugInfo 更新逻辑")

if __name__ == "__main__":
    main()