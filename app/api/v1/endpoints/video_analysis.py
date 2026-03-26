"""视频解析API端点

提供视频解析功能的API接口，包括模板管理、标签组管理和解析任务管理。
"""

import time
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_db
from app.core.app_logging import api_logger
from app.models.uploaded_file import UploadedFile
from app.models.prompt_template import PromptTemplate
from app.models.tag_group import TagGroup
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis
from app.schemas.video_analysis import (
    VideoAnalysisCreate,
    VideoAnalysisResponse,
    VideoAnalysisListResponse,
    AnalysisStartRequest,
    AnalysisStartResponse,
    AnalysisStreamChunk,
    PromptTemplateResponse,
    TagGroupResponse,
    VideoFileInfo
)
from app.schemas.common import ResponseModel, PaginatedResponse, PaginationParams

router = APIRouter()


@router.get("/videos/recent", response_model=ResponseModel[List[VideoFileInfo]])
def get_recent_videos(
    limit: int = 9,
    db: Session = Depends(get_db)
) -> Any:
    """获取最近上传的视频列表
    
    用于视频解析功能的视频选择，默认返回9个视频。
    """
    try:
        import os

        # 获取最近上传的视频文件
        candidate_limit = min(max(limit, 1) * 5, 100)
        videos = db.query(UploadedFile).filter(
            UploadedFile.file_size > 0,
            UploadedFile.file_path.isnot(None)
        ).order_by(desc(UploadedFile.created_at)).limit(candidate_limit).all()
        
        video_list = []
        for video in videos:
            if not video.file_path or not os.path.isfile(video.file_path):
                continue
            try:
                if os.path.getsize(video.file_path) <= 0:
                    continue
            except OSError:
                continue

            video_info = VideoFileInfo(
                id=video.id,
                original_filename=video.original_filename,
                saved_filename=video.saved_filename,
                title=video.title,
                file_size=video.file_size,
                duration=video.duration,
                width=video.width,
                height=video.height,
                format_name=video.format_name,
                created_at=video.created_at
            )
            video_list.append(video_info)
            if len(video_list) >= limit:
                break
        
        api_logger.info(f"Retrieved {len(video_list)} recent videos")
        
        return ResponseModel(
            code=200,
            message="Recent videos retrieved successfully",
            data=video_list
        )
        
    except Exception as e:
        api_logger.error(f"Failed to get recent videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recent videos: {str(e)}"
        )


