"""视频解析服务

集成多平台视频解析功能，支持抖音、TikTok、B站、小红书等平台的视频信息提取。
基于Douyin_TikTok_Download_API项目的核心算法实现。
"""

import asyncio
import re
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse, parse_qs
import httpx
from datetime import datetime

from app.core.config import settings
from app.core.app_logging import download_logger
from app.services.platform_adapters import get_platform_adapter
from app.crawlers.hybrid.hybrid_crawler import HybridCrawler


class VideoParsingService:
    """视频解析服务类
    
    负责解析各个平台的视频链接，提取视频信息和下载地址。
    支持抖音、TikTok、B站、小红书、快手、视频号等主流平台。
    """
    
    def __init__(self):
        self.timeout = 30
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.hybrid_crawler = HybridCrawler()
    
    async def parse_video_info(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析视频信息
        
        Args:
            url: 视频链接
            minimal: 是否返回最小信息集
            
        Returns:
            包含视频信息的字典
            
        Raises:
            ValueError: 当URL无效或不支持时
            Exception: 当解析失败时
        """
        try:
            platform = self._detect_platform(url)
            
            if platform == "douyin":
                return await self._parse_douyin_video(url, minimal)
            elif platform == "tiktok":
                return await self._parse_tiktok_video(url, minimal)
            elif platform == "bilibili":
                return await self._parse_bilibili_video(url, minimal)
            elif platform == "xiaohongshu":
                return await self._parse_xiaohongshu_video(url, minimal)
            elif platform == "kuaishou":
                return await self._parse_kuaishou_video(url, minimal)
            elif platform == "weixin":
                return await self._parse_weixin_video(url, minimal)
            else:
                raise ValueError(f"不支持的平台: {platform}")
                
        except Exception as e:
            download_logger.error(
                "视频解析失败",
                url=url,
                error=str(e)
            )
            raise Exception(f"视频解析失败: {str(e)}")
    
    def _detect_platform(self, url: str) -> str:
        """检测视频平台
        
        Args:
            url: 视频链接
            
        Returns:
            平台名称
        """
        url_lower = url.lower()
        
        if 'douyin.com' in url_lower or 'iesdouyin.com' in url_lower:
            return 'douyin'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'bilibili.com' in url_lower or 'b23.tv' in url_lower:
            return 'bilibili'
        elif 'xiaohongshu.com' in url_lower or 'xhslink.com' in url_lower:
            return 'xiaohongshu'
        elif 'kuaishou.com' in url_lower or 'chenzhongtech.com' in url_lower:
            return 'kuaishou'
        elif 'weixin.qq.com' in url_lower or 'mp.weixin.qq.com' in url_lower:
            return 'weixin'
        else:
            return 'unknown'
    
    async def _parse_douyin_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析抖音视频
        
        Args:
            url: 抖音视频链接
            minimal: 是否返回最小信息
            
        Returns:
            视频信息字典
        """
        try:
             # 使用HybridCrawler解析抖音视频
             video_data = await self.hybrid_crawler.hybrid_parsing_single_video(url, minimal=False)
             
             if video_data and video_data.get('platform') == 'douyin':
                 # HybridCrawler已经返回了格式化的数据，直接使用
                 video_info = {
                     'platform': video_data.get('platform', 'douyin'),
                     'video_id': video_data.get('aweme_id', 'unknown'),
                     'title': video_data.get('title', ''),
                     'description': video_data.get('description', ''),
                     'type': 'video',  # HybridCrawler会处理类型判断
                     'author': video_data.get('author', {}),
                     'duration': video_data.get('video', {}).get('duration', 0) // 1000 if video_data.get('video', {}).get('duration') else 0,
                     'create_time': datetime.fromtimestamp(video_data.get('create_time', 0)).isoformat() if video_data.get('create_time') else '',
                     'statistics': video_data.get('statistics', {}),
                     'original_url': url
                 }
                 
                 # 添加视频URL和缩略图
                 video_urls = video_data.get('video', {}).get('play_addr', [])
                 if video_urls:
                     video_info['video_url'] = video_urls[0] if isinstance(video_urls, list) else video_urls
                 
                 cover_urls = video_data.get('video', {}).get('cover', [])
                 if cover_urls:
                     video_info['thumbnail'] = cover_urls[0] if isinstance(cover_urls, list) else cover_urls
                 
                 if minimal:
                     video_info = self._format_minimal_info(video_info)
                 
                 download_logger.info(f"成功解析抖音视频: {video_info.get('title', 'Unknown')}")
                 return video_info
             else:
                 # 如果HybridCrawler失败，回退到原有方法
                 return await self._fallback_douyin_parsing(url, minimal)
            
        except Exception as e:
            download_logger.error(
                "抖音视频解析失败",
                url=url,
                error=str(e)
            )
            # 尝试回退方法
            try:
                return await self._fallback_douyin_parsing(url, minimal)
            except:
                raise Exception(f"视频解析失败: {str(e)}")
    
    async def _fallback_douyin_parsing(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """回退的抖音解析方法
        
        Args:
            url: 原始URL
            minimal: 是否返回最小信息
            
        Returns:
            视频信息字典
        """
        # 提取aweme_id
        aweme_id = await self._extract_douyin_aweme_id(url)
        if not aweme_id:
            raise ValueError("无法提取抖音视频ID")
        
        # 尝试多种方法获取视频信息
        video_info = await self._try_multiple_parsing_methods(url, aweme_id, minimal)
        if video_info:
            return video_info
        
        # 所有方法都失败，记录详细错误信息
        download_logger.error(f"所有解析方法都失败，URL: {url}, aweme_id: {aweme_id}")
        raise ValueError(f"无法解析抖音视频: {url}")
    
    async def _try_multiple_parsing_methods(self, url: str, aweme_id: str, minimal: bool = False) -> Optional[Dict[str, Any]]:
        """尝试多种解析方法获取抖音视频信息
        
        Args:
            url: 原始URL
            aweme_id: 视频ID
            minimal: 是否返回最小信息
            
        Returns:
            视频信息或None
        """
        # 方法1: 尝试官方API
        try:
            result = await self._try_douyin_api(aweme_id)
            if result:
                return self._format_douyin_info(result, url, minimal)
        except Exception as e:
            download_logger.debug(f"官方API方法失败: {e}")
        
        # 方法2: 尝试页面解析
        try:
            result = await self._try_page_parsing(url)
            if result:
                return self._format_douyin_info(result, url, minimal)
        except Exception as e:
            download_logger.debug(f"页面解析方法失败: {e}")
        
        # 方法3: 尝试yt-dlp
        try:
            result = await self._try_ytdlp_parsing(url)
            if result:
                return self._format_douyin_info(result, url, minimal)
        except Exception as e:
            download_logger.debug(f"yt-dlp方法失败: {e}")
        
        return None
    
    async def _try_douyin_api(self, aweme_id: str) -> Optional[Dict]:
        """尝试抖音官方API"""
        api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={aweme_id}"
        
        # 使用更真实的浏览器请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.douyin.com/',
            'Origin': 'https://www.douyin.com',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(api_url, headers=headers)
            response.raise_for_status()
            
            # 检查是否返回JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                return None
            
            data = response.json()
            aweme_detail = data.get('aweme_detail', {})
            
            if aweme_detail:
                return aweme_detail
        
        return None
    
    async def _try_page_parsing(self, url: str) -> Optional[Dict]:
        """尝试页面解析方法"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        }
        
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            content = response.text
            
            # 尝试从页面中提取JSON数据
            import re
            
            # 查找页面中的视频数据
            patterns = [
                r'window\._ROUTER_DATA\s*=\s*({.+?});',
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'<script[^>]*>\s*window\.__NUXT__\s*=\s*({.+?})\s*</script>'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    try:
                        import json
                        data = json.loads(match.group(1))
                        # 尝试从数据中提取视频信息
                        video_info = self._extract_video_from_page_data(data)
                        if video_info:
                            return video_info
                    except:
                        continue
        
        return None
    
    async def _try_ytdlp_parsing(self, url: str) -> Optional[Dict]:
        """尝试使用yt-dlp解析"""
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    # 转换yt-dlp格式到我们的格式
                    return {
                        'desc': info.get('title', ''),
                        'author': {
                            'nickname': info.get('uploader', ''),
                            'unique_id': info.get('uploader_id', '')
                        },
                        'duration': info.get('duration', 0) * 1000 if info.get('duration') else 0,
                        'create_time': 0,
                        'statistics': {
                            'digg_count': info.get('like_count', 0),
                            'comment_count': info.get('comment_count', 0),
                            'share_count': 0,
                            'play_count': info.get('view_count', 0)
                        },
                        'video': {
                            'play_addr': {
                                'url_list': [info.get('url', '')]
                            },
                            'cover': {
                                'url_list': [info.get('thumbnail', '')]
                            }
                        }
                    }
        except ImportError:
            download_logger.debug("yt-dlp未安装，跳过此方法")
        except Exception as e:
            download_logger.debug(f"yt-dlp解析失败: {e}")
        
        return None
    
    def _extract_video_from_page_data(self, data: Dict) -> Optional[Dict]:
        """从页面数据中提取视频信息"""
        # 这里需要根据实际的页面数据结构来提取
        # 由于抖音的页面结构经常变化，这里只做基本尝试
        try:
            # 尝试多种可能的数据路径
            possible_paths = [
                ['app', 'videoDetail'],
                ['videoDetail'],
                ['aweme', 'detail'],
                ['detail']
            ]
            
            for path in possible_paths:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    # 如果成功遍历完整个路径
                    if isinstance(current, dict) and current:
                        return current
        except:
            pass
        
        return None
    
    def _format_douyin_info(self, aweme_detail: Dict, url: str, minimal: bool = False) -> Dict[str, Any]:
        """格式化抖音视频信息"""
        video_info = {
            'platform': 'douyin',
            'video_id': aweme_detail.get('aweme_id', 'unknown'),
            'title': aweme_detail.get('desc', ''),
            'author': {
                'name': aweme_detail.get('author', {}).get('nickname', ''),
                'unique_id': aweme_detail.get('author', {}).get('unique_id', ''),
                'avatar': aweme_detail.get('author', {}).get('avatar_thumb', {}).get('url_list', [''])[0]
            },
            'duration': aweme_detail.get('duration', 0) // 1000,  # 转换为秒
            'create_time': datetime.fromtimestamp(aweme_detail.get('create_time', 0)).isoformat(),
            'statistics': {
                'digg_count': aweme_detail.get('statistics', {}).get('digg_count', 0),
                'comment_count': aweme_detail.get('statistics', {}).get('comment_count', 0),
                'share_count': aweme_detail.get('statistics', {}).get('share_count', 0),
                'play_count': aweme_detail.get('statistics', {}).get('play_count', 0)
            },
            'aweme_type': aweme_detail.get('aweme_type', 0),
            'original_url': url
        }
        
        # 获取视频/图片URL
        aweme_type = aweme_detail.get('aweme_type', 0)
        if aweme_type in [0, 4, 51, 55, 58, 61]:  # 视频类型
            video_info['type'] = 'video'
            video_info['video_url'] = self._extract_douyin_video_url(aweme_detail)
            video_info['thumbnail'] = aweme_detail.get('video', {}).get('cover', {}).get('url_list', [''])[0]
        elif aweme_type in [2, 68, 150]:  # 图片类型
            video_info['type'] = 'image'
            video_info['images'] = self._extract_douyin_images(aweme_detail)
            video_info['thumbnail'] = video_info['images'][0] if video_info['images'] else ''
        
        if minimal:
            return self._format_minimal_info(video_info)
        
        return video_info
    
    async def _extract_douyin_aweme_id(self, url: str) -> Optional[str]:
        """提取抖音视频ID
        
        Args:
            url: 抖音视频链接
            
        Returns:
            视频ID或None
        """
        # 直接从URL中提取 - 支持多种格式
        patterns = [
            r'/video/(\d+)',  # 标准格式
            r'aweme_id=(\d+)',  # API格式
            r'/share/video/(\d+)',  # 分享格式
            r'modal_id=(\d+)',  # 模态框格式
            r'/v/(\w+)',  # 短链接格式
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 处理短链接
        if 'v.douyin.com' in url or 'iesdouyin.com' in url:
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout, 
                    follow_redirects=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
                    }
                ) as client:
                    response = await client.get(url)
                    final_url = str(response.url)
                    
                    # 尝试从最终URL提取ID
                    for pattern in patterns:
                        match = re.search(pattern, final_url)
                        if match:
                            return match.group(1)
                    
                    # 尝试从响应内容中提取
                    content = response.text
                    match = re.search(r'"aweme_id"\s*:\s*"(\d+)"', content)
                    if match:
                        return match.group(1)
                        
            except Exception as e:
                download_logger.warning(f"展开短链接失败: {e}")
        
        return None
    
    def _extract_douyin_video_url(self, aweme_detail: Dict) -> str:
        """提取抖音视频下载URL
        
        Args:
            aweme_detail: 视频详情数据
            
        Returns:
            视频下载URL
        """
        video_data = aweme_detail.get('video', {})
        
        # 优先获取无水印视频
        play_addr = video_data.get('play_addr', {})
        if play_addr and play_addr.get('url_list'):
            return play_addr['url_list'][0]
        
        # 备选方案
        bit_rate = video_data.get('bit_rate', [])
        if bit_rate and bit_rate[0].get('play_addr', {}).get('url_list'):
            return bit_rate[0]['play_addr']['url_list'][0]
        
        return ''
    
    def _get_mock_douyin_data(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """获取模拟抖音数据
        
        Args:
            url: 原始URL
            minimal: 是否返回最小信息
            
        Returns:
            模拟的视频信息
        """
        video_info = {
            'platform': 'douyin',
            'video_id': 'mock_123456',
            'title': '这是一个抖音视频演示',
            'type': 'video',
            'author': {
                'name': '演示用户',
                'unique_id': 'demo_user',
                'avatar': 'https://example.com/avatar.jpg'
            },
            'duration': 30,
            'create_time': datetime.now().isoformat(),
            'statistics': {
                'digg_count': 1000,
                'comment_count': 50,
                'share_count': 20,
                'play_count': 5000
            },
            'video_url': 'https://example.com/video.mp4',
            'thumbnail': 'https://example.com/thumbnail.jpg',
            'original_url': url
        }
        
        if minimal:
            return self._format_minimal_info(video_info)
        
        return video_info
    
    def _extract_douyin_images(self, aweme_detail: Dict) -> List[str]:
        """提取抖音图片URL列表
        
        Args:
            aweme_detail: 视频详情数据
            
        Returns:
            图片URL列表
        """
        images = []
        image_post = aweme_detail.get('images', [])
        
        for img in image_post:
            url_list = img.get('url_list', [])
            if url_list:
                images.append(url_list[0])
        
        return images
    
    async def _parse_tiktok_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析TikTok视频
        
        Args:
            url: TikTok视频链接
            minimal: 是否返回最小信息
            
        Returns:
            视频信息字典
        """
        # TODO: 实现TikTok解析逻辑
        # 这里可以集成参考项目的TikTok解析代码
        raise NotImplementedError("TikTok解析功能待实现")
    
    async def _parse_bilibili_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析B站视频
        
        Args:
            url: B站视频链接
            minimal: 是否返回最小信息
            
        Returns:
            视频信息字典
        """
        # TODO: 实现B站解析逻辑
        raise NotImplementedError("B站解析功能待实现")
    
    async def _parse_xiaohongshu_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析小红书视频
        
        Args:
            url: 小红书视频链接
            minimal: 是否返回最小信息
            
        Returns:
            视频信息字典
        """
        # TODO: 实现小红书解析逻辑
        raise NotImplementedError("小红书解析功能待实现")
    
    async def _parse_kuaishou_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析快手视频
        
        Args:
            url: 快手视频链接
            minimal: 是否返回最小信息
            
        Returns:
            视频信息字典
        """
        # TODO: 实现快手解析逻辑
        raise NotImplementedError("快手解析功能待实现")
    
    async def _parse_weixin_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析微信视频号视频
        
        Args:
            url: 微信视频号链接
            minimal: 是否返回最小信息
            
        Returns:
            视频信息字典
        """
        # TODO: 实现微信视频号解析逻辑
        raise NotImplementedError("微信视频号解析功能待实现")
    
    def _format_minimal_info(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """格式化最小信息集
        
        Args:
            video_info: 完整视频信息
            
        Returns:
            最小信息集
        """
        return {
            'platform': video_info.get('platform'),
            'video_id': video_info.get('video_id'),
            'title': video_info.get('title'),
            'type': video_info.get('type'),
            'video_url': video_info.get('video_url'),
            'images': video_info.get('images', []),
            'thumbnail': video_info.get('thumbnail'),
            'duration': video_info.get('duration'),
            'author': {
                'name': video_info.get('author', {}).get('name', '')
            },
            'original_url': video_info.get('original_url')
        }


# 创建全局实例
video_parsing_service = VideoParsingService()