"""
WebSocket管理器模块
用于处理WebSocket连接和实时通信
"""
from typing import Dict, List, Any, Optional, Callable
import asyncio
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..core.logger import logger


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 所有活跃连接
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # 用户ID到连接ID的映射
        self.user_connections: Dict[str, List[str]] = {}
        # 对话ID到连接ID的映射
        self.dialogue_connections: Dict[str, List[str]] = {}
        # 连接ID到用户ID的映射
        self.connection_user: Dict[str, str] = {}
        # 连接ID到对话ID的映射
        self.connection_dialogue: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None, dialogue_id: Optional[str] = None) -> None:
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接
            connection_id: 连接ID
            user_id: 用户ID
            dialogue_id: 对话ID
        """
        await websocket.accept()
        
        # 存储连接
        if connection_id not in self.active_connections:
            self.active_connections[connection_id] = []
        self.active_connections[connection_id].append(websocket)
        
        # 关联用户
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
            self.connection_user[connection_id] = user_id
        
        # 关联对话
        if dialogue_id:
            if dialogue_id not in self.dialogue_connections:
                self.dialogue_connections[dialogue_id] = []
            self.dialogue_connections[dialogue_id].append(connection_id)
            self.connection_dialogue[connection_id] = dialogue_id
        
        logger.info(f"WebSocket连接已建立: {connection_id}, 用户: {user_id}, 对话: {dialogue_id}")
    
    def disconnect(self, connection_id: str) -> None:
        """
        断开WebSocket连接
        
        Args:
            connection_id: 连接ID
        """
        # 移除连接
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # 移除用户关联
        if connection_id in self.connection_user:
            user_id = self.connection_user[connection_id]
            if user_id in self.user_connections and connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            del self.connection_user[connection_id]
        
        # 移除对话关联
        if connection_id in self.connection_dialogue:
            dialogue_id = self.connection_dialogue[connection_id]
            if dialogue_id in self.dialogue_connections and connection_id in self.dialogue_connections[dialogue_id]:
                self.dialogue_connections[dialogue_id].remove(connection_id)
                if not self.dialogue_connections[dialogue_id]:
                    del self.dialogue_connections[dialogue_id]
            del self.connection_dialogue[connection_id]
        
        logger.info(f"WebSocket连接已断开: {connection_id}")
    
    async def send_personal_message(self, message: Any, connection_id: str) -> bool:
        """
        向特定连接发送消息
        
        Args:
            message: 消息内容
            connection_id: 连接ID
        
        Returns:
            是否成功发送
        """
        if connection_id not in self.active_connections:
            return False
        
        if isinstance(message, dict) or isinstance(message, list):
            message = json.dumps(message)
        
        for websocket in self.active_connections[connection_id]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
                return False
        
        return True
    
    async def send_to_user(self, message: Any, user_id: str) -> bool:
        """
        向特定用户的所有连接发送消息
        
        Args:
            message: 消息内容
            user_id: 用户ID
        
        Returns:
            是否成功发送
        """
        if user_id not in self.user_connections:
            return False
        
        success = True
        for connection_id in self.user_connections[user_id]:
            result = await self.send_personal_message(message, connection_id)
            success = success and result
        
        return success
    
    async def send_to_dialogue(self, message: Any, dialogue_id: str) -> bool:
        """
        向特定对话的所有连接发送消息
        
        Args:
            message: 消息内容
            dialogue_id: 对话ID
        
        Returns:
            是否成功发送
        """
        if dialogue_id not in self.dialogue_connections:
            return False
        
        success = True
        for connection_id in self.dialogue_connections[dialogue_id]:
            result = await self.send_personal_message(message, connection_id)
            success = success and result
        
        return success
    
    async def broadcast(self, message: Any) -> bool:
        """
        广播消息给所有连接
        
        Args:
            message: 消息内容
        
        Returns:
            是否成功发送
        """
        if isinstance(message, dict) or isinstance(message, list):
            message = json.dumps(message)
        
        success = True
        for connection_id in self.active_connections:
            for websocket in self.active_connections[connection_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"广播消息失败: {str(e)}")
                    success = False
        
        return success


# 创建全局WebSocket管理器实例
websocket_manager = ConnectionManager()
