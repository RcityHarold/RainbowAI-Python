"""
数据库存储库
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .database import db
from ..models.data_models import Message, Turn, Session, Dialogue


class MessageRepository:
    """消息存储库"""
    
    def __init__(self):
        self.logger = logging.getLogger("MessageRepository")
        self.table = "message"
    
    async def create(self, message: Message) -> Optional[Message]:
        """
        创建消息
        
        Args:
            message: 消息对象
        
        Returns:
            创建的消息对象
        """
        try:
            # 转换为字典
            data = message.dict()
            
            # 创建记录
            result = await db.create(self.table, data)
            
            if result:
                # 更新ID
                message.id = result.get("id", message.id)
                return message
            return None
        
        except Exception as e:
            self.logger.error(f"Error creating message: {str(e)}")
            return None
    
    async def get(self, message_id: str) -> Optional[Message]:
        """
        获取消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            消息对象
        """
        try:
            # 查询记录
            results = await db.select(self.table, message_id)
            
            if results and len(results) > 0:
                # 转换为对象
                return Message(**results[0])
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting message {message_id}: {str(e)}")
            return None
    
    async def update(self, message: Message) -> Optional[Message]:
        """
        更新消息
        
        Args:
            message: 消息对象
        
        Returns:
            更新后的消息对象
        """
        try:
            # 转换为字典
            data = message.dict()
            
            # 更新记录
            result = await db.update(self.table, message.id, data)
            
            if result:
                return message
            return None
        
        except Exception as e:
            self.logger.error(f"Error updating message {message.id}: {str(e)}")
            return None
    
    async def delete(self, message_id: str) -> bool:
        """
        删除消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            是否删除成功
        """
        try:
            # 删除记录
            return await db.delete(self.table, message_id)
        
        except Exception as e:
            self.logger.error(f"Error deleting message {message_id}: {str(e)}")
            return False
    
    async def get_by_turn(self, turn_id: str) -> List[Message]:
        """
        获取轮次的所有消息
        
        Args:
            turn_id: 轮次ID
        
        Returns:
            消息列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE turn_id = $turn_id ORDER BY created_at"
            results = await db.query(query, {"turn_id": turn_id})
            
            # 转换为对象
            messages = []
            for result in results:
                messages.append(Message(**result))
            
            return messages
        
        except Exception as e:
            self.logger.error(f"Error getting messages for turn {turn_id}: {str(e)}")
            return []
    
    async def get_by_session(self, session_id: str) -> List[Message]:
        """
        获取会话的所有消息
        
        Args:
            session_id: 会话ID
        
        Returns:
            消息列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE session_id = $session_id ORDER BY created_at"
            results = await db.query(query, {"session_id": session_id})
            
            # 转换为对象
            messages = []
            for result in results:
                messages.append(Message(**result))
            
            return messages
        
        except Exception as e:
            self.logger.error(f"Error getting messages for session {session_id}: {str(e)}")
            return []
    
    async def get_by_dialogue(self, dialogue_id: str) -> List[Message]:
        """
        获取对话的所有消息
        
        Args:
            dialogue_id: 对话ID
        
        Returns:
            消息列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE dialogue_id = $dialogue_id ORDER BY created_at"
            results = await db.query(query, {"dialogue_id": dialogue_id})
            
            # 转换为对象
            messages = []
            for result in results:
                messages.append(Message(**result))
            
            return messages
        
        except Exception as e:
            self.logger.error(f"Error getting messages for dialogue {dialogue_id}: {str(e)}")
            return []


