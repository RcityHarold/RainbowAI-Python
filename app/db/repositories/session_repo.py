"""
会话存储库模块
提供会话相关的数据库操作
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

# 模拟数据库存储
# 实际应用中应替换为真实数据库操作
_sessions_db = {}

logger = logging.getLogger("session_repo")


async def create(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建会话"""
    session_id = session_data.get("id")
    if not session_id:
        raise ValueError("session_id is required")
    
    _sessions_db[session_id] = session_data
    logger.info(f"Created session: {session_id}")
    
    return session_data


async def get(session_id: str) -> Optional[Dict[str, Any]]:
    """获取会话"""
    return _sessions_db.get(session_id)


async def update(session_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新会话"""
    if session_id not in _sessions_db:
        logger.warning(f"Session not found: {session_id}")
        return None
    
    session = _sessions_db[session_id]
    session.update(update_data)
    
    return session


async def delete(session_id: str) -> bool:
    """删除会话"""
    if session_id in _sessions_db:
        del _sessions_db[session_id]
        logger.info(f"Deleted session: {session_id}")
        return True
    
    logger.warning(f"Session not found for deletion: {session_id}")
    return False


async def get_by_dialogue(dialogue_id: str) -> List[Dict[str, Any]]:
    """获取对话的所有会话"""
    sessions = [s for s in _sessions_db.values() if s.get("dialogue_id") == dialogue_id]
    
    # 按创建时间排序
    sessions.sort(key=lambda x: x.get("created_at", datetime.min))
    
    return sessions


async def get_active_session(dialogue_id: str) -> Optional[Dict[str, Any]]:
    """获取对话的活跃会话"""
    sessions = [s for s in _sessions_db.values() if 
               s.get("dialogue_id") == dialogue_id and 
               not s.get("end_at")]
    
    if not sessions:
        return None
    
    # 返回最新创建的会话
    return max(sessions, key=lambda x: x.get("created_at", datetime.min))


async def search_sessions(
    dialogue_id: Optional[str] = None,
    session_type: Optional[str] = None,
    created_by: Optional[str] = None,
    is_active: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 10,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    搜索会话
    
    Args:
        dialogue_id: 对话ID
        session_type: 会话类型
        created_by: 创建者
        is_active: 是否活跃
        since: 开始时间
        until: 结束时间
        limit: 限制数量
        offset: 偏移量
    
    Returns:
        会话列表
    """
    sessions = list(_sessions_db.values())
    
    # 应用过滤条件
    if dialogue_id:
        sessions = [s for s in sessions if s.get("dialogue_id") == dialogue_id]
    
    if session_type:
        sessions = [s for s in sessions if s.get("session_type") == session_type]
    
    if created_by:
        sessions = [s for s in sessions if s.get("created_by") == created_by]
    
    if is_active is not None:
        if is_active:
            sessions = [s for s in sessions if not s.get("end_at")]
        else:
            sessions = [s for s in sessions if s.get("end_at")]
    
    if since:
        sessions = [s for s in sessions if s.get("created_at") and s.get("created_at") >= since]
    
    if until:
        sessions = [s for s in sessions if s.get("created_at") and s.get("created_at") <= until]
    
    # 按创建时间倒序排序
    sessions.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return sessions[offset:offset+limit]


async def get_recent_sessions(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
    """获取最近的会话"""
    since = datetime.utcnow() - timedelta(days=days)
    
    sessions = [s for s in _sessions_db.values() if 
               s.get("created_at") and s.get("created_at") >= since]
    
    # 按创建时间倒序排序
    sessions.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return sessions[:limit]


async def count_sessions(
    dialogue_id: Optional[str] = None,
    session_type: Optional[str] = None,
    created_by: Optional[str] = None,
    is_active: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None
) -> int:
    """
    计算会话数量
    
    Args:
        dialogue_id: 对话ID
        session_type: 会话类型
        created_by: 创建者
        is_active: 是否活跃
        since: 开始时间
        until: 结束时间
    
    Returns:
        会话数量
    """
    sessions = list(_sessions_db.values())
    
    # 应用过滤条件
    if dialogue_id:
        sessions = [s for s in sessions if s.get("dialogue_id") == dialogue_id]
    
    if session_type:
        sessions = [s for s in sessions if s.get("session_type") == session_type]
    
    if created_by:
        sessions = [s for s in sessions if s.get("created_by") == created_by]
    
    if is_active is not None:
        if is_active:
            sessions = [s for s in sessions if not s.get("end_at")]
        else:
            sessions = [s for s in sessions if s.get("end_at")]
    
    if since:
        sessions = [s for s in sessions if s.get("created_at") and s.get("created_at") >= since]
    
    if until:
        sessions = [s for s in sessions if s.get("created_at") and s.get("created_at") <= until]
    
    return len(sessions)


# 导出函数
session_repo = {
    "create": create,
    "get": get,
    "update": update,
    "delete": delete,
    "get_by_dialogue": get_by_dialogue,
    "get_active_session": get_active_session,
    "search_sessions": search_sessions,
    "get_recent_sessions": get_recent_sessions,
    "count_sessions": count_sessions
}
