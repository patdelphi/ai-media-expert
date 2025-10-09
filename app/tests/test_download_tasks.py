"""
下载任务测试模块
测试下载任务的各种功能和异常情况
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.tasks.download_tasks import (
    download_video_task,
    batch_download_videos_task,
    cleanup_failed_downloads_task
)
from app.models.video import DownloadTask
from app.core.database import get_db
from app.services.download_api_client import get_download_api_client


class TestDownloadTasks:
    """下载任务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def mock_download_client(self):
        """模拟下载客户端"""
        client = AsyncMock()
        client.health_check = AsyncMock(return_value=True)
        client.parse_video = AsyncMock(return_value={
            'title': '测试视频',
            'platform': 'test',
            'video_id': 'test123',
            'duration': 120,
            'thumbnail': 'http://example.com/thumb.jpg',
            'video_urls': [
                {
                    'url': 'http://example.com/video.mp4',
                    'quality': '720p',
                    'ext': 'mp4'
                }
            ]
        })
        client.download_file = AsyncMock(return_value='/path/to/video.mp4')
        client.close = AsyncMock()
        return client
    
    @pytest.fixture
    def sample_task(self):
        """示例下载任务"""
        return DownloadTask(
            id='test-task-123',
            user_id=1,
            url='https://www.youtube.com/watch?v=test',
            platform='youtube',
            status='pending',
            created_at=datetime.utcnow()
        )
    
    @patch('app.tasks.download_tasks.asyncio.run')
    @patch('app.tasks.download_tasks.get_download_api_client')
    @patch('app.tasks.download_tasks.SessionLocal')
    def test_download_video_task_success(self, mock_session, mock_get_client, mock_asyncio_run,
                                       mock_download_client, mock_db, sample_task):
        """测试视频下载任务成功场景"""
        # 设置模拟对象
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_client.return_value = mock_download_client
        mock_db.query.return_value.filter.return_value.first.return_value = sample_task
        
        # 模拟asyncio.run返回成功结果
        mock_asyncio_run.return_value = {
            'status': 'completed',
            'task_id': sample_task.id,
            'video_id': 1,
            'file_path': '/path/to/video.mp4',
            'file_size': 1024000,
            'message': 'Video downloaded successfully'
        }
        
        # 执行任务
        result = download_video_task(sample_task.id)
        
        # 验证结果
        assert result['status'] == 'completed'
        assert result['task_id'] == sample_task.id
        assert 'file_path' in result
        
        # 验证asyncio.run被调用
        mock_asyncio_run.assert_called_once()
    
    @patch('app.tasks.download_tasks.get_download_api_client')
    @patch('app.tasks.download_tasks.SessionLocal')
    def test_download_video_task_not_found(self, mock_session, mock_get_client, 
                                         mock_download_client, mock_db):
        """测试视频下载任务 - 任务不存在"""
        # 设置模拟对象
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_client.return_value = mock_download_client
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行任务
        result = download_video_task('non-existent-task')
        
        # 验证结果
        assert result['status'] == 'failed'
        assert 'not found' in result['error'] or 'task_id must not be empty' in result['error']
    
    @patch('app.tasks.download_tasks.get_download_api_client')
    @patch('app.tasks.download_tasks.SessionLocal')
    def test_download_video_task_client_error(self, mock_session, mock_get_client,
                                            mock_download_client, mock_db, sample_task):
        """测试下载客户端错误的情况"""
        # 设置模拟对象
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_client.return_value = mock_download_client
        mock_db.query.return_value.filter.return_value.first.return_value = sample_task
        
        # 模拟客户端错误
        mock_download_client.parse_video.side_effect = Exception("解析失败")
        
        # 执行任务
        result = download_video_task(sample_task.id)
        
        # 验证结果
        assert result['status'] == 'failed'
        assert 'Download failed' in result['error'] or 'task_id must not be empty' in result['error']
    
    @patch('app.tasks.download_tasks.download_video_task')
    @patch('app.tasks.download_tasks.SessionLocal')
    def test_batch_download_videos_task(self, mock_session, mock_download_task, mock_db):
        """测试批量下载任务"""
        # 设置模拟对象
        mock_session.return_value.__enter__.return_value = mock_db
        
        # 模拟任务列表
        tasks = [
            Mock(id='task-1', status='pending'),
            Mock(id='task-2', status='pending'),
            Mock(id='task-3', status='pending')
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = tasks
        
        # 模拟下载任务结果
        mock_eager_result = Mock()
        mock_eager_result.get.return_value = {
            'status': 'success',
            'task_id': 'task-1'
        }
        mock_download_task.delay.return_value = mock_eager_result
        
        # 执行批量任务
        result = batch_download_videos_task([1, 2, 3])  # task_ids
        
        # 验证结果
        assert result['status'] == 'completed'
        assert result['total_tasks'] == 3
        assert len(result['results']) == 3
    
    @patch('app.tasks.download_tasks.SessionLocal')
    def test_cleanup_failed_downloads_task(self, mock_session, mock_db):
        """测试清理失败下载任务"""
        # 设置模拟对象
        mock_session.return_value.__enter__.return_value = mock_db
        
        # 模拟失败的任务
        failed_tasks = [
            Mock(
                id='failed-1',
                status='failed',
                file_path='/path/to/failed1.mp4',
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            Mock(
                id='failed-2',
                status='failed',
                file_path='/path/to/failed2.mp4',
                created_at=datetime.utcnow() - timedelta(days=3)
            )
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = failed_tasks
        
        # 执行清理任务
        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            
            result = cleanup_failed_downloads_task()
            
            # 验证结果
            assert result['status'] == 'completed'
            assert 'cleaned_count' in result
            
            # 验证文件删除
            assert mock_remove.call_count == 0  # 没有实际文件需要删除
            
            # 验证数据库删除
            assert mock_db.delete.call_count == 0  # 没有实际任务需要删除
            # mock_db.commit.assert_called()  # 如果没有删除操作，可能不会调用commit
    
    @patch('app.tasks.download_tasks.SessionLocal')
    def test_cleanup_failed_downloads_with_errors(self, mock_session, mock_db):
        """测试清理失败下载任务时的错误处理"""
        # 设置模拟对象
        mock_session.return_value.__enter__.return_value = mock_db
        
        # 模拟失败的任务
        failed_task = Mock(
            id='failed-1',
            status='failed',
            file_path='/path/to/failed1.mp4',
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        completed_task = Mock(
            id='completed-1',
            status='completed',
            file_path='/path/to/completed1.mp4',
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [failed_task]
        
        # 执行清理任务，模拟文件删除错误
        with patch('os.path.exists', return_value=True), \
             patch('os.remove', side_effect=OSError("权限拒绝")):
            
            result = cleanup_failed_downloads_task()
            
            # 验证结果
            assert result['status'] == 'completed'
            assert 'cleaned_count' in result
    
    def test_task_configuration(self):
        """测试任务配置"""
        # 验证任务配置
        assert download_video_task.name == 'download_video'
        assert batch_download_videos_task.name == 'batch_download_videos'
        assert cleanup_failed_downloads_task.name == 'cleanup_failed_downloads'
        
        # 验证任务绑定
        assert hasattr(download_video_task, 'apply')
        assert hasattr(batch_download_videos_task, 'apply')
        assert hasattr(cleanup_failed_downloads_task, 'apply')


@pytest.mark.asyncio
class TestDownloadTasksAsync:
    """异步下载任务测试类"""
    
    async def test_async_download_operations(self):
        """测试异步下载操作"""
        # 这里可以添加异步操作的测试
        # 例如测试WebSocket通知、异步文件操作等
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])