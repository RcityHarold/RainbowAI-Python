"""
消息存储库模块
提供消息相关的数据库操作
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

# 模拟数据库存储
# 实际应用中应替换为真实数据库操作
_messages_db = {}

logger = logging.getLogger("message_repo")


async def create(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建消息"""
    message_id = message_data.get("id")
    if not message_id:
        raise ValueError("message_id is required")
    
    _messages_db[message_id] = message_data
    logger.info(f"Created message: {message_id}")
    
    return message_data


async def get(message_id: str) -> Optional[Dict[str, Any]]:
    """获取消息"""
    return _messages_db.get(message_id)


async def update(message_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新消息"""
    if message_id not in _messages_db:
        logger.warning(f"Message not found: {message_id}")
        return None
    
    message = _messages_db[message_id]
    message.update(update_data)
    
    return message


async def delete(message_id: str) -> bool:
    """删除消息"""
    if message_id in _messages_db:
        del _messages_db[message_id]
        logger.info(f"Deleted message: {message_id}")
        return True
    
    logger.warning(f"Message not found for deletion: {message_id}")
    return False


async def get_by_turn(turn_id: str) -> List[Dict[str, Any]]:
    """获取轮次的所有消息"""
    messages = [m for m in _messages_db.values() if m.get("turn_id") == turn_id]
    
    # 按创建时间排序
    messages.sort(key=lambda x: x.get("created_at", datetime.min))
    
    return messages


async def get_by_session(session_id: str) -> List[Dict[str, Any]]:
    """获取会话的所有消息"""
    messages = [m for m in _messages_db.values() if m.get("session_id") == session_id]
    
    # 按创建时间排序
    messages.sort(key=lambda x: x.get("created_at", datetime.min))
    
    return messages


async def get_by_dialogue(dialogue_id: str) -> List[Dict[str, Any]]:
    """获取对话的所有消息"""
    messages = [m for m in _messages_db.values() if m.get("dialogue_id") == dialogue_id]
    
    # 按创建时间排序
    messages.sort(key=lambda x: x.get("created_at", datetime.min))
    
    return messages


async def search_messages(
    dialogue_id: Optional[str] = None,
    session_id: Optional[str] = None,
    turn_id: Optional[str] = None,
    sender_role: Optional[str] = None,
    sender_id: Optional[str] = None,
    content_type: Optional[str] = None,
    query: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    搜索消息
    
    Args:
        dialogue_id: 对话ID
        session_id: 会话ID
        turn_id: 轮次ID
        sender_role: 发送者角色
        sender_id: 发送者ID
        content_type: 内容类型
        query: 搜索关键词
        since: 开始时间
        until: 结束时间
        limit: 限制数量
        offset: 偏移量
    
    Returns:
        消息列表
    """
    messages = list(_messages_db.values())
    
    # 应用过滤条件
    if dialogue_id:
        messages = [m for m in messages if m.get("dialogue_id") == dialogue_id]
    
    if session_id:
        messages = [m for m in messages if m.get("session_id") == session_id]
    
    if turn_id:
        messages = [m for m in messages if m.get("turn_id") == turn_id]
    
    if sender_role:
        messages = [m for m in messages if m.get("sender_role") == sender_role]
    
    if sender_id:
        messages = [m for m in messages if m.get("sender_id") == sender_id]
    
    if content_type:
        messages = [m for m in messages if m.get("content_type") == content_type]
    
    if query:
        messages = [m for m in messages if query.lower() in m.get("content", "").lower()]
    
    if since:
        messages = [m for m in messages if m.get("created_at") and m.get("created_at") >= since]
    
    if until:
        messages = [m for m in messages if m.get("created_at") and m.get("created_at") <= until]
    
    # 按创建时间排序
    messages.sort(key=lambda x: x.get("created_at", datetime.min))
    
    return messages[offset:offset+limit]


async def count_messages(
    dialogue_id: Optional[str] = None,
    session_id: Optional[str] = None,
    turn_id: Optional[str] = None,
    sender_role: Optional[str] = None,
    sender_id: Optional[str] = None,
    content_type: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None
) -> int:
    """
    计算消息数量
    
    Args:
        dialogue_id: 对话ID
        session_id: 会话ID
        turn_id: 轮次ID
        sender_role: 发送者角色
        sender_id: 发送者ID
        content_type: 内容类型
        since: 开始时间
        until: 结束时间
    
    Returns:
        消息数量
    """
    messages = list(_messages_db.values())
    
    # 应用过滤条件
    if dialogue_id:
        messages = [m for m in messages if m.get("dialogue_id") == dialogue_id]
    
    if session_id:
        messages = [m for m in messages if m.get("session_id") == session_id]
    
    if turn_id:
        messages = [m for m in messages if m.get("turn_id") == turn_id]
    
    if sender_role:
        messages = [m for m in messages if m.get("sender_role") == sender_role]
    
    if sender_id:
        messages = [m for m in messages if m.get("sender_id") == sender_id]
    
    if content_type:
        messages = [m for m in messages if m.get("content_type") == content_type]
    
    if since:
        messages = [m for m in messages if m.get("created_at") and m.get("created_at") >= since]
    
    if until:
        messages = [m for m in messages if m.get("created_at") and m.get("created_at") <= until]
    
    return len(messages)


# 导出函数
message_repo = {
    "create": create,
    "get": get,
    "update": update,
    "delete": delete,
    "get_by_turn": get_by_turn,
    "get_by_session": get_by_session,
    "get_by_dialogue": get_by_dialogue,
    "search_messages": search_messages,
    "count_messages": count_messages
}
