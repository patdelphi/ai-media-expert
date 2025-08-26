"""平台适配器模块

为不同的视频平台提供专门的适配器，处理平台特有的逻辑和需求。
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from app.core.logging import download_logger


class BasePlatformAdapter(ABC):
    """平台适配器基类"""
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """获取平台名称"""
        pass
    
    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """验证URL是否属于该平台"""
        pass
    
    @abstractmethod
    def extract_video_id(self, url: str) -> Optional[str]:
        """从URL中提取视频ID"""
        pass
    
    def preprocess_url(self, url: str) -> str:
        """预处理URL（可选重写）"""
        return url
    
    def get_custom_options(self) -> Dict:
        """获取平台特定的下载选项（可选重写）"""
        return {}


class TikTokAdapter(BasePlatformAdapter):
    """TikTok平台适配器"""
    
    def get_platform_name(self) -> str:
        return "tiktok"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'tiktok\.com.*?/video/\d+',
            r'vm\.tiktok\.com/\w+',
            r'tiktok\.com/@[\w.-]+/video/\d+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        # 匹配完整URL中的视频ID
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        
        # 匹配短链接
        if 'vm.tiktok.com' in url:
            return url.split('/')[-1]
        
        return None
    
    def preprocess_url(self, url: str) -> str:
        """预处理TikTok URL，展开短链接等"""
        # 这里可以添加短链接展开逻辑
        return url
    
    def get_custom_options(self) -> Dict:
        return {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            }
        }


class DouyinAdapter(BasePlatformAdapter):
    """抖音平台适配器"""
    
    def get_platform_name(self) -> str:
        return "douyin"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'douyin\.com.*?/video/\d+',
            r'iesdouyin\.com.*?/share/video/\d+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    def get_custom_options(self) -> Dict:
        return {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36'
            }
        }


class YouTubeAdapter(BasePlatformAdapter):
    """YouTube平台适配器"""
    
    def get_platform_name(self) -> str:
        return "youtube"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'youtube\.com/embed/',
            r'youtube\.com/v/'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        # 标准YouTube URL
        if 'youtube.com/watch' in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return params.get('v', [None])[0]
        
        # 短链接
        if 'youtu.be/' in url:
            return url.split('/')[-1].split('?')[0]
        
        # 嵌入链接
        if 'youtube.com/embed/' in url:
            return url.split('/embed/')[-1].split('?')[0]
        
        return None
    
    def get_custom_options(self) -> Dict:
        return {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['zh', 'en', 'zh-Hans', 'zh-Hant']
        }


class BilibiliAdapter(BasePlatformAdapter):
    """哔哩哔哩平台适配器"""
    
    def get_platform_name(self) -> str:
        return "bilibili"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'bilibili\.com/video/[Bb][Vv]\w+',
            r'b23\.tv/\w+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        # BV号格式
        match = re.search(r'/video/([Bb][Vv]\w+)', url)
        if match:
            return match.group(1)
        
        # 短链接需要展开
        if 'b23.tv' in url:
            return url.split('/')[-1]
        
        return None
    
    def get_custom_options(self) -> Dict:
        return {
            'http_headers': {
                'Referer': 'https://www.bilibili.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }


class InstagramAdapter(BasePlatformAdapter):
    """Instagram平台适配器"""
    
    def get_platform_name(self) -> str:
        return "instagram"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'instagram\.com/p/\w+',
            r'instagram\.com/reel/\w+',
            r'instagram\.com/tv/\w+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        match = re.search(r'/(p|reel|tv)/(\w+)', url)
        if match:
            return match.group(2)
        return None
    
    def get_custom_options(self) -> Dict:
        return {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            }
        }


class TwitterAdapter(BasePlatformAdapter):
    """Twitter/X平台适配器"""
    
    def get_platform_name(self) -> str:
        return "twitter"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'twitter\.com/\w+/status/\d+',
            r'x\.com/\w+/status/\d+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        match = re.search(r'/status/(\d+)', url)
        if match:
            return match.group(1)
        return None


class KuaishouAdapter(BasePlatformAdapter):
    """快手平台适配器"""
    
    def get_platform_name(self) -> str:
        return "kuaishou"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'kuaishou\.com/profile/\w+',
            r'kwai\.com/\w+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        # 快手的URL结构比较复杂，需要根据实际情况调整
        match = re.search(r'/profile/(\w+)', url)
        if match:
            return match.group(1)
        return None


# 平台适配器注册表
PLATFORM_ADAPTERS = {
    'tiktok': TikTokAdapter(),
    'douyin': DouyinAdapter(),
    'youtube': YouTubeAdapter(),
    'bilibili': BilibiliAdapter(),
    'instagram': InstagramAdapter(),
    'twitter': TwitterAdapter(),
    'kuaishou': KuaishouAdapter(),
}


def get_platform_adapter(url: str) -> Optional[BasePlatformAdapter]:
    """根据URL获取对应的平台适配器
    
    Args:
        url: 视频URL
    
    Returns:
        对应的平台适配器，如果没有找到则返回None
    """
    for adapter in PLATFORM_ADAPTERS.values():
        if adapter.validate_url(url):
            download_logger.debug(
                "Platform adapter found",
                url=url,
                platform=adapter.get_platform_name()
            )
            return adapter
    
    download_logger.warning(
        "No platform adapter found",
        url=url
    )
    return None


def get_supported_platforms() -> List[str]:
    """获取所有支持的平台列表
    
    Returns:
        支持的平台名称列表
    """
    return list(PLATFORM_ADAPTERS.keys())


def is_url_supported(url: str) -> bool:
    """检查URL是否被支持
    
    Args:
        url: 要检查的URL
    
    Returns:
        是否支持该URL
    """
    return get_platform_adapter(url) is not None