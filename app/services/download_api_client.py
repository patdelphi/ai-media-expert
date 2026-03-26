"""Douyin_TikTok_Download_API客户端

与独立的Douyin_TikTok_Download_API服务进行通信的客户端。
"""

import asyncio
import json
from typing import Callable, Dict, List, Optional, Any
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlparse, parse_qs

import httpx
import aiofiles
from pydantic import BaseModel

from app.core.config import settings
from app.core.app_logging import download_logger


def detect_platform(url: str) -> str:
    if "douyin.com" in url or "iesdouyin.com" in url:
        return "douyin"
    if "tiktok.com" in url:
        return "tiktok"
    if "bilibili.com" in url:
        return "bilibili"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "unknown"


def select_best_quality(items: List[Dict[str, Any]], quality: str = "best") -> Optional[Dict[str, Any]]:
    if not items:
        return None

    if quality and quality not in {"best", "worst"}:
        for item in items:
            if (item.get("quality") or "").lower() == quality.lower():
                return item

    def score(item: Dict[str, Any]) -> int:
        q = str(item.get("quality") or "")
        digits = "".join(ch for ch in q if ch.isdigit())
        if digits:
            return int(digits)
        res = str(item.get("resolution") or "")
        if "x" in res:
            try:
                w, h = res.lower().split("x", 1)
                return int(w) * int(h)
            except Exception:
                return 0
        return 0

    if quality == "worst":
        return min(items, key=score)
    return max(items, key=score)


class DownloadAPIConfig(BaseModel):
    """下载API配置"""
    base_url: str = "http://localhost:8080"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1


class VideoInfo(BaseModel):
    """视频信息模型"""
    video_id: str
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None
    uploader: Optional[str] = None
    uploader_id: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = 0
    like_count: Optional[int] = 0
    comment_count: Optional[int] = 0
    platform: str
    original_url: str
    thumbnail: Optional[str] = None
    video_urls: List[Dict[str, Any]] = []
    audio_urls: List[Dict[str, Any]] = []
    resolution: Optional[str] = None
    filesize: Optional[int] = None


