"""
自省系统存储库
提供自省会话和自省轮次的存储和检索功能
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

# 模拟数据库存储
# 实际应用中应替换为真实数据库操作
_sessions_db = {}
_turns_db = {}
_reports_db = {}
_memory_entries_db = {}

logger = logging.getLogger("introspection_repo")


async def create_session(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建自省会话"""
    if "id" not in session_data:
        session_data["id"] = f"introspection_session:{uuid.uuid4()}"
    
    session_id = session_data["id"]
    session_data["created_at"] = datetime.utcnow()
    
    _sessions_db[session_id] = session_data
    logger.info(f"Created introspection session: {session_id}")
    
    return session_data


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """获取自省会话"""
    return _sessions_db.get(session_id)


async def update_session(session_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新自省会话"""
    if session_id not in _sessions_db:
        logger.warning(f"Introspection session not found: {session_id}")
        return None
    
    session = _sessions_db[session_id]
    session.update(update_data)
    session["updated_at"] = datetime.utcnow()
    
    return session


async def list_sessions(ai_id: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """列出自省会话"""
    sessions = list(_sessions_db.values())
    
    if ai_id:
        sessions = [s for s in sessions if s.get("ai_id") == ai_id]
    
    # 按开始时间倒序排序
    sessions.sort(key=lambda x: x.get("started_at", datetime.min), reverse=True)
    
    return sessions[offset:offset+limit]


async def create_turn(turn_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建自省轮次"""
    if "id" not in turn_data:
        turn_data["id"] = f"introspection_turn:{uuid.uuid4()}"
    
    turn_id = turn_data["id"]
    session_id = turn_data.get("session_id")
    
    if not session_id:
        raise ValueError("session_id is required")
    
    turn_data["created_at"] = datetime.utcnow()
    _turns_db[turn_id] = turn_data
    
    # 更新会话的轮次列表
    session = await get_session(session_id)
    if session:
        turns = session.get("turns", [])
        turns.append(turn_id)
        await update_session(session_id, {"turns": turns})
    
    logger.info(f"Created introspection turn: {turn_id} for session: {session_id}")
    return turn_data


async def get_turn(turn_id: str) -> Optional[Dict[str, Any]]:
    """获取自省轮次"""
    return _turns_db.get(turn_id)


async def update_turn(turn_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新自省轮次"""
    if turn_id not in _turns_db:
        logger.warning(f"Introspection turn not found: {turn_id}")
        return None
    
    turn = _turns_db[turn_id]
    turn.update(update_data)
    turn["updated_at"] = datetime.utcnow()
    
    return turn


async def list_turns(session_id: str) -> List[Dict[str, Any]]:
    """列出会话的所有轮次"""
    turns = [t for t in _turns_db.values() if t.get("session_id") == session_id]
    
    # 按创建时间排序
    turns.sort(key=lambda x: x.get("created_at", datetime.min))
    
    return turns


async def create_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建自省报告"""
    if "id" not in report_data:
        report_data["id"] = f"introspection_report:{uuid.uuid4()}"
    
    report_id = report_data["id"]
    report_data["created_at"] = datetime.utcnow()
    
    _reports_db[report_id] = report_data
    logger.info(f"Created introspection report: {report_id}")
    
    return report_data


async def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """获取自省报告"""
    return _reports_db.get(report_id)


async def list_reports(ai_id: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """列出自省报告"""
    reports = list(_reports_db.values())
    
    if ai_id:
        reports = [r for r in reports if r.get("ai_id") == ai_id]
    
    # 按创建时间倒序排序
    reports.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return reports[offset:offset+limit]


async def create_memory_entry(entry_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建记忆条目"""
    if "id" not in entry_data:
        entry_data["id"] = f"memory_entry:{uuid.uuid4()}"
    
    entry_id = entry_data["id"]
    entry_data["created_at"] = datetime.utcnow()
    
    _memory_entries_db[entry_id] = entry_data
    logger.info(f"Created memory entry: {entry_id}")
    
    return entry_data


async def get_memory_entry(entry_id: str) -> Optional[Dict[str, Any]]:
    """获取记忆条目"""
    return _memory_entries_db.get(entry_id)


async def list_memory_entries(ai_id: str, memory_type: Optional[str] = None, tags: Optional[List[str]] = None, 
                             limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """列出记忆条目"""
    entries = [e for e in _memory_entries_db.values() if e.get("ai_id") == ai_id]
    
    if memory_type:
        entries = [e for e in entries if e.get("memory_type") == memory_type]
    
    if tags:
        entries = [e for e in entries if any(tag in e.get("tags", []) for tag in tags)]
    
    # 按重要性和创建时间排序
    entries.sort(key=lambda x: (x.get("importance", 0), x.get("created_at", datetime.min)), reverse=True)
    
    return entries[offset:offset+limit]


# 导出为单一对象，便于导入
introspection_repo = {
    "create_session": create_session,
    "get_session": get_session,
    "update_session": update_session,
    "list_sessions": list_sessions,
    "create_turn": create_turn,
    "get_turn": get_turn,
    "update_turn": update_turn,
    "list_turns": list_turns,
    "create_report": create_report,
    "get_report": get_report,
    "list_reports": list_reports,
    "create_memory_entry": create_memory_entry,
    "get_memory_entry": get_memory_entry,
    "list_memory_entries": list_memory_entries
}
