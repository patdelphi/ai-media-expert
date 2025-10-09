"""视频下载API端点

提供视频下载相关的API接口，包括URL解析、视频信息提取、下载管理等功能。
"""

import asyncio
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

from app.api.deps import get_db, get_current_user
from app.core.app_logging import download_logger
from app.models.user import User
from app.models.video import DownloadTask
from app.schemas.common import ResponseModel
from app.services.video_parsing_service import video_parsing_service
from app.services.download_service import DownloadService

router = APIRouter()
download_service = DownloadService()


class VideoParseRequest(BaseModel):
    """视频解析请求模型"""
    url: str
    minimal: bool = False


class VideoDownloadRequest(BaseModel):
    """视频下载请求模型"""
    url: str
    format: str = "mp4"
    quality: str = "1080p"
    download_video: bool = True
    download_audio: bool = True
    download_subtitles: bool = False
    download_thumbnail: bool = True


class DownloadTaskResponse(BaseModel):
    """下载任务响应模型"""
    id: str
    url: str
    title: str
    platform: str
    status: str
    progress: float
    created_at: str
    updated_at: str
    file_path: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/parse", response_model=ResponseModel, summary="解析视频信息")
async def parse_video_info(
    request: VideoParseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    解析视频链接，提取视频基本信息
    
    支持的平台：
    - 抖音 (douyin.com)
    - TikTok (tiktok.com)
    - B站 (bilibili.com)
    - 小红书 (xiaohongshu.com)
    - 快手 (kuaishou.com)
    - 微信视频号 (weixin.qq.com)
    
    Args:
        request: 解析请求参数
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        视频信息
    """
    try:
        download_logger.info(
            "开始解析视频",
            url=request.url,
            user_id=current_user.id,
            minimal=request.minimal
        )
        
        # 解析视频信息
        video_info = await video_parsing_service.parse_video_info(
            url=request.url,
            minimal=request.minimal
        )
        
        download_logger.info(
            "视频解析成功",
            url=request.url,
            platform=video_info.get('platform'),
            title=video_info.get('title')
        )
        
        return ResponseModel(
            code=200,
            message="视频解析成功",
            data=video_info
        )
        
    except ValueError as e:
        download_logger.warning(
            "视频解析失败 - 参数错误",
            url=request.url,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        download_logger.error(
            "视频解析失败 - 系统错误",
            url=request.url,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"视频解析失败: {str(e)}")


@router.post("/download", response_model=ResponseModel, summary="创建下载任务")
async def create_download_task(
    request: VideoDownloadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建视频下载任务
    
    Args:
        request: 下载请求参数
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        下载任务信息
    """
    try:
        download_logger.info(
            "创建下载任务",
            url=request.url,
            user_id=current_user.id,
            format=request.format,
            quality=request.quality
        )
        
        # 先解析视频信息
        video_info = await video_parsing_service.parse_video_info(
            url=request.url,
            minimal=True
        )
        
        # 创建下载任务
        task = await download_service.create_download_task(
            db=db,
            user_id=current_user.id,
            url=request.url,
            video_info=video_info,
            options={
                'format': request.format,
                'quality': request.quality,
                'download_video': request.download_video,
                'download_audio': request.download_audio,
                'download_subtitles': request.download_subtitles,
                'download_thumbnail': request.download_thumbnail
            }
        )
        
        # 添加到后台任务队列
        background_tasks.add_task(
            download_service.process_download_task,
            task_id=task.id,
            db=db
        )
        
        download_logger.info(
            "下载任务创建成功",
            task_id=task.id,
            url=request.url,
            title=video_info.get('title')
        )
        
        return ResponseModel(
            code=200,
            message="下载任务创建成功",
            data={
                'task_id': task.id,
                'status': task.status,
                'title': video_info.get('title'),
                'platform': video_info.get('platform')
            }
        )
        
    except ValueError as e:
        download_logger.warning(
            "创建下载任务失败 - 参数错误",
            url=request.url,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        download_logger.error(
            "创建下载任务失败 - 系统错误",
            url=request.url,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"创建下载任务失败: {str(e)}")


@router.get("/tasks", response_model=ResponseModel, summary="获取下载任务列表")
async def get_download_tasks(
    status: Optional[str] = Query(None, description="任务状态过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户的下载任务列表
    
    Args:
        status: 任务状态过滤 (pending, downloading, completed, failed, cancelled)
        limit: 返回数量限制
        offset: 偏移量
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        下载任务列表
    """
    try:
        tasks = await download_service.get_user_tasks(
            db=db,
            user_id=current_user.id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        task_list = [
            DownloadTaskResponse(
                id=task.id,
                url=task.url,
                title=task.title or "未知标题",
                platform=task.platform or "unknown",
                status=task.status,
                progress=task.progress or 0.0,
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat(),
                file_path=task.file_path,
                error_message=task.error_message
            )
            for task in tasks
        ]
        
        return ResponseModel(
            code=200,
            message="获取任务列表成功",
            data={
                'tasks': task_list,
                'total': len(task_list)
            }
        )
        
    except Exception as e:
        download_logger.error(
            "获取任务列表失败",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/tasks/{task_id}", response_model=ResponseModel, summary="获取下载任务详情")
async def get_download_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定下载任务的详细信息
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        任务详细信息
    """
    try:
        task = await download_service.get_task_by_id(
            db=db,
            task_id=task_id,
            user_id=current_user.id
        )
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task_info = DownloadTaskResponse(
            id=task.id,
            url=task.url,
            title=task.title or "未知标题",
            platform=task.platform or "unknown",
            status=task.status,
            progress=task.progress or 0.0,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            file_path=task.file_path,
            error_message=task.error_message
        )
        
        return ResponseModel(
            code=200,
            message="获取任务详情成功",
            data=task_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(
            "获取任务详情失败",
            task_id=task_id,
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.post("/tasks/{task_id}/cancel", response_model=ResponseModel, summary="取消下载任务")
async def cancel_download_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    取消指定的下载任务
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        操作结果
    """
    try:
        success = await download_service.cancel_task(
            db=db,
            task_id=task_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在或无法取消")
        
        download_logger.info(
            "任务取消成功",
            task_id=task_id,
            user_id=current_user.id
        )
        
        return ResponseModel(
            code=200,
            message="任务取消成功",
            data={'task_id': task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(
            "取消任务失败",
            task_id=task_id,
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.post("/tasks/{task_id}/retry", response_model=ResponseModel, summary="重试下载任务")
async def retry_download_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    重试失败的下载任务
    
    Args:
        task_id: 任务ID
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        操作结果
    """
    try:
        task = await download_service.get_task_by_id(
            db=db,
            task_id=task_id,
            user_id=current_user.id
        )
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status not in ['failed', 'cancelled']:
            raise HTTPException(status_code=400, detail="只能重试失败或已取消的任务")
        
        # 重置任务状态
        await download_service.reset_task(
            db=db,
            task_id=task_id
        )
        
        # 添加到后台任务队列
        background_tasks.add_task(
            download_service.process_download_task,
            task_id=task_id,
            db=db
        )
        
        download_logger.info(
            "任务重试成功",
            task_id=task_id,
            user_id=current_user.id
        )
        
        return ResponseModel(
            code=200,
            message="任务重试成功",
            data={'task_id': task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(
            "重试任务失败",
            task_id=task_id,
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"重试任务失败: {str(e)}")


@router.delete("/tasks/{task_id}", response_model=ResponseModel, summary="删除下载任务")
async def delete_download_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除指定的下载任务
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        操作结果
    """
    try:
        success = await download_service.delete_task(
            db=db,
            task_id=task_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        download_logger.info(
            "任务删除成功",
            task_id=task_id,
            user_id=current_user.id
        )
        
        return ResponseModel(
            code=200,
            message="任务删除成功",
            data={'task_id': task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(
            "删除任务失败",
            task_id=task_id,
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")


@router.get("/platforms", response_model=ResponseModel, summary="获取支持的平台列表")
async def get_supported_platforms():
    """
    获取支持的视频平台列表
    
    Returns:
        支持的平台信息
    """
    platforms = [
        {
            'name': 'douyin',
            'display_name': '抖音',
            'icon': 'fab fa-tiktok',
            'color': 'text-red-500',
            'supported_features': ['video', 'image', 'audio']
        },
        {
            'name': 'tiktok',
            'display_name': 'TikTok',
            'icon': 'fab fa-tiktok',
            'color': 'text-black',
            'supported_features': ['video', 'audio']
        },
        {
            'name': 'bilibili',
            'display_name': 'B站',
            'icon': 'fas fa-b',
            'color': 'text-blue-500',
            'supported_features': ['video', 'audio', 'subtitles']
        },
        {
            'name': 'xiaohongshu',
            'display_name': '小红书',
            'icon': 'fas fa-book',
            'color': 'text-pink-500',
            'supported_features': ['video', 'image']
        },
        {
            'name': 'kuaishou',
            'display_name': '快手',
            'icon': 'fas fa-play',
            'color': 'text-yellow-500',
            'supported_features': ['video', 'audio']
        },
        {
            'name': 'weixin',
            'display_name': '微信视频号',
            'icon': 'fab fa-weixin',
            'color': 'text-green-500',
            'supported_features': ['video', 'audio']
        }
    ]
    
    return ResponseModel(
        code=200,
        message="获取平台列表成功",
        data={
            'platforms': platforms,
            'total': len(platforms)
        }
    )