class TurnRepository:
    """轮次存储库"""
    
    def __init__(self):
        self.logger = logging.getLogger("TurnRepository")
        self.table = "turn"
    
    async def create(self, turn: Turn) -> Optional[Turn]:
        """
        创建轮次
        
        Args:
            turn: 轮次对象
        
        Returns:
            创建的轮次对象
        """
        try:
            # 转换为字典
            data = turn.dict()
            
            # 创建记录
            result = await db.create(self.table, data)
            
            if result:
                # 更新ID
                turn.id = result.get("id", turn.id)
                return turn
            return None
        
        except Exception as e:
            self.logger.error(f"Error creating turn: {str(e)}")
            return None
    
    async def get(self, turn_id: str) -> Optional[Turn]:
        """
        获取轮次
        
        Args:
            turn_id: 轮次ID
        
        Returns:
            轮次对象
        """
        try:
            # 查询记录
            results = await db.select(self.table, turn_id)
            
            if results and len(results) > 0:
                # 转换为对象
                return Turn(**results[0])
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting turn {turn_id}: {str(e)}")
            return None
    
    async def update(self, turn: Turn) -> Optional[Turn]:
        """
        更新轮次
        
        Args:
            turn: 轮次对象
        
        Returns:
            更新后的轮次对象
        """
        try:
            # 转换为字典
            data = turn.dict()
            
            # 更新记录
            result = await db.update(self.table, turn.id, data)
            
            if result:
                return turn
            return None
        
        except Exception as e:
            self.logger.error(f"Error updating turn {turn.id}: {str(e)}")
            return None
    
    async def delete(self, turn_id: str) -> bool:
        """
        删除轮次
        
        Args:
            turn_id: 轮次ID
        
        Returns:
            是否删除成功
        """
        try:
            # 删除记录
            return await db.delete(self.table, turn_id)
        
        except Exception as e:
            self.logger.error(f"Error deleting turn {turn_id}: {str(e)}")
            return False
    
    async def get_by_session(self, session_id: str) -> List[Turn]:
        """
        获取会话的所有轮次
        
        Args:
            session_id: 会话ID
        
        Returns:
            轮次列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE session_id = $session_id ORDER BY started_at"
            results = await db.query(query, {"session_id": session_id})
            
            # 转换为对象
            turns = []
            for result in results:
                turns.append(Turn(**result))
            
            return turns
        
        except Exception as e:
            self.logger.error(f"Error getting turns for session {session_id}: {str(e)}")
            return []
    
    async def get_by_dialogue(self, dialogue_id: str) -> List[Turn]:
        """
        获取对话的所有轮次
        
        Args:
            dialogue_id: 对话ID
        
        Returns:
            轮次列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE dialogue_id = $dialogue_id ORDER BY started_at"
            results = await db.query(query, {"dialogue_id": dialogue_id})
            
            # 转换为对象
            turns = []
            for result in results:
                turns.append(Turn(**result))
            
            return turns
        
        except Exception as e:
            self.logger.error(f"Error getting turns for dialogue {dialogue_id}: {str(e)}")
            return []
    
    async def get_unresponded(self) -> List[Turn]:
        """
        获取所有未响应的轮次
        
        Returns:
            轮次列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE status = 'unresponded' ORDER BY started_at"
            results = await db.query(query)
            
            # 转换为对象
            turns = []
            for result in results:
                turns.append(Turn(**result))
            
            return turns
        
        except Exception as e:
            self.logger.error(f"Error getting unresponded turns: {str(e)}")
            return []


class SessionRepository:
    """会话存储库"""
    
    def __init__(self):
        self.logger = logging.getLogger("SessionRepository")
        self.table = "session"
    
    async def create(self, session: Session) -> Optional[Session]:
        """
        创建会话
        
        Args:
            session: 会话对象
        
        Returns:
            创建的会话对象
        """
        try:
            # 转换为字典
            data = session.dict()
            
            # 创建记录
            result = await db.create(self.table, data)
            
            if result:
                # 更新ID
                session.id = result.get("id", session.id)
                return session
            return None
        
        except Exception as e:
            self.logger.error(f"Error creating session: {str(e)}")
            return None
    
    async def get(self, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话对象
        """
        try:
            # 查询记录
            results = await db.select(self.table, session_id)
            
            if results and len(results) > 0:
                # 转换为对象
                return Session(**results[0])
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    async def update(self, session: Session) -> Optional[Session]:
        """
        更新会话
        
        Args:
            session: 会话对象
        
        Returns:
            更新后的会话对象
        """
        try:
            # 转换为字典
            data = session.dict()
            
            # 更新记录
            result = await db.update(self.table, session.id, data)
            
            if result:
                return session
            return None
        
        except Exception as e:
            self.logger.error(f"Error updating session {session.id}: {str(e)}")
            return None
    
    async def delete(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            是否删除成功
        """
        try:
            # 删除记录
            return await db.delete(self.table, session_id)
        
        except Exception as e:
            self.logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    async def get_by_dialogue(self, dialogue_id: str) -> List[Session]:
        """
        获取对话的所有会话
        
        Args:
            dialogue_id: 对话ID
        
        Returns:
            会话列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE dialogue_id = $dialogue_id ORDER BY start_at"
            results = await db.query(query, {"dialogue_id": dialogue_id})
            
            # 转换为对象
            sessions = []
            for result in results:
                sessions.append(Session(**result))
            
            return sessions
        
        except Exception as e:
            self.logger.error(f"Error getting sessions for dialogue {dialogue_id}: {str(e)}")
            return []
    
    async def get_active_sessions(self) -> List[Session]:
        """
        获取所有活跃会话（未结束的会话）
        
        Returns:
            会话列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE end_at IS NULL ORDER BY start_at"
            results = await db.query(query)
            
            # 转换为对象
            sessions = []
            for result in results:
                sessions.append(Session(**result))
            
            return sessions
        
        except Exception as e:
            self.logger.error(f"Error getting active sessions: {str(e)}")
            return []


class DialogueRepository:
    """对话存储库"""
    
    def __init__(self):
        self.logger = logging.getLogger("DialogueRepository")
        self.table = "dialogue"
    
    async def create(self, dialogue: Dialogue) -> Optional[Dialogue]:
        """
        创建对话
        
        Args:
            dialogue: 对话对象
        
        Returns:
            创建的对话对象
        """
        try:
            # 转换为字典
            data = dialogue.dict()
            
            # 创建记录
            result = await db.create(self.table, data)
            
            if result:
                # 更新ID
                dialogue.id = result.get("id", dialogue.id)
                return dialogue
            return None
        
        except Exception as e:
            self.logger.error(f"Error creating dialogue: {str(e)}")
            return None
    
    async def get(self, dialogue_id: str) -> Optional[Dialogue]:
        """
        获取对话
        
        Args:
            dialogue_id: 对话ID
        
        Returns:
            对话对象
        """
        try:
            # 查询记录
            results = await db.select(self.table, dialogue_id)
            
            if results and len(results) > 0:
                # 转换为对象
                return Dialogue(**results[0])
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting dialogue {dialogue_id}: {str(e)}")
            return None
    
    async def update(self, dialogue: Dialogue) -> Optional[Dialogue]:
        """
        更新对话
        
        Args:
            dialogue: 对话对象
        
        Returns:
            更新后的对话对象
        """
        try:
            # 转换为字典
            data = dialogue.dict()
            
            # 更新记录
            result = await db.update(self.table, dialogue.id, data)
            
            if result:
                return dialogue
            return None
        
        except Exception as e:
            self.logger.error(f"Error updating dialogue {dialogue.id}: {str(e)}")
            return None
    
    async def delete(self, dialogue_id: str) -> bool:
        """
        删除对话
        
        Args:
            dialogue_id: 对话ID
        
        Returns:
            是否删除成功
        """
        try:
            # 删除记录
            return await db.delete(self.table, dialogue_id)
        
        except Exception as e:
            self.logger.error(f"Error deleting dialogue {dialogue_id}: {str(e)}")
            return False
    
    async def get_by_human(self, human_id: str) -> List[Dialogue]:
        """
        获取人类的所有对话
        
        Args:
            human_id: 人类ID
        
        Returns:
            对话列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE human_id = $human_id ORDER BY last_activity_at DESC"
            results = await db.query(query, {"human_id": human_id})
            
            # 转换为对象
            dialogues = []
            for result in results:
                dialogues.append(Dialogue(**result))
            
            return dialogues
        
        except Exception as e:
            self.logger.error(f"Error getting dialogues for human {human_id}: {str(e)}")
            return []
    
    async def get_by_ai(self, ai_id: str) -> List[Dialogue]:
        """
        获取AI的所有对话
        
        Args:
            ai_id: AI ID
        
        Returns:
            对话列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE ai_id = $ai_id ORDER BY last_activity_at DESC"
            results = await db.query(query, {"ai_id": ai_id})
            
            # 转换为对象
            dialogues = []
            for result in results:
                dialogues.append(Dialogue(**result))
            
            return dialogues
        
        except Exception as e:
            self.logger.error(f"Error getting dialogues for AI {ai_id}: {str(e)}")
            return []
    
    async def get_active_dialogues(self) -> List[Dialogue]:
        """
        获取所有活跃对话
        
        Returns:
            对话列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE is_active = true ORDER BY last_activity_at DESC"
            results = await db.query(query)
            
            # 转换为对象
            dialogues = []
            for result in results:
                dialogues.append(Dialogue(**result))
            
            return dialogues
        
        except Exception as e:
            self.logger.error(f"Error getting active dialogues: {str(e)}")
            return []


class IntrospectionRepository:
    """自我反思会话存储库"""
    
    def __init__(self):
        self.logger = logging.getLogger("IntrospectionRepository")
        self.table = "introspection_session"
    
    async def create(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建自我反思会话
        
        Args:
            session: 自我反思会话数据
        
        Returns:
            创建的自我反思会话
        """
        try:
            # 确保有ID
            if "id" not in session:
                session["id"] = f"introspection:{db.generate_id()}"
            
            # 确保有时间戳
            if "started_at" not in session:
                session["started_at"] = datetime.utcnow()
            
            # 创建记录
            result = await db.create(self.table, session)
            return result
        
        except Exception as e:
            self.logger.error(f"Error creating introspection session: {str(e)}")
            return None
    
    async def update(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新自我反思会话
        
        Args:
            session: 自我反思会话数据
        
        Returns:
            更新后的自我反思会话
        """
        try:
            # 获取ID
            session_id = session.get("id")
            if not session_id:
                raise ValueError("会话ID不能为空")
            
            # 更新记录
            result = await db.update(self.table, session_id, session)
            return result
        
        except Exception as e:
            self.logger.error(f"Error updating introspection session {session.get('id')}: {str(e)}")
            return None
    
    async def find_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID查找自我反思会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            自我反思会话
        """
        try:
            # 查询记录
            results = await db.select(self.table, session_id)
            
            if results and len(results) > 0:
                return results[0]
            return None
        
        except Exception as e:
            self.logger.error(f"Error finding introspection session {session_id}: {str(e)}")
            return None
    
    async def find(
        self,
        query: Dict[str, Any],
        limit: int = 10,
        offset: int = 0,
        sort_by: str = "started_at",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        查找自我反思会话
        
        Args:
            query: 查询条件
            limit: 限制数量
            offset: 偏移量
            sort_by: 排序字段
            sort_order: 排序顺序
        
        Returns:
            自我反思会话列表
        """
        try:
            # 构建查询
            query_str = "SELECT * FROM " + self.table
            
            # 添加条件
            if query:
                conditions = []
                for key, value in query.items():
                    conditions.append(f"{key} = ${key}")
                
                if conditions:
                    query_str += " WHERE " + " AND ".join(conditions)
            
            # 添加排序
            query_str += f" ORDER BY {sort_by} {sort_order}"
            
            # 添加分页
            query_str += f" LIMIT {limit} OFFSET {offset}"
            
            # 执行查询
            results = await db.query(query_str, query)
            return results
        
        except Exception as e:
            self.logger.error(f"Error finding introspection sessions: {str(e)}")
            return []
    
    async def count(self, query: Dict[str, Any]) -> int:
        """
        计算符合条件的自我反思会话数量
        
        Args:
            query: 查询条件
        
        Returns:
            会话数量
        """
        try:
            # 构建查询
            query_str = "SELECT count() FROM " + self.table
            
            # 添加条件
            if query:
                conditions = []
                for key, value in query.items():
                    conditions.append(f"{key} = ${key}")
                
                if conditions:
                    query_str += " WHERE " + " AND ".join(conditions)
            
            # 执行查询
            results = await db.query(query_str, query)
            
            if results and len(results) > 0:
                return results[0].get("count", 0)
            return 0
        
        except Exception as e:
            self.logger.error(f"Error counting introspection sessions: {str(e)}")
            return 0
    
    async def delete(self, session_id: str) -> bool:
        """
        删除自我反思会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            是否成功删除
        """
        try:
            # 删除记录
            return await db.delete(self.table, session_id)
        
        except Exception as e:
            self.logger.error(f"Error deleting introspection session {session_id}: {str(e)}")
            return False


class ToolCallRepository:
    """工具调用存储库"""
    
    def __init__(self):
        self.logger = logging.getLogger("ToolCallRepository")
        self.table = "tool_call"
    
    async def create(self, tool_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建工具调用记录
        
        Args:
            tool_call: 工具调用数据
        
        Returns:
            创建的工具调用记录
        """
        try:
            # 确保有ID
            if "id" not in tool_call:
                tool_call["id"] = f"tool_call:{db.generate_id()}"
            
            # 确保有时间戳
            if "created_at" not in tool_call:
                tool_call["created_at"] = datetime.utcnow()
            
            # 创建记录
            result = await db.create(self.table, tool_call)
            return result
        
        except Exception as e:
            self.logger.error(f"Error creating tool call: {str(e)}")
            return None
    
    async def update(self, tool_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新工具调用记录
        
        Args:
            tool_call: 工具调用数据
        
        Returns:
            更新后的工具调用记录
        """
        try:
            # 获取ID
            tool_call_id = tool_call.get("id")
            if not tool_call_id:
                raise ValueError("工具调用ID不能为空")
            
            # 更新记录
            result = await db.update(self.table, tool_call_id, tool_call)
            return result
        
        except Exception as e:
            self.logger.error(f"Error updating tool call {tool_call.get('id')}: {str(e)}")
            return None
    
    async def get(self, tool_call_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工具调用记录
        
        Args:
            tool_call_id: 工具调用ID
        
        Returns:
            工具调用记录
        """
        try:
            # 查询记录
            results = await db.select(self.table, tool_call_id)
            
            if results and len(results) > 0:
                return results[0]
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting tool call {tool_call_id}: {str(e)}")
            return None
    
    async def get_by_turn(self, turn_id: str) -> List[Dict[str, Any]]:
        """
        获取轮次的所有工具调用
        
        Args:
            turn_id: 轮次ID
        
        Returns:
            工具调用列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE turn_id = $turn_id ORDER BY created_at"
            results = await db.query(query, {"turn_id": turn_id})
            return results
        
        except Exception as e:
            self.logger.error(f"Error getting tool calls for turn {turn_id}: {str(e)}")
            return []
    
    async def get_by_dialogue(self, dialogue_id: str) -> List[Dict[str, Any]]:
        """
        获取对话的所有工具调用
        
        Args:
            dialogue_id: 对话ID
        
        Returns:
            工具调用列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE dialogue_id = $dialogue_id ORDER BY created_at"
            results = await db.query(query, {"dialogue_id": dialogue_id})
            return results
        
        except Exception as e:
            self.logger.error(f"Error getting tool calls for dialogue {dialogue_id}: {str(e)}")
            return []
    
    async def get_failed_tool_calls(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取失败的工具调用
        
        Args:
            limit: 限制数量
        
        Returns:
            工具调用列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE success = false ORDER BY created_at DESC LIMIT {limit}"
            results = await db.query(query)
            return results
        
        except Exception as e:
            self.logger.error(f"Error getting failed tool calls: {str(e)}")
            return []


class EventLogRepository:
    """事件日志存储库"""
    
    def __init__(self):
        self.logger = logging.getLogger("EventLogRepository")
        self.table = "event_log"
    
    async def create(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建事件日志
        
        Args:
            event: 事件数据
        
        Returns:
            创建的事件日志
        """
        try:
            # 确保有ID
            if "id" not in event:
                event["id"] = f"event:{db.generate_id()}"
            
            # 确保有时间戳
            if "created_at" not in event:
                event["created_at"] = datetime.utcnow()
            
            # 创建记录
            result = await db.create(self.table, event)
            return result
        
        except Exception as e:
            self.logger.error(f"Error creating event log: {str(e)}")
            return None
    
    async def get(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        获取事件日志
        
        Args:
            event_id: 事件ID
        
        Returns:
            事件日志
        """
        try:
            # 查询记录
            results = await db.select(self.table, event_id)
            
            if results and len(results) > 0:
                return results[0]
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting event log {event_id}: {str(e)}")
            return None
    
    async def get_by_dialogue(self, dialogue_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取对话的所有事件日志
        
        Args:
            dialogue_id: 对话ID
            limit: 限制数量
        
        Returns:
            事件日志列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE dialogue_id = $dialogue_id ORDER BY created_at DESC LIMIT {limit}"
            results = await db.query(query, {"dialogue_id": dialogue_id})
            return results
        
        except Exception as e:
            self.logger.error(f"Error getting event logs for dialogue {dialogue_id}: {str(e)}")
            return []
    
    async def get_by_type(self, event_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取特定类型的事件日志
        
        Args:
            event_type: 事件类型
            limit: 限制数量
        
        Returns:
            事件日志列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE event_type = $event_type ORDER BY created_at DESC LIMIT {limit}"
            results = await db.query(query, {"event_type": event_type})
            return results
        
        except Exception as e:
            self.logger.error(f"Error getting event logs of type {event_type}: {str(e)}")
            return []
    
    async def get_error_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取错误事件日志
        
        Args:
            limit: 限制数量
        
        Returns:
            事件日志列表
        """
        try:
            # 查询记录
            query = f"SELECT * FROM {self.table} WHERE event_type LIKE 'error%' ORDER BY created_at DESC LIMIT {limit}"
            results = await db.query(query)
            return results
        
        except Exception as e:
            self.logger.error(f"Error getting error event logs: {str(e)}")
            return []


# 创建存储库实例
message_repo = MessageRepository()
turn_repo = TurnRepository()
session_repo = SessionRepository()
dialogue_repo = DialogueRepository()
introspection_repo = IntrospectionRepository()
tool_call_repo = ToolCallRepository()
event_log_repo = EventLogRepository()
