#!/usr/bin/env python3
"""
测试AI API调用和调试信息的脚本

用于验证视频解析功能是否正常工作，包括：
1. 创建解析任务
2. 检查调试信息
3. 验证流式响应
"""

import asyncio
import json
from datetime import datetime
from app.core.database import SessionLocal
from app.models.uploaded_file import UploadedFile
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis
from app.services.ai_service import ai_service

async def test_ai_api_debug():
    """测试AI API调用和调试信息"""
    db = SessionLocal()
    
    try:
        # 获取第一个视频文件
        video_file = db.query(UploadedFile).first()
        if not video_file:
            print("❌ 没有找到视频文件")
            return
        
        print(f"📹 使用视频: {video_file.original_filename}")
        
        # 获取AI配置
        ai_config = db.query(AIConfig).first()
        if not ai_config:
            print("❌ 没有找到AI配置")
            return
        
        print(f"🤖 使用AI配置: {ai_config.name} ({ai_config.provider}/{ai_config.model})")
        
        # 创建解析任务
        analysis = VideoAnalysis(
            video_file_id=video_file.id,
            prompt_content="请分析这个视频的内容，包括视觉元素、音频特征和整体质量。",
            ai_config_id=ai_config.id,
            status="pending",
            progress=0
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        print(f"📝 创建解析任务: ID={analysis.id}")
        
        # 测试AI API调用
        print("\n🚀 开始AI API调用测试...")
        
        try:
            # 模拟调用AI API
            prompt = f"""请分析以下视频文件：

**视频信息：**
- 文件名: {video_file.original_filename}
- 时长: {video_file.duration or 'N/A'}秒
- 分辨率: {video_file.width}x{video_file.height} 像素
- 格式: {video_file.format_name or 'N/A'}
- 文件大小: {video_file.file_size} 字节

**分析要求：**
{analysis.prompt_content}

请根据上述视频信息和分析要求，提供详细的分析报告。输出格式为Markdown。
"""
            
            # 更新状态为处理中
            analysis.status = "processing"
            analysis.started_at = datetime.now()
            analysis.progress = 30
            db.commit()
            
            print("📊 调用AI服务...")
            
            # 调用AI API
            content_chunks = []
            async for chunk in ai_service.call_ai_api(
                ai_config=ai_config,
                prompt=prompt,
                analysis=analysis,
                db=db
            ):
                content_chunks.append(chunk)
                print(f"📦 接收到内容块: {len(chunk)} 字符")
                
                # 刷新分析对象以获取最新的调试信息
                db.refresh(analysis)
                
                # 显示调试信息
                if analysis.debug_info:
                    print(f"🔍 调试状态: {analysis.debug_info.get('status', 'N/A')}")
                    if 'curl_command' in analysis.debug_info:
                        print(f"💻 Curl命令已生成: {len(analysis.debug_info['curl_command'])} 字符")
                    if 'current_total_tokens' in analysis.debug_info:
                        print(f"🎯 当前Token: {analysis.debug_info['current_total_tokens']}")
            
            # 完成处理
            full_content = ''.join(content_chunks)
            analysis.status = "completed"
            analysis.progress = 100
            analysis.completed_at = datetime.now()
            analysis.processing_time = (analysis.completed_at - analysis.started_at).total_seconds()
            
            db.commit()
            
            print(f"\n✅ AI API调用完成!")
            print(f"📄 生成内容长度: {len(full_content)} 字符")
            print(f"⏱️  处理时间: {analysis.processing_time:.2f} 秒")
            print(f"🎯 总Token数: {analysis.total_tokens or 0}")
            
            # 显示调试信息摘要
            if analysis.debug_info:
                print("\n🔍 调试信息摘要:")
                print(f"  - API状态: {analysis.debug_info.get('status', 'N/A')}")
                print(f"  - API URL: {analysis.debug_info.get('api_url', 'N/A')}")
                print(f"  - 请求ID: {analysis.request_id}")
                print(f"  - 模型: {analysis.model_name}")
                print(f"  - 提供商: {analysis.api_provider}")
                
                if 'curl_command' in analysis.debug_info:
                    print(f"  - Curl命令: 已生成 ({len(analysis.debug_info['curl_command'])} 字符)")
                    print(f"    {analysis.debug_info['curl_command'][:100]}...")
            
            print(f"\n📋 内容预览:")
            print(full_content[:200] + "..." if len(full_content) > 200 else full_content)
            
        except Exception as e:
            print(f"❌ AI API调用失败: {str(e)}")
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.error_code = "TEST_ERROR"
            db.commit()
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 开始AI API调试测试...\n")
    asyncio.run(test_ai_api_debug())
    print("\n🏁 测试完成")