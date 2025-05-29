"""
彩虹城AI对话管理系统主入口
"""
import logging
import asyncio
import uuid
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from .core.input_hub import InputHub
from .core.dialogue_core import DialogueCore
from .models.data_models import (
    Message,
    Turn,
    Session,
    Dialogue
)
from .schemas.api_schemas import (
    InputRequest, 
    MessageResponse, 
    DialogueResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
    DialogueFilterParams,
    SessionFilterParams,
    MessageFilterParams,
    ToolRequestSchema,
    ToolResponseSchema,
    NewDialogueRequest
)

# 导入日志模块
from .core.logger import logger

# 导入中间件
from .middleware import setup_middleware

# 创建FastAPI应用
app = FastAPI(
    title="RainbowAI对话管理系统",
    description="彩虹城AI Agent对话管理系统API",
    version="0.1.0"
)

# 设置中间件
setup_middleware(app)

# 创建核心组件
input_hub = InputHub()
dialogue_core = DialogueCore()

# 导入数据库和服务
from .db.database import db
from .db.repositories import message_repo, turn_repo, session_repo, dialogue_repo
from .services.dialogue_service import dialogue_service

# 导入API路由
from .api import sessions, turns, messages, tools, realtime, media, introspection, multi_agent, knowledge_base
from .api.dialogues import router as dialogues_router
from .core.multimodal_handler import multimodal_handler
from .config import get_config


@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": "RainbowAI对话管理系统",
        "version": "0.1.0",
        "status": "running"
    }


@app.post("/api/input", response_model=MessageResponse)
async def process_input(
    input_request: InputRequest,
    background_tasks: BackgroundTasks
):
    """
    处理用户输入
    """
    try:
        # 处理输入
        message = await input_hub.process_input(
            input_type=input_request.type,
            input_data=input_request.data,
            user_id=input_request.user_id,
            dialogue_id=input_request.dialogue_id,
            session_id=input_request.session_id,
            turn_id=input_request.turn_id
        )
        
        # 存储消息
        await message_repo.create(message)
        
        # 在后台处理对话
        background_tasks.add_task(
            process_dialogue,
            message
        )
        
        return MessageResponse(
            message_id=message.id,
            status="processing",
            content=message.content,
            content_type=message.content_type
        )
    
    except Exception as e:
        logger.error(f"Error processing input: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/dialogues/{dialogue_id}", response_model=DialogueResponse)
async def get_dialogue(dialogue_id: str):
    """
    获取对话
    """
    # 从数据库获取对话
    dialogue = await dialogue_repo.get(dialogue_id)
    if not dialogue:
        raise HTTPException(
            status_code=404,
            detail=f"Dialogue not found: {dialogue_id}"
        )
    
    # 获取会话列表
    dialogue_sessions = await session_repo.get_by_dialogue(dialogue_id)
    
    return DialogueResponse(
        dialogue=dialogue,
        sessions=dialogue_sessions
    )


