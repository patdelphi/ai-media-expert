"""视频下载服务

实现视频下载的核心业务逻辑，包括URL解析、平台适配、下载管理等。
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import yt_dlp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import download_logger
from app.models.video import DownloadTask, Video
from app.services.platform_adapters import get_platform_adapter


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
    
    def extract_video_info(self, url: str) -> Dict:
        """提取视频信息
        
        使用yt-dlp提取视频的基本信息，不进行实际下载。
        
        Args:
            url: 视频URL
        
        Returns:
            包含视频信息的字典
        
        Raises:
            Exception: 当URL无效或提取失败时
        """
        try:
            # 配置yt-dlp选项
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,  # 只提取信息，不下载
            }
            
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
                    "Video info extracted",
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