"""混合爬虫模块

集成抖音和TikTok爬虫，提供统一的视频解析接口。
基于Douyin_TikTok_Download_API项目的核心功能。
"""

import asyncio
from typing import Dict, Any, Optional

from app.core.app_logging import download_logger
from app.crawlers.utils.utils import is_douyin_url, is_tiktok_url, is_bilibili_url
from app.crawlers.douyin.web.web_crawler import DouyinWebCrawler  # 导入抖音Web爬虫
from app.crawlers.tiktok.web.web_crawler import TikTokWebCrawler  # 导入TikTok Web爬虫
from app.crawlers.tiktok.app.app_crawler import TikTokAPPCrawler  # 导入TikTok App爬虫


class HybridCrawler:
    """混合爬虫类
    
    集成抖音和TikTok的爬虫功能，提供统一的视频解析接口。
    """
    
    def __init__(self):
        self.DouyinWebCrawler = DouyinWebCrawler()
        self.TikTokWebCrawler = TikTokWebCrawler()
        self.TikTokAPPCrawler = TikTokAPPCrawler()

    async def hybrid_parsing_single_video(self, url: str, minimal: bool = False) -> Dict[str, Any]:
        """解析单个视频
        
        Args:
            url: 视频URL
            minimal: 是否返回最小数据集
            
        Returns:
            Dict[str, Any]: 解析后的视频数据
            
        Raises:
            ValueError: 无法识别视频来源
            Exception: 解析过程中的其他错误
        """
        try:
            # 解析抖音视频/Parse Douyin video
            if "douyin" in url:
                platform = "douyin"
                aweme_id = await self.DouyinWebCrawler.get_aweme_id(url)
                data = await self.DouyinWebCrawler.fetch_one_video(aweme_id)
                data = data.get("aweme_detail")
                # $.aweme_detail.aweme_type
                aweme_type = data.get("aweme_type")
            # 解析TikTok视频/Parse TikTok video
            elif "tiktok" in url:
                platform = "tiktok"
                aweme_id = await self.TikTokWebCrawler.get_aweme_id(url)

                # 2024-09-14: Switch to TikTokAPPCrawler instead of TikTokWebCrawler
                # data = await self.TikTokWebCrawler.fetch_one_video(aweme_id)
                # data = data.get("itemInfo").get("itemStruct")

                data = await self.TikTokAPPCrawler.fetch_one_video(aweme_id)
                # $.imagePost exists if aweme_type is photo
                aweme_type = data.get("aweme_type")
            else:
                raise ValueError("hybrid_parsing_single_video: Cannot judge the video source from the URL.")

            # 检查是否需要返回最小数据/Check if minimal data is required
            if not minimal:
                return data

            # 如果是最小数据，处理数据/If it is minimal data, process the data
            url_type_code_dict = {
                # common
                0: 'video',
                # Douyin
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
            # 判断链接类型/Judge link type
            url_type = url_type_code_dict.get(aweme_type, 'video')

            """
            以下为(视频||图片)数据处理的四个方法,如果你需要自定义数据处理请在这里修改.
            The following are four methods of (video || image) data processing. 
            If you need to customize data processing, please modify it here.
            
            创建已知数据字典(索引相同)，稍后使用.update()方法更新数据
            Create a known data dictionary (index the same), 
            and then use the .update() method to update the data
            """

            result_data = {
                'type': url_type,
                'platform': platform,
                'aweme_id': aweme_id,
                'desc': data.get("desc"),
                'create_time': data.get("create_time"),
                'author': data.get("author"),
                'music': data.get("music"),
                'statistics': data.get("statistics"),
                'cover_data': {
                    'cover': data.get("video", {}).get("cover"),
                    'origin_cover': data.get("video", {}).get("origin_cover"),
                    'dynamic_cover': data.get("video", {}).get("dynamic_cover")
                },
                'hashtags': data.get('text_extra'),
            }
            
            # 创建一个空变量，稍后使用.update()方法更新数据/Create an empty variable and use the .update() method to update the data
            api_data = None
            
            # 判断链接类型并处理数据/Judge link type and process data
            # 抖音数据处理/Douyin data processing
            if platform == 'douyin':
                # 抖音视频数据处理/Douyin video data processing
                if url_type == 'video':
                    # 将信息储存在字典中/Store information in a dictionary
                    uri = data['video']['play_addr']['uri']
                    wm_video_url_HQ = data['video']['play_addr']['url_list'][0]
                    wm_video_url = f"https://aweme.snssdk.com/aweme/v1/playwm/?video_id={uri}&radio=1080p&line=0"
                    nwm_video_url_HQ = wm_video_url_HQ.replace('playwm', 'play')
                    nwm_video_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={uri}&ratio=1080p&line=0"
                    api_data = {
                        'video_data':
                            {
                                'wm_video_url': wm_video_url,
                                'wm_video_url_HQ': wm_video_url_HQ,
                                'nwm_video_url': nwm_video_url,
                                'nwm_video_url_HQ': nwm_video_url_HQ
                            }
                    }
                # 抖音图片数据处理/Douyin image data processing
                elif url_type == 'image':
                    # 无水印图片列表/No watermark image list
                    no_watermark_image_list = []
                    # 有水印图片列表/With watermark image list
                    watermark_image_list = []
                    # 遍历图片列表/Traverse image list
                    for i in data['images']:
                        no_watermark_image_list.append(i['url_list'][0])
                        watermark_image_list.append(i['download_url_list'][0])
                    api_data = {
                        'image_data':
                            {
                                'no_watermark_image_list': no_watermark_image_list,
                                'watermark_image_list': watermark_image_list
                            }
                    }
            # TikTok数据处理/TikTok data processing
            elif platform == 'tiktok':
                # TikTok视频数据处理/TikTok video data processing
                if url_type == 'video':
                    # 将信息储存在字典中/Store information in a dictionary
                    wm_video = (
                        data.get('video', {})
                        .get('download_addr', {})
                        .get('url_list', [None])[0]
                    )

                    api_data = {
                        'video_data':
                            {
                                'wm_video_url': wm_video,
                                'wm_video_url_HQ': wm_video,
                                'nwm_video_url': data['video']['play_addr']['url_list'][0],
                                'nwm_video_url_HQ': data['video']['bit_rate'][0]['play_addr']['url_list'][0]
                            }
                    }
                # TikTok图片数据处理/TikTok image data processing
                elif url_type == 'image':
                    # 无水印图片列表/No watermark image list
                    no_watermark_image_list = []
                    # 有水印图片列表/With watermark image list
                    watermark_image_list = []
                    for i in data['image_post_info']['images']:
                        no_watermark_image_list.append(i['display_image']['url_list'][0])
                        watermark_image_list.append(i['owner_watermark_image']['url_list'][0])
                    api_data = {
                        'image_data':
                            {
                                'no_watermark_image_list': no_watermark_image_list,
                                'watermark_image_list': watermark_image_list
                            }
                    }
            
            # 更新数据/Update data
            if api_data:
                result_data.update(api_data)
            
            return result_data
            
        except Exception as e:
            download_logger.error(f"视频解析失败 - URL: {url}, 错误: {str(e)}")
            raise

    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """获取视频信息的简化接口
        
        Args:
            url: 视频URL
            
        Returns:
            Optional[Dict[str, Any]]: 视频信息，失败时返回None
        """
        try:
            return await self.hybrid_parsing_single_video(url, minimal=True)
        except Exception as e:
            download_logger.error(f"获取视频信息失败: {e}")
            return None

    async def main(self):
        """测试方法"""
        # 测试混合解析单一视频接口/Test hybrid parsing single video endpoint
        # url = "https://v.douyin.com/L4FJNR3/"
        # url = "https://www.tiktok.com/@taylorswift/video/7359655005701311786"
        url = "https://www.tiktok.com/@flukegk83/video/7360734489271700753"
        # url = "https://www.tiktok.com/@minecraft/photo/7369296852669205791"
        minimal = True
        result = await self.hybrid_parsing_single_video(url, minimal=minimal)
        print(result)


if __name__ == '__main__':
    # 实例化混合爬虫/Instantiate hybrid crawler
    hybrid_crawler = HybridCrawler()
    # 运行测试代码/Run test code
    asyncio.run(hybrid_crawler.main())