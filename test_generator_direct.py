#!/usr/bin/env python3
"""
直接测试流式响应生成器

不通过HTTP请求，直接测试生成器函数是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.video_analysis import VideoAnalysis
from app.schemas.video_analysis import AnalysisStreamChunk
import json
import time

def test_generator_directly():
    """直接测试生成器函数"""
    print("🧪 直接测试流式响应生成器")
    print("=" * 40)
    
    # 获取一个现有的分析记录
    db = SessionLocal()
    try:
        analysis = db.query(VideoAnalysis).order_by(VideoAnalysis.created_at.desc()).first()
        
        if not analysis:
            print("❌ 没有找到分析记录")
            return
        
        print(f"📊 使用分析记录: ID {analysis.id}, 状态: {analysis.status}")
        analysis_id = analysis.id
        
    finally:
        db.close()
    
    # 模拟生成器函数
    def test_generate_stream():
        """测试版本的生成器函数"""
        print("🔧 开始生成器测试...")
        
        from app.core.database import SessionLocal
        
        # 创建新的数据库会话用于生成器
        stream_db = SessionLocal()
        
        try:
            print("📊 创建数据库会话成功")
            
            # 重新获取分析对象
            current_analysis = stream_db.query(VideoAnalysis).filter(
                VideoAnalysis.id == analysis_id
            ).first()
            
            if not current_analysis:
                print("❌ 未找到分析记录")
                chunk = AnalysisStreamChunk(
                    type="error",
                    content="Analysis not found",
                    metadata={"error_code": "NOT_FOUND"}
                )
                yield f"data: {json.dumps(chunk.dict())}\n\n"
                return
            
            print(f"📊 获取分析记录成功: {current_analysis.status}")
            
            # 发送初始状态
            chunk = AnalysisStreamChunk(
                type="progress",
                progress=current_analysis.progress,
                metadata={"status": current_analysis.status}
            )
            yield f"data: {json.dumps(chunk.dict())}\n\n"
            print(f"✅ 发送初始状态: {current_analysis.status}")
            
            # 如果任务已完成，直接返回结果
            if current_analysis.status == "completed":
                print("📊 任务已完成，发送完成信息")
                
                if current_analysis.analysis_result:
                    chunk = AnalysisStreamChunk(
                        type="content",
                        content=current_analysis.analysis_result[:100] + "...",  # 截断内容
                        progress=100
                    )
                    yield f"data: {json.dumps(chunk.dict())}\n\n"
                    print(f"✅ 发送内容: {len(current_analysis.analysis_result)} 字符")
                
                # 发送调试信息
                debug_metadata = {
                    "status": current_analysis.status,
                    "api_call_time": current_analysis.api_call_time.isoformat() if current_analysis.api_call_time else None,
                    "api_response_time": current_analysis.api_response_time.isoformat() if current_analysis.api_response_time else None,
                    "api_duration": current_analysis.api_duration,
                    "prompt_tokens": current_analysis.prompt_tokens,
                    "completion_tokens": current_analysis.completion_tokens,
                    "total_tokens": current_analysis.total_tokens,
                    "temperature": current_analysis.temperature,
                    "max_tokens": current_analysis.max_tokens,
                    "model_name": current_analysis.model_name,
                    "api_provider": current_analysis.api_provider,
                    "request_id": current_analysis.request_id,
                    "debug_info": current_analysis.debug_info
                }
                
                chunk = AnalysisStreamChunk(
                    type="progress",
                    progress=100,
                    metadata=debug_metadata
                )
                yield f"data: {json.dumps(chunk.dict())}\n\n"
                print(f"✅ 发送调试信息")
                
                chunk = AnalysisStreamChunk(
                    type="complete",
                    progress=100,
                    metadata={
                        "confidence_score": current_analysis.confidence_score,
                        "processing_time": current_analysis.processing_time
                    }
                )
                yield f"data: {json.dumps(chunk.dict())}\n\n"
                print(f"✅ 发送完成信号")
                return
            
            # 如果任务失败，返回错误信息
            if current_analysis.status == "failed":
                print("📊 任务失败，发送错误信息")
                chunk = AnalysisStreamChunk(
                    type="error",
                    content=current_analysis.error_message or "Analysis failed",
                    metadata={"error_code": current_analysis.error_code}
                )
                yield f"data: {json.dumps(chunk.dict())}\n\n"
                return
            
            # 对于进行中的任务，模拟几次状态检查
            print(f"📊 任务进行中，模拟状态检查...")
            for i in range(3):
                try:
                    # 刷新数据
                    stream_db.refresh(current_analysis)
                    
                    # 发送进度更新和调试信息
                    debug_metadata = {
                        "status": current_analysis.status,
                        "api_call_time": current_analysis.api_call_time.isoformat() if current_analysis.api_call_time else None,
                        "api_response_time": current_analysis.api_response_time.isoformat() if current_analysis.api_response_time else None,
                        "api_duration": current_analysis.api_duration,
                        "prompt_tokens": current_analysis.prompt_tokens,
                        "completion_tokens": current_analysis.completion_tokens,
                        "total_tokens": current_analysis.total_tokens,
                        "temperature": current_analysis.temperature,
                        "max_tokens": current_analysis.max_tokens,
                        "model_name": current_analysis.model_name,
                        "api_provider": current_analysis.api_provider,
                        "request_id": current_analysis.request_id,
                        "debug_info": current_analysis.debug_info
                    }
                    
                    chunk = AnalysisStreamChunk(
                        type="progress",
                        progress=current_analysis.progress,
                        metadata=debug_metadata
                    )
                    yield f"data: {json.dumps(chunk.dict())}\n\n"
                    print(f"✅ 发送进度更新 #{i+1}: {current_analysis.progress}%")
                    
                    # 检查调试信息
                    debug_fields = [k for k, v in debug_metadata.items() if v is not None]
                    print(f"   调试字段: {debug_fields[:5]}")
                    
                    # 检查是否完成
                    if current_analysis.status == "completed":
                        print(f"✅ 任务在循环中完成")
                        chunk = AnalysisStreamChunk(
                            type="complete",
                            progress=100,
                            metadata={
                                "confidence_score": current_analysis.confidence_score,
                                "processing_time": current_analysis.processing_time
                            }
                        )
                        yield f"data: {json.dumps(chunk.dict())}\n\n"
                        break
                    
                    if current_analysis.status == "failed":
                        print(f"❌ 任务在循环中失败")
                        chunk = AnalysisStreamChunk(
                            type="error",
                            content=current_analysis.error_message or "Analysis failed",
                            metadata={"error_code": current_analysis.error_code}
                        )
                        yield f"data: {json.dumps(chunk.dict())}\n\n"
                        break
                    
                    # 模拟等待
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ 循环中出现异常: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    chunk = AnalysisStreamChunk(
                        type="error",
                        content=f"Stream error: {str(e)}",
                        metadata={"error_code": "STREAM_ERROR"}
                    )
                    yield f"data: {json.dumps(chunk.dict())}\n\n"
                    break
            
            print(f"✅ 生成器测试完成")
                    
        except Exception as e:
            print(f"❌ 生成器异常: {e}")
            import traceback
            traceback.print_exc()
            
            chunk = AnalysisStreamChunk(
                type="error",
                content=f"Stream generation error: {str(e)}",
                metadata={"error_code": "GENERATION_ERROR"}
            )
            yield f"data: {json.dumps(chunk.dict())}\n\n"
        finally:
            # 确保关闭数据库会话
            print(f"🔧 关闭数据库会话")
            stream_db.close()
    
    # 测试生成器
    print("\n🚀 开始测试生成器...")
    try:
        chunk_count = 0
        for chunk in test_generate_stream():
            chunk_count += 1
            print(f"📦 生成器输出 #{chunk_count}: {chunk[:100]}{'...' if len(chunk) > 100 else ''}")
            
            # 解析JSON检查格式
            if chunk.startswith('data: '):
                data_str = chunk[6:].strip()
                try:
                    data = json.loads(data_str)
                    event_type = data.get('type', 'unknown')
                    print(f"   事件类型: {event_type}")
                    
                    if event_type == 'progress':
                        metadata = data.get('metadata', {})
                        debug_fields = [k for k, v in metadata.items() if v is not None]
                        print(f"   调试字段数量: {len(debug_fields)}")
                        
                except json.JSONDecodeError as e:
                    print(f"   ⚠️ JSON解析失败: {e}")
        
        print(f"\n📊 生成器测试总结:")
        print(f"  - 生成数据块: {chunk_count}")
        print(f"  - 测试结果: {'✅ 成功' if chunk_count > 0 else '❌ 失败'}")
        
    except Exception as e:
        print(f"❌ 生成器测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generator_directly()