@router.get("/videos", response_model=ResponseModel[PaginatedResponse[VideoFileInfo]])
def get_videos(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """获取可用于解析的视频列表（分页）"""
    try:
        import os

        query = db.query(UploadedFile).filter(
            UploadedFile.file_size > 0,
            UploadedFile.file_path.isnot(None)
        ).order_by(desc(UploadedFile.created_at))

        total = query.count()

        items: List[VideoFileInfo] = []
        offset = pagination.offset
        batch_size = min(max(pagination.size, 1) * 5, 200)
        attempts = 0

        while len(items) < pagination.size and attempts < 20:
            batch = query.offset(offset).limit(batch_size).all()
            if not batch:
                break

            for video in batch:
                if not video.file_path or not os.path.isfile(video.file_path):
                    continue
                try:
                    if os.path.getsize(video.file_path) <= 0:
                        continue
                except OSError:
                    continue

                items.append(VideoFileInfo(
                    id=video.id,
                    original_filename=video.original_filename,
                    saved_filename=video.saved_filename,
                    title=video.title,
                    file_size=video.file_size,
                    duration=video.duration,
                    width=video.width,
                    height=video.height,
                    format_name=video.format_name,
                    created_at=video.created_at
                ))

                if len(items) >= pagination.size:
                    break

            offset += batch_size
            attempts += 1

        paginated_data = PaginatedResponse.create(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size
        )

        return ResponseModel(
            code=200,
            message="Videos retrieved successfully",
            data=paginated_data
        )
    except Exception as e:
        api_logger.error(f"Failed to get videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve videos: {str(e)}"
        )


@router.get("/videos/{video_id}", response_model=ResponseModel[VideoFileInfo])
def get_video_detail(
    video_id: int,
    require_file: bool = False,
    db: Session = Depends(get_db)
) -> Any:
    """获取单个可用于解析的视频信息"""
    try:
        import os

        video = db.query(UploadedFile).filter(
            UploadedFile.id == video_id
        ).first()

        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file not found"
            )

        if require_file:
            if video.file_size <= 0 or not video.file_path or not os.path.isfile(video.file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video file is not available"
                )

            try:
                if os.path.getsize(video.file_path) <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Video file is not available"
                    )
            except OSError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video file is not available"
                )

        return ResponseModel(
            code=200,
            message="Video retrieved successfully",
            data=VideoFileInfo(
                id=video.id,
                original_filename=video.original_filename,
                saved_filename=video.saved_filename,
                title=video.title,
                file_size=video.file_size,
                duration=video.duration,
                width=video.width,
                height=video.height,
                format_name=video.format_name,
                created_at=video.created_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to get video detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve video: {str(e)}"
        )


@router.get("/templates", response_model=ResponseModel[List[PromptTemplateResponse]])
def get_prompt_templates(
    is_active: bool = True,
    db: Session = Depends(get_db)
) -> Any:
    """获取提示词模板列表"""
    try:
        query = db.query(PromptTemplate)
        if is_active:
            query = query.filter(PromptTemplate.is_active == True)
        
        templates = query.order_by(desc(PromptTemplate.created_at)).all()
        
        template_list = []
        for template in templates:
            template_info = PromptTemplateResponse(
                id=template.id,
                title=template.title,
                content=template.content,
                is_active=template.is_active,
                usage_count=template.usage_count,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            template_list.append(template_info)
        
        api_logger.info(f"Retrieved {len(template_list)} prompt templates")
        
        return ResponseModel(
            code=200,
            message="Prompt templates retrieved successfully",
            data=template_list
        )
        
    except Exception as e:
        api_logger.error(f"Failed to get prompt templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve prompt templates: {str(e)}"
        )


@router.get("/tag-groups", response_model=ResponseModel[List[TagGroupResponse]])
def get_tag_groups(
    is_active: bool = True,
    db: Session = Depends(get_db)
) -> Any:
    """获取标签组列表"""
    try:
        query = db.query(TagGroup)
        if is_active:
            query = query.filter(TagGroup.is_active == True)
        
        tag_groups = query.order_by(desc(TagGroup.created_at)).all()
        
        tag_group_list = []
        for tag_group in tag_groups:
            # 构建标签列表
            tags = []
            for tag in tag_group.tags:
                tags.append({
                    "id": tag.id,
                    "name": tag.name,
                    "color": tag.color,
                    "is_active": tag.is_active
                })
            
            tag_group_info = TagGroupResponse(
                id=tag_group.id,
                name=tag_group.name,
                description=tag_group.description,
                is_active=tag_group.is_active,
                tags=tags,
                created_at=tag_group.created_at,
                updated_at=tag_group.updated_at
            )
            tag_group_list.append(tag_group_info)
        
        api_logger.info(f"Retrieved {len(tag_group_list)} tag groups")
        
        return ResponseModel(
            code=200,
            message="Tag groups retrieved successfully",
            data=tag_group_list
        )
        
    except Exception as e:
        api_logger.error(f"Failed to get tag groups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tag groups: {str(e)}"
        )


@router.get("/ai-configs", response_model=ResponseModel[List[dict]])
def get_ai_configs(
    is_active: bool = True,
    db: Session = Depends(get_db)
) -> Any:
    """获取AI配置列表（不包含API密钥）"""
    try:
        query = db.query(AIConfig)
        if is_active:
            query = query.filter(AIConfig.is_active == True)
        
        configs = query.order_by(desc(AIConfig.created_at)).all()
        
        config_list = []
        for config in configs:
            # 不返回API密钥等敏感信息
            config_info = {
                "id": config.id,
                "name": config.name,
                "provider": config.provider,
                "model": config.model,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "is_active": config.is_active,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
            config_list.append(config_info)
        
        api_logger.info(f"Retrieved {len(config_list)} AI configs")
        
        return ResponseModel(
            code=200,
            message="AI configs retrieved successfully",
            data=config_list
        )
        
    except Exception as e:
        api_logger.error(f"Failed to get AI configs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve AI configs: {str(e)}"
        )


@router.post("/start", response_model=ResponseModel[AnalysisStartResponse])
def start_video_analysis(
    request: AnalysisStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """开始视频解析任务"""
    try:
        import os

        # 验证视频文件是否存在
        video_file = db.query(UploadedFile).filter(
            UploadedFile.id == request.video_file_id
        ).first()
        if not video_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file not found"
            )

        if not video_file.file_path or not os.path.isfile(video_file.file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video file is not available on disk"
            )

        try:
            if os.path.getsize(video_file.file_path) <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Video file is empty"
                )
        except OSError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video file cannot be accessed"
            )
        
        # 验证AI配置是否存在
        ai_config = db.query(AIConfig).filter(
            AIConfig.id == request.ai_config_id,
            AIConfig.is_active == True
        ).first()
        if not ai_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI config not found or inactive"
            )
        
        # 验证模板（如果提供）
        template = None
        if request.template_id:
            template = db.query(PromptTemplate).filter(
                PromptTemplate.id == request.template_id,
                PromptTemplate.is_active == True
            ).first()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Prompt template not found or inactive"
                )
        
        # 生成提示词内容
        prompt_content = request.custom_prompt or ""
        if template:
            prompt_content = template.content
        
        # 如果有标签组，整合标签
        if request.tag_group_ids:
            tag_groups = db.query(TagGroup).filter(
                TagGroup.id.in_(request.tag_group_ids),
                TagGroup.is_active == True
            ).all()
            
            # 收集所有标签
            all_tags = []
            for tag_group in tag_groups:
                for tag in tag_group.tags:
                    if tag.is_active:
                        all_tags.append(tag.name)
            
            # 将标签添加到提示词中
            if all_tags:
                tags_text = ", ".join(all_tags)
                prompt_content += f"\n\n相关标签: {tags_text}"
        
        # 创建解析任务
        analysis = VideoAnalysis(
            video_file_id=request.video_file_id,
            template_id=request.template_id,
            tag_group_ids=request.tag_group_ids,
            prompt_content=prompt_content,
            ai_config_id=request.ai_config_id,
            transmission_method=request.transmission_method or 'url',
            status="pending",
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # 启动后台解析任务
        def run_async_task():
            import asyncio
            import threading
            
            def run_in_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(process_video_analysis(analysis.id, db))
                finally:
                    loop.close()
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
        
        background_tasks.add_task(run_async_task)
        
        api_logger.info(
            f"Started video analysis task {analysis.id} for video {video_file.original_filename}"
        )
        
        response = AnalysisStartResponse(
            analysis_id=analysis.id,
            status="pending",
            message="Video analysis task started successfully",
            stream_url=f"/api/v1/video-analysis/{analysis.id}/stream"
        )
        
        return ResponseModel(
            code=200,
            message="Analysis started successfully",
            data=response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to start video analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=ResponseModel[VideoAnalysisResponse])
def get_analysis_result(
    analysis_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """获取解析结果"""
    try:
        analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        # 构建响应数据
        response_data = VideoAnalysisResponse(
            id=analysis.id,
            video_file_id=analysis.video_file_id,
            template_id=analysis.template_id,
            tag_group_ids=analysis.tag_group_ids,
            ai_config_id=analysis.ai_config_id,
            prompt_content=analysis.prompt_content,
            status=analysis.status,
            progress=analysis.progress,
            analysis_result=analysis.analysis_result,
            result_summary=analysis.result_summary,
            result_metadata=analysis.result_metadata,
            confidence_score=analysis.confidence_score,
            quality_score=analysis.quality_score,
            processing_time=analysis.processing_time,
            token_usage=analysis.token_usage,
            cost_estimate=analysis.cost_estimate,
            error_message=analysis.error_message,
            error_code=analysis.error_code,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at
        )
        
        return ResponseModel(
            code=200,
            message="Analysis result retrieved successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to get analysis result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis result: {str(e)}"
        )


@router.get("/{analysis_id}/stream")
def stream_analysis_result(
    analysis_id: int,
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """流式获取解析结果"""
    try:
        analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        def generate_stream():
            """生成流式数据"""
            import json
            import time
            from app.core.database import SessionLocal
            from app.core.app_logging import api_logger
            
            # 创建新的数据库会话用于生成器
            stream_db = SessionLocal()
            
            try:
                # 重新获取分析对象
                current_analysis = stream_db.query(VideoAnalysis).filter(
                    VideoAnalysis.id == analysis_id
                ).first()
                
                if not current_analysis:
                    chunk = AnalysisStreamChunk(
                        type="error",
                        content="Analysis not found",
                        metadata={"error_code": "NOT_FOUND"}
                    )
                    yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                    return
                
                # 发送初始状态
                chunk = AnalysisStreamChunk(
                    type="progress",
                    progress=current_analysis.progress,
                    metadata={"status": current_analysis.status}
                )
                yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                
                # 如果任务已完成，直接返回结果
                if current_analysis.status == "completed":
                    if current_analysis.analysis_result:
                        chunk = AnalysisStreamChunk(
                            type="content",
                            content=current_analysis.analysis_result,
                            progress=100
                        )
                        yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                    
                    chunk = AnalysisStreamChunk(
                        type="complete",
                        progress=100,
                        metadata={
                            "confidence_score": current_analysis.confidence_score,
                            "processing_time": current_analysis.processing_time
                        }
                    )
                    yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                    return
                
                # 如果任务失败，返回错误信息
                if current_analysis.status == "failed":
                    chunk = AnalysisStreamChunk(
                        type="error",
                        content=current_analysis.error_message or "Analysis failed",
                        metadata={"error_code": current_analysis.error_code}
                    )
                    yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                    return
                
                # 对于进行中的任务，定期检查状态
                last_content_length = 0  # 跟踪上次发送的内容长度
                start_time = time.monotonic()
                max_seconds = 60 * 30
                
                while current_analysis.status in ["pending", "processing"]:
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
                            "debug_info": current_analysis.debug_info  # 添加完整的调试信息
                        }
                        
                        chunk = AnalysisStreamChunk(
                            type="progress",
                            progress=current_analysis.progress,
                            metadata=debug_metadata
                        )
                        yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                        
                        # 只有当内容发生变化时才发送内容更新
                        if current_analysis.analysis_result:
                            current_content_length = len(current_analysis.analysis_result)
                            if current_content_length > last_content_length:
                                # 发送增量内容（新增的部分）
                                new_content = current_analysis.analysis_result[last_content_length:]
                                chunk = AnalysisStreamChunk(
                                    type="content",
                                    content=new_content,
                                    progress=current_analysis.progress
                                )
                                yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                                last_content_length = current_content_length
                        
                        # 检查是否完成
                        if current_analysis.status == "completed":
                            chunk = AnalysisStreamChunk(
                                type="complete",
                                progress=100,
                                metadata={
                                    "confidence_score": current_analysis.confidence_score,
                                    "processing_time": current_analysis.processing_time
                                }
                            )
                            yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                            break
                        
                        if current_analysis.status == "failed":
                            chunk = AnalysisStreamChunk(
                                type="error",
                                content=current_analysis.error_message or "Analysis failed",
                                metadata={"error_code": current_analysis.error_code}
                            )
                            yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                            break
                        
                        # 等待一段时间再检查
                        time.sleep(2)
                        if time.monotonic() - start_time > max_seconds:
                            chunk = AnalysisStreamChunk(
                                type="timeout",
                                progress=current_analysis.progress,
                                metadata={"status": current_analysis.status}
                            )
                            yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                            return
                        
                    except Exception as e:
                        api_logger.error(f"Error in stream iteration: {str(e)}")
                        chunk = AnalysisStreamChunk(
                            type="error",
                            content=f"Stream error: {str(e)}",
                            metadata={"error_code": "STREAM_ERROR"}
                        )
                        yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
                        break
                    
            except Exception as e:
                api_logger.error(f"Error in generate_stream: {str(e)}")
                chunk = AnalysisStreamChunk(
                    type="error",
                    content=f"Stream generation error: {str(e)}",
                    metadata={"error_code": "GENERATION_ERROR"}
                )
                yield f"data: {json.dumps(chunk.model_dump(), default=str)}\n\n"
            finally:
                # 确保关闭数据库会话
                stream_db.close()
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to stream analysis result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream analysis result: {str(e)}"
        )


@router.get("/", response_model=ResponseModel[PaginatedResponse[VideoAnalysisListResponse]])
def get_analysis_history(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Any:
    """获取解析历史记录"""
    try:
        query = db.query(VideoAnalysis)
        
        if status_filter:
            query = query.filter(VideoAnalysis.status == status_filter)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        analyses = query.order_by(desc(VideoAnalysis.created_at)).offset(
            pagination.offset
        ).limit(pagination.size).all()
        
        # 构建响应数据
        analysis_list = []
        for analysis in analyses:
            analysis_info = VideoAnalysisListResponse(
                id=analysis.id,
                video_file_id=analysis.video_file_id,
                template_id=analysis.template_id,
                ai_config_id=analysis.ai_config_id,
                status=analysis.status,
                progress=analysis.progress,
                result_summary=analysis.result_summary,
                confidence_score=analysis.confidence_score,
                processing_time=analysis.processing_time,
                created_at=analysis.created_at,
                completed_at=analysis.completed_at
            )
            analysis_list.append(analysis_info)
        
        paginated_data = PaginatedResponse.create(
            items=analysis_list,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
        
        api_logger.info(f"Retrieved {len(analysis_list)} analysis records")
        
        return ResponseModel(
            code=200,
            message="Analysis history retrieved successfully",
            data=paginated_data
        )
        
    except Exception as e:
        api_logger.error(f"Failed to get analysis history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis history: {str(e)}"
        )


async def process_video_analysis(analysis_id: int, db: Session):
    """处理视频解析任务（后台任务）
    
    使用真实的AI API进行视频解析。
    """
    import asyncio
    from datetime import datetime
    from app.services.ai_service import ai_service
    from app.core.app_logging import api_logger
    
    try:
        # 获取解析任务
        analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            api_logger.error(f"Analysis {analysis_id} not found")
            return
        
        # 更新状态为处理中
        analysis.status = "processing"
        analysis.started_at = datetime.now()
        analysis.progress = 10
        db.commit()
        
        # 获取AI配置
        ai_config = db.query(AIConfig).filter(
            AIConfig.id == analysis.ai_config_id
        ).first()
        
        if not ai_config:
            analysis.status = "failed"
            analysis.error_message = "AI config not found"
            analysis.error_code = "CONFIG_NOT_FOUND"
            db.commit()
            return
        
        # 获取视频文件信息
        video_file = db.query(UploadedFile).filter(
            UploadedFile.id == analysis.video_file_id
        ).first()
        
        if not video_file:
            analysis.status = "failed"
            analysis.error_message = "Video file not found"
            analysis.error_code = "VIDEO_NOT_FOUND"
            db.commit()
            return
        
        # 开始真实的AI API处理
        api_logger.info(f"Processing analysis {analysis_id} with AI config {ai_config.name}")
        
        # 检查是否为视频理解模型，生成视频URL
        if ai_config.model.lower() in ['glm-4.5v', 'glm-4v']:
            try:
                # 为视频理解模型生成可访问的视频URL
                from app.core.config import settings
                import os
                
                # 验证视频文件是否存在
                # 使用file_path字段，因为Video模型中没有saved_filename字段
                video_file_path = video_file.file_path
                if not os.path.exists(video_file_path):
                    api_logger.error(f"Video file not found: {video_file_path}")
                    analysis.status = "failed"
                    analysis.error_message = "Video file not found"
                    analysis.error_code = "VIDEO_FILE_NOT_FOUND"
                    db.commit()
                    return
                
                # 设置视频文件路径（用于Base64编码备选方案）
                analysis.video_file_path = video_file_path
                
                # 生成公网可访问的视频URL
                base_url = settings.get_base_url()
                # 从file_path中提取文件名
                filename = os.path.basename(video_file.file_path)
                video_url = f"{base_url}/uploads/videos/{filename}"
                analysis.video_url = video_url
                db.commit()
                
                api_logger.info(f"Generated video URL for GLM model: {video_url}")
                api_logger.info(f"Video file path for Base64 fallback: {video_file_path}")
                api_logger.info(f"Base URL source: {base_url} (ngrok: {settings.ngrok_url}, public: {settings.public_base_url})")
                
                # 验证URL格式
                if not (video_url.startswith('http://') or video_url.startswith('https://')):
                    api_logger.warning(f"Generated URL may not be accessible externally: {video_url}")
                    
            except Exception as e:
                api_logger.error(f"Failed to generate video URL: {str(e)}")
                analysis.status = "failed"
                analysis.error_message = f"Failed to generate video URL: {str(e)}"
                analysis.error_code = "VIDEO_URL_GENERATION_FAILED"
                db.commit()
                return
            
            # 构建视频理解的提示词
            enhanced_prompt = f"""请分析这个视频的内容：

**分析要求：**
{analysis.prompt_content}

**视频基本信息：**
- 文件名: {video_file.original_filename}
- 时长: {video_file.duration or 'N/A'}秒
- 分辨率: {video_file.width}x{video_file.height} 像素
- 格式: {video_file.format_name or 'N/A'}

请基于视频的实际内容进行深度分析，输出格式为Markdown。
"""
        else:
            # 对于非视频理解模型，使用原有的元数据分析方式
            enhanced_prompt = f"""请分析以下视频文件：

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
        
        # 更新进度到30%
        analysis.progress = 30
        db.commit()
        
        # 调用AI API进行流式处理
        full_result = ""
        async for content_chunk in ai_service.call_ai_api(
            ai_config=ai_config,
            prompt=enhanced_prompt,
            analysis=analysis,
            db=db
        ):
            full_result += content_chunk
            
            # 根据内容长度更新进度
            if len(full_result) > 100:
                analysis.progress = min(90, 30 + (len(full_result) // 50))
                db.commit()
        
        # 完成解析
        analysis.status = "completed"
        analysis.progress = 100
        analysis.analysis_result = full_result
        analysis.result_summary = f"视频解析完成，共生成{len(full_result)}字符的分析报告。"
        analysis.confidence_score = 0.85
        analysis.quality_score = 0.90
        analysis.completed_at = datetime.now()
        analysis.processing_time = (datetime.now() - analysis.started_at).total_seconds()
        
        # Token使用统计
        analysis.token_usage = {
            "input_tokens": analysis.prompt_tokens or 0,
            "output_tokens": analysis.completion_tokens or 0,
            "total_tokens": analysis.total_tokens or 0
        }
        
        # 成本估算（每1000 tokens约0.002美元）
        if analysis.total_tokens:
            analysis.cost_estimate = (analysis.total_tokens / 1000) * 0.002
        
        db.commit()
        
        api_logger.info(f"Analysis {analysis_id} completed successfully")
        
    except Exception as e:
        api_logger.error(f"Analysis {analysis_id} failed: {str(e)}")
        
        # 更新失败状态
        analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.id == analysis_id
        ).first()
        
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.error_code = "PROCESSING_ERROR"
            analysis.completed_at = datetime.now()
            if analysis.started_at:
                analysis.processing_time = (datetime.now() - analysis.started_at).total_seconds()
            db.commit()
