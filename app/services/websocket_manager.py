"""WebSocket管理器

实现WebSocket连接管理和实时消息推送功能，主要用于下载进度的实时更新。
"""

import asyncio
import json
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.app_logging import download_logger
from app.models.video import DownloadTask


class ConnectionManager:
    """WebSocket连接管理器
    
    负责管理WebSocket连接，处理消息广播和用户订阅。
    """
    
    def __init__(self):
        # 存储活跃连接：{user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 用户订阅的任务：{user_id: {task_ids}}
        self.user_subscriptions: Dict[str, Set[str]] = {}
        # 连接到用户的映射：{connection_id: user_id}
        self.connection_to_user: Dict[str, str] = {}
        
        download_logger.info("WebSocket连接管理器初始化完成")
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
            connection_id: 连接ID
        """
        await websocket.accept()
        
        # 初始化用户连接存储
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
            self.user_subscriptions[user_id] = set()
        
        # 存储连接
        self.active_connections[user_id][connection_id] = websocket
        self.connection_to_user[connection_id] = user_id
        
        download_logger.info(
            "WebSocket连接建立",
            user_id=user_id,
            connection_id=connection_id,
            total_connections=sum(len(conns) for conns in self.active_connections.values())
        )
        
        # 发送连接成功消息
        await self.send_personal_message(
            user_id,
            {
                "type": "connection_established",
                "message": "WebSocket连接建立成功",
                "timestamp": datetime.utcnow().isoformat()
            },
            connection_id
        )
    
    def disconnect(self, user_id: str, connection_id: str):
        """断开WebSocket连接
        
        Args:
            user_id: 用户ID
            connection_id: 连接ID
        """
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]
                
                # 如果用户没有其他连接，清理相关数据
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    if user_id in self.user_subscriptions:
                        del self.user_subscriptions[user_id]
        
        if connection_id in self.connection_to_user:
            del self.connection_to_user[connection_id]
        
        download_logger.info(
            "WebSocket连接断开",
            user_id=user_id,
            connection_id=connection_id,
            remaining_connections=sum(len(conns) for conns in self.active_connections.values())
        )
    
    async def send_personal_message(
        self,
        user_id: str,
        message: Dict[str, Any],
        connection_id: Optional[str] = None
    ):
        """发送个人消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
            connection_id: 特定连接ID，如果为None则发送给用户的所有连接
        """
        if user_id not in self.active_connections:
            return
        
        message_json = json.dumps(message, ensure_ascii=False)
        
        if connection_id:
            # 发送给特定连接
            if connection_id in self.active_connections[user_id]:
                websocket = self.active_connections[user_id][connection_id]
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    download_logger.warning(
                        "发送WebSocket消息失败",
                        user_id=user_id,
                        connection_id=connection_id,
                        error=str(e)
                    )
                    # 清理失效连接
                    self.disconnect(user_id, connection_id)
        else:
            # 发送给用户的所有连接
            failed_connections = []
            for conn_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    download_logger.warning(
                        "发送WebSocket消息失败",
                        user_id=user_id,
                        connection_id=conn_id,
                        error=str(e)
                    )
                    failed_connections.append(conn_id)
            
            # 清理失效连接
            for conn_id in failed_connections:
                self.disconnect(user_id, conn_id)
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """广播消息给所有连接
        
        Args:
            message: 消息内容
        """
        message_json = json.dumps(message, ensure_ascii=False)
        
        failed_connections = []
        
        for user_id, connections in self.active_connections.items():
            for connection_id, websocket in connections.items():
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    download_logger.warning(
                        "广播WebSocket消息失败",
                        user_id=user_id,
                        connection_id=connection_id,
                        error=str(e)
                    )
                    failed_connections.append((user_id, connection_id))
        
        # 清理失效连接
        for user_id, connection_id in failed_connections:
            self.disconnect(user_id, connection_id)
    
    def subscribe_task(self, user_id: str, task_id: str):
        """订阅任务更新
        
        Args:
            user_id: 用户ID
            task_id: 任务ID
        """
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        self.user_subscriptions[user_id].add(task_id)
        
        download_logger.info(
            "用户订阅任务更新",
            user_id=user_id,
            task_id=task_id
        )
    
    def unsubscribe_task(self, user_id: str, task_id: str):
        """取消订阅任务更新
        
        Args:
            user_id: 用户ID
            task_id: 任务ID
        """
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(task_id)
            
            download_logger.info(
                "用户取消订阅任务更新",
                user_id=user_id,
                task_id=task_id
            )
    
    async def notify_task_update(self, task: DownloadTask):
        """通知任务更新
        
        Args:
            task: 下载任务对象
        """
        # 查找订阅了该任务的用户
        subscribed_users = []
        for user_id, task_ids in self.user_subscriptions.items():
            if task.id in task_ids:
                subscribed_users.append(user_id)
        
        if not subscribed_users:
            return
        
        # 构建任务更新消息
        message = {
            "type": "task_update",
            "data": {
                "task_id": task.id,
                "status": task.status,
                "progress": task.progress or 0.0,
                "title": task.title,
                "platform": task.platform,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "error_message": task.error_message,
                "file_path": task.file_path
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 发送给订阅用户
        for user_id in subscribed_users:
            await self.send_personal_message(user_id, message)
        
        download_logger.info(
            "任务更新通知已发送",
            task_id=task.id,
            status=task.status,
            progress=task.progress,
            subscribers=len(subscribed_users)
        )
    
    async def notify_download_complete(self, task: DownloadTask):
        """通知下载完成
        
        Args:
            task: 下载任务对象
        """
        message = {
            "type": "download_complete",
            "data": {
                "task_id": task.id,
                "title": task.title,
                "platform": task.platform,
                "file_path": task.file_path,
                "completed_at": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 发送给任务所有者
        await self.send_personal_message(task.user_id, message)
        
        download_logger.info(
            "下载完成通知已发送",
            task_id=task.id,
            user_id=task.user_id,
            title=task.title
        )
    
    async def notify_download_failed(self, task: DownloadTask):
        """通知下载失败
        
        Args:
            task: 下载任务对象
        """
        message = {
            "type": "download_failed",
            "data": {
                "task_id": task.id,
                "title": task.title,
                "platform": task.platform,
                "error_message": task.error_message,
                "failed_at": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 发送给任务所有者
        await self.send_personal_message(task.user_id, message)
        
        download_logger.info(
            "下载失败通知已发送",
            task_id=task.id,
            user_id=task.user_id,
            error=task.error_message
        )
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息
        
        Returns:
            连接统计信息
        """
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        total_users = len(self.active_connections)
        total_subscriptions = sum(len(subs) for subs in self.user_subscriptions.values())
        
        return {
            "total_connections": total_connections,
            "total_users": total_users,
            "total_subscriptions": total_subscriptions,
            "users_with_connections": list(self.active_connections.keys())
        }