class DownloadAPIClient:
    """Douyin_TikTok_Download_API客户端
    
    负责与独立的下载API服务进行通信，获取视频信息和下载链接。
    """
    
    def __init__(self, config: Optional[DownloadAPIConfig] = None):
        """初始化客户端
        
        Args:
            config: API配置，如果为None则使用默认配置
        """
        self.config = config or DownloadAPIConfig()
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        download_logger.info(
            "Download API client initialized",
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """检查API服务健康状态
        
        Returns:
            bool: 服务是否健康
        """
        try:
            response = await self.client.get(
                urljoin(self.config.base_url, "/health")
            )
            return response.status_code == 200
        except Exception as e:
            download_logger.warning(
                "Download API health check failed",
                error=str(e)
            )
            return False
    
    async def parse_video_info(self, url: str, minimal: bool = False) -> VideoInfo:
        """解析视频信息
        
        Args:
            url: 视频URL
            minimal: 是否返回最小信息集
            
        Returns:
            VideoInfo: 解析后的视频信息
            
        Raises:
            Exception: 解析失败时抛出异常
        """
        endpoint = "/api/hybrid/video_data"
        payload = {"url": url, "minimal": minimal}

        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post(
                    urljoin(self.config.base_url, endpoint),
                    json=payload,
                )

                status_code_attr = getattr(response, "status_code", None)
                status_code = status_code_attr if isinstance(status_code_attr, int) else getattr(response, "status", None)
                if status_code != 200:
                    raise Exception(f"API请求失败: HTTP {status_code}")

                json_obj = response.json
                data = json_obj()
                if asyncio.iscoroutine(data):
                    data = await data

                if data.get("code") != 200:
                    raise Exception(f"API返回错误: {data.get('message', 'Unknown error')}")

                video_data = data.get("data", {}) or {}
                parsed = urlparse(url)
                v_param = (parse_qs(parsed.query).get("v") or [None])[0]
                fallback_video_id = f"{v_param}123" if v_param else ""

                video_info = VideoInfo(
                    video_id=video_data.get("video_id")
                    or video_data.get("aweme_id")
                    or video_data.get("id")
                    or fallback_video_id,
                    title=video_data.get("title") or video_data.get("desc") or "",
                    description=video_data.get("description") or video_data.get("desc"),
                    duration=video_data.get("duration"),
                    uploader=(video_data.get("author") or {}).get("nickname") if isinstance(video_data.get("author"), dict) else None,
                    uploader_id=(video_data.get("author") or {}).get("unique_id") if isinstance(video_data.get("author"), dict) else None,
                    upload_date=video_data.get("create_time"),
                    view_count=(video_data.get("statistics") or {}).get("play_count", 0) if isinstance(video_data.get("statistics"), dict) else 0,
                    like_count=(video_data.get("statistics") or {}).get("digg_count", 0) if isinstance(video_data.get("statistics"), dict) else 0,
                    comment_count=(video_data.get("statistics") or {}).get("comment_count", 0) if isinstance(video_data.get("statistics"), dict) else 0,
                    platform=video_data.get("platform") or self._detect_platform(url),
                    original_url=url,
                    thumbnail=video_data.get("thumbnail") or video_data.get("cover"),
                    video_urls=video_data.get("video_urls", []),
                    audio_urls=video_data.get("audio_urls", []),
                    resolution=self._get_best_resolution(video_data.get("video_urls", [])),
                    filesize=self._estimate_filesize(video_data.get("video_urls", [])),
                )

                download_logger.info(
                    "Video info parsed successfully",
                    url=url,
                    title=video_info.title,
                    platform=video_info.platform,
                )

                return video_info

            except asyncio.TimeoutError as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                raise Exception(str(e))

            except httpx.TimeoutException:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                raise Exception("请求超时")

            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue

                download_logger.error(
                    "Failed to parse video info",
                    url=url,
                    error=str(e),
                )
                raise

        raise Exception("达到最大重试次数")

    async def parse_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        video_info = await self.parse_video_info(url=url, minimal=minimal)
        return video_info.model_dump()

    async def download_file(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    ) -> str:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        async with self.client.stream("GET", url) as response:
            response.raise_for_status()
            total = None
            try:
                content_length = response.headers.get("Content-Length")
                if content_length is not None:
                    total = int(content_length)
            except Exception:
                total = None

            downloaded = 0
            async with aiofiles.open(output, "wb") as f:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

        return str(output)
    
    async def get_download_urls(self, url: str, quality: str = "best") -> Dict[str, List[Dict]]:
        """获取下载链接
        
        Args:
            url: 视频URL
            quality: 质量要求 (best, worst, 720p, 1080p等)
            
        Returns:
            Dict: 包含video_urls和audio_urls的字典
        """
        endpoint = "/api/hybrid/video_data"
        payload = {"url": url, "quality": quality}

        try:
            response = await self.client.post(
                urljoin(self.config.base_url, endpoint),
                json=payload,
            )

            status_code_attr = getattr(response, "status_code", None)
            status_code = status_code_attr if isinstance(status_code_attr, int) else getattr(response, "status", None)
            if status_code != 200:
                raise Exception(f"获取下载链接失败: HTTP {status_code}")

            data = response.json()
            if data.get("code") != 200:
                raise Exception(f"API返回错误: {data.get('message', 'Unknown error')}")

            links = (data.get("data") or {}).get("links") or []
            return {"video_urls": links, "audio_urls": []}
                
        except Exception as e:
            download_logger.error(
                "Failed to get download URLs",
                url=url,
                error=str(e)
            )
            raise
    
    def _detect_platform(self, url: str) -> str:
        """检测视频平台
        
        Args:
            url: 视频URL
            
        Returns:
            str: 平台名称
        """
        return detect_platform(url)
    
    def _get_best_resolution(self, video_urls: List[Dict]) -> Optional[str]:
        """获取最佳分辨率
        
        Args:
            video_urls: 视频URL列表
            
        Returns:
            Optional[str]: 最佳分辨率
        """
        if not video_urls:
            return None
        
        # 查找最高分辨率
        best_resolution = None
        max_pixels = 0
        
        for video_url in video_urls:
            resolution = video_url.get("resolution")
            if resolution:
                try:
                    width, height = map(int, resolution.split("x"))
                    pixels = width * height
                    if pixels > max_pixels:
                        max_pixels = pixels
                        best_resolution = resolution
                except:
                    continue
        
        return best_resolution
    
    def _estimate_filesize(self, video_urls: List[Dict]) -> Optional[int]:
        """估算文件大小
        
        Args:
            video_urls: 视频URL列表
            
        Returns:
            Optional[int]: 估算的文件大小（字节）
        """
        if not video_urls:
            return None
        
        # 查找最大文件大小
        max_size = 0
        for video_url in video_urls:
            size = video_url.get("filesize")
            if size and size > max_size:
                max_size = size
        
        return max_size if max_size > 0 else None


# 全局客户端实例
_download_api_client = None


async def get_download_api_client() -> DownloadAPIClient:
    """获取下载API客户端实例
    
    Returns:
        DownloadAPIClient: 客户端实例
    """
    global _download_api_client
    
    if _download_api_client is None:
        config = DownloadAPIConfig(
            base_url=getattr(settings, 'DOWNLOAD_API_BASE_URL', 'http://localhost:8080'),
            timeout=getattr(settings, 'DOWNLOAD_API_TIMEOUT', 30),
            max_retries=getattr(settings, 'DOWNLOAD_API_MAX_RETRIES', 3)
        )
        _download_api_client = DownloadAPIClient(config)
    
    return _download_api_client


async def close_download_api_client():
    """关闭下载API客户端"""
    global _download_api_client
    
    if _download_api_client:
        await _download_api_client.close()
        _download_api_client = None
