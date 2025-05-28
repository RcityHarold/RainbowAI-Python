"""
自我反思API路由
提供自我反思相关的API端点
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path

from ..models.api_models import (
    IntrospectionSessionCreate,
    IntrospectionSessionResponse,
    IntrospectionSessionListResponse,
    APIResponse
)
from ..core.introspection_engine import introspection_engine
from ..db.repositories import introspection_repo
from ..services.auth_service import get_current_user


router = APIRouter(prefix="/introspection", tags=["introspection"])


@router.post("/sessions", response_model=IntrospectionSessionResponse)
async def create_introspection_session(
    session_data: IntrospectionSessionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    创建自我反思会话
    """
    # 启动自我反思会话
    session = await introspection_engine.start_introspection_session(
        ai_id=session_data.ai_id,
        session_type=session_data.session_type,
        trigger_source=session_data.trigger_source,
        goal=session_data.goal,
        metadata=session_data.metadata
    )
    
    if "error" in session:
        raise HTTPException(status_code=400, detail=session["error"])
    
    return session


@router.get("/sessions", response_model=IntrospectionSessionListResponse)
async def list_introspection_sessions(
    ai_id: Optional[str] = Query(None, description="AI ID"),
    session_type: Optional[str] = Query(None, description="会话类型"),
    limit: int = Query(10, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取自我反思会话列表
    """
    # 构建查询条件
    query = {}
    if ai_id:
        query["ai_id"] = ai_id
    if session_type:
        query["session_type"] = session_type
    
    # 查询数据库
    total = await introspection_repo.count(query)
    sessions = await introspection_repo.find(query, limit=limit, offset=offset)
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": sessions
    }


@router.get("/sessions/{session_id}", response_model=IntrospectionSessionResponse)
async def get_introspection_session(
    session_id: str = Path(..., description="会话ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取自我反思会话详情
    """
    session = await introspection_repo.find_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="自我反思会话不存在")
    
    return session


@router.post("/trigger/performance-review", response_model=APIResponse)
async def trigger_performance_review(
    ai_id: str = Query(..., description="AI ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    触发性能评估
    """
    # 启动性能评估会话
    session = await introspection_engine.start_introspection_session(
        ai_id=ai_id,
        session_type="performance_review",
        trigger_source="api_trigger",
        goal="评估AI助手的整体性能和用户体验",
        metadata={"triggered_by": current_user.get("id")}
    )
    
    if "error" in session:
        raise HTTPException(status_code=400, detail=session["error"])
    
    return {
        "success": True,
        "message": "已成功触发性能评估",
        "data": {"session_id": session["id"]}
    }


@router.post("/trigger/error-analysis", response_model=APIResponse)
async def trigger_error_analysis(
    ai_id: str = Query(..., description="AI ID"),
    error_context: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    触发错误分析
    """
    # 启动错误分析会话
    session = await introspection_engine.start_introspection_session(
        ai_id=ai_id,
        session_type="error_analysis",
        trigger_source="api_trigger",
        goal="分析最近的错误和失败，找出根本原因",
        metadata={
            "triggered_by": current_user.get("id"),
            "error_context": error_context or {}
        }
    )
    
    if "error" in session:
        raise HTTPException(status_code=400, detail=session["error"])
    
    return {
        "success": True,
        "message": "已成功触发错误分析",
        "data": {"session_id": session["id"]}
    }


@router.post("/trigger/improvement-planning", response_model=APIResponse)
async def trigger_improvement_planning(
    ai_id: str = Query(..., description="AI ID"),
    focus_areas: Optional[List[str]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    触发改进计划
    """
    # 启动改进计划会话
    session = await introspection_engine.start_introspection_session(
        ai_id=ai_id,
        session_type="improvement_planning",
        trigger_source="api_trigger",
        goal="基于用户反馈和性能数据制定改进计划",
        metadata={
            "triggered_by": current_user.get("id"),
            "focus_areas": focus_areas or []
        }
    )
    
    if "error" in session:
        raise HTTPException(status_code=400, detail=session["error"])
    
    return {
        "success": True,
        "message": "已成功触发改进计划",
        "data": {"session_id": session["id"]}
    }