# 创建全局连接管理器实例
connection_manager = ConnectionManager()


class WebSocketService:
    """WebSocket服务类
    
    提供WebSocket相关的业务逻辑处理。
    """
    
    def __init__(self):
        self.manager = connection_manager
    
    async def handle_client_message(self, websocket: WebSocket, user_id: str, message: str):
        """处理客户端消息
        
        Args:
            websocket: WebSocket连接
            user_id: 用户ID
            message: 消息内容
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe_task":
                task_id = data.get("task_id")
                if task_id:
                    self.manager.subscribe_task(user_id, task_id)
                    await self.manager.send_personal_message(
                        user_id,
                        {
                            "type": "subscription_confirmed",
                            "task_id": task_id,
                            "message": f"已订阅任务 {task_id} 的更新"
                        }
                    )
            
            elif message_type == "unsubscribe_task":
                task_id = data.get("task_id")
                if task_id:
                    self.manager.unsubscribe_task(user_id, task_id)
                    await self.manager.send_personal_message(
                        user_id,
                        {
                            "type": "unsubscription_confirmed",
                            "task_id": task_id,
                            "message": f"已取消订阅任务 {task_id} 的更新"
                        }
                    )
            
            elif message_type == "ping":
                await self.manager.send_personal_message(
                    user_id,
                    {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            elif message_type == "get_stats":
                stats = self.manager.get_connection_stats()
                await self.manager.send_personal_message(
                    user_id,
                    {
                        "type": "stats",
                        "data": stats
                    }
                )
            
            else:
                download_logger.warning(
                    "收到未知类型的WebSocket消息",
                    user_id=user_id,
                    message_type=message_type
                )
        
        except json.JSONDecodeError:
            download_logger.warning(
                "收到无效的JSON消息",
                user_id=user_id,
                message=message
            )
        except Exception as e:
            download_logger.error(
                "处理WebSocket消息时发生错误",
                user_id=user_id,
                error=str(e)
            )


# 创建全局WebSocket服务实例
websocket_service = WebSocketService()