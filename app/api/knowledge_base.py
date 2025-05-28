"""
知识库集成API路由
提供知识库查询和管理的API端点
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body

from ..models.api_models import (
    KnowledgeBaseConnectorCreate,
    KnowledgeBaseConnectorResponse,
    KnowledgeBaseConnectorListResponse,
    KnowledgeBaseSearchResponse,
    KnowledgeBaseDocumentResponse,
    APIResponse
)
from ..core.knowledge_base import kb_manager
from ..services.auth_service import get_current_user


router = APIRouter(prefix="/knowledge-base", tags=["knowledge_base"])


@router.post("/connectors", response_model=KnowledgeBaseConnectorResponse)
async def register_connector(
    connector_data: KnowledgeBaseConnectorCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    注册知识库连接器
    """
    try:
        # 注册连接器
        connector_id = kb_manager.register_connector(connector_data.dict())
        
        # 获取连接器信息
        connectors = kb_manager.list_connectors()
        for connector in connectors:
            if connector["id"] == connector_id:
                return connector
        
        raise HTTPException(status_code=500, detail="注册成功但无法获取连接器信息")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"注册知识库连接器失败: {str(e)}")


@router.get("/connectors", response_model=KnowledgeBaseConnectorListResponse)
async def list_connectors(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取知识库连接器列表
    """
    connectors = kb_manager.list_connectors()
    
    return {
        "total": len(connectors),
        "items": connectors
    }


@router.get("/connectors/{connector_id}", response_model=KnowledgeBaseConnectorResponse)
async def get_connector(
    connector_id: str = Path(..., description="连接器ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取知识库连接器详情
    """
    connectors = kb_manager.list_connectors()
    for connector in connectors:
        if connector["id"] == connector_id:
            return connector
    
    raise HTTPException(status_code=404, detail="知识库连接器不存在")


@router.delete("/connectors/{connector_id}", response_model=APIResponse)
async def remove_connector(
    connector_id: str = Path(..., description="连接器ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    移除知识库连接器
    """
    success = kb_manager.remove_connector(connector_id)
    if not success:
        raise HTTPException(status_code=404, detail="知识库连接器不存在")
    
    return {
        "success": True,
        "message": "已成功移除知识库连接器",
        "data": {"connector_id": connector_id}
    }


@router.get("/search", response_model=KnowledgeBaseSearchResponse)
async def search_all_knowledge_bases(
    query: str = Query(..., description="搜索查询"),
    limit_per_connector: int = Query(3, ge=1, le=10, description="每个连接器的结果数量限制"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    搜索所有知识库
    """
    results = await kb_manager.search_all(query, limit_per_connector)
    
    # 计算总结果数
    total_results = sum(len(results_list) for results_list in results.values())
    
    return {
        "query": query,
        "total_results": total_results,
        "connector_count": len(results),
        "results": results
    }


@router.get("/connectors/{connector_id}/search", response_model=KnowledgeBaseSearchResponse)
async def search_knowledge_base(
    connector_id: str = Path(..., description="连接器ID"),
    query: str = Query(..., description="搜索查询"),
    limit: int = Query(5, ge=1, le=20, description="结果数量限制"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    搜索特定知识库
    """
    try:
        results = await kb_manager.search(connector_id, query, limit)
        
        return {
            "query": query,
            "total_results": len(results),
            "connector_count": 1,
            "results": {connector_id: results}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索知识库失败: {str(e)}")


@router.get("/connectors/{connector_id}/documents/{document_id}", response_model=KnowledgeBaseDocumentResponse)
async def get_document(
    connector_id: str = Path(..., description="连接器ID"),
    document_id: str = Path(..., description="文档ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取知识库文档详情
    """
    try:
        document = await kb_manager.get_document(connector_id, document_id)
        
        return {
            "connector_id": connector_id,
            "document_id": document_id,
            "document": document
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")


@router.get("/connectors/{connector_id}/health", response_model=APIResponse)
async def check_connector_health(
    connector_id: str = Path(..., description="连接器ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    检查知识库连接器健康状态
    """
    try:
        health_status = await kb_manager.check_health(connector_id)
        
        return {
            "success": health_status.get("status") == "ok",
            "message": "知识库连接器健康状态检查完成",
            "data": health_status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.get("/health", response_model=APIResponse)
async def check_all_connectors_health(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    检查所有知识库连接器健康状态
    """
    try:
        health_statuses = await kb_manager.check_all_health()
        
        # 计算总体健康状态
        all_healthy = all(status.get("status") == "ok" for status in health_statuses.values())
        
        return {
            "success": True,
            "message": "所有知识库连接器健康状态检查完成",
            "data": {
                "all_healthy": all_healthy,
                "connector_count": len(health_statuses),
                "health_statuses": health_statuses
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")
