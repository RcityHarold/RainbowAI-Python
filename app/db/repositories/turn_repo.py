"""
轮次存储库模块
提供轮次相关的数据库操作
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

# 模拟数据库存储
# 实际应用中应替换为真实数据库操作
_turns_db = {}

logger = logging.getLogger("turn_repo")


async def create(turn_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建轮次"""
    turn_id = turn_data.get("id")
    if not turn_id:
        raise ValueError("turn_id is required")
    
    _turns_db[turn_id] = turn_data
    logger.info(f"Created turn: {turn_id}")
    
    return turn_data


async def get(turn_id: str) -> Optional[Dict[str, Any]]:
    """获取轮次"""
    return _turns_db.get(turn_id)


async def update(turn_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新轮次"""
    if turn_id not in _turns_db:
        logger.warning(f"Turn not found: {turn_id}")
        return None
    
    turn = _turns_db[turn_id]
    turn.update(update_data)
    
    return turn


async def delete(turn_id: str) -> bool:
    """删除轮次"""
    if turn_id in _turns_db:
        del _turns_db[turn_id]
        logger.info(f"Deleted turn: {turn_id}")
        return True
    
    logger.warning(f"Turn not found for deletion: {turn_id}")
    return False


async def get_by_session(session_id: str) -> List[Dict[str, Any]]:
    """获取会话的所有轮次"""
    turns = [t for t in _turns_db.values() if t.get("session_id") == session_id]
    
    # 按创建时间排序
    turns.sort(key=lambda x: x.get("created_at", datetime.min))
    
    return turns


async def get_by_dialogue(dialogue_id: str) -> List[Dict[str, Any]]:
    """获取对话的所有轮次"""
    turns = [t for t in _turns_db.values() if t.get("dialogue_id") == dialogue_id]
    
    # 按创建时间排序
    turns.sort(key=lambda x: x.get("created_at", datetime.min))
    
    return turns


async def get_unresponded_turns(dialogue_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取未回应的轮次"""
    turns = list(_turns_db.values())
    
    # 过滤未回应的轮次
    turns = [t for t in turns if not t.get("is_completed", False)]
    
    # 如果指定了对话ID，进一步过滤
    if dialogue_id:
        turns = [t for t in turns if t.get("dialogue_id") == dialogue_id]
    
    # 按创建时间排序
    turns.sort(key=lambda x: x.get("created_at", datetime.min))
    
    return turns


async def search_turns(
    dialogue_id: Optional[str] = None,
    session_id: Optional[str] = None,
    initiator_role: Optional[str] = None,
    responder_role: Optional[str] = None,
    is_completed: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 10,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    搜索轮次
    
    Args:
        dialogue_id: 对话ID
        session_id: 会话ID
        initiator_role: 发起者角色
        responder_role: 响应者角色
        is_completed: 是否已完成
        since: 开始时间
        until: 结束时间
        limit: 限制数量
        offset: 偏移量
    
    Returns:
        轮次列表
    """
    turns = list(_turns_db.values())
    
    # 应用过滤条件
    if dialogue_id:
        turns = [t for t in turns if t.get("dialogue_id") == dialogue_id]
    
    if session_id:
        turns = [t for t in turns if t.get("session_id") == session_id]
    
    if initiator_role:
        turns = [t for t in turns if t.get("initiator_role") == initiator_role]
    
    if responder_role:
        turns = [t for t in turns if t.get("responder_role") == responder_role]
    
    if is_completed is not None:
        turns = [t for t in turns if t.get("is_completed", False) == is_completed]
    
    if since:
        turns = [t for t in turns if t.get("created_at") and t.get("created_at") >= since]
    
    if until:
        turns = [t for t in turns if t.get("created_at") and t.get("created_at") <= until]
    
    # 按创建时间倒序排序
    turns.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return turns[offset:offset+limit]


async def count_turns(
    dialogue_id: Optional[str] = None,
    session_id: Optional[str] = None,
    initiator_role: Optional[str] = None,
    responder_role: Optional[str] = None,
    is_completed: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None
) -> int:
    """
    计算轮次数量
    
    Args:
        dialogue_id: 对话ID
        session_id: 会话ID
        initiator_role: 发起者角色
        responder_role: 响应者角色
        is_completed: 是否已完成
        since: 开始时间
        until: 结束时间
    
    Returns:
        轮次数量
    """
    turns = list(_turns_db.values())
    
    # 应用过滤条件
    if dialogue_id:
        turns = [t for t in turns if t.get("dialogue_id") == dialogue_id]
    
    if session_id:
        turns = [t for t in turns if t.get("session_id") == session_id]
    
    if initiator_role:
        turns = [t for t in turns if t.get("initiator_role") == initiator_role]
    
    if responder_role:
        turns = [t for t in turns if t.get("responder_role") == responder_role]
    
    if is_completed is not None:
        turns = [t for t in turns if t.get("is_completed", False) == is_completed]
    
    if since:
        turns = [t for t in turns if t.get("created_at") and t.get("created_at") >= since]
    
    if until:
        turns = [t for t in turns if t.get("created_at") and t.get("created_at") <= until]
    
    return len(turns)


# 导出函数
turn_repo = {
    "create": create,
    "get": get,
    "update": update,
    "delete": delete,
    "get_by_session": get_by_session,
    "get_by_dialogue": get_by_dialogue,
    "get_unresponded_turns": get_unresponded_turns,
    "search_turns": search_turns,
    "count_turns": count_turns
}
