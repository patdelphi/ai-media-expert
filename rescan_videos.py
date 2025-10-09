#!/usr/bin/env python3
"""
重新扫描uploads目录中的视频文件并添加到数据库
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.models.video import Video
from app.core.database import Base
from app.services.video_metadata import VideoMetadataExtractor

def rescan_videos():
    """重新扫描并添加视频文件到数据库"""
    
    # 数据库连接
    DATABASE_URL = "sqlite:///./ai_media_expert.db"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 视频上传目录
    uploads_dir = Path("uploads/videos")
    
    if not uploads_dir.exists():
        print(f"上传目录不存在: {uploads_dir}")
        return
    
    # 获取所有mp4文件
    video_files = list(uploads_dir.glob("*.mp4"))
    print(f"找到 {len(video_files)} 个视频文件")
    
    if not video_files:
        print("没有找到视频文件")
        return
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 清空现有视频记录
        db.query(Video).delete()
        db.commit()
        print("已清空现有视频记录")
        
        # 添加每个视频文件
        for video_file in video_files:
            try:
                print(f"处理视频文件: {video_file.name}")
                
                # 创建视频记录（不依赖ffprobe）
                video = Video(
                    title=f"Video {video_file.stem}",  # 视频标题
                    original_filename=video_file.name,  # 原始文件名
                    file_path=str(video_file),
                    file_size=video_file.stat().st_size,
                    duration=None,  # 暂时设为None
                    resolution=None,  # 暂时设为None
                    format='mp4',
                    fps=None,
                    bitrate=None,
                    codec=None
                )
                
                db.add(video)
                db.commit()
                db.refresh(video)
                
                print(f"  -> 添加成功，ID: {video.id}")
                
            except Exception as e:
                print(f"  -> 处理失败: {e}")
                db.rollback()
                continue
        
        # 显示最终结果
        total_videos = db.query(Video).count()
        print(f"\n数据库中现有 {total_videos} 个视频文件")
        
        # 显示前几个视频的信息
        videos = db.query(Video).limit(5).all()
        for video in videos:
            print(f"  ID: {video.id}, 文件名: {video.original_filename}, 大小: {video.file_size} bytes")
            
    except Exception as e:
        print(f"数据库操作失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("开始重新扫描视频文件...")
    rescan_videos()
    print("扫描完成！")