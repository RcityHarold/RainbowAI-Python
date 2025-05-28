"""
API路由模块
集成所有API路由
"""
from fastapi import APIRouter

from .realtime import router as realtime_router
from .media import router as media_router

# 创建主路由
api_router = APIRouter()

# 包含子路由
api_router.include_router(realtime_router, tags=["实时通信"])
api_router.include_router(media_router, tags=["媒体处理"])
