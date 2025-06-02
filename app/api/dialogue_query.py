"""
对话查询API模块
提供统一的对话查询接口
"""
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from ..services.dialogue_service import dialogue_service
from ..models.data_models import Dialogue, Session, Turn, Message
from ..core.constants import DialogueTypes, SessionTypes, RoleTypes, ContentTypes


router = APIRouter()


# 响应模型
class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class DialogueQueryResponse(PaginatedResponse):
    """对话查询响应"""
    items: List[Dialogue]


class SessionQueryResponse(PaginatedResponse):
    """会话查询响应"""
    items: List[Session]


class TurnQueryResponse(PaginatedResponse):
    """轮次查询响应"""
    items: List[Turn]


class MessageQueryResponse(PaginatedResponse):
    """消息查询响应"""
    items: List[Message]


class DialogueDetail(BaseModel):
    """对话详情"""
    dialogue: Dialogue
    sessions: List[Session]
    latest_messages: List[Message]


class SessionDetail(BaseModel):
    """会话详情"""
    session: Session
    turns: List[Turn]
    messages: List[Message]


class TurnDetail(BaseModel):
    """轮次详情"""
    turn: Turn
    messages: List[Message]


# 查询对话列表
@router.get("/dialogues", response_model=DialogueQueryResponse)
async def query_dialogues(
    query: Optional[str] = None,
    dialogue_type: Optional[str] = None,
    human_id: Optional[str] = None,
    ai_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    查询对话列表
    
    Args:
        query: 搜索关键词
        dialogue_type: 对话类型
        human_id: 人类ID
        ai_id: AI ID
        is_active: 是否活跃
        since: 开始时间
        until: 结束时间
        page: 页码
        page_size: 每页数量
    
    Returns:
        对话列表
    """
    offset = (page - 1) * page_size
    
    # 获取对话列表
    dialogues = await dialogue_service.dialogue_repo["search_dialogues"](
        query=query,
        dialogue_type=dialogue_type,
        human_id=human_id,
        ai_id=ai_id,
        is_active=is_active,
        since=since,
        until=until,
        limit=page_size,
        offset=offset
    )
    
    # 获取总数
    total = await dialogue_service.dialogue_repo["count_dialogues"](
        dialogue_type=dialogue_type,
        human_id=human_id,
        ai_id=ai_id,
        is_active=is_active,
        since=since,
        until=until
    )
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    return DialogueQueryResponse(
        items=dialogues,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# 查询会话列表
@router.get("/sessions", response_model=SessionQueryResponse)
async def query_sessions(
    dialogue_id: Optional[str] = None,
    session_type: Optional[str] = None,
    created_by: Optional[str] = None,
    is_active: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    查询会话列表
    
    Args:
        dialogue_id: 对话ID
        session_type: 会话类型
        created_by: 创建者
        is_active: 是否活跃
        since: 开始时间
        until: 结束时间
        page: 页码
        page_size: 每页数量
    
    Returns:
        会话列表
    """
    offset = (page - 1) * page_size
    
    # 获取会话列表
    sessions = await dialogue_service.session_repo["search_sessions"](
        dialogue_id=dialogue_id,
        session_type=session_type,
        created_by=created_by,
        is_active=is_active,
        since=since,
        until=until,
        limit=page_size,
        offset=offset
    )
    
    # 获取总数
    total = await dialogue_service.session_repo["count_sessions"](
        dialogue_id=dialogue_id,
        session_type=session_type,
        created_by=created_by,
        is_active=is_active,
        since=since,
        until=until
    )
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    return SessionQueryResponse(
        items=sessions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# 查询轮次列表
@router.get("/turns", response_model=TurnQueryResponse)
async def query_turns(
    dialogue_id: Optional[str] = None,
    session_id: Optional[str] = None,
    initiator_role: Optional[str] = None,
    responder_role: Optional[str] = None,
    is_completed: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    查询轮次列表
    
    Args:
        dialogue_id: 对话ID
        session_id: 会话ID
        initiator_role: 发起者角色
        responder_role: 响应者角色
        is_completed: 是否已完成
        since: 开始时间
        until: 结束时间
        page: 页码
        page_size: 每页数量
    
    Returns:
        轮次列表
    """
    offset = (page - 1) * page_size
    
    # 获取轮次列表
    turns = await dialogue_service.turn_repo["search_turns"](
        dialogue_id=dialogue_id,
        session_id=session_id,
        initiator_role=initiator_role,
        responder_role=responder_role,
        is_completed=is_completed,
        since=since,
        until=until,
        limit=page_size,
        offset=offset
    )
    
    # 获取总数
    total = await dialogue_service.turn_repo["count_turns"](
        dialogue_id=dialogue_id,
        session_id=session_id,
        initiator_role=initiator_role,
        responder_role=responder_role,
        is_completed=is_completed,
        since=since,
        until=until
    )
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    return TurnQueryResponse(
        items=turns,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# 查询消息列表
@router.get("/messages", response_model=MessageQueryResponse)
async def query_messages(
    dialogue_id: Optional[str] = None,
    session_id: Optional[str] = None,
    turn_id: Optional[str] = None,
    sender_role: Optional[str] = None,
    sender_id: Optional[str] = None,
    content_type: Optional[str] = None,
    query: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    查询消息列表
    
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
        page: 页码
        page_size: 每页数量
    
    Returns:
        消息列表
    """
    offset = (page - 1) * page_size
    
    # 获取消息列表
    messages = await dialogue_service.message_repo["search_messages"](
        dialogue_id=dialogue_id,
        session_id=session_id,
        turn_id=turn_id,
        sender_role=sender_role,
        sender_id=sender_id,
        content_type=content_type,
        query=query,
        since=since,
        until=until,
        limit=page_size,
        offset=offset
    )
    
    # 获取总数
    total = await dialogue_service.message_repo["count_messages"](
        dialogue_id=dialogue_id,
        session_id=session_id,
        turn_id=turn_id,
        sender_role=sender_role,
        sender_id=sender_id,
        content_type=content_type,
        since=since,
        until=until
    )
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    return MessageQueryResponse(
        items=messages,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# 获取对话详情
@router.get("/dialogues/{dialogue_id}", response_model=DialogueDetail)
async def get_dialogue_detail(dialogue_id: str):
    """
    获取对话详情
    
    Args:
        dialogue_id: 对话ID
    
    Returns:
        对话详情
    """
    # 获取对话
    dialogue = await dialogue_service.dialogue_repo["get"](dialogue_id)
    if not dialogue:
        raise HTTPException(
            status_code=404,
            detail=f"Dialogue {dialogue_id} not found"
        )
    
    # 获取会话列表
    sessions = await dialogue_service.session_repo["get_by_dialogue"](dialogue_id)
    
    # 获取最新消息
    messages = await dialogue_service.message_repo["search_messages"](
        dialogue_id=dialogue_id,
        limit=10
    )
    
    return DialogueDetail(
        dialogue=dialogue,
        sessions=sessions,
        latest_messages=messages
    )


# 获取会话详情
@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session_detail(session_id: str):
    """
    获取会话详情
    
    Args:
        session_id: 会话ID
    
    Returns:
        会话详情
    """
    # 获取会话
    session = await dialogue_service.session_repo["get"](session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    # 获取轮次列表
    turns = await dialogue_service.turn_repo["get_by_session"](session_id)
    
    # 获取消息列表
    messages = await dialogue_service.message_repo["get_by_session"](session_id)
    
    return SessionDetail(
        session=session,
        turns=turns,
        messages=messages
    )


# 获取轮次详情
@router.get("/turns/{turn_id}", response_model=TurnDetail)
async def get_turn_detail(turn_id: str):
    """
    获取轮次详情
    
    Args:
        turn_id: 轮次ID
    
    Returns:
        轮次详情
    """
    # 获取轮次
    turn = await dialogue_service.turn_repo["get"](turn_id)
    if not turn:
        raise HTTPException(
            status_code=404,
            detail=f"Turn {turn_id} not found"
        )
    
    # 获取消息列表
    messages = await dialogue_service.message_repo["get_by_turn"](turn_id)
    
    return TurnDetail(
        turn=turn,
        messages=messages
    )


# 获取未回应的轮次
@router.get("/unresponded_turns", response_model=List[Turn])
async def get_unresponded_turns(dialogue_id: Optional[str] = None):
    """
    获取未回应的轮次
    
    Args:
        dialogue_id: 对话ID
    
    Returns:
        未回应的轮次列表
    """
    turns = await dialogue_service.turn_repo["get_unresponded_turns"](dialogue_id)
    return turns


# 获取最近活跃的会话
@router.get("/recent_sessions", response_model=List[Session])
async def get_recent_sessions(days: int = Query(7, ge=1), limit: int = Query(10, ge=1, le=100)):
    """
    获取最近活跃的会话
    
    Args:
        days: 最近几天
        limit: 限制数量
    
    Returns:
        最近活跃的会话列表
    """
    sessions = await dialogue_service.session_repo["get_recent_sessions"](days, limit)
    return sessions


# 搜索历史对话
@router.get("/search", response_model=DialogueQueryResponse)
async def search_dialogues(
    query: str,
    dialogue_type: Optional[str] = None,
    human_id: Optional[str] = None,
    ai_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    搜索历史对话
    
    Args:
        query: 搜索关键词
        dialogue_type: 对话类型
        human_id: 人类ID
        ai_id: AI ID
        is_active: 是否活跃
        since: 开始时间
        until: 结束时间
        page: 页码
        page_size: 每页数量
    
    Returns:
        对话列表
    """
    offset = (page - 1) * page_size
    
    # 获取对话列表
    dialogues = await dialogue_service.dialogue_repo["search_dialogues"](
        query=query,
        dialogue_type=dialogue_type,
        human_id=human_id,
        ai_id=ai_id,
        is_active=is_active,
        since=since,
        until=until,
        limit=page_size,
        offset=offset
    )
    
    # 获取总数
    total = await dialogue_service.dialogue_repo["count_dialogues"](
        dialogue_type=dialogue_type,
        human_id=human_id,
        ai_id=ai_id,
        is_active=is_active,
        since=since,
        until=until
    )
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    return DialogueQueryResponse(
        items=dialogues,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# 获取用户的活跃对话
@router.get("/user/{user_id}/active", response_model=List[Dialogue])
async def get_user_active_dialogues(
    user_id: str,
    role_type: str = Query(RoleTypes.HUMAN, description="用户角色类型")
):
    """
    获取用户的活跃对话
    
    Args:
        user_id: 用户ID
        role_type: 角色类型
    
    Returns:
        活跃对话列表
    """
    if role_type == RoleTypes.HUMAN:
        dialogues = await dialogue_service.get_active_dialogues(human_id=user_id)
    else:
        dialogues = await dialogue_service.get_active_dialogues(ai_id=user_id)
    
    return dialogues
