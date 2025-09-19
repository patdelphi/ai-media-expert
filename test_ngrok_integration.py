#!/usr/bin/env python3
"""
ngrok集成测试脚本

测试GLM-4.5V视频理解模型与ngrok公网访问的完整集成功能。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import requests
import json
from pathlib import Path
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.video import UploadedFile, AIConfig
from app.models.video_analysis import VideoAnalysis
from app.core.logging import setup_logging

def test_configuration():
    """测试配置是否正确"""
    print("🔧 测试配置...")
    
    # 检查基础URL配置
    base_url = settings.get_base_url()
    print(f"📍 基础URL: {base_url}")
    print(f"🌐 ngrok URL: {settings.ngrok_url}")
    print(f"🔗 公网URL: {settings.public_base_url}")
    
    # 检查是否使用公网地址
    if base_url.startswith('https://') and ('ngrok' in base_url or settings.public_base_url):
        print("✅ 配置正确：使用公网地址")
        return True
    elif base_url.startswith('http://localhost'):
        print("⚠️  警告：使用本地地址，GLM模型可能无法访问")
        return False
    else:
        print(f"❓ 未知配置：{base_url}")
        return False

def test_video_file_access():
    """测试视频文件访问"""
    print("\n📁 测试视频文件访问...")
    
    db = SessionLocal()
    try:
        # 获取最新的视频文件
        video_file = db.query(UploadedFile).filter(
            UploadedFile.file_type == 'video'
        ).order_by(UploadedFile.created_at.desc()).first()
        
        if not video_file:
            print("❌ 未找到视频文件，请先上传视频")
            return False
        
        print(f"📹 测试视频: {video_file.original_filename}")
        
        # 检查本地文件是否存在
        local_path = os.path.join(settings.upload_dir, video_file.saved_filename)
        if not os.path.exists(local_path):
            print(f"❌ 本地文件不存在: {local_path}")
            return False
        
        print(f"✅ 本地文件存在: {local_path}")
        
        # 生成公网URL
        base_url = settings.get_base_url()
        video_url = f"{base_url}/uploads/{video_file.saved_filename}"
        print(f"🌐 公网URL: {video_url}")
        
        # 测试URL访问
        try:
            response = requests.head(video_url, timeout=10)
            if response.status_code == 200:
                print("✅ 视频URL可访问")
                return True
            else:
                print(f"❌ 视频URL访问失败: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {str(e)}")
            return False
            
    finally:
        db.close()

def test_glm_config():
    """测试GLM配置"""
    print("\n🤖 测试GLM配置...")
    
    db = SessionLocal()
    try:
        # 查找GLM配置
        glm_config = db.query(AIConfig).filter(
            AIConfig.model.ilike('%glm-4.5v%')
        ).first()
        
        if not glm_config:
            print("❌ 未找到GLM-4.5V配置")
            print("💡 请在系统配置中添加GLM-4.5V模型配置")
            return False
        
        print(f"✅ 找到GLM配置: {glm_config.name}")
        print(f"📋 模型: {glm_config.model}")
        print(f"🔑 API密钥: {'***' + glm_config.api_key[-4:] if glm_config.api_key else 'None'}")
        print(f"🌐 API基础URL: {glm_config.api_base}")
        
        if not glm_config.api_key:
            print("❌ API密钥未配置")
            return False
        
        if not glm_config.is_active:
            print("❌ 配置未激活")
            return False
        
        return True
        
    finally:
        db.close()

def test_analysis_creation():
    """测试分析任务创建"""
    print("\n📊 测试分析任务创建...")
    
    db = SessionLocal()
    try:
        # 获取视频文件和GLM配置
        video_file = db.query(UploadedFile).filter(
            UploadedFile.file_type == 'video'
        ).order_by(UploadedFile.created_at.desc()).first()
        
        glm_config = db.query(AIConfig).filter(
            AIConfig.model.ilike('%glm-4.5v%'),
            AIConfig.is_active == True
        ).first()
        
        if not video_file or not glm_config:
            print("❌ 缺少必要的视频文件或GLM配置")
            return False
        
        # 创建测试分析任务
        analysis = VideoAnalysis(
            video_file_id=video_file.id,
            ai_config_id=glm_config.id,
            prompt_content="请分析这个视频的主要内容，包括场景、人物、动作等视觉元素。",
            status="pending"
        )
        
        db.add(analysis)
        db.commit()
        
        print(f"✅ 创建分析任务: ID {analysis.id}")
        
        # 模拟URL生成过程
        base_url = settings.get_base_url()
        video_url = f"{base_url}/uploads/{video_file.saved_filename}"
        analysis.video_url = video_url
        db.commit()
        
        print(f"🔗 生成视频URL: {video_url}")
        
        return analysis.id
        
    except Exception as e:
        print(f"❌ 创建分析任务失败: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

def test_api_endpoint():
    """测试API端点"""
    print("\n🔌 测试API端点...")
    
    try:
        # 测试后端健康检查
        base_url = settings.get_base_url()
        health_url = f"{base_url}/health"
        
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ 后端服务正常: {health_url}")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接后端服务: {str(e)}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n📋 生成测试报告...")
    
    report = {
        "configuration": test_configuration(),
        "video_access": test_video_file_access(),
        "glm_config": test_glm_config(),
        "api_endpoint": test_api_endpoint()
    }
    
    analysis_id = test_analysis_creation()
    report["analysis_creation"] = analysis_id is not None
    
    # 统计结果
    passed = sum(1 for result in report.values() if result)
    total = len(report)
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    for test_name, result in report.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！ngrok集成配置正确")
        print("\n💡 使用建议：")
        print("1. 确保ngrok隧道保持运行")
        print("2. 使用GLM-4.5V模型进行视频分析")
        print("3. 查看调试信息确认使用'视频内容理解模式'")
    else:
        print("⚠️  部分测试失败，请检查配置")
        print("\n🔧 故障排除：")
        if not report["configuration"]:
            print("- 检查.env文件中的NGROK_URL配置")
            print("- 确保ngrok隧道正在运行")
        if not report["video_access"]:
            print("- 检查视频文件是否存在")
            print("- 验证静态文件服务配置")
        if not report["glm_config"]:
            print("- 在系统配置中添加GLM-4.5V模型")
            print("- 配置正确的API密钥")
        if not report["api_endpoint"]:
            print("- 检查后端服务是否运行")
            print("- 验证网络连接")
    
    return report

def main():
    """主函数"""
    print("🧪 ngrok集成测试")
    print("=" * 50)
    
    # 设置日志
    setup_logging()
    
    try:
        report = generate_test_report()
        
        # 保存测试报告
        report_file = "ngrok_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 测试报告已保存: {report_file}")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()