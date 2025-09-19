"""WebSocket API端点

提供WebSocket连接和实时通信功能。
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.app_logging import download_logger
from app.services.websocket_manager import connection_manager, websocket_service
from app.models.user import User

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket连接端点
    
    Args:
        websocket: WebSocket连接对象
        user_id: 用户ID
        db: 数据库会话
    """
    # 生成连接ID
    connection_id = str(uuid.uuid4())
    
    try:
        # 验证用户是否存在（对于演示用户放宽验证）
        user = db.query(User).filter(User.id == user_id).first()
        if not user and user_id not in ['demo_user', 'test_user']:
            await websocket.close(code=4001, reason="用户不存在")
            return
        
        # 如果是演示用户但数据库中不存在，创建临时用户信息
        if not user:
            user_info = {
                'id': user_id,
                'username': f'demo_{user_id}',
                'email': f'{user_id}@demo.com'
            }
        else:
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        
        # 建立连接
        await connection_manager.connect(websocket, user_id, connection_id)
        
        download_logger.info(
            "WebSocket连接已建立",
            user_id=user_id,
            connection_id=connection_id,
            username=user.username
        )
        
        # 监听消息
        while True:
            try:
                # 接收客户端消息
                message = await websocket.receive_text()
                
                # 处理消息
                await websocket_service.handle_client_message(
                    websocket, user_id, message
                )
                
            except WebSocketDisconnect:
                download_logger.info(
                    "WebSocket连接主动断开",
                    user_id=user_id,
                    connection_id=connection_id
                )
                break
            except Exception as e:
                download_logger.error(
                    "WebSocket消息处理错误",
                    user_id=user_id,
                    connection_id=connection_id,
                    error=str(e)
                )
                # 发送错误消息给客户端
                try:
                    await connection_manager.send_personal_message(
                        user_id,
                        {
                            "type": "error",
                            "message": "消息处理失败",
                            "error": str(e)
                        },
                        connection_id
                    )
                except:
                    # 如果发送错误消息也失败，则断开连接
                    break
    
    except Exception as e:
        download_logger.error(
            "WebSocket连接建立失败",
            user_id=user_id,
            connection_id=connection_id,
            error=str(e)
        )
        try:
            await websocket.close(code=4000, reason=f"连接失败: {str(e)}")
        except:
            pass
    
    finally:
        # 清理连接
        connection_manager.disconnect(user_id, connection_id)
        
        download_logger.info(
            "WebSocket连接已清理",
            user_id=user_id,
            connection_id=connection_id
        )


@router.websocket("/ws")
async def websocket_endpoint_with_token(
    websocket: WebSocket,
    token: str = None
):
    """带token验证的WebSocket连接端点
    
    Args:
        websocket: WebSocket连接对象
        token: 认证token（通过查询参数传递）
    """
    connection_id = str(uuid.uuid4())
    
    try:
        # 这里可以添加token验证逻辑
        if not token:
            await websocket.close(code=4001, reason="缺少认证token")
            return
        
        # TODO: 实现token验证和用户获取逻辑
        # 目前使用简单的模拟
        user_id = "demo_user"  # 实际应该从token中解析
        
        # 建立连接
        await connection_manager.connect(websocket, user_id, connection_id)
        
        download_logger.info(
            "WebSocket连接已建立（token验证）",
            user_id=user_id,
            connection_id=connection_id
        )
        
        # 监听消息
        while True:
            try:
                message = await websocket.receive_text()
                await websocket_service.handle_client_message(
                    websocket, user_id, message
                )
            except WebSocketDisconnect:
                break
            except Exception as e:
                download_logger.error(
                    "WebSocket消息处理错误",
                    user_id=user_id,
                    error=str(e)
                )
                break
    
    except Exception as e:
        download_logger.error(
            "WebSocket连接失败",
            connection_id=connection_id,
            error=str(e)
        )
    
    finally:
        connection_manager.disconnect(user_id, connection_id)


@router.get("/ws/stats")
async def get_websocket_stats():
    """获取WebSocket连接统计信息
    
    Returns:
        连接统计信息
    """
    try:
        stats = connection_manager.get_connection_stats()
        return {
            "code": 200,
            "message": "获取统计信息成功",
            "data": stats
        }
    except Exception as e:
        download_logger.error(
            "获取WebSocket统计信息失败",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="获取统计信息失败")


@router.post("/ws/broadcast")
async def broadcast_message(
    message: dict,
    current_user: User = Depends(get_current_user)
):
    """广播消息（管理员功能）
    
    Args:
        message: 要广播的消息
        current_user: 当前用户
    
    Returns:
        操作结果
    """
    # 检查用户权限（这里简单检查，实际应该有更完善的权限系统）
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        # 添加消息类型和时间戳
        broadcast_message = {
            "type": "broadcast",
            "data": message,
            "timestamp": datetime.utcnow().isoformat(),
            "sender": "system"
        }
        
        await connection_manager.broadcast_message(broadcast_message)
        
        download_logger.info(
            "系统广播消息已发送",
            sender=current_user.username,
            message=message
        )
        
        return {
            "code": 200,
            "message": "广播消息发送成功",
            "data": {
                "recipients": connection_manager.get_connection_stats()["total_connections"]
            }
        }
    
    except Exception as e:
        download_logger.error(
            "广播消息发送失败",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="广播消息发送失败")