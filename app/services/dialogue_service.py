"""
对话服务模块
提供对话相关的高级服务
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..db.repositories import message_repo, turn_repo, session_repo, dialogue_repo
from ..models.data_models import Message, Turn, Session, Dialogue
from ..core.dialogue_core import DialogueCore


class DialogueService:
    """对话服务"""
    
    def __init__(self):
        self.logger = logging.getLogger("DialogueService")
        self.dialogue_core = DialogueCore()
    
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
        message: Message
    ) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message: 消息对象
        
        Returns:
            处理结果
        """
        try:
            # 获取或创建对话上下文
            dialogue = await dialogue_repo.get(message.dialogue_id) if message.dialogue_id else None
            session = await session_repo.get(message.session_id) if message.session_id else None
            turn = await turn_repo.get(message.turn_id) if message.turn_id else None
            
            # 处理消息
            result = await self.dialogue_core.process_message(
                message=message,
                dialogue=dialogue,
                session=session,
                turn=turn
            )
            
            # 保存处理结果
            dialogue = result["dialogue"]
            session = result["session"]
            turn = result["turn"]
            response_message = result["response_message"]
            
            # 保存对话
            if dialogue.id:
                await dialogue_repo.update(dialogue)
            else:
                await dialogue_repo.create(dialogue)
            
            # 保存会话
            if session.id:
                await session_repo.update(session)
            else:
                await session_repo.create(session)
            
            # 保存轮次
            if turn.id:
                await turn_repo.update(turn)
            else:
                await turn_repo.create(turn)
            
            # 保存响应消息
            await message_repo.create(response_message)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            raise
    
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
