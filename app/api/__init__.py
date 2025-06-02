"""
API路由模块
集成所有API路由
"""
from fastapi import APIRouter

# 导入现有的路由器
from .realtime import router as realtime_router
from .media import router as media_router
from .introspection import router as introspection_router
from .knowledge_base import router as knowledge_base_router
from .multi_agent import router as multi_agent_router

# 创建主路由
api_router = APIRouter()

# 包含子路由
api_router.include_router(realtime_router, tags=["实时通信"])
api_router.include_router(media_router, tags=["媒体处理"])
api_router.include_router(introspection_router, tags=["自我反思"])
api_router.include_router(knowledge_base_router, tags=["知识库"])
api_router.include_router(multi_agent_router, tags=["多智能体"])

# 为缺失的模块创建虚拟路由器
class RouterWrapper:
    def __init__(self, prefix="", tags=None):
        self.router = APIRouter(prefix=prefix, tags=tags or [])
        
    def __getattr__(self, name):
        # 返回路由器对象，以便main.py中的include_router调用能够正常工作
        if name == "router":
            return self.router
        raise AttributeError(f"{self.__class__.__name__} has no attribute {name}")

# 创建缺失的模块
sessions = RouterWrapper(prefix="/api/sessions", tags=["会话"])
turns = RouterWrapper(prefix="/api/turns", tags=["对话轮次"])
messages = RouterWrapper(prefix="/api/messages", tags=["消息"])
tools = RouterWrapper(prefix="/api/tools", tags=["工具"])
