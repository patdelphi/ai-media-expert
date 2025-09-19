"""基础爬虫客户端

提供异步HTTP请求、错误处理、重试机制等基础功能。
基于Douyin_TikTok_Download_API项目的BaseCrawler实现。
"""

import httpx
import json
import asyncio
import re
from typing import Dict, Optional, Any
from httpx import Response

from app.core.app_logging import download_logger


class APIError(Exception):
    """API错误基类"""
    pass


class APIConnectionError(APIError):
    """API连接错误"""
    pass


class APIResponseError(APIError):
    """API响应错误"""
    pass


class APITimeoutError(APIError):
    """API超时错误"""
    pass


class APIUnavailableError(APIError):
    """API不可用错误"""
    pass


class APIUnauthorizedError(APIError):
    """API未授权错误"""
    pass


class APINotFoundError(APIError):
    """API未找到错误"""
    pass


class APIRateLimitError(APIError):
    """API限流错误"""
    pass


class APIRetryExhaustedError(APIError):
    """API重试耗尽错误"""
    pass


class BaseCrawler:
    """基础爬虫客户端
    
    提供异步HTTP请求、连接管理、错误处理等基础功能。
    """

    def __init__(
        self,
        proxies: dict = None,
        max_retries: int = 3,
        max_connections: int = 50,
        timeout: int = 10,
        max_tasks: int = 50,
        crawler_headers: dict = None,
    ):
        """初始化爬虫客户端
        
        Args:
            proxies: 代理配置
            max_retries: 最大重试次数
            max_connections: 最大连接数
            timeout: 超时时间
            max_tasks: 最大任务数
            crawler_headers: 请求头
        """
        if isinstance(proxies, dict):
            self.proxies = proxies
        else:
            self.proxies = None

        # 爬虫请求头
        self.crawler_headers = crawler_headers or {}

        # 异步任务数限制
        self._max_tasks = max_tasks
        self.semaphore = asyncio.Semaphore(max_tasks)

        # 限制最大连接数
        self._max_connections = max_connections
        self.limits = httpx.Limits(max_connections=max_connections)

        # 业务逻辑重试次数
        self._max_retries = max_retries
        # 底层连接重试次数
        self.atransport = httpx.AsyncHTTPTransport(retries=max_retries)

        # 超时等待时间
        self._timeout = timeout
        self.timeout = httpx.Timeout(timeout)
        
        # 异步客户端
        client_kwargs = {
            'headers': self.crawler_headers,
            'timeout': self.timeout,
            'limits': self.limits,
            'transport': self.atransport,
        }
        
        # 只有在有代理时才添加proxies参数
        if self.proxies:
            client_kwargs['proxies'] = self.proxies
            
        self.aclient = httpx.AsyncClient(**client_kwargs)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def close(self):
        """关闭客户端"""
        if hasattr(self, 'aclient') and self.aclient:
            await self.aclient.aclose()

    async def fetch_response(self, endpoint: str) -> Response:
        """获取响应数据

        Args:
            endpoint: 接口地址

        Returns:
            Response: 原始响应对象
        """
        return await self.get_fetch_data(endpoint)

    async def fetch_get_json(self, endpoint: str) -> dict:
        """获取JSON数据

        Args:
            endpoint: 接口地址

        Returns:
            dict: 解析后的JSON数据
        """
        response = await self.get_fetch_data(endpoint)
        return self.parse_json(response)

    async def fetch_post_json(self, endpoint: str, params: dict = None, data=None) -> dict:
        """POST请求获取JSON数据

        Args:
            endpoint: 接口地址
            params: 请求参数
            data: 请求数据

        Returns:
            dict: 解析后的JSON数据
        """
        response = await self.post_fetch_data(endpoint, params or {}, data)
        return self.parse_json(response)

    def parse_json(self, response: Response) -> dict:
        """解析JSON响应对象

        Args:
            response: 原始响应对象

        Returns:
            dict: 解析后的JSON数据
        """
        if response is not None and isinstance(response, Response):
            try:
                return response.json()
            except json.JSONDecodeError as e:
                download_logger.error(f"JSON解析失败: {e}")
                raise APIResponseError(f"JSON解析失败: {e}")
        else:
            raise APIResponseError("响应对象为空或类型错误")

    async def get_fetch_data(self, url: str) -> Response:
        """GET请求获取数据

        Args:
            url: 请求URL

        Returns:
            Response: 响应对象
        """
        async with self.semaphore:
            for attempt in range(self._max_retries + 1):
                try:
                    response = await self.aclient.get(url)
                    if response.status_code == 200:
                        return response
                    elif response.status_code == 404:
                        raise APINotFoundError(f"资源未找到: {url}")
                    elif response.status_code == 401:
                        raise APIUnauthorizedError(f"未授权访问: {url}")
                    elif response.status_code == 429:
                        raise APIRateLimitError(f"请求频率限制: {url}")
                    else:
                        download_logger.warning(f"请求失败，状态码: {response.status_code}, URL: {url}")
                        if attempt == self._max_retries:
                            raise APIResponseError(f"请求失败，状态码: {response.status_code}")
                        
                except httpx.TimeoutException:
                    download_logger.warning(f"请求超时，尝试 {attempt + 1}/{self._max_retries + 1}: {url}")
                    if attempt == self._max_retries:
                        raise APITimeoutError(f"请求超时: {url}")
                        
                except httpx.ConnectError:
                    download_logger.warning(f"连接失败，尝试 {attempt + 1}/{self._max_retries + 1}: {url}")
                    if attempt == self._max_retries:
                        raise APIConnectionError(f"连接失败: {url}")
                        
                except Exception as e:
                    download_logger.error(f"请求异常，尝试 {attempt + 1}/{self._max_retries + 1}: {e}")
                    if attempt == self._max_retries:
                        raise APIError(f"请求异常: {e}")
                
                # 重试前等待
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
            
            raise APIRetryExhaustedError(f"重试耗尽: {url}")

    async def post_fetch_data(self, url: str, params: dict = None, data=None) -> Response:
        """POST请求获取数据

        Args:
            url: 请求URL
            params: 请求参数
            data: 请求数据

        Returns:
            Response: 响应对象
        """
        async with self.semaphore:
            for attempt in range(self._max_retries + 1):
                try:
                    response = await self.aclient.post(url, params=params, data=data)
                    if response.status_code == 200:
                        return response
                    elif response.status_code == 404:
                        raise APINotFoundError(f"资源未找到: {url}")
                    elif response.status_code == 401:
                        raise APIUnauthorizedError(f"未授权访问: {url}")
                    elif response.status_code == 429:
                        raise APIRateLimitError(f"请求频率限制: {url}")
                    else:
                        download_logger.warning(f"POST请求失败，状态码: {response.status_code}, URL: {url}")
                        if attempt == self._max_retries:
                            raise APIResponseError(f"POST请求失败，状态码: {response.status_code}")
                        
                except httpx.TimeoutException:
                    download_logger.warning(f"POST请求超时，尝试 {attempt + 1}/{self._max_retries + 1}: {url}")
                    if attempt == self._max_retries:
                        raise APITimeoutError(f"POST请求超时: {url}")
                        
                except httpx.ConnectError:
                    download_logger.warning(f"POST连接失败，尝试 {attempt + 1}/{self._max_retries + 1}: {url}")
                    if attempt == self._max_retries:
                        raise APIConnectionError(f"POST连接失败: {url}")
                        
                except Exception as e:
                    download_logger.error(f"POST请求异常，尝试 {attempt + 1}/{self._max_retries + 1}: {e}")
                    if attempt == self._max_retries:
                        raise APIError(f"POST请求异常: {e}")
                
                # 重试前等待
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
            
            raise APIRetryExhaustedError(f"POST重试耗尽: {url}")