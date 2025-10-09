"""下载队列管理器

实现异步下载任务队列，支持并发下载、进度跟踪、暂停/恢复/取消等功能。
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.app_logging import download_logger
from app.models.video import DownloadTask
from app.services.download_service import DownloadService
from app.services.websocket_manager import connection_manager


class DownloadQueueManager:
    """下载队列管理器
    
    负责管理下载任务队列，控制并发下载数量，跟踪任务状态。
    """
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.download_service = DownloadService()
        
        # 任务队列和状态管理
        self.pending_tasks: asyncio.Queue = asyncio.Queue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.cancelled_tasks: Set[str] = set()
        
        # 队列管理器状态
        self._running = False
        self._queue_processor_task: Optional[asyncio.Task] = None
        
        download_logger.info(
            "Download queue manager initialized",
            max_concurrent=max_concurrent
        )
    
    async def start(self):
        """启动队列管理器"""
        if self._running:
            return
        
        self._running = True
        self._queue_processor_task = asyncio.create_task(self._process_queue())
        
        download_logger.info("Download queue manager started")
    
    async def stop(self):
        """停止队列管理器"""
        if not self._running:
            return
        
        self._running = False
        
        # 取消所有运行中的任务
        for task_id, task in self.running_tasks.items():
            task.cancel()
            download_logger.info("Cancelled running task", task_id=task_id)
        
        # 等待队列处理器停止
        if self._queue_processor_task:
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass
        
        download_logger.info("Download queue manager stopped")
    
    async def add_task(self, task_id: str, db: Session):
        """添加任务到队列
        
        Args:
            task_id: 任务ID
            db: 数据库会话
        """
        await self.pending_tasks.put((task_id, db))
        
        download_logger.info(
            "Task added to queue",
            task_id=task_id,
            queue_size=self.pending_tasks.qsize()
        )
    
    async def cancel_task(self, task_id: str, db: Session) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            db: 数据库会话
            
        Returns:
            是否成功取消
        """
        # 标记为已取消
        self.cancelled_tasks.add(task_id)
        
        # 如果任务正在运行，取消它
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            
            download_logger.info(
                "Running task cancelled",
                task_id=task_id
            )
        
        # 更新数据库状态
        success = await self.download_service.cancel_task(
            db=db,
            task_id=task_id,
            user_id=""  # 这里需要从任务中获取用户ID
        )
        
        return success
    
    async def pause_task(self, task_id: str) -> bool:
        """暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功暂停
        """
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            
            download_logger.info(
                "Task paused",
                task_id=task_id
            )
            return True
        
        return False
    
    async def get_queue_status(self) -> Dict:
        """获取队列状态
        
        Returns:
            队列状态信息
        """
        return {
            'running': self._running,
            'pending_count': self.pending_tasks.qsize(),
            'running_count': len(self.running_tasks),
            'max_concurrent': self.max_concurrent,
            'running_tasks': list(self.running_tasks.keys())
        }
    
    def get_queue_stats(self) -> Dict:
        """获取队列统计信息
        
        Returns:
            队列统计数据
        """
        return {
            'max_concurrent': self.max_concurrent,
            'running_count': len(self.running_tasks),
            'pending_count': self.pending_tasks.qsize(),
            'cancelled_count': len(self.cancelled_tasks),
            'is_running': self._running
        }
    
    async def _process_queue(self):
        """队列处理器主循环"""
        download_logger.info("Queue processor started")
        
        while self._running:
            try:
                # 检查是否可以启动新任务
                if len(self.running_tasks) >= self.max_concurrent:
                    await asyncio.sleep(1)
                    continue
                
                # 从队列中获取任务
                try:
                    task_id, db = await asyncio.wait_for(
                        self.pending_tasks.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 检查任务是否已被取消
                if task_id in self.cancelled_tasks:
                    self.cancelled_tasks.discard(task_id)
                    download_logger.info(
                        "Skipping cancelled task",
                        task_id=task_id
                    )
                    continue
                
                # 启动任务
                await self._start_task(task_id, db)
                
            except Exception as e:
                download_logger.error(
                    "Error in queue processor",
                    error=str(e)
                )
                await asyncio.sleep(1)
        
        download_logger.info("Queue processor stopped")
    
    async def _start_task(self, task_id: str, db: Session):
        """启动单个下载任务
        
        Args:
            task_id: 任务ID
            db: 数据库会话
        """
        download_logger.info(
            "Starting download task",
            task_id=task_id
        )
        
        # 创建异步任务
        task = asyncio.create_task(
            self._execute_download_task(task_id, db)
        )
        
        # 添加到运行中的任务列表
        self.running_tasks[task_id] = task
        
        # 设置任务完成回调
        task.add_done_callback(
            lambda t: self._on_task_completed(task_id, t)
        )
    
    async def _execute_download_task(self, task_id: str, db: Session):
        """执行下载任务
        
        Args:
            task_id: 任务ID
            db: 数据库会话
        """
        try:
            # 检查任务是否存在
            task = db.query(DownloadTask).filter(
                DownloadTask.id == task_id
            ).first()
            
            if not task:
                download_logger.error(
                    "Task not found in database",
                    task_id=task_id
                )
                return
            
            # 检查任务是否已被取消
            if task_id in self.cancelled_tasks:
                download_logger.info(
                    "Task was cancelled before execution",
                    task_id=task_id
                )
                return
            
            # 更新任务状态为下载中
            task.status = 'downloading'
            task.updated_at = datetime.utcnow()
            db.commit()
            
            # 发送WebSocket通知
            await connection_manager.notify_task_update(task)
            
            download_logger.info(
                "Download task execution started",
                task_id=task_id,
                url=task.url,
                title=task.title
            )
            
            # 执行实际的下载逻辑
            await self._perform_download(task, db)
            
            # 如果没有被取消，标记为完成
            if task_id not in self.cancelled_tasks:
                task.status = 'completed'
                task.progress = 100.0
                task.updated_at = datetime.utcnow()
                db.commit()
                
                download_logger.info(
                    "Download task completed successfully",
                    task_id=task_id,
                    file_path=task.file_path
                )
            
        except asyncio.CancelledError:
            # 任务被取消
            download_logger.info(
                "Download task was cancelled",
                task_id=task_id
            )
            
            # 更新数据库状态
            task = db.query(DownloadTask).filter(
                DownloadTask.id == task_id
            ).first()
            if task:
                task.status = 'cancelled'
                task.updated_at = datetime.utcnow()
                db.commit()
            
            raise
        
        except Exception as e:
            # 任务执行失败
            download_logger.error(
                "Download task execution failed",
                task_id=task_id,
                error=str(e)
            )
            
            # 更新数据库状态
            task = db.query(DownloadTask).filter(
                DownloadTask.id == task_id
            ).first()
            if task:
                task.status = 'failed'
                task.error_message = str(e)
                task.updated_at = datetime.utcnow()
                db.commit()
                
                # 发送下载失败通知
                await connection_manager.notify_download_failed(task)
    
    async def _perform_download(self, task: DownloadTask, db: Session):
        """执行实际的下载操作
        
        Args:
            task: 下载任务
            db: 数据库会话
        """
        # 这里实现具体的下载逻辑
        # 目前使用模拟下载来演示进度更新
        
        total_steps = 100
        for step in range(total_steps + 1):
            # 检查是否被取消
            if task.id in self.cancelled_tasks:
                download_logger.info(
                    "Download cancelled during execution",
                    task_id=task.id,
                    progress=step
                )
                break
            
            # 更新进度
            progress = (step / total_steps) * 100
            task.progress = progress
            task.updated_at = datetime.utcnow()
            db.commit()
            
            # 每10%进度发送一次WebSocket通知
            if step % 10 == 0:
                await connection_manager.notify_task_update(task)
            
            # 模拟下载时间
            await asyncio.sleep(0.1)
        
        # 设置文件路径（模拟）
        if task.id not in self.cancelled_tasks:
            task.file_path = f"{self.download_service.download_dir}/{task.title}.mp4"
            task.status = 'completed'
            task.progress = 100.0
            db.commit()
            
            # 发送下载完成通知
            await connection_manager.notify_download_complete(task)
    
    def _on_task_completed(self, task_id: str, task: asyncio.Task):
        """任务完成回调
        
        Args:
            task_id: 任务ID
            task: 异步任务对象
        """
        # 从运行中的任务列表移除
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        # 从取消列表中移除（如果存在）
        self.cancelled_tasks.discard(task_id)
        
        # 记录任务完成
        if task.cancelled():
            download_logger.info(
                "Task completed (cancelled)",
                task_id=task_id
            )
        elif task.exception():
            download_logger.error(
                "Task completed (failed)",
                task_id=task_id,
                error=str(task.exception())
            )
        else:
            download_logger.info(
                "Task completed (success)",
                task_id=task_id
            )


# 创建全局队列管理器实例
download_queue_manager = DownloadQueueManager(
    max_concurrent=getattr(settings, 'max_concurrent_downloads', 3)
)