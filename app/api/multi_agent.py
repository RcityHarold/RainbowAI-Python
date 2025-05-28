"""
多智能体协作API路由
提供多智能体协作相关的API端点
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body

from ..models.api_models import (
    CollaborationSessionCreate,
    CollaborationSessionResponse,
    CollaborationSessionListResponse,
    CollaborationMessageCreate,
    CollaborationMessageResponse,
    CollaborationMessageListResponse,
    AgentResponse,
    AgentListResponse,
    APIResponse
)
from ..core.multi_agent_coordinator import multi_agent_coordinator, Agent
from ..services.auth_service import get_current_user


router = APIRouter(prefix="/multi-agent", tags=["multi_agent"])


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取可用智能体列表
    """
    agents = multi_agent_coordinator.list_agents()
    
    return {
        "total": len(agents),
        "items": agents
    }


@router.post("/agents", response_model=AgentResponse)
async def create_agent(
    agent_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    创建新智能体
    """
    try:
        # 创建新智能体
        agent = Agent(
            agent_id=agent_data.get("agent_id", f"agent:{agent_data.get('name', 'unnamed')}"),
            name=agent_data.get("name", "未命名智能体"),
            role=agent_data.get("role", "通用助手"),
            description=agent_data.get("description", ""),
            capabilities=agent_data.get("capabilities", []),
            system_prompt=agent_data.get("system_prompt", ""),
            metadata=agent_data.get("metadata", {})
        )
        
        # 注册智能体
        multi_agent_coordinator.register_agent(agent)
        
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "description": agent.description,
            "capabilities": agent.capabilities
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建智能体失败: {str(e)}")


@router.post("/sessions", response_model=CollaborationSessionResponse)
async def create_collaboration_session(
    session_data: CollaborationSessionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    创建协作会话
    """
    # 创建协作会话
    session = await multi_agent_coordinator.create_collaboration_session(
        task=session_data.task,
        agent_ids=session_data.agent_ids,
        initiator_id=current_user.get("id"),
        metadata=session_data.metadata
    )
    
    if "error" in session:
        raise HTTPException(status_code=400, detail=session["error"])
    
    return session


@router.get("/sessions", response_model=CollaborationSessionListResponse)
async def list_collaboration_sessions(
    limit: int = Query(10, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取协作会话列表
    """
    # 获取所有会话
    sessions = list(multi_agent_coordinator.sessions.values())
    
    # 排序和分页
    sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    total = len(sessions)
    paged_sessions = sessions[offset:offset+limit]
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": paged_sessions
    }


@router.get("/sessions/{session_id}", response_model=CollaborationSessionResponse)
async def get_collaboration_session(
    session_id: str = Path(..., description="会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取协作会话详情
    """
    session = multi_agent_coordinator.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="协作会话不存在")
    
    return session


@router.post("/sessions/{session_id}/messages", response_model=CollaborationMessageResponse)
async def send_message(
    message_data: CollaborationMessageCreate,
    session_id: str = Path(..., description="会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    发送消息到协作会话
    """
    # 发送消息
    result = await multi_agent_coordinator.send_message(
        session_id=session_id,
        sender_id="user",
        content=message_data.content,
        target_agent_ids=message_data.target_agent_ids,
        metadata=message_data.metadata
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "发送消息失败"))
    
    return {
        "id": result["message_id"],
        "session_id": session_id,
        "sender_id": "user",
        "content": message_data.content,
        "created_at": result.get("created_at", ""),
        "success": True
    }


@router.get("/sessions/{session_id}/messages", response_model=CollaborationMessageListResponse)
async def get_session_messages(
    session_id: str = Path(..., description="会话ID"),
    limit: int = Query(50, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取协作会话消息
    """
    # 获取会话消息
    messages = await multi_agent_coordinator.get_session_messages(
        session_id=session_id,
        limit=limit,
        offset=offset
    )
    
    return {
        "total": len(messages),
        "offset": offset,
        "limit": limit,
        "items": messages
    }


@router.post("/sessions/{session_id}/close", response_model=APIResponse)
async def close_collaboration_session(
    session_id: str = Path(..., description="会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    关闭协作会话
    """
    # 关闭会话
    result = await multi_agent_coordinator.close_session(session_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "关闭会话失败"))
    
    return {
        "success": True,
        "message": "协作会话已关闭",
        "data": {"session_id": session_id}
    }


@router.post("/sessions/{session_id}/system-message", response_model=CollaborationMessageResponse)
async def send_system_message(
    message_data: CollaborationMessageCreate,
    session_id: str = Path(..., description="会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    发送系统消息到协作会话
    """
    # 发送系统消息
    result = await multi_agent_coordinator.send_system_message(
        session_id=session_id,
        content=message_data.content,
        target_agent_ids=message_data.target_agent_ids,
        metadata=message_data.metadata
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "发送系统消息失败"))
    
    return {
        "id": result["message_id"],
        "session_id": session_id,
        "sender_id": "system:coordinator",
        "content": message_data.content,
        "created_at": result.get("created_at", ""),
        "success": True
    }
