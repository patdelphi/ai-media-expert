"""
下载API客户端测试模块
测试下载API客户端的各种功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from app.services.download_api_client import (
    DownloadAPIClient,
    get_download_api_client,
    close_download_api_client,
    detect_platform,
    select_best_quality,
)


class TestDownloadAPIClient:
    """下载API客户端测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app.services.download_api_client import DownloadAPIConfig
        config = DownloadAPIConfig(
            base_url="http://test-api:8080",
            timeout=30
        )
        return DownloadAPIClient(config=config)
    
    @pytest.fixture
    def mock_response(self):
        """模拟HTTP响应"""
        response = Mock()
        response.status = 200
        response.json = AsyncMock(return_value={
            'code': 200,
            'data': {
                'title': '测试视频',
                'platform': 'youtube',
                'duration': 120
            }
        })
        return response
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """测试健康检查成功"""
        with patch.object(client.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_get.return_value = mock_response
            
            result = await client.health_check()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """测试健康检查失败"""
        with patch.object(client.client, 'get') as mock_get:
            mock_get.side_effect = Exception("连接失败")
            
            result = await client.health_check()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_parse_video_success(self, client, mock_response):
        """测试解析视频成功"""
        with patch.object(client.client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            result = await client.parse_video_info("https://www.youtube.com/watch?v=test")
            
            assert result is not None
            assert result.video_id == "test123"
            assert result.title == "测试视频"
            assert result.platform == "youtube"
    
    @pytest.mark.asyncio
    async def test_parse_video_with_options(self, client, mock_response):
        """测试带选项的视频解析"""
        with patch.object(client.client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            await client.parse_video_info(
                "https://www.youtube.com/watch?v=test",
                minimal=True
            )
            
            # 验证调用参数
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_video_api_error(self, client):
        """测试视频解析API错误"""
        with patch.object(client.client, 'post') as mock_post:
            mock_post.side_effect = Exception("API错误")
            
            with pytest.raises(Exception) as exc_info:
                await client.parse_video_info("invalid-url")
            
            assert "API错误" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_download_links_success(self, client):
        """测试获取下载链接成功"""
        with patch.object(client.client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'code': 200,
                'data': {
                    'links': [
                        {
                            'url': 'http://example.com/video.mp4',
                            'quality': '720p',
                            'format': 'mp4',
                            'size': 1024000
                        }
                    ]
                }
            }
            mock_post.return_value = mock_response
            
            result = await client.get_download_urls("https://www.youtube.com/watch?v=test")
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_download_file_success(self, client):
        """测试文件下载成功"""
        class DummyResponse:
            def __init__(self, chunks):
                self._chunks = chunks
                self.headers = {"Content-Length": str(sum(len(c) for c in chunks))}

            def raise_for_status(self):
                return None

            async def aiter_bytes(self):
                for c in self._chunks:
                    yield c

        class DummyStream:
            def __init__(self, response):
                self._response = response

            async def __aenter__(self):
                return self._response

            async def __aexit__(self, exc_type, exc, tb):
                return False

        chunks = [b"abc", b"defg"]
        response = DummyResponse(chunks)

        with patch.object(client.client, "stream", return_value=DummyStream(response)):
            out = Path("downloads") / "test_download.bin"
            out.parent.mkdir(parents=True, exist_ok=True)
            try:
                path = await client.download_file("http://example.com/file.bin", str(out))
                assert Path(path).exists()
                assert Path(path).read_bytes() == b"".join(chunks)
            finally:
                if out.exists():
                    out.unlink()
    
    @pytest.mark.asyncio
    async def test_download_file_with_progress_callback(self, client):
        """测试带进度回调的文件下载"""
        class DummyResponse:
            def __init__(self, chunks):
                self._chunks = chunks
                self.headers = {"Content-Length": str(sum(len(c) for c in chunks))}

            def raise_for_status(self):
                return None

            async def aiter_bytes(self):
                for c in self._chunks:
                    yield c

        class DummyStream:
            def __init__(self, response):
                self._response = response

            async def __aenter__(self):
                return self._response

            async def __aexit__(self, exc_type, exc, tb):
                return False

        chunks = [b"a", b"bb", b"ccc"]
        response = DummyResponse(chunks)
        calls = []

        def cb(downloaded, total):
            calls.append((downloaded, total))

        with patch.object(client.client, "stream", return_value=DummyStream(response)):
            out = Path("downloads") / "test_progress.bin"
            out.parent.mkdir(parents=True, exist_ok=True)
            try:
                await client.download_file("http://example.com/file.bin", str(out), progress_callback=cb)
            finally:
                if out.exists():
                    out.unlink()

        assert calls
        assert calls[-1][0] == sum(len(c) for c in chunks)
        assert calls[-1][1] == sum(len(c) for c in chunks)
    
    def test_detect_platform(self):
        """测试平台检测功能"""
        assert detect_platform("https://www.douyin.com/video/123") == "douyin"
        assert detect_platform("https://www.tiktok.com/@u/video/123") == "tiktok"
        assert detect_platform("https://www.youtube.com/watch?v=abc") == "youtube"
    
    def test_select_best_quality(self):
        """测试最佳质量选择"""
        items = [
            {"url": "a", "quality": "360p"},
            {"url": "b", "quality": "1080p"},
            {"url": "c", "quality": "720p"},
        ]
        assert select_best_quality(items, "best")["url"] == "b"
        assert select_best_quality(items, "worst")["url"] == "a"
        assert select_best_quality(items, "720p")["url"] == "c"
    
    @pytest.mark.asyncio
    async def test_client_session_management(self):
        """测试客户端会话管理"""
        # 测试获取客户端
        client1 = await get_download_api_client()
        client2 = await get_download_api_client()
        
        # 应该返回同一个实例
        assert client1 is client2
        
        # 测试关闭客户端
        await close_download_api_client()
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, client):
        """测试超时处理"""
        with patch.object(client.client, 'post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("请求超时")
            
            with pytest.raises(Exception) as exc_info:
                await client.parse_video_info("https://www.youtube.com/watch?v=test")
            
            assert "超时" in str(exc_info.value) or "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, client):
        """测试网络错误处理"""
        with patch.object(client.client, 'post') as mock_post:
            mock_post.side_effect = Exception("网络连接失败")
            
            with pytest.raises(Exception) as exc_info:
                await client.parse_video_info("https://www.youtube.com/watch?v=test")
            
            assert "网络" in str(exc_info.value) or "失败" in str(exc_info.value)


class TestDownloadAPIClientIntegration:
    """下载API客户端集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_download_workflow(self):
        """测试完整的下载工作流程"""
        # 这个测试需要真实的API服务器
        # 在CI/CD环境中可以跳过或使用测试服务器
        pytest.skip("需要真实的API服务器进行集成测试")
        
        client = DownloadAPIClient("http://localhost:8080")
        
        try:
            # 1. 健康检查
            health = await client.health_check()
            assert health is True
            
            # 2. 解析视频
            video_info = await client.parse_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            assert video_info['title']
            assert video_info['platform'] == 'youtube'
            
            # 3. 获取下载链接
            links = await client.get_download_links("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            assert len(links) > 0
            
            # 4. 下载文件（这里只测试API调用，不实际下载）
            # file_path = await client.download_file(links[0]['url'], "/tmp/test_video.mp4")
            # assert file_path
            
        finally:
            await client.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
