"""视频下载服务

实现视频下载的核心业务逻辑，包括URL解析、平台适配、下载管理等。
"""

import os
import re
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import yt_dlp
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.app_logging import download_logger
from app.models.video import DownloadTask, Video
from app.services.platform_adapters import get_platform_adapter
from app.services.video_parsing_service import video_parsing_service


class DownloadService:
    """视频下载服务类
    
    负责管理视频下载的整个生命周期，包括URL解析、信息提取、
    文件下载、元数据保存等功能。
    """
    
    def __init__(self):
        self.download_dir = settings.download_dir
        self.max_concurrent = settings.max_concurrent_downloads
        self.timeout = settings.download_timeout
        
        # 确保下载目录存在
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    async def create_download_task(
        self,
        db: Session,
        user_id: str,
        url: str,
        video_info: Dict,
        options: Dict
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
        from uuid import uuid4
        
        task = DownloadTask(
            id=str(uuid4()),
            user_id=user_id,
            url=url,
            title=video_info.get('title', 'Unknown Title'),
            platform=video_info.get('platform', 'unknown'),
            status='pending',
            progress=0.0,
            options=options,
            video_info=video_info
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        download_logger.info(
            "Download task created",
            task_id=task.id,
            user_id=user_id,
            url=url,
            title=task.title
        )
        
        return task
    
    async def get_user_tasks(
        self,
        db: Session,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[DownloadTask]:
        """获取用户的下载任务列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            status: 状态过滤
            limit: 数量限制
            offset: 偏移量
            
        Returns:
            任务列表
        """
        query = db.query(DownloadTask).filter(DownloadTask.user_id == user_id)
        
        if status:
            query = query.filter(DownloadTask.status == status)
        
        tasks = query.order_by(DownloadTask.created_at.desc()).offset(offset).limit(limit).all()
        
        return tasks
    
    async def get_task_by_id(
        self,
        db: Session,
        task_id: str,
        user_id: str
    ) -> Optional[DownloadTask]:
        """根据ID获取任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            任务对象或None
        """
        return db.query(DownloadTask).filter(
            DownloadTask.id == task_id,
            DownloadTask.user_id == user_id
        ).first()
    
    async def cancel_task(
        self,
        db: Session,
        task_id: str,
        user_id: str
    ) -> bool:
        """取消任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        task = await self.get_task_by_id(db, task_id, user_id)
        if not task or task.status in ['completed', 'cancelled']:
            return False
        
        task.status = 'cancelled'
        task.updated_at = datetime.utcnow()
        db.commit()
        
        download_logger.info(
            "Task cancelled",
            task_id=task_id,
            user_id=user_id
        )
        
        return True
    
    async def reset_task(
        self,
        db: Session,
        task_id: str
    ) -> bool:
        """重置任务状态
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
        if not task:
            return False
        
        task.status = 'pending'
        task.progress = 0.0
        task.error_message = None
        task.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    async def delete_task(
        self,
        db: Session,
        task_id: str,
        user_id: str
    ) -> bool:
        """删除任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        task = await self.get_task_by_id(db, task_id, user_id)
        if not task:
            return False
        
        # 如果有文件，尝试删除
        if task.file_path and os.path.exists(task.file_path):
            try:
                os.remove(task.file_path)
            except Exception as e:
                download_logger.warning(
                    "Failed to delete file",
                    file_path=task.file_path,
                    error=str(e)
                )
        
        db.delete(task)
        db.commit()
        
        download_logger.info(
            "Task deleted",
            task_id=task_id,
            user_id=user_id
        )
        
        return True
    
    async def process_download_task(self, task_id: str, db: Session):
        """处理下载任务
        
        Args:
            task_id: 任务ID
            db: 数据库会话
        """
        task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
        if not task:
            download_logger.error("Task not found", task_id=task_id)
            return
        
        try:
            # 更新任务状态为下载中
            task.status = 'downloading'
            task.updated_at = datetime.utcnow()
            db.commit()
            
            download_logger.info(
                "Starting download task",
                task_id=task_id,
                url=task.url,
                title=task.title
            )
            
            # 实际的视频下载逻辑
            await self._download_video_file(task, db)
            
            if task.status != 'cancelled':
                task.status = 'completed'
                task.progress = 100.0
                task.updated_at = datetime.utcnow()
                db.commit()
                
                download_logger.info(
                    "Download task completed",
                    task_id=task_id,
                    file_path=task.file_path
                )
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.updated_at = datetime.utcnow()
            db.commit()
            
            download_logger.error(
                "Download task failed",
                task_id=task_id,
                error=str(e)
            )
    
    async def _download_video_file(self, task: DownloadTask, db: Session):
        """实际下载视频文件
        
        Args:
            task: 下载任务
            db: 数据库会话
        """
        import asyncio
        import httpx
        from pathlib import Path
        
        try:
            # 从视频信息中获取下载URL
            video_info = task.video_info or {}
            video_url = video_info.get('video_url')
            
            if not video_url:
                # 如果没有直接的视频URL，尝试使用yt-dlp
                await self._download_with_ytdlp(task, db)
                return
            
            # 准备下载路径
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', task.title or 'video')
            file_extension = video_info.get('ext', 'mp4')
            filename = f"{safe_title}.{file_extension}"
            file_path = Path(self.download_dir) / filename
            
            # 确保下载目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 开始下载
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream('GET', video_url) as response:
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    with open(file_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            if task.status == 'cancelled':
                                f.close()
                                if file_path.exists():
                                    file_path.unlink()
                                return
                            
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # 更新进度
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                task.progress = min(progress, 99.0)  # 保留1%给后处理
                                task.updated_at = datetime.utcnow()
                                db.commit()
            
            # 设置文件路径
            task.file_path = str(file_path)
            task.progress = 100.0
            db.commit()
            
            download_logger.info(
                "Video downloaded successfully",
                task_id=task.id,
                file_path=str(file_path),
                file_size=downloaded
            )
            
        except Exception as e:
            download_logger.error(
                "Video download failed",
                task_id=task.id,
                error=str(e)
            )
            raise
    
    async def _download_with_ytdlp(self, task: DownloadTask, db: Session):
        """使用yt-dlp下载视频
        
        Args:
            task: 下载任务
            db: 数据库会话
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def progress_hook(d):
            """yt-dlp进度回调"""
            if d['status'] == 'downloading':
                if 'total_bytes' in d and d['total_bytes']:
                    progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif '_percent_str' in d:
                    progress_str = d['_percent_str'].replace('%', '')
                    try:
                        progress = float(progress_str)
                    except:
                        progress = 0
                else:
                    progress = 0
                
                task.progress = min(progress, 99.0)
                task.updated_at = datetime.utcnow()
                db.commit()
            
            elif d['status'] == 'finished':
                task.file_path = d['filename']
                task.progress = 100.0
                db.commit()
        
        def download_with_ytdlp():
            """在线程中执行yt-dlp下载"""
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', task.title or 'video')
            
            ydl_opts = {
                'outtmpl': str(Path(self.download_dir) / f'{safe_title}.%(ext)s'),
                'format': 'best[height<=720]/best',  # 优先720p，回退到最佳质量
                'progress_hooks': [progress_hook],
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([task.url])
        
        # 在线程池中执行下载
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, download_with_ytdlp)
    
    def download_video(
        self, 
        task_id: int, 
        url: str, 
        options: Dict,
        progress_callback=None
    ) -> Tuple[str, Dict]:
        """下载视频文件
        
        执行实际的视频下载操作。
        
        Args:
            task_id: 下载任务ID
            url: 视频URL
            options: 下载选项
            progress_callback: 进度回调函数
        
        Returns:
            (文件路径, 视频信息) 的元组
        
        Raises:
            Exception: 当下载失败时
        """
        try:
            # 首先提取视频信息
            video_info = self.extract_video_info(url)
            
            # 生成文件名和路径
            filename = self._generate_filename(video_info, options)
            file_path = self.download_dir / filename
            
            # 配置yt-dlp下载选项
            ydl_opts = self._build_download_options(file_path, options)
            
            # 添加进度钩子
            if progress_callback:
                ydl_opts['progress_hooks'] = [progress_callback]
            
            # 执行下载
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 验证文件是否下载成功
            if not file_path.exists():
                raise Exception("Downloaded file not found")
            
            # 更新文件信息
            video_info.update({
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
            })
            
            download_logger.info(
                "Video downloaded successfully",
                task_id=task_id,
                url=url,
                file_path=str(file_path),
                file_size=video_info['file_size']
            )
            
            return str(file_path), video_info
            
        except Exception as e:
            download_logger.error(
                "Video download failed",
                task_id=task_id,
                url=url,
                error=str(e)
            )
            raise Exception(f"Video download failed: {str(e)}")
    
    def validate_url(self, url: str) -> bool:
        """验证URL是否有效
        
        Args:
            url: 要验证的URL
        
        Returns:
            URL是否有效
        """
        try:
            # 基本URL格式验证
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # 检查是否为支持的平台
            platform = self._detect_platform(url)
            if not platform:
                return False
            
            # 尝试提取基本信息（不下载）
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': True,  # 快速提取
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info is not None
                
        except Exception:
            return False
    
    def get_supported_platforms(self) -> List[str]:
        """获取支持的平台列表
        
        Returns:
            支持的平台名称列表
        """
        return [
            'tiktok', 'douyin', 'youtube', 'bilibili', 
            'instagram', 'twitter', 'facebook', 'kuaishou'
        ]
    
    def _detect_platform(self, url: str) -> Optional[str]:
        """检测视频平台
        
        Args:
            url: 视频URL
        
        Returns:
            平台名称，如果无法识别则返回None
        """
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
        """解析上传日期
        
        Args:
            date_str: 日期字符串（YYYYMMDD格式）
        
        Returns:
            ISO格式的日期字符串
        """
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
        """获取最佳分辨率
        
        Args:
            formats: 格式列表
        
        Returns:
            分辨率字符串（如"1920x1080"）
        """
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
    
    def _generate_filename(self, video_info: Dict, options: Dict) -> str:
        """生成文件名
        
        Args:
            video_info: 视频信息
            options: 下载选项
        
        Returns:
            生成的文件名
        """
        # 清理标题，移除不安全的字符
        title = video_info.get('title', 'video')
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = safe_title[:100]  # 限制长度
        
        # 获取扩展名
        ext = options.get('format_preference', 'mp4')
        if not ext.startswith('.'):
            ext = f'.{ext}'
        
        # 添加时间戳避免重名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 构建文件名
        filename = f"{safe_title}_{timestamp}{ext}"
        
        return filename
    
    def _build_download_options(self, file_path: Path, options: Dict) -> Dict:
        """构建yt-dlp下载选项
        
        Args:
            file_path: 输出文件路径
            options: 用户选项
        
        Returns:
            yt-dlp选项字典
        """
        ydl_opts = {
            'outtmpl': str(file_path),
            'format': self._build_format_selector(options),
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['zh', 'en'],
            'ignoreerrors': False,
        }
        
        # 仅音频选项
        if options.get('audio_only', False):
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        
        return ydl_opts
    
    def _build_format_selector(self, options: Dict) -> str:
        """构建格式选择器
        
        Args:
            options: 下载选项
        
        Returns:
            yt-dlp格式选择器字符串
        """
        quality = options.get('quality', 'best')
        format_pref = options.get('format_preference', 'mp4')
        
        if quality == 'best':
            return f'best[ext={format_pref}]/best'
        elif quality == 'worst':
            return f'worst[ext={format_pref}]/worst'
        elif quality.endswith('p'):
            # 特定分辨率，如720p, 1080p
            height = quality[:-1]
            return f'best[height<={height}][ext={format_pref}]/best[height<={height}]'
        else:
            return f'best[ext={format_pref}]/best'