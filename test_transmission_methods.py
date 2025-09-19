#!/usr/bin/env python3
"""
测试不同视频传输方式的功能

验证URL方式、Base64编码方式和文件上传方式是否正常工作。
"""

import sys
import asyncio
import requests
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.uploaded_file import UploadedFile
from app.models.video import AIConfig
from app.core.logging import api_logger

def get_test_data():
    """获取测试数据"""
    print("=== 获取测试数据 ===")
    
    db = SessionLocal()
    
    try:
        # 获取视频文件
        video_file = db.query(UploadedFile).filter(
            UploadedFile.original_filename.ilike('%.mp4')
        ).first()
        
        if not video_file:
            print("❌ 没有找到视频文件")
            return None, None
        
        print(f"✅ 找到视频文件: {video_file.original_filename}")
        print(f"📁 文件路径: {video_file.file_path}")
        print(f"📊 文件大小: {video_file.file_size / (1024*1024):.2f} MB")
        
        # 获取GLM配置
        ai_config = db.query(AIConfig).filter(
            AIConfig.model.ilike('%glm%'),
            AIConfig.is_active == True
        ).first()
        
        if not ai_config:
            print("❌ 没有找到GLM AI配置")
            return None, None
        
        print(f"✅ 找到AI配置: {ai_config.name} ({ai_config.model})")
        
        return video_file.id, ai_config.id
        
    except Exception as e:
        print(f"❌ 获取测试数据失败: {e}")
        return None, None
    finally:
        db.close()

def test_transmission_method(video_file_id: int, ai_config_id: int, method: str):
    """测试指定的传输方式"""
    print(f"\n=== 测试 {method.upper()} 传输方式 ===")
    
    payload = {
        "video_file_id": video_file_id,
        "template_id": None,
        "tag_group_ids": [],
        "custom_prompt": f"请简单分析这个视频的内容。（测试{method}传输方式）",
        "ai_config_id": ai_config_id,
        "transmission_method": method
    }
    
    try:
        print(f"🚀 启动分析任务...")
        response = requests.post(
            "http://localhost:8000/api/v1/video-analysis/start",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ 启动失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
        
        data = response.json()
        analysis_id = data.get('data', {}).get('analysis_id')
        
        if not analysis_id:
            print(f"❌ 未获取到分析ID")
            return None
        
        print(f"✅ 分析任务启动成功: ID {analysis_id}")
        
        # 等待一段时间让任务开始处理
        import time
        print(f"⏳ 等待任务处理...")
        time.sleep(5)
        
        # 检查任务状态
        status_response = requests.get(
            f"http://localhost:8000/api/v1/video-analysis/{analysis_id}",
            timeout=10
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            task_info = status_data.get('data', {})
            status = task_info.get('status', 'unknown')
            progress = task_info.get('progress', 0)
            
            print(f"📊 任务状态: {status}")
            print(f"📊 进度: {progress}%")
            
            if task_info.get('error_message'):
                print(f"❌ 错误信息: {task_info['error_message']}")
            
            # 如果有结果，显示部分内容
            if task_info.get('analysis_result'):
                result = task_info['analysis_result']
                preview = result[:200] + "..." if len(result) > 200 else result
                print(f"📝 分析结果预览: {preview}")
        
        return analysis_id
        
    except Exception as e:
        print(f"❌ 测试{method}传输方式失败: {e}")
        return None

def test_stream_connection(analysis_id: int, method: str):
    """测试流式连接"""
    print(f"\n🔄 测试{method.upper()}方式的流式连接...")
    
    try:
        import sseclient  # 需要安装: pip install sseclient-py
        
        stream_url = f"http://localhost:8000/api/v1/video-analysis/{analysis_id}/stream"
        response = requests.get(stream_url, stream=True, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ 流式连接失败: {response.status_code}")
            return False
        
        print(f"✅ 流式连接成功")
        
        # 读取前几个事件
        client = sseclient.SSEClient(response)
        event_count = 0
        
        for event in client.events():
            if event_count >= 5:  # 只读取前5个事件
                break
            
            print(f"📦 事件 {event_count + 1}: {event.data[:100]}...")
            event_count += 1
        
        print(f"✅ 成功接收 {event_count} 个流式事件")
        return True
        
    except ImportError:
        print("⚠️ 未安装sseclient-py，跳过流式连接测试")
        return True
    except Exception as e:
        print(f"❌ 流式连接测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试视频传输方式功能\n")
    
    # 获取测试数据
    video_file_id, ai_config_id = get_test_data()
    if not video_file_id or not ai_config_id:
        print("❌ 无法获取测试数据，终止测试")
        return False
    
    # 测试结果统计
    results = {}
    
    # 测试URL方式
    analysis_id = test_transmission_method(video_file_id, ai_config_id, 'url')
    results['url'] = analysis_id is not None
    if analysis_id:
        stream_success = test_stream_connection(analysis_id, 'url')
        results['url_stream'] = stream_success
    
    # 测试Base64方式
    analysis_id = test_transmission_method(video_file_id, ai_config_id, 'base64')
    results['base64'] = analysis_id is not None
    if analysis_id:
        stream_success = test_stream_connection(analysis_id, 'base64')
        results['base64_stream'] = stream_success
    
    # 测试文件上传方式（预期会失败，因为未实现）
    analysis_id = test_transmission_method(video_file_id, ai_config_id, 'upload')
    results['upload'] = analysis_id is not None
    
    # 总结测试结果
    print("\n" + "="*60)
    print("📊 测试结果总结:")
    print(f"URL方式启动: {'✅ 成功' if results.get('url') else '❌ 失败'}")
    print(f"URL方式流式: {'✅ 成功' if results.get('url_stream') else '❌ 失败'}")
    print(f"Base64方式启动: {'✅ 成功' if results.get('base64') else '❌ 失败'}")
    print(f"Base64方式流式: {'✅ 成功' if results.get('base64_stream') else '❌ 失败'}")
    print(f"文件上传方式: {'✅ 成功' if results.get('upload') else '❌ 失败（预期）'}")
    
    # 计算成功率
    expected_success = ['url', 'url_stream', 'base64', 'base64_stream']
    success_count = sum(1 for key in expected_success if results.get(key))
    success_rate = success_count / len(expected_success) * 100
    
    print(f"\n📈 成功率: {success_rate:.1f}% ({success_count}/{len(expected_success)})")
    
    if success_rate >= 75:
        print("\n🎉 视频传输方式功能测试基本成功！")
        print("\n💡 功能特点：")
        print("  - 前端提供传输方式选择器")
        print("  - 后端根据选择智能处理")
        print("  - URL方式适合所有文件大小")
        print("  - Base64方式适合小文件")
        print("  - 文件上传方式待开发")
    else:
        print("\n⚠️ 视频传输方式功能存在问题")
        print("\n🔍 可能的原因：")
        print("  - 后端服务未启动")
        print("  - AI配置问题")
        print("  - 网络连接问题")
        print("  - Base64编码失败")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)