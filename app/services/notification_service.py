"""
通知服务模块
提供实时通知和事件推送功能
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.websocket_manager import websocket_manager
from ..core.logger import logger
from ..models.data_models import Message, Turn, Session, Dialogue


class NotificationService:
    """通知服务"""
    
    async def send_message_notification(self, message: Message) -> bool:
        """
        发送消息通知
        
        Args:
            message: 消息对象
        
        Returns:
            是否成功
        """
        try:
            # 构建通知消息
            notification = {
                "type": "new_message",
                "message_id": message.id,
                "dialogue_id": message.dialogue_id,
                "session_id": message.session_id,
                "turn_id": message.turn_id,
                "sender_role": message.sender_role,
                "sender_id": message.sender_id,
                "content_type": message.content_type,
                "created_at": message.created_at.isoformat()
            }
            
            # 如果是文本内容，包含内容预览
            if message.content_type == "text":
                notification["content_preview"] = (
                    message.content[:100] + "..." if len(message.content) > 100 else message.content
                )
            
            # 推送给对话中的所有用户
            success = await websocket_manager.send_to_dialogue(notification, message.dialogue_id)
            
            if success:
                logger.info(f"消息通知已发送: {message.id}")
            else:
                logger.warning(f"消息通知发送失败: {message.id}")
            
            return success
        
        except Exception as e:
            logger.error(f"发送消息通知错误: {str(e)}")
            return False
    
    async def send_processing_notification(self, message: Message) -> bool:
        """
        发送消息处理开始通知
        
        Args:
            message: 消息对象
        
        Returns:
            是否成功
        """
        try:
            # 构建通知消息
            notification = {
                "type": "processing_started",
                "message_id": message.id,
                "dialogue_id": message.dialogue_id,
                "session_id": message.session_id,
                "turn_id": message.turn_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 推送给对话中的所有用户
            success = await websocket_manager.send_to_dialogue(notification, message.dialogue_id)
            
            if success:
                logger.info(f"处理开始通知已发送: {message.id}")
            else:
                logger.warning(f"处理开始通知发送失败: {message.id}")
            
            return success
        
        except Exception as e:
            logger.error(f"发送处理开始通知错误: {str(e)}")
            return False
    
    async def send_processing_complete_notification(self, message_id: str, dialogue_id: str) -> bool:
        """
        发送消息处理完成通知
        
        Args:
            message_id: 消息ID
            dialogue_id: 对话ID
        
        Returns:
            是否成功
        """
        try:
            # 构建通知消息
            notification = {
                "type": "processing_complete",
                "message_id": message_id,
                "dialogue_id": dialogue_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 推送给对话中的所有用户
            success = await websocket_manager.send_to_dialogue(notification, dialogue_id)
            
            if success:
                logger.info(f"处理完成通知已发送: {message_id}")
            else:
                logger.warning(f"处理完成通知发送失败: {message_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"发送处理完成通知错误: {str(e)}")
            return False
    
    async def send_error_notification(self, dialogue_id: str, error_message: str) -> bool:
        """
        发送错误通知
        
        Args:
            dialogue_id: 对话ID
            error_message: 错误信息
        
        Returns:
            是否成功
        """
        try:
            # 构建通知消息
            notification = {
                "type": "error",
                "dialogue_id": dialogue_id,
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 推送给对话中的所有用户
            success = await websocket_manager.send_to_dialogue(notification, dialogue_id)
            
            if success:
                logger.info(f"错误通知已发送: {dialogue_id}")
            else:
                logger.warning(f"错误通知发送失败: {dialogue_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"发送错误通知错误: {str(e)}")
            return False
    
    async def send_dialogue_update_notification(self, dialogue: Dialogue, update_type: str) -> bool:
        """
        发送对话更新通知
        
        Args:
            dialogue: 对话对象
            update_type: 更新类型
        
        Returns:
            是否成功
        """
        try:
            # 构建通知消息
            notification = {
                "type": "dialogue_update",
                "dialogue_id": dialogue.id,
                "update_type": update_type,
                "is_active": dialogue.is_active,
                "last_activity_at": dialogue.last_activity_at.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 推送给对话中的所有用户
            success = await websocket_manager.send_to_dialogue(notification, dialogue.id)
            
            if success:
                logger.info(f"对话更新通知已发送: {dialogue.id}, 类型: {update_type}")
            else:
                logger.warning(f"对话更新通知发送失败: {dialogue.id}, 类型: {update_type}")
            
            return success
        
        except Exception as e:
            logger.error(f"发送对话更新通知错误: {str(e)}")
            return False
    
    async def send_stream_response(self, dialogue_id: str, session_id: str, turn_id: str, content: str, is_complete: bool = False) -> bool:
        """
        发送流式响应
        
        Args:
            dialogue_id: 对话ID
            session_id: 会话ID
            turn_id: 轮次ID
            content: 内容
            is_complete: 是否完成
        
        Returns:
            是否成功
        """
        try:
            # 构建流式响应消息
            stream_message = {
                "type": "stream_response",
                "dialogue_id": dialogue_id,
                "session_id": session_id,
                "turn_id": turn_id,
                "content": content,
                "is_complete": is_complete,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 推送给对话中的所有用户
            success = await websocket_manager.send_to_dialogue(stream_message, dialogue_id)
            
            if not success:
                logger.warning(f"流式响应发送失败: {dialogue_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"发送流式响应错误: {str(e)}")
            return False


# 创建通知服务实例
notification_service = NotificationService()
