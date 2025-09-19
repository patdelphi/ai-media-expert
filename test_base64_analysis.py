#!/usr/bin/env python3
"""
测试Base64视频分析功能

创建一个完整的视频分析任务，测试Base64编码方式是否能正常工作。
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.uploaded_file import UploadedFile
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis
from app.services.ai_service import ai_service
from app.core.logging import api_logger

def create_test_analysis():
    """创建测试分析任务"""
    print("=== 创建测试分析任务 ===")
    
    db = SessionLocal()
    
    try:
        # 查找视频文件（通过文件扩展名判断）
        video_file = db.query(UploadedFile).filter(
            UploadedFile.original_filename.ilike('%.mp4')
        ).first()
        
        if not video_file:
            print("❌ 没有找到视频文件")
            return None
        
        print(f"✅ 找到视频文件: {video_file.original_filename}")
        print(f"📁 文件路径: {video_file.file_path}")
        
        # 查找GLM配置
        ai_config = db.query(AIConfig).filter(
            AIConfig.model.ilike('%glm%'),
            AIConfig.is_active == True
        ).first()
        
        if not ai_config:
            print("❌ 没有找到GLM AI配置")
            return None
        
        print(f"✅ 找到AI配置: {ai_config.name} ({ai_config.model})")
        
        # 创建分析任务
        analysis = VideoAnalysis(
            video_file_id=video_file.id,
            ai_config_id=ai_config.id,
            prompt_content="请分析这个视频的内容，包括场景、人物、动作等视觉元素。",
            status="pending",
            video_file_path=video_file.file_path,  # 设置文件路径用于Base64编码
            # 故意不设置video_url，强制使用Base64方式
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        print(f"✅ 创建分析任务: ID {analysis.id}")
        print(f"📝 提示词: {analysis.prompt_content}")
        print(f"🎯 强制使用Base64编码（未设置video_url）")
        
        return analysis.id
        
    except Exception as e:
        print(f"❌ 创建分析任务失败: {e}")
        db.rollback()
        return None
    finally:
        db.close()

async def test_base64_analysis(analysis_id: int):
    """测试Base64分析功能"""
    print(f"\n=== 测试Base64分析功能 (ID: {analysis_id}) ===")
    
    db = SessionLocal()
    
    try:
        # 获取分析任务
        analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            print(f"❌ 分析任务 {analysis_id} 不存在")
            return False
        
        # 获取AI配置
        ai_config = db.query(AIConfig).filter(
            AIConfig.id == analysis.ai_config_id
        ).first()
        
        if not ai_config:
            print("❌ AI配置不存在")
            return False
        
        print(f"🤖 AI配置: {ai_config.name}")
        print(f"📁 视频文件路径: {analysis.video_file_path}")
        print(f"🔗 视频URL: {analysis.video_url or '未设置（将使用Base64）'}")
        
        # 更新分析状态
        analysis.status = "processing"
        analysis.started_at = datetime.now()
        db.commit()
        
        print("\n🔄 开始AI分析...")
        
        # 调用AI服务
        full_content = ""
        chunk_count = 0
        
        async for chunk in ai_service.call_ai_api(
            ai_config=ai_config,
            prompt=analysis.prompt_content,
            analysis=analysis,
            db=db
        ):
            if chunk:
                full_content += chunk
                chunk_count += 1
                
                # 显示前几个chunk的内容
                if chunk_count <= 3:
                    print(f"📦 Chunk {chunk_count}: {chunk[:100]}...")
                elif chunk_count == 4:
                    print("📦 ... (更多chunks)")
        
        print(f"\n✅ 分析完成！")
        print(f"📊 总chunks: {chunk_count}")
        print(f"📏 内容长度: {len(full_content)} 字符")
        
        # 显示分析结果摘要
        if full_content:
            print(f"\n📋 分析结果摘要:")
            print(f"{full_content[:500]}..." if len(full_content) > 500 else full_content)
        
        # 更新分析结果
        analysis.status = "completed"
        analysis.analysis_result = full_content
        analysis.result_summary = full_content[:200] + "..." if len(full_content) > 200 else full_content
        analysis.completed_at = datetime.now()
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        
        # 更新失败状态
        if 'analysis' in locals():
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
        
        return False
    finally:
        db.close()

def verify_analysis_result(analysis_id: int):
    """验证分析结果"""
    print(f"\n=== 验证分析结果 (ID: {analysis_id}) ===")
    
    db = SessionLocal()
    
    try:
        analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            print(f"❌ 分析任务 {analysis_id} 不存在")
            return False
        
        print(f"📊 任务状态: {analysis.status}")
        print(f"⏱️ 开始时间: {analysis.started_at}")
        print(f"⏱️ 完成时间: {analysis.completed_at}")
        
        if analysis.status == "completed":
            print(f"✅ 分析成功完成")
            print(f"📝 结果摘要: {analysis.result_summary}")
            
            if hasattr(analysis, 'debug_info') and analysis.debug_info:
                debug_info = analysis.debug_info
                print(f"🔧 调试信息:")
                print(f"  模型: {debug_info.get('model', 'N/A')}")
                print(f"  提供商: {debug_info.get('provider', 'N/A')}")
                if 'response_info' in debug_info:
                    resp_info = debug_info['response_info']
                    print(f"  状态码: {resp_info.get('status_code', 'N/A')}")
                    print(f"  内容长度: {resp_info.get('content_length', 'N/A')}")
            
            return True
        elif analysis.status == "failed":
            print(f"❌ 分析失败")
            print(f"💥 错误信息: {analysis.error_message}")
            return False
        else:
            print(f"⏳ 分析状态: {analysis.status}")
            return False
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        db.close()

async def main():
    """主函数"""
    print("🚀 开始Base64视频分析测试\n")
    
    # 创建测试分析任务
    analysis_id = create_test_analysis()
    if not analysis_id:
        print("❌ 无法创建测试任务，终止测试")
        return False
    
    # 测试Base64分析
    analysis_success = await test_base64_analysis(analysis_id)
    
    # 验证结果
    verification_success = verify_analysis_result(analysis_id)
    
    # 总结
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print(f"创建任务: {'✅ 成功' if analysis_id else '❌ 失败'}")
    print(f"Base64分析: {'✅ 成功' if analysis_success else '❌ 失败'}")
    print(f"结果验证: {'✅ 成功' if verification_success else '❌ 失败'}")
    
    overall_success = analysis_id and analysis_success and verification_success
    
    if overall_success:
        print("\n🎉 Base64视频分析功能测试成功！")
        print("\n💡 功能特点：")
        print("  - 自动检测URL不可用时回退到Base64编码")
        print("  - 支持ffmpeg压缩减小文件大小")
        print("  - 完整的错误处理和日志记录")
        print("  - 与现有系统无缝集成")
    else:
        print("\n⚠️ Base64视频分析功能存在问题")
        print("\n🔍 可能的原因：")
        print("  - AI API配置问题")
        print("  - 网络连接问题")
        print("  - 视频文件格式不支持")
        print("  - Base64编码失败")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)