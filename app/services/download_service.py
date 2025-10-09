"""视频下载服务

实现视频下载的核心业务逻辑，包括URL解析、平台适配、下载管理等。
"""

import os
import re
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from urllib.parse import urlparse
import aiofiles
import aiohttp

import yt_dlp
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.app_logging import download_logger
from app.models.video import DownloadTask, Video
from app.services.platform_adapters import get_platform_adapter
from app.services.video_parsing_service import video_parsing_service
from app.services.download_api_client import get_download_api_client


class DownloadProgressCallback:
    """下载进度回调类"""
    
    def __init__(self, task_id: int, db: Session):
        self.task_id = task_id
        self.db = db
        self.last_update = datetime.now()
        
    def __call__(self, downloaded: int, total: int, speed: Optional[int] = None):
        """更新下载进度到数据库"""
        now = datetime.now()
        # 限制更新频率，避免过于频繁的数据库操作
        if (now - self.last_update).total_seconds() < 1:
            return
            
        try:
            task = self.db.query(DownloadTask).filter(DownloadTask.id == self.task_id).first()
            if task:
                if total > 0:
                    task.progress = min((downloaded / total) * 100, 99)
                task.downloaded_size = downloaded
                task.file_size = total if total > 0 else task.file_size
                if speed:
                    task.download_speed = speed
                    # 计算预计剩余时间
                    if total > downloaded and speed > 0:
                        remaining_bytes = total - downloaded
                        task.eta = int(remaining_bytes / speed)
                
                self.db.commit()
                self.last_update = now
                
        except Exception as e:
            download_logger.error(
                "Failed to update download progress",
                task_id=self.task_id,
                error=str(e)
            )


