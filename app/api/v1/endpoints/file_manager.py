"""文件管理API

提供文件列表、删除、下载等管理功能。
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.uploaded_file import UploadedFile

router = APIRouter()

# 上传目录配置
UPLOAD_DIR = Path("uploads/videos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/files")
async def list_files(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """获取文件列表"""
    try:
        # 从数据库获取文件信息
        db_files = db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).all()
        
        files = []
        for db_file in db_files:
            # 检查文件是否仍然存在
            file_path = Path(db_file.file_path)
            if file_path.exists():
                files.append({
                    "name": db_file.original_filename,  # 使用原始文件名
                    "saved_name": db_file.saved_filename,  # 保存的文件名
                    "size": db_file.file_size,
                    "type": db_file.content_type,
                    "upload_time": db_file.created_at.timestamp(),
                    "path": db_file.saved_filename,  # 用于下载的路径
                    
                    # 视频基本信息
                    "duration": db_file.duration,
                    "format_name": db_file.format_name,
                    "bit_rate": db_file.bit_rate,
                    
                    # 视频流信息
                    "width": db_file.width,
                    "height": db_file.height,
                    "video_codec": db_file.video_codec,
                    "frame_rate": db_file.frame_rate,
                    "aspect_ratio": db_file.aspect_ratio,
                    "video_ratio": db_file.video_ratio,
                    
                    # 音频流信息
                    "audio_codec": db_file.audio_codec,
                    "sample_rate": db_file.sample_rate,
                    "channels": db_file.channels,
                    
                    # 文件信息
                    "title": db_file.title,
                    "description": db_file.description,
                    "file_created_at": db_file.file_created_at.timestamp() if db_file.file_created_at else None
                })
        
        return {
            "success": True,
            "files": files,
            "total_count": len(files),
            "total_size": sum(f["size"] for f in files),
            "upload_dir": str(UPLOAD_DIR)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.get("/files/{filename}")
async def download_file(filename: str, db: Session = Depends(get_db)):
    """下载文件"""
    try:
        # 从数据库查找文件记录
        db_file = db.query(UploadedFile).filter(
            UploadedFile.original_filename == filename
        ).first()
        
        if not db_file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path = Path(db_file.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="不是有效的文件")
        
        return FileResponse(
            path=str(file_path),
            filename=db_file.original_filename,  # 使用原始文件名
            media_type=db_file.content_type or 'application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")


@router.delete("/files/{filename}")
async def delete_file(filename: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """删除文件"""
    try:
        # 从数据库查找文件记录
        db_file = db.query(UploadedFile).filter(
            UploadedFile.original_filename == filename
        ).first()
        
        if not db_file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path = Path(db_file.file_path)
        
        # 删除物理文件
        if file_path.exists():
            file_path.unlink()
        
        # 删除数据库记录
        db.delete(db_file)
        db.commit()
        
        return {
            "success": True,
            "message": f"文件 {filename} 已删除",
            "filename": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


@router.put("/update-time/{filename}")
async def update_file_time(
    filename: str,
    request: dict,
    db: Session = Depends(get_db)
):
    """更新文件创建时间"""
    try:
        # 查找文件记录
        db_file = db.query(UploadedFile).filter(
            UploadedFile.saved_filename == filename
        ).first()
        
        if not db_file:
            return {
                "success": False,
                "error": "文件不存在"
            }
        
        # 更新创建时间
        from datetime import datetime
        new_time = datetime.fromtimestamp(request.get('file_created_at'))
        db_file.file_created_at = new_time
        
        db.commit()
        
        return {
            "success": True,
            "message": "文件创建时间已更新",
            "new_time": new_time.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"更新失败: {str(e)}"
        }


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """获取文件统计信息"""
    try:
        files = []
        total_size = 0
        video_count = 0
        other_count = 0
        
        if UPLOAD_DIR.exists():
            for file_path in UPLOAD_DIR.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    file_size = stat.st_size
                    total_size += file_size
                    
                    file_type = get_file_type(file_path.suffix)
                    if file_type.startswith('video/'):
                        video_count += 1
                    else:
                        other_count += 1
                    
                    files.append({
                        "name": file_path.name,
                        "size": file_size,
                        "type": file_type
                    })
        
        return {
            "success": True,
            "total_files": len(files),
            "total_size": total_size,
            "video_files": video_count,
            "other_files": other_count,
            "upload_dir": str(UPLOAD_DIR)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


def get_file_type(extension: str) -> str:
    """根据文件扩展名获取MIME类型"""
    extension = extension.lower()
    
    video_extensions = {
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
        '.webm': 'video/webm',
        '.mkv': 'video/x-matroska',
        '.m4v': 'video/x-m4v'
    }
    
    image_extensions = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    
    audio_extensions = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.aac': 'audio/aac',
        '.ogg': 'audio/ogg'
    }
    
    text_extensions = {
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.csv': 'text/csv'
    }
    
    if extension in video_extensions:
        return video_extensions[extension]
    elif extension in image_extensions:
        return image_extensions[extension]
    elif extension in audio_extensions:
        return audio_extensions[extension]
    elif extension in text_extensions:
        return text_extensions[extension]
    elif extension == '.pdf':
        return 'application/pdf'
    else:
        return 'application/octet-stream'