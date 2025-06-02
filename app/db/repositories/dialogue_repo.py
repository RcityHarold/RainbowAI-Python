"""
对话存储库模块
提供对话相关的数据库操作
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

# 模拟数据库存储
# 实际应用中应替换为真实数据库操作
_dialogues_db = {}

logger = logging.getLogger("dialogue_repo")


async def create(dialogue_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建对话"""
    dialogue_id = dialogue_data.get("id")
    if not dialogue_id:
        raise ValueError("dialogue_id is required")
    
    _dialogues_db[dialogue_id] = dialogue_data
    logger.info(f"Created dialogue: {dialogue_id}")
    
    return dialogue_data


async def get(dialogue_id: str) -> Optional[Dict[str, Any]]:
    """获取对话"""
    return _dialogues_db.get(dialogue_id)


async def update(dialogue_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新对话"""
    if dialogue_id not in _dialogues_db:
        logger.warning(f"Dialogue not found: {dialogue_id}")
        return None
    
    dialogue = _dialogues_db[dialogue_id]
    dialogue.update(update_data)
    
    return dialogue


async def delete(dialogue_id: str) -> bool:
    """删除对话"""
    if dialogue_id in _dialogues_db:
        del _dialogues_db[dialogue_id]
        logger.info(f"Deleted dialogue: {dialogue_id}")
        return True
    
    logger.warning(f"Dialogue not found for deletion: {dialogue_id}")
    return False


async def get_active_dialogues() -> List[Dict[str, Any]]:
    """获取所有活跃对话"""
    return [d for d in _dialogues_db.values() if d.get("is_active", True)]


async def get_by_human_id(human_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """获取指定人类的对话"""
    dialogues = [d for d in _dialogues_db.values() if d.get("human_id") == human_id]
    
    # 按创建时间倒序排序
    dialogues.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return dialogues[offset:offset+limit]


async def get_by_ai_id(ai_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """获取指定AI的对话"""
    dialogues = [d for d in _dialogues_db.values() if d.get("ai_id") == ai_id]
    
    # 按创建时间倒序排序
    dialogues.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return dialogues[offset:offset+limit]


async def search_dialogues(
    query: Optional[str] = None,
    dialogue_type: Optional[str] = None,
    human_id: Optional[str] = None,
    ai_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 10,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    搜索对话
    
    Args:
        query: 搜索关键词
        dialogue_type: 对话类型
        human_id: 人类ID
        ai_id: AI ID
        is_active: 是否活跃
        since: 开始时间
        until: 结束时间
        limit: 限制数量
        offset: 偏移量
    
    Returns:
        对话列表
    """
    dialogues = list(_dialogues_db.values())
    
    # 应用过滤条件
    if query:
        dialogues = [d for d in dialogues if 
                    query.lower() in d.get("title", "").lower() or 
                    query.lower() in d.get("description", "").lower()]
    
    if dialogue_type:
        dialogues = [d for d in dialogues if d.get("dialogue_type") == dialogue_type]
    
    if human_id:
        dialogues = [d for d in dialogues if d.get("human_id") == human_id]
    
    if ai_id:
        dialogues = [d for d in dialogues if d.get("ai_id") == ai_id]
    
    if is_active is not None:
        dialogues = [d for d in dialogues if d.get("is_active", True) == is_active]
    
    if since:
        dialogues = [d for d in dialogues if d.get("created_at") and d.get("created_at") >= since]
    
    if until:
        dialogues = [d for d in dialogues if d.get("created_at") and d.get("created_at") <= until]
    
    # 按创建时间倒序排序
    dialogues.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return dialogues[offset:offset+limit]


async def get_recent_dialogues(days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
    """获取最近的对话"""
    since = datetime.utcnow() - timedelta(days=days)
    
    dialogues = [d for d in _dialogues_db.values() if 
                d.get("created_at") and d.get("created_at") >= since]
    
    # 按创建时间倒序排序
    dialogues.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return dialogues[:limit]


async def count_dialogues(
    dialogue_type: Optional[str] = None,
    human_id: Optional[str] = None,
    ai_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None
) -> int:
    """
    计算对话数量
    
    Args:
        dialogue_type: 对话类型
        human_id: 人类ID
        ai_id: AI ID
        is_active: 是否活跃
        since: 开始时间
        until: 结束时间
    
    Returns:
        对话数量
    """
    dialogues = list(_dialogues_db.values())
    
    # 应用过滤条件
    if dialogue_type:
        dialogues = [d for d in dialogues if d.get("dialogue_type") == dialogue_type]
    
    if human_id:
        dialogues = [d for d in dialogues if d.get("human_id") == human_id]
    
    if ai_id:
        dialogues = [d for d in dialogues if d.get("ai_id") == ai_id]
    
    if is_active is not None:
        dialogues = [d for d in dialogues if d.get("is_active", True) == is_active]
    
    if since:
        dialogues = [d for d in dialogues if d.get("created_at") and d.get("created_at") >= since]
    
    if until:
        dialogues = [d for d in dialogues if d.get("created_at") and d.get("created_at") <= until]
    
    return len(dialogues)


# 导出函数
dialogue_repo = {
    "create": create,
    "get": get,
    "update": update,
    "delete": delete,
    "get_active_dialogues": get_active_dialogues,
    "get_by_human_id": get_by_human_id,
    "get_by_ai_id": get_by_ai_id,
    "search_dialogues": search_dialogues,
    "get_recent_dialogues": get_recent_dialogues,
    "count_dialogues": count_dialogues
}
