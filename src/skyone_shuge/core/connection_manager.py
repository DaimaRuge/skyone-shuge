"""
WebSocket 连接管理器
管理用户连接，支持实时消息推送
"""

import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器
    
    管理所有活跃的 WebSocket 连接，支持：
    - 用户级连接池（一个用户可多设备连接）
    - 消息广播和定向推送
    - 自动清理断开的连接
    """
    
    def __init__(self):
        # 用户ID -> WebSocket 连接集合
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> 连接信息
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        logger.info("ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """建立新的 WebSocket 连接
        
        Args:
            websocket: FastAPI WebSocket 对象
            user_id: 用户唯一标识
        """
        await websocket.accept()
        
        # 初始化用户连接集合
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        
        self.user_connections[user_id].add(websocket)
        self.connection_info[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "client_info": {}
        }
        
        logger.info(f"WebSocket connected: user={user_id}, total_users={len(self.user_connections)}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """断开 WebSocket 连接并清理
        
        Args:
            websocket: 要断开的 WebSocket 对象
        """
        info = self.connection_info.pop(websocket, None)
        if info:
            user_id = info.get("user_id")
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                # 清理空用户
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """发送消息给指定用户的所有连接
        
        Args:
            user_id: 目标用户ID
            message: 消息内容字典
            
        Returns:
            是否至少有一个连接成功发送
        """
        if user_id not in self.user_connections:
            logger.debug(f"No active connections for user: {user_id}")
            return False
        
        connections = self.user_connections[user_id].copy()
        disconnected = []
        sent_count = 0
        
        # 添加时间戳
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        for ws in connections:
            try:
                await ws.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                disconnected.append(ws)
        
        # 清理断开的连接
        for ws in disconnected:
            await self.disconnect(ws)
        
        return sent_count > 0
    
    async def send_to_connection(
        self, 
        websocket: WebSocket, 
        message: Dict[str, Any]
    ) -> bool:
        """发送消息给特定连接
        
        Args:
            websocket: 目标 WebSocket 连接
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        try:
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to connection: {e}")
            await self.disconnect(websocket)
            return False
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """广播消息给所有连接
        
        Args:
            message: 消息内容
            
        Returns:
            成功发送的连接数
        """
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        sent_count = 0
        all_connections = []
        
        # 收集所有连接
        for connections in self.user_connections.values():
            all_connections.extend(connections)
        
        disconnected = []
        for ws in all_connections:
            try:
                await ws.send_json(message)
                sent_count += 1
            except Exception:
                disconnected.append(ws)
        
        # 清理断开的连接
        for ws in disconnected:
            await self.disconnect(ws)
        
        return sent_count
    
    def get_user_connections(self, user_id: str) -> Set[WebSocket]:
        """获取用户的所有连接
        
        Args:
            user_id: 用户ID
            
        Returns:
            该用户的 WebSocket 连接集合
        """
        return self.user_connections.get(user_id, set()).copy()
    
    def get_user_count(self) -> int:
        """获取当前在线用户数量"""
        return len(self.user_connections)
    
    def get_connection_count(self) -> int:
        """获取当前连接总数"""
        return len(self.connection_info)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            "online_users": self.get_user_count(),
            "total_connections": self.get_connection_count(),
            "users": {
                user_id: len(connections)
                for user_id, connections in self.user_connections.items()
            }
        }


# 全局连接管理器实例
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """获取全局连接管理器实例（单例模式）"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def reset_connection_manager() -> None:
    """重置连接管理器（主要用于测试）"""
    global _connection_manager
    _connection_manager = None