class DownloadService:
    """视频下载服务
    
    负责管理视频下载的整个生命周期：
    1. URL解析和信息提取
    2. 文件下载和进度跟踪
    3. 元数据保存
    """
    
    def __init__(self):
        """初始化下载服务"""
        self.download_dir = settings.download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # 下载配置
        self.max_concurrent_downloads = settings.max_concurrent_downloads
        self.timeout = settings.download_timeout
        
        download_logger.info(
            "Download service initialized",
            download_dir=str(self.download_dir),
            max_concurrent=self.max_concurrent_downloads,
            timeout=self.timeout
        )

    async def extract_video_info(self, url: str, minimal: bool = False) -> Dict:
        """提取视频信息
        
        优先使用自定义解析器，回退到yt-dlp。
        
        Args:
            url: 视频URL
            minimal: 是否返回最小信息集
        
        Returns:
            包含视频信息的字典
        
        Raises:
            Exception: 当URL无效或提取失败时
        """
        try:
            # 首先尝试使用自定义解析器
            try:
                video_info = await video_parsing_service.parse_video_info(url, minimal)
                download_logger.info(
                    "Video info extracted using custom parser",
                    url=url,
                    title=video_info.get('title'),
                    platform=video_info.get('platform'),
                    duration=video_info.get('duration')
                )
                return video_info
            except Exception as custom_error:
                download_logger.warning(
                    "Custom parser failed, falling back to yt-dlp",
                    url=url,
                    error=str(custom_error)
                )
            
            # 回退到yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,
            }
            
            # 获取平台适配器的自定义选项
            adapter = get_platform_adapter(url)
            if adapter:
                custom_opts = adapter.get_custom_options()
                ydl_opts.update(custom_opts)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # 标准化信息格式
                video_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'description': info.get('description', ''),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader') or info.get('channel'),
                    'uploader_id': info.get('uploader_id') or info.get('channel_id'),
                    'upload_date': self._parse_upload_date(info.get('upload_date')),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'comment_count': info.get('comment_count', 0),
                    'video_id': info.get('id'),
                    'platform': self._detect_platform(url),
                    'original_url': url,
                    'thumbnail': info.get('thumbnail'),
                    'formats': info.get('formats', []),
                    'ext': info.get('ext', 'mp4'),
                    'resolution': self._get_best_resolution(info.get('formats', [])),
                    'filesize': info.get('filesize') or info.get('filesize_approx'),
                }
                
                download_logger.info(
                    "Video info extracted using yt-dlp",
                    url=url,
                    title=video_info['title'],
                    platform=video_info['platform'],
                    duration=video_info['duration']
                )
                
                return video_info
                
        except Exception as e:
            download_logger.error(
                "Failed to extract video info",
                url=url,
                error=str(e)
            )
            raise Exception(f"Failed to extract video information: {str(e)}")

    async def process_download_task(self, task_id: int, db: Session) -> Dict:
        """处理下载任务
        
        Args:
            task_id: 任务ID
            db: 数据库会话
            
        Returns:
            Dict: 处理结果
        """
        task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
        if not task:
            return {"status": "failed", "error": "Task not found"}
        
        try:
            # 更新任务状态为处理中
            task.status = "processing"
            task.started_at = datetime.now()
            db.commit()
            
            download_logger.info(
                "Starting download task processing",
                task_id=task_id,
                url=task.url
            )
            
            # 获取下载API客户端
            api_client = await get_download_api_client()
            
            # 解析视频信息
            video_info = await api_client.parse_video_info(task.url, minimal=False)
            
            # 更新任务的视频信息
            task.platform = video_info.platform
            db.commit()
            
            # 选择最佳下载URL
            download_url = self._select_download_url(
                video_info.video_urls, 
                task.quality or "best",
                task.audio_only
            )
            
            if not download_url:
                raise Exception("No suitable download URL found")
            
            # 生成文件路径
            file_path = self._generate_file_path(video_info, task.format_preference or "mp4")
            
            # 创建进度回调
            progress_callback = DownloadProgressCallback(task_id, db)
            
            # 下载文件
            success = await self.download_file(
                download_url["url"], 
                file_path, 
                progress_callback
            )
            
            if success:
                # 保存视频元数据到数据库
                video = await self._save_video_metadata(db, video_info, file_path)
                
                # 更新任务状态
                task.status = "completed"
                task.completed_at = datetime.now()
                task.progress = 100
                task.file_path = str(file_path)
                task.video_id = video.id if video else None
                db.commit()
                
                download_logger.info(
                    "Download task completed successfully",
                    task_id=task_id,
                    file_path=str(file_path)
                )
                
                return {
                    "status": "completed",
                    "file_path": str(file_path),
                    "video_id": video.id if video else None
                }
            else:
                raise Exception("File download failed")
                
        except Exception as e:
            # 更新任务状态为失败
            task.status = "failed"
            task.error_message = str(e)
            task.retry_count += 1
            db.commit()
            
            download_logger.error(
                "Download task failed",
                task_id=task_id,
                error=str(e),
                retry_count=task.retry_count
            )
            
            return {
                "status": "failed",
                "error": str(e),
                "retry_count": task.retry_count
            }

    async def download_file(
        self, 
        url: str, 
        file_path: Path, 
        progress_callback: Optional[Callable[[int, int, Optional[int]], None]] = None
    ) -> bool:
        """下载文件
        
        Args:
            url: 下载URL
            file_path: 保存路径
            progress_callback: 进度回调函数
            
        Returns:
            bool: 下载是否成功
        """
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        download_logger.error(
                            "Failed to download file",
                            url=url,
                            status=response.status
                        )
                        return False
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    start_time = datetime.now()
                    
                    # 确保目录存在
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 计算下载速度
                            elapsed = (datetime.now() - start_time).total_seconds()
                            speed = int(downloaded_size / elapsed) if elapsed > 0 else 0
                            
                            # 调用进度回调
                            if progress_callback:
                                progress_callback(downloaded_size, total_size, speed)
                    
                    download_logger.info(
                        "File downloaded successfully",
                        url=url,
                        file_path=str(file_path),
                        size=downloaded_size
                    )
                    return True
                    
        except Exception as e:
            download_logger.error(
                "File download failed",
                url=url,
                file_path=str(file_path),
                error=str(e)
            )
            return False

    def _select_download_url(self, video_urls: List[Dict], quality: str, audio_only: bool) -> Optional[Dict]:
        """选择最佳下载URL"""
        if not video_urls:
            return None
        
        # 如果只要音频，查找音频格式
        if audio_only:
            for url_info in video_urls:
                if url_info.get("ext") in ["mp3", "m4a", "aac"]:
                    return url_info
        
        # 根据质量要求筛选
        if quality == "best":
            # 选择最高质量
            best_url = None
            max_resolution = 0
            
            for url_info in video_urls:
                resolution = url_info.get("resolution", "0x0")
                try:
                    width, height = map(int, resolution.split("x"))
                    pixels = width * height
                    if pixels > max_resolution:
                        max_resolution = pixels
                        best_url = url_info
                except:
                    continue
            
            return best_url or video_urls[0]
        
        elif quality == "worst":
            # 选择最低质量
            worst_url = None
            min_resolution = float('inf')
            
            for url_info in video_urls:
                resolution = url_info.get("resolution", "0x0")
                try:
                    width, height = map(int, resolution.split("x"))
                    pixels = width * height
                    if pixels < min_resolution:
                        min_resolution = pixels
                        worst_url = url_info
                except:
                    continue
            
            return worst_url or video_urls[0]
        
        else:
            # 查找指定分辨率
            for url_info in video_urls:
                if quality in url_info.get("resolution", ""):
                    return url_info
            
            # 如果没找到指定分辨率，返回第一个
            return video_urls[0]

    def _generate_file_path(self, video_info, format_ext: str) -> Path:
        """生成文件保存路径"""
        # 清理文件名中的非法字符
        title = re.sub(r'[<>:"/\\|?*]', '_', video_info.title)
        title = title[:100]  # 限制文件名长度
        
        # 按平台分类存储
        platform_dir = self.download_dir / video_info.platform
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title}_{timestamp}.{format_ext}"
        
        return platform_dir / filename

    async def _save_video_metadata(self, db: Session, video_info, file_path: Path) -> Optional[Video]:
        """保存视频元数据到数据库"""
        try:
            # 检查是否已存在相同的视频
            existing_video = db.query(Video).filter(
                Video.platform_video_id == video_info.video_id,
                Video.platform == video_info.platform
            ).first()
            
            if existing_video:
                return existing_video
            
            # 创建新的视频记录
            video = Video(
                title=video_info.title,
                description=video_info.description,
                platform=video_info.platform,
                platform_video_id=video_info.video_id,
                url=video_info.original_url,
                thumbnail_url=video_info.thumbnail,
                duration=video_info.duration,
                view_count=video_info.view_count,
                like_count=video_info.like_count,
                comment_count=video_info.comment_count,
                uploader_name=video_info.uploader,
                uploader_id=video_info.uploader_id,
                upload_date=self._parse_upload_date(video_info.upload_date),
                file_path=str(file_path),
                file_size=file_path.stat().st_size if file_path.exists() else None,
                resolution=video_info.resolution,
                format=file_path.suffix[1:] if file_path.suffix else None
            )
            
            db.add(video)
            db.commit()
            db.refresh(video)
            
            download_logger.info(
                "Video metadata saved",
                video_id=video.id,
                title=video.title,
                platform=video.platform
            )
            
            return video
            
        except Exception as e:
            download_logger.error(
                "Failed to save video metadata",
                error=str(e)
            )
            return None

    def _detect_platform(self, url: str) -> Optional[str]:
        """检测视频平台"""
        url_lower = url.lower()
        
        platform_patterns = {
            'tiktok': [r'tiktok\.com', r'vm\.tiktok\.com'],
            'douyin': [r'douyin\.com', r'iesdouyin\.com'],
            'youtube': [r'youtube\.com', r'youtu\.be', r'youtube-nocookie\.com'],
            'bilibili': [r'bilibili\.com', r'b23\.tv'],
            'instagram': [r'instagram\.com'],
            'twitter': [r'twitter\.com', r'x\.com', r't\.co'],
            'facebook': [r'facebook\.com', r'fb\.watch'],
            'kuaishou': [r'kuaishou\.com', r'kwai\.com'],
        }
        
        for platform, patterns in platform_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform
        
        return None

    def _parse_upload_date(self, date_str: Optional[str]) -> Optional[str]:
        """解析上传日期"""
        if not date_str:
            return None
        
        try:
            # yt-dlp通常返回YYYYMMDD格式
            if len(date_str) == 8 and date_str.isdigit():
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                return f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, IndexError):
            pass
        
        return None

    def _get_best_resolution(self, formats: List[Dict]) -> Optional[str]:
        """获取最佳分辨率"""
        if not formats:
            return None
        
        best_format = None
        max_height = 0
        
        for fmt in formats:
            height = fmt.get('height')
            if height and height > max_height:
                max_height = height
                best_format = fmt
        
        if best_format:
            width = best_format.get('width')
            height = best_format.get('height')
            if width and height:
                return f"{width}x{height}"
        
        return None

    async def update_task_celery_id(
        self,
        db: Session,
        task_id: str,
        celery_task_id: str
    ) -> bool:
        """更新任务的Celery任务ID
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            celery_task_id: Celery任务ID
            
        Returns:
            是否更新成功
        """
        try:
            task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
            if not task:
                download_logger.warning(
                    "任务不存在",
                    task_id=task_id
                )
                return False
                
            task.celery_task_id = celery_task_id
            task.updated_at = datetime.now()
            db.commit()
            
            download_logger.info(
                "Celery任务ID更新成功",
                task_id=task_id,
                celery_task_id=celery_task_id
            )
            return True
            
        except Exception as e:
            download_logger.error(
                "更新Celery任务ID失败",
                task_id=task_id,
                celery_task_id=celery_task_id,
                error=str(e)
            )
            db.rollback()
            return False


    async def create_download_task(
        self,
        db: Session,
        user_id: int,
        url: str,
        video_info: Dict,
        options: Dict = None
    ) -> DownloadTask:
        """创建下载任务
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            url: 视频URL
            video_info: 视频信息
            options: 下载选项
            
        Returns:
            创建的下载任务
        """
        try:
            # 检查是否已存在相同URL的未完成任务
            existing_task = db.query(DownloadTask).filter(
                DownloadTask.user_id == user_id,
                DownloadTask.url == url,
                DownloadTask.status.in_(["pending", "processing"])
            ).first()
            
            if existing_task:
                download_logger.warning(
                    "下载任务已存在",
                    user_id=user_id,
                    url=url,
                    existing_task_id=existing_task.id
                )
                return existing_task
            
            # 创建新的下载任务
            task = DownloadTask(
                user_id=user_id,
                url=url,
                platform=video_info.get('platform'),
                status="pending",
                quality=options.get('quality', 'best') if options else 'best',
                format_preference=options.get('format', 'mp4') if options else 'mp4',
                audio_only=options.get('download_audio', False) if options else False,
                options=options or {}
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            download_logger.info(
                "下载任务创建成功",
                task_id=task.id,
                user_id=user_id,
                url=url,
                platform=video_info.get('platform')
            )
            
            return task
            
        except Exception as e:
            download_logger.error(
                "创建下载任务失败",
                user_id=user_id,
                url=url,
                error=str(e)
            )
            db.rollback()
            raise


# 全局下载服务实例
download_service = DownloadService()