"""WebSocket API端点

提供WebSocket连接和实时通信功能。
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.app_logging import download_logger
from app.core.security import verify_token
from app.models.user import User
from app.services.websocket_manager import connection_manager, websocket_service

router = APIRouter()


def _authenticate_websocket_token(token: Optional[str], db: Session) -> User:
    """校验 WebSocket token 并返回用户。"""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少认证token")

    payload = verify_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不可用")
    return user


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """带 token 验证的 WebSocket 连接端点。"""
    connection_id = str(uuid.uuid4())
    user_id: Optional[str] = None

    try:
        user = _authenticate_websocket_token(token, db)
        user_id = str(user.id)

        if websocket.application_state.name == "CONNECTED":
            await websocket.close(code=4001, reason="连接状态异常")
            return

        await connection_manager.connect(websocket, user_id, connection_id)

        download_logger.info(
            "WebSocket连接已建立（token验证）",
            user_id=user_id,
            connection_id=connection_id,
            username=user.username,
        )

        while True:
            try:
                message = await websocket.receive_text()
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
                except Exception:
                    break

    except HTTPException as exc:
        download_logger.warning(
            "WebSocket认证失败",
            connection_id=connection_id,
            error=exc.detail,
        )
        await websocket.close(code=4001, reason=exc.detail)
    except Exception as e:
        download_logger.error(
            "WebSocket连接建立失败",
            user_id=user_id,
            connection_id=connection_id,
            error=str(e)
        )
        try:
            await websocket.close(code=4000, reason=f"连接失败: {str(e)}")
        except Exception:
            pass

    finally:
        if user_id is not None:
            connection_manager.disconnect(user_id, connection_id)
            download_logger.info(
                "WebSocket连接已清理",
                user_id=user_id,
                connection_id=connection_id
            )


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