@app.get("/api/dialogues")
async def list_dialogues(
    filter_params: DialogueFilterParams = Depends(),
    pagination: PaginationParams = Depends()
):
    """
    获取对话列表，支持筛选和分页
    """
    try:
        # 计算分页参数
        skip = (pagination.page - 1) * pagination.page_size
        limit = pagination.page_size
        
        # 构建查询条件
        conditions = []
        params = {}
        
        if filter_params.human_id:
            conditions.append("human_id = $human_id")
            params["human_id"] = filter_params.human_id
        
        if filter_params.ai_id:
            conditions.append("ai_id = $ai_id")
            params["ai_id"] = filter_params.ai_id
        
        if filter_params.dialogue_type:
            conditions.append("dialogue_type = $dialogue_type")
            params["dialogue_type"] = filter_params.dialogue_type
        
        if filter_params.status:
            conditions.append("status = $status")
            params["status"] = filter_params.status
        else:
            # 默认只显示活跃对话
            conditions.append("status = 'active'")
        
        if filter_params.start_date:
            conditions.append("created_at >= $start_date")
            params["start_date"] = filter_params.start_date.isoformat()
        
        if filter_params.end_date:
            conditions.append("created_at <= $end_date")
            params["end_date"] = filter_params.end_date.isoformat()
        
        if filter_params.search_text:
            # 全文搜索，在实际应用中可能需要更复杂的全文搜索实现
            search_term = f"%{filter_params.search_text}%"
            conditions.append("(metadata CONTAINS $search_text)")
            params["search_text"] = search_term
        
        # 构建查询
        where_clause = " AND ".join(conditions) if conditions else ""
        count_query = f"SELECT count() FROM dialogue" + (f" WHERE {where_clause}" if where_clause else "")
        data_query = f"SELECT * FROM dialogue" + (f" WHERE {where_clause}" if where_clause else "") + f" ORDER BY last_activity_at DESC LIMIT {limit} START {skip}"
        
        # 执行查询
        count_result = await db.query(count_query, params)
        total = count_result[0]["count"] if count_result else 0
        
        results = await db.query(data_query, params)
        dialogues = [Dialogue(**result) for result in results]
        
        # 构建分页响应
        return PaginatedResponse[
            Dialogue
        ](
            items=dialogues,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size
        )
    
    except Exception as e:
        logger.error(f"Error listing dialogues: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing dialogues: {str(e)}"
        )


