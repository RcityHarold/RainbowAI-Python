"""
对话服务模块
提供对话相关的高级服务
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

from ..db.repositories import message_repo, turn_repo, session_repo, dialogue_repo
from ..models.data_models import Message, Turn, Session, Dialogue
# 避免循环导入
# from ..core.dialogue_core import DialogueCore
from ..core.websocket_manager import websocket_manager
from .notification_service import notification_service


class DialogueService:
    """对话服务"""
    
    def __init__(self):
        self.logger = logging.getLogger("DialogueService")
        # 不在初始化时创建dialogue_core实例，而是在需要时才创建
        self.dialogue_core = None
        
    async def create_dialogue_with_type(
        self,
        dialogue_type: str,
        human_id: Optional[str] = None,
        ai_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dialogue]:
        """
        创建指定类型的对话，并验证必要参数
        
        Args:
            dialogue_type: 对话类型
            human_id: 人类ID
            ai_id: AI ID
            title: 对话标题
            description: 对话描述
            metadata: 元数据
        
        Returns:
            创建的对话对象
        """
        from ..core.constants import DialogueTypes
        
        # 验证对话类型
        if dialogue_type not in DialogueTypes.ALL:
            self.logger.error(f"Invalid dialogue type: {dialogue_type}")
            return None
        
        # 根据对话类型验证必要参数
        if dialogue_type == DialogueTypes.HUMAN_AI:
            # 人类 ⇄ AI 私聊
            if not human_id or not ai_id:
                self.logger.error(f"human_id and ai_id are required for dialogue type: {dialogue_type}")
                return None
        
        elif dialogue_type == DialogueTypes.AI_SELF:
            # AI ⇄ 自我（自省/觉知）
            if not ai_id:
                self.logger.error(f"ai_id is required for dialogue type: {dialogue_type}")
                return None
        
        elif dialogue_type == DialogueTypes.AI_AI:
            # AI ⇄ AI 对话
            if not ai_id or not metadata or "participant_ai_ids" not in metadata:
                self.logger.error(f"ai_id and participant_ai_ids are required for dialogue type: {dialogue_type}")
                return None
        
        elif dialogue_type == DialogueTypes.HUMAN_HUMAN_PRIVATE:
            # 人类 ⇄ 人类 私聊
            if not human_id or not metadata or "second_human_id" not in metadata:
                self.logger.error(f"human_id and second_human_id are required for dialogue type: {dialogue_type}")
                return None
        
        elif dialogue_type == DialogueTypes.HUMAN_HUMAN_GROUP:
            # 人类 ⇄ 人类 群聊
            if not metadata or "group_members" not in metadata or len(metadata["group_members"]) < 2:
                self.logger.error(f"At least two group_members are required for dialogue type: {dialogue_type}")
                return None
        
        elif dialogue_type == DialogueTypes.HUMAN_AI_GROUP:
            # 人类 ⇄ AI 群组 (LIO)
            if not metadata or "human_members" not in metadata or "ai_members" not in metadata:
                self.logger.error(f"human_members and ai_members are required for dialogue type: {dialogue_type}")
                return None
            if len(metadata["human_members"]) < 1 or len(metadata["ai_members"]) < 1:
                self.logger.error(f"At least one human and one AI member are required for dialogue type: {dialogue_type}")
                return None
        
        elif dialogue_type == DialogueTypes.AI_MULTI_HUMAN:
            # AI ⇄ 多人类 群组
            if not ai_id or not metadata or "human_participants" not in metadata or len(metadata["human_participants"]) < 1:
                self.logger.error(f"ai_id and at least one human_participant are required for dialogue type: {dialogue_type}")
                return None
        
        # 创建对话
        return await self.create_dialogue(
            dialogue_type=dialogue_type,
            human_id=human_id,
            ai_id=ai_id,
            title=title,
            description=description,
            metadata=metadata
        )
    
    async def create_dialogue(
        self,
        dialogue_type: str,
        human_id: Optional[str] = None,
        ai_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dialogue]:
        """
        创建对话
        
        Args:
            dialogue_type: 对话类型
            human_id: 人类ID
            ai_id: AI ID
            title: 对话标题
            description: 对话描述
            metadata: 元数据
        
        Returns:
            创建的对话对象
        """
        try:
            # 创建对话对象
            dialogue = Dialogue(
                dialogue_type=dialogue_type,
                human_id=human_id,
                ai_id=ai_id,
                title=title,
                description=description,
                metadata=metadata or {}
            )
            
            # 保存到数据库
            return await dialogue_repo.create(dialogue)
        
        except Exception as e:
            self.logger.error(f"Error creating dialogue: {str(e)}")
            return None
    
    async def create_session(
        self,
        dialogue_id: str,
        session_type: str,
        created_by: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Session]:
        """
        创建会话
        
        Args:
            dialogue_id: 对话ID
            session_type: 会话类型
            created_by: 创建者
            description: 描述
            metadata: 元数据
        
        Returns:
            创建的会话对象
        """
        try:
            # 创建会话对象
            session = Session(
                dialogue_id=dialogue_id,
                session_type=session_type,
                created_by=created_by,
                description=description,
                metadata=metadata or {}
            )
            
            # 保存到数据库
            created_session = await session_repo.create(session)
            
            if created_session:
                # 更新对话
                dialogue = await dialogue_repo.get(dialogue_id)
                if dialogue:
                    dialogue.sessions.append(created_session.id)
                    dialogue.last_activity_at = datetime.utcnow()
                    await dialogue_repo.update(dialogue)
            
            return created_session
        
        except Exception as e:
            self.logger.error(f"Error creating session: {str(e)}")
            return None
    
    async def create_turn(
        self,
        dialogue_id: str,
        session_id: str,
        initiator_role: str,
        responder_role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Turn]:
        """
        创建轮次
        
        Args:
            dialogue_id: 对话ID
            session_id: 会话ID
            initiator_role: 发起者角色
            responder_role: 响应者角色
            metadata: 元数据
        
        Returns:
            创建的轮次对象
        """
        try:
            # 创建轮次对象
            turn = Turn(
                dialogue_id=dialogue_id,
                session_id=session_id,
                initiator_role=initiator_role,
                responder_role=responder_role,
                metadata=metadata or {}
            )
            
            # 保存到数据库
            created_turn = await turn_repo.create(turn)
            
            if created_turn:
                # 更新会话
                session = await session_repo.get(session_id)
                if session:
                    session.turns.append(created_turn.id)
                    await session_repo.update(session)
                
                # 更新对话
                dialogue = await dialogue_repo.get(dialogue_id)
                if dialogue:
                    dialogue.last_activity_at = datetime.utcnow()
                    await dialogue_repo.update(dialogue)
            
            return created_turn
        
        except Exception as e:
            self.logger.error(f"Error creating turn: {str(e)}")
            return None
    
    async def create_message(
        self,
        dialogue_id: str,
        session_id: str,
        turn_id: str,
        sender_role: str,
        sender_id: str,
        content: str,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """
        创建消息
        
        Args:
            dialogue_id: 对话ID
            session_id: 会话ID
            turn_id: 轮次ID
            sender_role: 发送者角色
            sender_id: 发送者ID
            content: 内容
            content_type: 内容类型
            metadata: 元数据
        
        Returns:
            创建的消息对象
        """
        try:
            # 创建消息对象
            message = Message(
                dialogue_id=dialogue_id,
                session_id=session_id,
                turn_id=turn_id,
                sender_role=sender_role,
                sender_id=sender_id,
                content=content,
                content_type=content_type,
                metadata=metadata or {}
            )
            
            # 保存到数据库
            created_message = await message_repo.create(message)
            
            if created_message:
                # 更新轮次
                turn = await turn_repo.get(turn_id)
                if turn:
                    turn.messages.append(created_message.id)
                    await turn_repo.update(turn)
                
                # 更新对话
                dialogue = await dialogue_repo.get(dialogue_id)
                if dialogue:
                    dialogue.last_activity_at = datetime.utcnow()
                    await dialogue_repo.update(dialogue)
            
            return created_message
        
        except Exception as e:
            self.logger.error(f"Error creating message: {str(e)}")
            return None
    
    async def process_message(
        self,
        message: Message,
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message: 消息对象
            stream: 是否使用流式响应
        
        Returns:
            处理结果
        """
        try:
            # 获取对话历史
            history = await self.get_dialogue_history(message.dialogue_id)
            
            # 发送消息处理开始通知
            await notification_service.send_processing_notification(message)
            
            # 定义流式响应回调函数
            async def stream_callback(content: str, is_complete: bool):
                await notification_service.send_stream_response(
                    dialogue_id=message.dialogue_id,
                    session_id=message.session_id,
                    turn_id=message.turn_id,
                    content=content,
                    is_complete=is_complete
                )
            
            # 延迟导入和实例化DialogueCore，避免循环导入
            if self.dialogue_core is None:
                from ..core.dialogue_core import DialogueCore
                self.dialogue_core = DialogueCore()
                
            # 使用对话核心处理消息（流式响应）
            if stream:
                result = await self.dialogue_core.process_message(
                    message=message, 
                    history=history,
                    stream_callback=stream_callback
                )
            else:
                # 不使用流式响应
                result = await self.dialogue_core.process_message(
                    message=message, 
                    history=history
                )
            
            # 创建响应消息
            response_message = await self.create_message(
                dialogue_id=message.dialogue_id,
                session_id=message.session_id,
                turn_id=message.turn_id,
                sender_role="ai",
                sender_id=result.get("ai_id", "ai-system"),
                content=result.get("content", ""),
                content_type=result.get("content_type", "text"),
                metadata=result.get("metadata", {})
            )
            
            # 更新轮次状态
            turn = await turn_repo.get(message.turn_id)
            if turn:
                turn.status = "responded"
                turn.closed_at = datetime.utcnow()
                turn.response_time = (turn.closed_at - turn.started_at).total_seconds()
                await turn_repo.update(turn)
            
            # 更新对话最后活动时间
            dialogue = await dialogue_repo.get(message.dialogue_id)
            if dialogue:
                dialogue.last_activity_at = datetime.utcnow()
                await dialogue_repo.update(dialogue)
                
                # 发送对话更新通知
                await notification_service.send_dialogue_update_notification(dialogue, "message_processed")
            
            # 发送消息完成通知
            if response_message:
                await notification_service.send_message_notification(response_message)
                await notification_service.send_processing_complete_notification(
                    message_id=response_message.id,
                    dialogue_id=message.dialogue_id
                )
            
            return {
                "success": True,
                "message_id": response_message.id if response_message else None,
                "content": result.get("content", ""),
                "content_type": result.get("content_type", "text"),
                "metadata": result.get("metadata", {})
            }
        
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            # 发送错误通知
            await notification_service.send_error_notification(message.dialogue_id, str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_dialogue_history(
        self,
        dialogue_id: str,
        max_messages: int = 50
    ) -> List[Message]:
        """
        获取对话历史
        
        Args:
            dialogue_id: 对话ID
            max_messages: 最大消息数
        
        Returns:
            消息列表
        """
        try:
            # 获取对话的所有消息
            messages = await message_repo.get_by_dialogue(dialogue_id)
            
            # 按创建时间排序
            messages.sort(key=lambda m: m.created_at)
            
            # 限制消息数量
            if len(messages) > max_messages:
                messages = messages[-max_messages:]
            
            return messages
        
        except Exception as e:
            self.logger.error(f"Error getting dialogue history: {str(e)}")
            return []
    
    async def get_session_history(
        self,
        session_id: str
    ) -> List[Message]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
        
        Returns:
            消息列表
        """
        try:
            # 获取会话的所有消息
            messages = await message_repo.get_by_session(session_id)
            
            # 按创建时间排序
            messages.sort(key=lambda m: m.created_at)
            
            return messages
        
        except Exception as e:
            self.logger.error(f"Error getting session history: {str(e)}")
            return []
    
    async def get_active_dialogues(
        self,
        human_id: Optional[str] = None,
        ai_id: Optional[str] = None
    ) -> List[Dialogue]:
        """
        获取活跃对话
        
        Args:
            human_id: 人类ID
            ai_id: AI ID
        
        Returns:
            对话列表
        """
        try:
            # 获取活跃对话
            dialogues = await dialogue_repo.get_active_dialogues()
            
            # 过滤
            if human_id:
                dialogues = [d for d in dialogues if d.human_id == human_id]
            if ai_id:
                dialogues = [d for d in dialogues if d.ai_id == ai_id]
            
            return dialogues
        
        except Exception as e:
            self.logger.error(f"Error getting active dialogues: {str(e)}")
            return []
    
    async def close_session(
        self,
        session_id: str
    ) -> bool:
        """
        关闭会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            是否成功
        """
        try:
            # 获取会话
            session = await session_repo.get(session_id)
            if not session:
                return False
            
            # 关闭会话
            session.end_at = datetime.utcnow()
            await session_repo.update(session)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error closing session: {str(e)}")
            return False
    
    async def close_dialogue(
        self,
        dialogue_id: str
    ) -> bool:
        """
        关闭对话
        
        Args:
            dialogue_id: 对话ID
        
        Returns:
            是否成功
        """
        try:
            # 获取对话
            dialogue = await dialogue_repo.get(dialogue_id)
            if not dialogue:
                return False
            
            # 关闭对话
            dialogue.is_active = False
            await dialogue_repo.update(dialogue)
            
            # 关闭所有会话
            sessions = await session_repo.get_by_dialogue(dialogue_id)
            for session in sessions:
                if not session.end_at:
                    session.end_at = datetime.utcnow()
                    await session_repo.update(session)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error closing dialogue: {str(e)}")
            return False


# 创建服务实例
dialogue_service = DialogueService()
