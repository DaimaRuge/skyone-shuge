"""
WebSocket 路由 - 实时通信端点
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from jose import JWTError, jwt
import logging

from ...core.connection_manager import ConnectionManager, get_connection_manager
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


async def verify_token(token: str) -> Optional[dict]:
    """验证 JWT Token
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        解码后的用户信息，验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return {"id": user_id, "email": payload.get("email")}
    except JWTError:
        return None


class WSMessageType:
    """WebSocket 消息类型"""
    # 系统消息
    PING = "ping"
    PONG = "pong"
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"
    ERROR = "error"
    
    # 任务进度
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    # 文档处理
    DOC_UPLOADED = "doc_uploaded"
    DOC_PARSING = "doc_parsing"
    DOC_CHUNKING = "doc_chunking"
    DOC_EMBEDDING = "doc_embedding"
    DOC_INDEXING = "doc_indexing"
    DOC_COMPLETED = "doc_completed"
    DOC_FAILED = "doc_failed"
    
    # 通知
    NOTIFICATION = "notification"
    SUBSCRIBE_SUCCESS = "subscribe_success"


@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Token"),
    manager: ConnectionManager = Depends(get_connection_manager)
):
    """WebSocket 主连接端点
    
    客户端通过 JWT Token 建立连接后，可实时接收：
    - 任务进度更新
    - 文档处理状态
    - 系统通知
    
    Args:
        websocket: WebSocket 连接对象
        token: URL 参数中的 JWT Token
        manager: 连接管理器
    """
    # 验证 Token
    user = await verify_token(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    user_id = user["id"]
    
    # 建立连接
    await manager.connect(websocket, user_id)
    
    # 发送认证成功消息
    await manager.send_to_connection(websocket, {
        "type": WSMessageType.AUTH_SUCCESS,
        "payload": {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat()
        }
    })
    
    # 订阅的任务ID集合
    subscribed_tasks: set = set()
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload", {})
            
            logger.debug(f"WS message from {user_id}: {msg_type}")
            
            # 处理心跳
            if msg_type == WSMessageType.PING:
                await manager.send_to_connection(websocket, {
                    "type": WSMessageType.PONG,
                    "payload": {"timestamp": datetime.utcnow().isoformat()}
                })
            
            # 订阅任务进度
            elif msg_type == "subscribe_task":
                task_id = payload.get("task_id")
                if task_id:
                    subscribed_tasks.add(task_id)
                    await manager.send_to_connection(websocket, {
                        "type": WSMessageType.SUBSCRIBE_SUCCESS,
                        "payload": {"task_id": task_id, "subscribed": True}
                    })
            
            # 取消订阅任务
            elif msg_type == "unsubscribe_task":
                task_id = payload.get("task_id")
                if task_id in subscribed_tasks:
                    subscribed_tasks.remove(task_id)
            
            # 获取连接统计
            elif msg_type == "get_stats":
                stats = manager.get_stats()
                await manager.send_to_connection(websocket, {
                    "type": "stats",
                    "payload": stats
                })
            
            # 未知消息类型
            else:
                await manager.send_to_connection(websocket, {
                    "type": WSMessageType.ERROR,
                    "payload": {"message": f"Unknown message type: {msg_type}"}
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user_id}")
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await manager.disconnect(websocket)


@router.get("/stats")
async def get_websocket_stats(
    manager: ConnectionManager = Depends(get_connection_manager)
) -> dict:
    """获取 WebSocket 连接统计（管理接口）"""
    return manager.get_stats()
