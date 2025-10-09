"""混合爬虫

统一的多平台视频解析入口，支持抖音、TikTok、B站等平台。
基于Douyin_TikTok_Download_API项目的HybridCrawler实现。
"""

import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from app.core.app_logging import download_logger
from app.crawlers.utils.utils import is_douyin_url, is_tiktok_url, is_bilibili_url


class HybridCrawler:
    """混合爬虫类
    
    提供统一的多平台视频解析功能。
    """
    
    def __init__(self):
        """初始化混合爬虫"""
        # 延迟导入避免循环依赖
        self._douyin_crawler = None
        self._tiktok_crawler = None
        self._bilibili_crawler = None
    
    @property
    def douyin_crawler(self):
        """获取抖音爬虫实例"""
        if self._douyin_crawler is None:
            try:
                from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler
                self._douyin_crawler = DouyinWebCrawler()
            except ImportError as e:
                download_logger.error(f"导入抖音爬虫失败: {e}")
                self._douyin_crawler = None
        return self._douyin_crawler
    
    @property
    def tiktok_crawler(self):
        """获取TikTok爬虫实例"""
        if self._tiktok_crawler is None:
            try:
                from app.crawlers.tiktok.web.web_crawler import TikTokWebCrawler
                self._tiktok_crawler = TikTokWebCrawler()
            except ImportError as e:
                download_logger.error(f"导入TikTok爬虫失败: {e}")
                self._tiktok_crawler = None
        return self._tiktok_crawler
    
    @property
    def bilibili_crawler(self):
        """获取B站爬虫实例"""
        if self._bilibili_crawler is None:
            try:
                from app.crawlers.bilibili.web.web_crawler import BilibiliWebCrawler
                self._bilibili_crawler = BilibiliWebCrawler()
            except ImportError as e:
                download_logger.error(f"导入B站爬虫失败: {e}")
                self._bilibili_crawler = None
        return self._bilibili_crawler
    
    async def hybrid_parsing_single_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析单个视频
        
        Args:
            url: 视频URL
            minimal: 是否返回最小数据集
            
        Returns:
            Dict[str, Any]: 视频信息
            
        Raises:
            ValueError: 无法识别视频来源
            Exception: 解析失败
        """
        try:
            # 判断平台并解析
            if is_douyin_url(url):
                return await self._parse_douyin_video(url, minimal)
            elif is_tiktok_url(url):
                return await self._parse_tiktok_video(url, minimal)
            elif is_bilibili_url(url):
                return await self._parse_bilibili_video(url, minimal)
            else:
                raise ValueError(f"无法识别视频来源: {url}")
                
        except Exception as e:
            download_logger.error(f"视频解析失败: {url}, 错误: {e}")
            raise
    
    async def _parse_douyin_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析抖音视频
        
        Args:
            url: 抖音视频URL
            minimal: 是否返回最小数据集
            
        Returns:
            Dict[str, Any]: 视频信息
        """
        if not self.douyin_crawler:
            raise Exception("抖音爬虫未初始化")
        
        try:
            # 获取aweme_id
            aweme_id = await self.douyin_crawler.get_aweme_id(url)
            if not aweme_id:
                raise Exception("无法提取抖音视频ID")
            
            # 获取视频详情
            data = await self.douyin_crawler.fetch_one_video(aweme_id)
            if not data or 'aweme_detail' not in data:
                raise Exception("获取抖音视频详情失败")
            
            video_data = data['aweme_detail']
            aweme_type = video_data.get('aweme_type', 0)
            
            if minimal:
                return self._format_minimal_data(video_data, 'douyin', aweme_type)
            else:
                return self._format_douyin_data(video_data)
                
        except Exception as e:
            download_logger.error(f"抖音视频解析失败: {url}, 错误: {e}")
            raise
    
    async def _parse_tiktok_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析TikTok视频
        
        Args:
            url: TikTok视频URL
            minimal: 是否返回最小数据集
            
        Returns:
            Dict[str, Any]: 视频信息
        """
        if not self.tiktok_crawler:
            raise Exception("TikTok爬虫未初始化")
        
        try:
            # 获取aweme_id
            aweme_id = await self.tiktok_crawler.get_aweme_id(url)
            if not aweme_id:
                raise Exception("无法提取TikTok视频ID")
            
            # 获取视频详情
            data = await self.tiktok_crawler.fetch_one_video(aweme_id)
            if not data:
                raise Exception("获取TikTok视频详情失败")
            
            aweme_type = data.get('aweme_type', 0)
            
            if minimal:
                return self._format_minimal_data(data, 'tiktok', aweme_type)
            else:
                return self._format_tiktok_data(data)
                
        except Exception as e:
            download_logger.error(f"TikTok视频解析失败: {url}, 错误: {e}")
            raise
    
    async def _parse_bilibili_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析B站视频
        
        Args:
            url: B站视频URL
            minimal: 是否返回最小数据集
            
        Returns:
            Dict[str, Any]: 视频信息
        """
        if not self.bilibili_crawler:
            # B站爬虫暂未实现，返回基础信息
            download_logger.warning("B站爬虫暂未实现")
            return {
                'platform': 'bilibili',
                'title': '未知标题',
                'description': '',
                'url': url,
                'error': 'B站爬虫暂未实现'
            }
        
        # TODO: 实现B站视频解析
        return {
            'platform': 'bilibili',
            'title': '未知标题',
            'description': '',
            'url': url
        }
    
    def _format_minimal_data(self, data: Dict[str, Any], platform: str, aweme_type: int) -> Dict[str, Any]:
        """格式化最小数据集
        
        Args:
            data: 原始视频数据
            platform: 平台名称
            aweme_type: 视频类型
            
        Returns:
            Dict[str, Any]: 格式化后的最小数据
        """
        # 视频类型映射
        url_type_code_dict = {
            # 通用
            0: 'video',
            # 抖音
            2: 'image',
            4: 'video',
            68: 'image',
            # TikTok
            51: 'video',
            55: 'video',
            58: 'video',
            61: 'video',
            150: 'image'
        }
        
        url_type = url_type_code_dict.get(aweme_type, 'video')
        
        # 提取基础信息
        if platform == 'douyin':
            author_info = data.get('author', {})
            return {
                'platform': platform,
                'type': url_type,
                'title': data.get('desc', ''),
                'aweme_id': data.get('aweme_id', ''),
                'author': {
                    'nickname': author_info.get('nickname', '') if isinstance(author_info, dict) else str(author_info)
                },
                'duration': data.get('duration', 0),
                'create_time': data.get('create_time', 0),
                'statistics': {
                    'digg_count': data.get('statistics', {}).get('digg_count', 0),
                    'comment_count': data.get('statistics', {}).get('comment_count', 0),
                    'share_count': data.get('statistics', {}).get('share_count', 0),
                    'play_count': data.get('statistics', {}).get('play_count', 0)
                }
            }
        elif platform == 'tiktok':
            author_info = data.get('author', {})
            return {
                'platform': platform,
                'type': url_type,
                'title': data.get('desc', ''),
                'aweme_id': data.get('aweme_id', ''),
                'author': {
                    'nickname': author_info.get('nickname', '') if isinstance(author_info, dict) else str(author_info)
                },
                'duration': data.get('duration', 0),
                'create_time': data.get('create_time', 0),
                'statistics': {
                    'digg_count': data.get('statistics', {}).get('digg_count', 0),
                    'comment_count': data.get('statistics', {}).get('comment_count', 0),
                    'share_count': data.get('statistics', {}).get('share_count', 0),
                    'play_count': data.get('statistics', {}).get('play_count', 0)
                }
            }
        else:
            return {
                'platform': platform,
                'type': url_type,
                'title': '未知标题',
                'data': data
            }
    
    def _format_douyin_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化抖音完整数据
        
        Args:
            data: 抖音原始数据
            
        Returns:
            Dict[str, Any]: 格式化后的数据
        """
        return {
            'platform': 'douyin',
            'aweme_id': data.get('aweme_id', ''),
            'title': data.get('desc', ''),
            'description': data.get('desc', ''),
            'author': {
                'uid': data.get('author', {}).get('uid', ''),
                'nickname': data.get('author', {}).get('nickname', ''),
                'avatar': data.get('author', {}).get('avatar_thumb', {}).get('url_list', [''])[0]
            },
            'video': {
                'duration': data.get('duration', 0),
                'ratio': data.get('video', {}).get('ratio', ''),
                'cover': data.get('video', {}).get('cover', {}).get('url_list', [''])[0],
                'play_addr': data.get('video', {}).get('play_addr', {}).get('url_list', [])
            },
            'music': {
                'title': data.get('music', {}).get('title', ''),
                'author': data.get('music', {}).get('author', ''),
                'play_url': data.get('music', {}).get('play_url', {}).get('url_list', [''])[0]
            },
            'statistics': {
                'digg_count': data.get('statistics', {}).get('digg_count', 0),
                'comment_count': data.get('statistics', {}).get('comment_count', 0),
                'share_count': data.get('statistics', {}).get('share_count', 0),
                'play_count': data.get('statistics', {}).get('play_count', 0)
            },
            'create_time': data.get('create_time', 0),
            'aweme_type': data.get('aweme_type', 0),
            'raw_data': data
        }
    
    def _format_tiktok_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化TikTok完整数据
        
        Args:
            data: TikTok原始数据
            
        Returns:
            Dict[str, Any]: 格式化后的数据
        """
        return {
            'platform': 'tiktok',
            'aweme_id': data.get('aweme_id', ''),
            'title': data.get('desc', ''),
            'description': data.get('desc', ''),
            'author': {
                'uid': data.get('author', {}).get('uid', ''),
                'nickname': data.get('author', {}).get('nickname', ''),
                'avatar': data.get('author', {}).get('avatar_thumb', {}).get('url_list', [''])[0]
            },
            'video': {
                'duration': data.get('duration', 0),
                'ratio': data.get('video', {}).get('ratio', ''),
                'cover': data.get('video', {}).get('cover', {}).get('url_list', [''])[0],
                'play_addr': data.get('video', {}).get('play_addr', {}).get('url_list', [])
            },
            'music': {
                'title': data.get('music', {}).get('title', ''),
                'author': data.get('music', {}).get('author', ''),
                'play_url': data.get('music', {}).get('play_url', {}).get('url_list', [''])[0]
            },
            'statistics': {
                'digg_count': data.get('statistics', {}).get('digg_count', 0),
                'comment_count': data.get('statistics', {}).get('comment_count', 0),
                'share_count': data.get('statistics', {}).get('share_count', 0),
                'play_count': data.get('statistics', {}).get('play_count', 0)
            },
            'create_time': data.get('create_time', 0),
            'aweme_type': data.get('aweme_type', 0),
            'raw_data': data
        }