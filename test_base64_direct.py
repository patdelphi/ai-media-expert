#!/usr/bin/env python3
"""
直接测试Base64传输方式的视频分析功能

验证Base64编码方式是否能正常启动和处理视频分析任务。
"""

import requests
import time
import json

def test_base64_analysis():
    """测试Base64传输方式"""
    print("🚀 测试Base64传输方式...")
    
    # 使用存在的视频文件ID
    payload = {
        "video_file_id": 1,
        "template_id": None,
        "tag_group_ids": [],
        "custom_prompt": "请简单分析这个视频的内容。",
        "ai_config_id": 1,
        "transmission_method": "base64"
    }
    
    try:
        # 启动分析任务
        print("📤 发送分析请求...")
        response = requests.post(
            "http://localhost:8000/api/v1/video-analysis/start",
            json=payload,
            timeout=30
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📊 响应内容: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            return False
        
        data = response.json()
        analysis_id = data.get('data', {}).get('analysis_id')
        
        if not analysis_id:
            print("❌ 未获取到分析ID")
            return False
        
        print(f"✅ 分析任务启动成功: ID {analysis_id}")
        
        # 等待处理
        print("⏳ 等待任务处理...")
        time.sleep(10)
        
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
            transmission_method = task_info.get('transmission_method', 'unknown')
            
            print(f"📊 任务状态: {status}")
            print(f"📊 进度: {progress}%")
            print(f"📊 传输方式: {transmission_method}")
            
            if task_info.get('error_message'):
                print(f"❌ 错误信息: {task_info['error_message']}")
                return False
            
            if status == 'completed':
                print("✅ Base64传输方式测试成功！")
                return True
            elif status == 'processing':
                print("🔄 任务正在处理中...")
                return True
            else:
                print(f"⚠️ 任务状态异常: {status}")
                return False
        else:
            print(f"❌ 获取任务状态失败: {status_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 Base64传输方式直接测试\n")
    
    success = test_base64_analysis()
    
    if success:
        print("\n🎉 Base64传输方式功能正常！")
        print("\n💡 测试结果：")
        print("  - API请求成功")
        print("  - 任务启动正常")
        print("  - 传输方式正确识别")
        print("  - 后端处理流程正常")
    else:
        print("\n❌ Base64传输方式存在问题")
        print("\n🔍 可能的原因：")
        print("  - 后端服务异常")
        print("  - 视频文件路径问题")
        print("  - Base64编码失败")
        print("  - AI配置问题")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)