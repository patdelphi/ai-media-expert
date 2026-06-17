"""自动打标任务接口

提供自动打标任务创建与详情查询能力。
"""

from __future__ import annotations

import asyncio
import os
import threading
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.app_logging import api_logger
from app.core.database import SessionLocal
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.models.video import AIConfig
from app.models.video_auto_tag import VideoAutoTagTask
from app.schemas.common import ResponseModel
from app.schemas.video_auto_tag import (
    VideoAutoTagStartRequest,
    VideoAutoTagStartResponse,
    VideoAutoTagTaskHistoryItemResponse,
    VideoAutoTagTaskResponse,
)
from app.services.video_auto_tag_service import video_auto_tag_service

router = APIRouter()


def _ensure_file_owner(current_user: User, video_file: UploadedFile) -> None:
    """校验视频归属。"""
    if current_user.role == "admin":
        return
    if str(video_file.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to access this video")


def _run_auto_tag_task(task_id: int) -> None:
    """在后台线程中运行自动打标任务。"""
    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(video_auto_tag_service.process_task(task_id, db))
        finally:
            loop.close()
    finally:
        db.close()


@router.post("/start", response_model=ResponseModel[VideoAutoTagStartResponse])
def start_video_auto_tag_task(
    request: VideoAutoTagStartRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """启动自动打标任务。"""
    video_file = db.query(UploadedFile).filter(UploadedFile.id == request.video_file_id).first()
    if not video_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")
    _ensure_file_owner(current_user, video_file)

    if not video_file.file_path or not os.path.isfile(video_file.file_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Video file is not available on disk")

    ai_config = db.query(AIConfig).filter(AIConfig.id == request.ai_config_id, AIConfig.is_active == True).first()
    if not ai_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI config not found or inactive")

    task = video_auto_tag_service.create_task(
        db=db,
        current_user=current_user,
        video_file=video_file,
        ai_config=ai_config,
        tag_group_ids=request.tag_group_ids,
        transmission_method=request.transmission_method,
    )

    def _background_runner() -> None:
        thread = threading.Thread(target=_run_auto_tag_task, args=(task.id,))
        thread.start()

    background_tasks.add_task(_background_runner)

    api_logger.info(
        "Started video auto tag task",
        task_id=task.id,
        video_file_id=video_file.id,
        user_id=current_user.id,
        ai_config_id=ai_config.id,
    )

    return ResponseModel(
        code=200,
        message="Video auto tag task started successfully",
        data=VideoAutoTagStartResponse(
            task_id=task.id,
            status=task.status,
            message="Video auto tag task started successfully",
        ),
    )


@router.get("/video-files/{video_file_id}/tasks", response_model=ResponseModel[list[VideoAutoTagTaskHistoryItemResponse]])
def list_video_auto_tag_tasks(
    video_file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """获取指定视频的自动打标任务历史。"""
    video_file = db.query(UploadedFile).filter(UploadedFile.id == video_file_id).first()
    if not video_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")
    _ensure_file_owner(current_user, video_file)

    tasks = (
        db.query(VideoAutoTagTask)
        .filter(
            VideoAutoTagTask.video_file_id == video_file_id,
            VideoAutoTagTask.is_active == True,
        )
        .order_by(VideoAutoTagTask.id.desc())
        .all()
    )

    return ResponseModel(
        code=200,
        message="Video auto tag task history retrieved successfully",
        data=[VideoAutoTagTaskHistoryItemResponse.model_validate(task) for task in tasks],
    )


@router.get("/{task_id}", response_model=ResponseModel[VideoAutoTagTaskResponse])
def get_video_auto_tag_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """获取自动打标任务详情。"""
    task = db.query(VideoAutoTagTask).filter(VideoAutoTagTask.id == task_id, VideoAutoTagTask.is_active == True).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auto tag task not found")

    if current_user.role != "admin" and str(task.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to access this task")

    return ResponseModel(
        code=200,
        message="Video auto tag task retrieved successfully",
        data=VideoAutoTagTaskResponse.model_validate(task),
    )
