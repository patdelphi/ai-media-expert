#!/usr/bin/env python3
"""最小化文件上传接口

提供简单的文件上传功能，支持视频文件上传和基本信息存储。
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
import os
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.uploaded_file import UploadedFile
from app.utils.video_utils import get_complete_video_info, get_video_creation_time
import re

router = APIRouter()

# 上传目录配置
UPLOAD_DIR = Path("uploads/videos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def extract_time_from_filename(filename: str) -> Optional[datetime]:
    """从文件名中提取时间信息"""
    # 常见的时间格式模式
    patterns = [
        # 20231225_143022 格式
        r'(\d{8})_(\d{6})',
        # 2023-12-25_14-30-22 格式
        r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})',
        # 20231225143022 格式
        r'(\d{14})',
        # IMG_20231225_143022 格式
        r'IMG_(\d{8})_(\d{6})',
        # VID_20231225_143022 格式
        r'VID_(\d{8})_(\d{6})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                if len(match.groups()) == 2:
                    date_part, time_part = match.groups()
                    if '-' in date_part:
                        # 2023-12-25_14-30-22 格式
                        datetime_str = f"{date_part} {time_part.replace('-', ':')}"
                        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        # 20231225_143022 格式
                        datetime_str = f"{date_part}{time_part}"
                        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
                elif len(match.groups()) == 1:
                    # 20231225143022 格式
                    datetime_str = match.group(1)
                    return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
            except ValueError:
                continue
    
    return None


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传文件接口"""
    try:
        # 生成唯一的文件名
        file_extension = Path(file.filename).suffix
        saved_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / saved_filename
        
        # 保存原始文件名
        original_filename = file.filename
        
        # 保存文件到磁盘
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # 获取文件的原始创建时间
        file_created_time = None
        
        # 先尝试从视频元数据获取创建时间
        if file.content_type and file.content_type.startswith('video/'):
            try:
                file_created_time = get_video_creation_time(str(file_path))
                if file_created_time:
                    print(f"成功从视频元数据获取创建时间: {file_created_time}")
            except Exception as e:
                print(f"从视频元数据获取创建时间失败: {e}")
        
        # 如果没有获取到元数据创建时间，尝试从文件名中提取时间
        if not file_created_time:
            file_created_time = extract_time_from_filename(file.filename)
            if file_created_time:
                print(f"从文件名提取到创建时间: {file_created_time}")
        
        # 最后使用文件系统时间
        if not file_created_time:
            file_stat = os.stat(file_path)
            file_created_time = datetime.fromtimestamp(file_stat.st_mtime)
            print(f"使用文件系统修改时间作为创建时间: {file_created_time}")
        
        # 获取完整视频信息（如果是视频文件）
        video_info = {}
        if file.content_type and file.content_type.startswith('video/'):
            complete_info = get_complete_video_info(str(file_path))
            if complete_info:
                video_info = complete_info
        
        # 保存文件信息到数据库
        db_file = UploadedFile(
<<<<<<< HEAD
            user_id="anonymous",  # 临时设置为匿名用户，后续可以集成用户认证
=======
>>>>>>> ad3f17f (feat: 完善视频上传功能 - 修复时长格式化、上传时间显示、移除时间编辑按钮)
            original_filename=original_filename,
            saved_filename=saved_filename,
            file_size=file.size,
            content_type=file.content_type,
            file_path=str(file_path),
            file_created_at=file_created_time,
            **video_info
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return {
            "success": True,
            "message": "文件上传成功",
            "file_id": db_file.id,
            "original_filename": original_filename,
            "saved_filename": saved_filename,
            "file_size": file.size,
            "content_type": file.content_type,
            "file_created_at": file_created_time.isoformat() if file_created_time else None,
            "video_info": video_info
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"上传失败: {str(e)}"
        }