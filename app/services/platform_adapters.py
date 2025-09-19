"""平台适配器模块

为不同的视频平台提供专门的适配器，处理平台特有的逻辑和需求。
集成了Douyin_TikTok_Download_API项目的爬虫组件。
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs

from app.core.app_logging import download_logger
from app.crawlers.hybrid.hybrid_crawler import HybridCrawler


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
    """TikTok平台适配器
    
    集成HybridCrawler提供更强大的解析能力。
    """
    
    def __init__(self):
        self.hybrid_crawler = HybridCrawler()
    
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
    
    async def parse_video_info(self, url: str) -> Dict[str, Any]:
        """使用HybridCrawler解析视频信息
        
        Args:
            url: 视频URL
            
        Returns:
            Dict[str, Any]: 解析后的视频信息
        """
        try:
            return await self.hybrid_crawler.hybrid_parsing_single_video(url, minimal=False)
        except Exception as e:
            download_logger.error(f"TikTok视频解析失败: {e}")
            raise
    
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


class BilibiliAdapter(BasePlatformAdapter):
    """B站平台适配器"""
    
    def get_platform_name(self) -> str:
        return "bilibili"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'bilibili\.com/video/[Bb][Vv]\w+',
            r'b23\.tv/\w+',
            r'bilibili\.com/s/video/[Bb][Vv]\w+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        # 匹配BV号
        match = re.search(r'[Bb][Vv](\w+)', url)
        if match:
            return f"BV{match.group(1)}"
        
        # 匹配短链接
        if 'b23.tv' in url:
            return url.split('/')[-1]
        
        return None
    
    def get_custom_options(self) -> Dict:
        return {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/'
            }
        }


class XiaohongshuAdapter(BasePlatformAdapter):
    """小红书平台适配器"""
    
    def get_platform_name(self) -> str:
        return "xiaohongshu"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'xiaohongshu\.com/explore/\w+',
            r'xiaohongshu\.com/discovery/item/\w+',
            r'xhslink\.com/\w+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        # 匹配explore链接
        match = re.search(r'/explore/(\w+)', url)
        if match:
            return match.group(1)
        
        # 匹配discovery链接
        match = re.search(r'/item/(\w+)', url)
        if match:
            return match.group(1)
        
        # 匹配短链接
        if 'xhslink.com' in url:
            return url.split('/')[-1]
        
        return None
    
    def get_custom_options(self) -> Dict:
        return {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'Referer': 'https://www.xiaohongshu.com/'
            }
        }


class KuaishouAdapter(BasePlatformAdapter):
    """快手平台适配器"""
    
    def get_platform_name(self) -> str:
        return "kuaishou"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'kuaishou\.com/profile/\w+',
            r'kuaishou\.com/short-video/\w+',
            r'chenzhongtech\.com/\w+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        # 匹配短视频链接
        match = re.search(r'/short-video/(\w+)', url)
        if match:
            return match.group(1)
        
        # 匹配用户主页链接
        match = re.search(r'/profile/(\w+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def get_custom_options(self) -> Dict:
        return {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'Referer': 'https://www.kuaishou.com/'
            }
        }


class WeixinAdapter(BasePlatformAdapter):
    """微信视频号平台适配器"""
    
    def get_platform_name(self) -> str:
        return "weixin"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'mp\.weixin\.qq\.com/s\?.*',
            r'weixin\.qq\.com/r/\w+',
            r'channels\.weixin\.qq\.com/\w+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        # 从URL参数中提取
        parsed = urlparse(url)
        if parsed.query:
            params = parse_qs(parsed.query)
            # 尝试获取不同的ID参数
            for key in ['__biz', 'mid', 'idx', 'sn']:
                if key in params:
                    return params[key][0]
        
        # 匹配路径中的ID
        match = re.search(r'/r/(\w+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def get_custom_options(self) -> Dict:
        return {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'Referer': 'https://mp.weixin.qq.com/'
            }
        }


class DouyinAdapter(BasePlatformAdapter):
    """抖音平台适配器
    
    集成HybridCrawler提供更强大的解析能力。
    """
    
    def __init__(self):
        self.hybrid_crawler = HybridCrawler()
    
    def get_platform_name(self) -> str:
        return "douyin"
    
    def validate_url(self, url: str) -> bool:
        patterns = [
            r'douyin\.com.*?/video/\d+',
            r'iesdouyin\.com.*?/share/video/\d+',
            r'v\.douyin\.com/\w+',
            r'douyin\.com/user/\w+',
            r'douyin\.com/aweme/v1/.*',
            r'www\.douyin\.com/.*',
            r'douyin\.com/note/\d+',
            r'douyin\.com/discover\?modal_id=\d+'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        # 匹配完整URL中的视频ID
        patterns = [
            r'/video/(\d+)',  # 标准视频链接
            r'modal_id=(\d+)',  # 发现页面模态框
            r'/note/(\d+)',  # 笔记链接
            r'aweme_id=(\d+)',  # API链接
            r'/share/video/(\d+)',  # 分享链接
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 匹配短链接
        if 'v.douyin.com' in url:
            short_code = url.split('/')[-1].split('?')[0]
            return short_code
        
        return None
    
    async def parse_video_info(self, url: str) -> Dict[str, Any]:
        """使用HybridCrawler解析视频信息
        
        Args:
            url: 视频URL
            
        Returns:
            Dict[str, Any]: 解析后的视频信息
        """
        try:
            return await self.hybrid_crawler.hybrid_parsing_single_video(url, minimal=False)
        except Exception as e:
            download_logger.error(f"抖音视频解析失败: {e}")
            raise
    
    def preprocess_url(self, url: str) -> str:
        """预处理抖音URL，展开短链接等"""
        # 这里可以添加短链接展开逻辑
        return url
    
    def get_custom_options(self) -> Dict:
        return {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.douyin.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Upgrade-Insecure-Requests': '1'
            },
            'format': 'best[height<=720]/best',  # 优先720p质量
            'no_warnings': True,
            'extract_flat': False
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
        对应的平台适配器实例，如果不支持则返回None
    """
    adapters = [
        TikTokAdapter(),
        DouyinAdapter(),
        BilibiliAdapter(),
        XiaohongshuAdapter(),
        KuaishouAdapter(),
        WeixinAdapter(),
    ]
    
    for adapter in adapters:
        if adapter.validate_url(url):
            download_logger.info(
                "Found platform adapter",
                platform=adapter.get_platform_name(),
                url=url
            )
            return adapter
    
    download_logger.warning(
        "No platform adapter found",
        url=url
    )
    return None


def get_all_supported_platforms() -> List[Dict[str, Any]]:
    """获取所有支持的平台信息
    
    Returns:
        支持的平台列表
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
    
    return platforms


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