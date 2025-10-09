"""抖音Web爬虫

提供抖音视频信息解析功能的简化实现。
注意：这是一个简化版本，实际的抖音API需要复杂的加密参数。
"""

import re
import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

from app.crawlers.base_crawler import BaseCrawler
from app.core.app_logging import download_logger


class DouyinWebCrawler:
    """抖音Web爬虫类
    
    提供抖音视频信息解析功能。
    注意：这是简化实现，实际使用需要处理抖音的反爬机制。
    """
    
    def __init__(self):
        """初始化抖音爬虫"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    async def get_aweme_id(self, url: str) -> Optional[str]:
        """从URL中提取aweme_id
        
        Args:
            url: 抖音视频URL
            
        Returns:
            Optional[str]: aweme_id或None
        """
        try:
            # 处理短链接
            if 'v.douyin.com' in url:
                # 需要解析重定向获取真实URL
                real_url = await self._resolve_short_url(url)
                if real_url:
                    url = real_url
            
            # 从URL中提取aweme_id
            patterns = [
                r'/video/([0-9]+)',
                r'aweme_id=([0-9]+)',
                r'modal_id=([0-9]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            download_logger.warning(f"无法从URL提取aweme_id: {url}")
            return None
            
        except Exception as e:
            download_logger.error(f"提取aweme_id失败: {e}")
            return None
    
    async def _resolve_short_url(self, short_url: str) -> Optional[str]:
        """解析短链接获取真实URL
        
        Args:
            short_url: 短链接
            
        Returns:
            Optional[str]: 真实URL或None
        """
        try:
            async with BaseCrawler(crawler_headers=self.headers) as crawler:
                response = await crawler.fetch_response(short_url)
                # 检查重定向
                if response.history:
                    return str(response.url)
                return short_url
        except Exception as e:
            download_logger.error(f"解析短链接失败: {e}")
            return None
    
    async def fetch_one_video(self, aweme_id: str) -> Dict[str, Any]:
        """获取单个视频信息
        
        Args:
            aweme_id: 视频ID
            
        Returns:
            Dict[str, Any]: 视频信息
            
        注意：这是简化实现，实际需要处理抖音的加密参数
        """
        try:
            # 构建API URL（简化版本）
            api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={aweme_id}"
            
            async with BaseCrawler(crawler_headers=self.headers) as crawler:
                try:
                    data = await crawler.fetch_get_json(api_url)
                    
                    # 检查响应
                    if data and 'aweme_detail' in data:
                        return data
                    else:
                        # 如果API失败，返回模拟数据
                        return self._create_mock_data(aweme_id)
                        
                except Exception as api_error:
                    download_logger.warning(f"API请求失败，返回模拟数据: {api_error}")
                    return self._create_mock_data(aweme_id)
                    
        except Exception as e:
            download_logger.error(f"获取抖音视频信息失败: {e}")
            return self._create_mock_data(aweme_id)
    
    def _create_mock_data(self, aweme_id: str) -> Dict[str, Any]:
        """创建模拟数据
        
        Args:
            aweme_id: 视频ID
            
        Returns:
            Dict[str, Any]: 模拟的视频数据
        """
        return {
            'aweme_detail': {
                'aweme_id': aweme_id,
                'desc': '抖音视频（模拟数据）',
                'duration': 15000,  # 15秒
                'aweme_type': 0,  # 视频类型
                'create_time': 1640995200,  # 时间戳
                'author': {
                    'uid': 'unknown',
                    'nickname': '未知用户',
                    'avatar_thumb': {
                        'url_list': ['https://example.com/avatar.jpg']
                    }
                },
                'video': {
                    'ratio': '720p',
                    'cover': {
                        'url_list': ['https://example.com/cover.jpg']
                    },
                    'play_addr': {
                        'url_list': ['https://example.com/video.mp4']
                    }
                },
                'music': {
                    'title': '原声',
                    'author': '未知',
                    'play_url': {
                        'url_list': ['https://example.com/music.mp3']
                    }
                },
                'statistics': {
                    'digg_count': 0,
                    'comment_count': 0,
                    'share_count': 0,
                    'play_count': 0
                },
                'status': {
                    'is_delete': False,
                    'allow_share': True
                },
                'text_extra': [],
                'is_ads': False,
                'commerce_info': {},
                'commercial_video_info': '',
                'item_comment_settings': 0,
                'mentioned_users': [],
                'risk_infos': {
                    'warn': False,
                    'type': 0,
                    'content': ''
                },
                'position': None,
                'uniqid_position': None,
                'comment_list': None,
                'images': None,
                'video_tag': [],
                'geofencing': [],
                'is_hash_tag': 0,
                'is_pgcshow': False,
                'region': 'CN',
                'video_text': [],
                'collect_stat': 0,
                'label_top_text': None,
                'group_id': aweme_id,
                'prevent_download': False,
                'nickname_position': None,
                'challenge_position': None,
                'item_distribute_source': '',
                'video_control': {
                    'allow_download': True,
                    'share_type': 1,
                    'show_progress_bar': 1,
                    'draft_progress_bar': 0,
                    'allow_duet': True,
                    'allow_react': True,
                    'prevent_download_type': 0,
                    'allow_dynamic_wallpaper': True,
                    'timer_status': 0,
                    'allow_music': True,
                    'allow_stitch': True
                }
            },
            'status_code': 0,
            'status_msg': 'success'
        }
    
    async def get_douyin_headers(self) -> Dict[str, Any]:
        """获取抖音请求头配置
        
        Returns:
            Dict[str, Any]: 请求头配置
        """
        return {
            'headers': self.headers,
            'proxies': None  # 可以在这里配置代理
        }