@app.post("/api/dialogues")
async def create_dialogue(
    dialogue_type: str,
    human_id: Optional[str] = None,
    ai_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    创建新对话
    """
    try:
        dialogue = await dialogue_service.create_dialogue(
            dialogue_type=dialogue_type,
            human_id=human_id,
            ai_id=ai_id,
            metadata=metadata
        )
        
        if not dialogue:
            raise HTTPException(
                status_code=500,
                detail="Failed to create dialogue"
            )
        
        return {"dialogue_id": dialogue.id}
    
    except Exception as e:
        logger.error(f"Error creating dialogue: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating dialogue: {str(e)}"
        )


@app.get("/api/messages/{message_id}", response_model=MessageResponse)
async def get_message(message_id: str):
    """
    获取消息
    """
    # 从数据库获取消息
    message = await message_repo.get(message_id)
    if not message:
        raise HTTPException(
            status_code=404,
            detail=f"Message not found: {message_id}"
        )
    
    return MessageResponse(
        message_id=message.id,
        status="completed",
        content=message.content,
        content_type=message.content_type,
        metadata=message.metadata
    )


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    filter_params: MessageFilterParams = Depends(),
    pagination: PaginationParams = Depends()
):
    """
    获取会话消息，支持筛选和分页
    """
    try:
        # 获取会话
        session = await session_repo.get(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        # 计算分页参数
        skip = (pagination.page - 1) * pagination.page_size
        limit = pagination.page_size
        
        # 构建查询条件
        conditions = ["session_id = $session_id"]
        params = {"session_id": session_id}
        
        if filter_params.role:
            conditions.append("role = $role")
            params["role"] = filter_params.role
        
        if filter_params.content_type:
            conditions.append("content_type = $content_type")
            params["content_type"] = filter_params.content_type
        
        if filter_params.start_date:
            conditions.append("created_at >= $start_date")
            params["start_date"] = filter_params.start_date.isoformat()
        
        if filter_params.end_date:
            conditions.append("created_at <= $end_date")
            params["end_date"] = filter_params.end_date.isoformat()
        
        if filter_params.search_text:
            # 全文搜索
            search_term = f"%{filter_params.search_text}%"
            conditions.append("(content CONTAINS $search_text)")
            params["search_text"] = search_term
        
        # 构建查询
        where_clause = " AND ".join(conditions)
        count_query = f"SELECT count() FROM message WHERE {where_clause}"
        data_query = f"SELECT * FROM message WHERE {where_clause} ORDER BY created_at ASC LIMIT {limit} START {skip}"
        
        # 执行查询
        count_result = await db.query(count_query, params)
        total = count_result[0]["count"] if count_result else 0
        
        results = await db.query(data_query, params)
        messages = [Message(**result) for result in results]
        
        # 转换为响应格式
        message_responses = [
            MessageResponse(
                message_id=message.id,
                status="completed",
                content=message.content,
                content_type=message.content_type,
                metadata=message.metadata
            )
            for message in messages
        ]
        
        # 构建分页响应
        return PaginatedResponse[
            MessageResponse
        ](
            items=message_responses,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size
        )
    
    except Exception as e:
        logger.error(f"Error getting session messages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting session messages: {str(e)}"
        )


@app.get("/api/dialogues/{dialogue_id}/messages")
async def get_dialogue_messages(
    dialogue_id: str,
    filter_params: MessageFilterParams = Depends(),
    pagination: PaginationParams = Depends()
):
    """
    获取对话消息，支持筛选和分页
    """
    try:
        # 获取对话
        dialogue = await dialogue_repo.get(dialogue_id)
        if not dialogue:
            raise HTTPException(
                status_code=404,
                detail=f"Dialogue not found: {dialogue_id}"
            )
        
        # 计算分页参数
        skip = (pagination.page - 1) * pagination.page_size
        limit = pagination.page_size
        
        # 构建查询条件
        conditions = ["dialogue_id = $dialogue_id"]
        params = {"dialogue_id": dialogue_id}
        
        if filter_params.session_id:
            conditions.append("session_id = $session_id")
            params["session_id"] = filter_params.session_id
        
        if filter_params.turn_id:
            conditions.append("turn_id = $turn_id")
            params["turn_id"] = filter_params.turn_id
        
        if filter_params.role:
            conditions.append("role = $role")
            params["role"] = filter_params.role
        
        if filter_params.content_type:
            conditions.append("content_type = $content_type")
            params["content_type"] = filter_params.content_type
        
        if filter_params.start_date:
            conditions.append("created_at >= $start_date")
            params["start_date"] = filter_params.start_date.isoformat()
        
        if filter_params.end_date:
            conditions.append("created_at <= $end_date")
            params["end_date"] = filter_params.end_date.isoformat()
        
        if filter_params.search_text:
            # 全文搜索
            search_term = f"%{filter_params.search_text}%"
            conditions.append("(content CONTAINS $search_text)")
            params["search_text"] = search_term
        
        # 构建查询
        where_clause = " AND ".join(conditions)
        count_query = f"SELECT count() FROM message WHERE {where_clause}"
        data_query = f"SELECT * FROM message WHERE {where_clause} ORDER BY created_at ASC LIMIT {limit} START {skip}"
        
        # 执行查询
        count_result = await db.query(count_query, params)
        total = count_result[0]["count"] if count_result else 0
        
        results = await db.query(data_query, params)
        messages = [Message(**result) for result in results]
        
        # 转换为响应格式
        message_responses = [
            MessageResponse(
                message_id=message.id,
                status="completed",
                content=message.content,
                content_type=message.content_type,
                metadata=message.metadata
            )
            for message in messages
        ]
        
        # 构建分页响应
        return PaginatedResponse[
            MessageResponse
        ](
            items=message_responses,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size
        )
    
    except Exception as e:
        logger.error(f"Error getting dialogue messages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting dialogue messages: {str(e)}"
        )


@app.post("/api/dialogues/{dialogue_id}/close")
async def close_dialogue(dialogue_id: str):
    """
    关闭对话
    """
    try:
        # 关闭对话
        success = await dialogue_service.close_dialogue(dialogue_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Dialogue not found or already closed: {dialogue_id}"
            )
        
        return {"status": "success", "message": f"Dialogue {dialogue_id} closed"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing dialogue: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error closing dialogue: {str(e)}"
        )


@app.post("/api/tools")
async def invoke_tool(request: ToolRequestSchema):
    """
    调用工具
    """
    try:
        # 创建工具调用器
        tool_invoker = ToolInvoker()
        
        # 调用工具
        result = await tool_invoker.invoke_tool(
            tool_id=request.tool_id,
            parameters=request.parameters
        )
        
        # 转换为响应格式
        response = ToolResponseSchema.from_tool_result(result)
        
        return response
    
    except Exception as e:
        logger.error(f"Error invoking tool: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error invoking tool: {str(e)}"
        )


@app.get("/api/tools")
async def list_tools():
    """
    获取可用工具列表
    """
    try:
        # 创建工具调用器
        tool_invoker = ToolInvoker()
        
        # 获取工具列表
        tools = tool_invoker.get_available_tools()
        
        return {"tools": tools}
    
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing tools: {str(e)}"
        )


@app.get("/api/tools/categories")
async def get_tool_categories():
    """
    获取工具类别
    """
    try:
        # 创建工具调用器
        tool_invoker = ToolInvoker()
        
        # 获取工具类别
        categories = tool_invoker.get_tool_categories()
        
        return {"categories": categories}
    
    except Exception as e:
        logger.error(f"Error getting tool categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tool categories: {str(e)}"
        )


@app.post("/api/dialogues/new", response_model=DialogueResponse)
async def new_dialogue(request: NewDialogueRequest):
    """
    新建对话
    """
    try:
        # 创建对话
        dialogue = await dialogue_service.create_dialogue(
            dialogue_type=request.dialogue_type,
            human_id=request.human_id,
            ai_id=request.ai_id,
            title=request.title,
            description=request.description,
            metadata=request.metadata
        )
        
        if not dialogue:
            raise HTTPException(
                status_code=500,
                detail="Failed to create dialogue"
            )
        
        # 创建默认会话
        session = await dialogue_service.create_session(
            dialogue_id=dialogue.id,
            session_type="dialogue",
            created_by="system",
            description="初始对话会话"
        )
        
        if not session:
            # 如果会话创建失败，也返回对话信息
            logger.warning(f"Failed to create initial session for dialogue {dialogue.id}")
            return DialogueResponse(dialogue=dialogue, sessions=[])
        
        # 返回对话和会话信息
        return DialogueResponse(
            dialogue=dialogue,
            sessions=[session]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating new dialogue: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating new dialogue: {str(e)}"
        )


async def process_dialogue(message: Message):
    """
    处理对话（后台任务）
    """
    try:
        logger.info(f"Processing dialogue for message: {message.id}")
        
        # 使用对话服务处理消息
        result = await dialogue_service.process_message(message)
        
        logger.info(f"Dialogue processing completed for message: {message.id}")
    
    except Exception as e:
        logger.error(f"Error processing dialogue: {str(e)}")


# 注册API路由
app.include_router(dialogues_router, prefix="/api/dialogues", tags=["dialogues"])
app.include_router(sessions.router)
app.include_router(turns.router)
app.include_router(messages.router)
app.include_router(tools.router)
app.include_router(realtime.router)
app.include_router(media.router)
app.include_router(introspection.router)
app.include_router(multi_agent.router)
app.include_router(knowledge_base.router)

@app.on_event("startup")
async def startup_event():
    """应用程序启动事件"""
    # 连接数据库
    await db.connect()
    logger.info("Database connected")
    
    # 创建媒体目录
    config = get_config()
    media_dir = config.get("MEDIA_STORAGE_PATH", "media")
    os.makedirs(media_dir, exist_ok=True)
    os.makedirs(os.path.join(media_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(media_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(media_dir, "video"), exist_ok=True)
    
    # 挂载媒体目录作为静态文件
    app.mount("/media", StaticFiles(directory=media_dir), name="media")
    logger.info(f"Media directory mounted: {media_dir}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用程序关闭事件"""
    # 断开数据库连接
    await db.disconnect()
    logger.info("Database disconnected")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
