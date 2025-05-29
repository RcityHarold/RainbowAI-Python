"""
对话API模块
提供对话相关的API端点
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from ..services.dialogue_service import dialogue_service
from ..models.data_models import Dialogue, Session, Message
from ..core.constants import DialogueTypes, SessionTypes, RoleTypes


router = APIRouter()


# 响应模型
class DialogueResponse(BaseModel):
    dialogue: Dialogue
    sessions: List[Session] = []


# 请求模型 - 基础对话请求
class BaseDialogueRequest(BaseModel):
    title: Optional[str] = Field(None, description="对话标题")
    description: Optional[str] = Field(None, description="对话描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


# 人类-AI对话请求
class HumanAIDialogueRequest(BaseDialogueRequest):
    human_id: str = Field(..., description="人类ID")
    ai_id: str = Field(..., description="AI ID")


# AI自我对话请求
class AISelfDialogueRequest(BaseDialogueRequest):
    ai_id: str = Field(..., description="AI ID")


# AI-AI对话请求
class AIAIDialogueRequest(BaseDialogueRequest):
    ai_id: str = Field(..., description="主AI ID")
    participant_ai_ids: List[str] = Field(..., description="参与的AI ID列表")


# 人类-人类私聊请求
class HumanHumanPrivateRequest(BaseDialogueRequest):
    human_id: str = Field(..., description="第一个人类ID")
    second_human_id: str = Field(..., description="第二个人类ID")


# 人类-人类群聊请求
class HumanHumanGroupRequest(BaseDialogueRequest):
    group_members: List[str] = Field(..., description="群组成员ID列表")


# 人类-AI群组请求
class HumanAIGroupRequest(BaseDialogueRequest):
    human_members: List[str] = Field(..., description="人类成员ID列表")
    ai_members: List[str] = Field(..., description="AI成员ID列表")


# AI-多人类群组请求
class AIMultiHumanRequest(BaseDialogueRequest):
    ai_id: str = Field(..., description="AI ID")
    human_participants: List[str] = Field(..., description="人类参与者ID列表")


# 创建人类-AI私聊对话
@router.post("/human_ai", response_model=DialogueResponse)
async def create_human_ai_dialogue(request: HumanAIDialogueRequest):
    """创建人类 ⇄ AI 私聊对话"""
    dialogue = await dialogue_service.create_dialogue_with_type(
        dialogue_type=DialogueTypes.HUMAN_AI,
        human_id=request.human_id,
        ai_id=request.ai_id,
        title=request.title,
        description=request.description,
        metadata=request.metadata
    )
    
    if not dialogue:
        raise HTTPException(
            status_code=400,
            detail="Failed to create human-AI dialogue"
        )
    
    # 创建默认会话
    session = await dialogue_service.create_session(
        dialogue_id=dialogue.id,
        session_type=SessionTypes.DIALOGUE,
        created_by="system",
        description="初始对话会话"
    )
    
    return DialogueResponse(
        dialogue=dialogue,
        sessions=[session] if session else []
    )


# 创建AI自我对话
@router.post("/ai_self", response_model=DialogueResponse)
async def create_ai_self_dialogue(request: AISelfDialogueRequest):
    """创建 AI ⇄ 自我（自省/觉知）对话"""
    dialogue = await dialogue_service.create_dialogue_with_type(
        dialogue_type=DialogueTypes.AI_SELF,
        ai_id=request.ai_id,
        title=request.title,
        description=request.description,
        metadata=request.metadata
    )
    
    if not dialogue:
        raise HTTPException(
            status_code=400,
            detail="Failed to create AI self-reflection dialogue"
        )
    
    # 创建默认会话
    session = await dialogue_service.create_session(
        dialogue_id=dialogue.id,
        session_type=SessionTypes.INTROSPECTION,
        created_by="system",
        description="AI自我反思会话"
    )
    
    return DialogueResponse(
        dialogue=dialogue,
        sessions=[session] if session else []
    )


# 创建AI-AI对话
@router.post("/ai_ai", response_model=DialogueResponse)
async def create_ai_ai_dialogue(request: AIAIDialogueRequest):
    """创建 AI ⇄ AI 对话"""
    metadata = request.metadata or {}
    metadata["participant_ai_ids"] = request.participant_ai_ids
    
    dialogue = await dialogue_service.create_dialogue_with_type(
        dialogue_type=DialogueTypes.AI_AI,
        ai_id=request.ai_id,
        title=request.title,
        description=request.description,
        metadata=metadata
    )
    
    if not dialogue:
        raise HTTPException(
            status_code=400,
            detail="Failed to create AI-AI dialogue"
        )
    
    # 创建默认会话
    session = await dialogue_service.create_session(
        dialogue_id=dialogue.id,
        session_type=SessionTypes.MULTI_AGENT,
        created_by="system",
        description="AI间协作会话"
    )
    
    return DialogueResponse(
        dialogue=dialogue,
        sessions=[session] if session else []
    )


# 创建人类-人类私聊
@router.post("/human_human_private", response_model=DialogueResponse)
async def create_human_human_private_dialogue(request: HumanHumanPrivateRequest):
    """创建人类 ⇄ 人类私聊对话"""
    metadata = request.metadata or {}
    metadata["second_human_id"] = request.second_human_id
    
    dialogue = await dialogue_service.create_dialogue_with_type(
        dialogue_type=DialogueTypes.HUMAN_HUMAN_PRIVATE,
        human_id=request.human_id,
        title=request.title,
        description=request.description,
        metadata=metadata
    )
    
    if not dialogue:
        raise HTTPException(
            status_code=400,
            detail="Failed to create human-human private dialogue"
        )
    
    # 创建默认会话
    session = await dialogue_service.create_session(
        dialogue_id=dialogue.id,
        session_type=SessionTypes.DIALOGUE,
        created_by="system",
        description="人类私聊会话"
    )
    
    return DialogueResponse(
        dialogue=dialogue,
        sessions=[session] if session else []
    )


# 创建人类-人类群聊
@router.post("/human_human_group", response_model=DialogueResponse)
async def create_human_human_group_dialogue(request: HumanHumanGroupRequest):
    """创建人类 ⇄ 人类群聊对话"""
    if len(request.group_members) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two group members are required"
        )
    
    metadata = request.metadata or {}
    metadata["group_members"] = request.group_members
    
    dialogue = await dialogue_service.create_dialogue_with_type(
        dialogue_type=DialogueTypes.HUMAN_HUMAN_GROUP,
        title=request.title,
        description=request.description,
        metadata=metadata
    )
    
    if not dialogue:
        raise HTTPException(
            status_code=400,
            detail="Failed to create human-human group dialogue"
        )
    
    # 创建默认会话
    session = await dialogue_service.create_session(
        dialogue_id=dialogue.id,
        session_type=SessionTypes.GROUP_CHAT,
        created_by="system",
        description="人类群聊会话"
    )
    
    return DialogueResponse(
        dialogue=dialogue,
        sessions=[session] if session else []
    )


# 创建人类-AI群组对话
@router.post("/human_ai_group", response_model=DialogueResponse)
async def create_human_ai_group_dialogue(request: HumanAIGroupRequest):
    """创建人类 ⇄ AI 群组 (LIO)对话"""
    if len(request.human_members) < 1 or len(request.ai_members) < 1:
        raise HTTPException(
            status_code=400,
            detail="At least one human and one AI member are required"
        )
    
    metadata = request.metadata or {}
    metadata["human_members"] = request.human_members
    metadata["ai_members"] = request.ai_members
    
    dialogue = await dialogue_service.create_dialogue_with_type(
        dialogue_type=DialogueTypes.HUMAN_AI_GROUP,
        title=request.title,
        description=request.description,
        metadata=metadata
    )
    
    if not dialogue:
        raise HTTPException(
            status_code=400,
            detail="Failed to create human-AI group dialogue"
        )
    
    # 创建默认会话
    session = await dialogue_service.create_session(
        dialogue_id=dialogue.id,
        session_type=SessionTypes.LIO,
        created_by="system",
        description="人类-AI群组会话"
    )
    
    return DialogueResponse(
        dialogue=dialogue,
        sessions=[session] if session else []
    )


# 创建AI-多人类群组对话
@router.post("/ai_multi_human", response_model=DialogueResponse)
async def create_ai_multi_human_dialogue(request: AIMultiHumanRequest):
    """创建 AI ⇄ 多人类群组对话"""
    if len(request.human_participants) < 1:
        raise HTTPException(
            status_code=400,
            detail="At least one human participant is required"
        )
    
    metadata = request.metadata or {}
    metadata["human_participants"] = request.human_participants
    
    dialogue = await dialogue_service.create_dialogue_with_type(
        dialogue_type=DialogueTypes.AI_MULTI_HUMAN,
        ai_id=request.ai_id,
        title=request.title,
        description=request.description,
        metadata=metadata
    )
    
    if not dialogue:
        raise HTTPException(
            status_code=400,
            detail="Failed to create AI-multi-human dialogue"
        )
    
    # 创建默认会话
    session = await dialogue_service.create_session(
        dialogue_id=dialogue.id,
        session_type=SessionTypes.GROUP_CHAT,
        created_by="system",
        description="AI-多人类群组会话"
    )
    
    return DialogueResponse(
        dialogue=dialogue,
        sessions=[session] if session else []
    )


# 获取对话详情
@router.get("/{dialogue_id}", response_model=DialogueResponse)
async def get_dialogue(dialogue_id: str):
    """获取对话详情"""
    dialogue = await dialogue_service.dialogue_repo.get(dialogue_id)
    if not dialogue:
        raise HTTPException(
            status_code=404,
            detail=f"Dialogue {dialogue_id} not found"
        )
    
    sessions = await dialogue_service.session_repo.get_by_dialogue(dialogue_id)
    
    return DialogueResponse(
        dialogue=dialogue,
        sessions=sessions
    )


# 获取用户的活跃对话列表
@router.get("/user/{user_id}", response_model=List[Dialogue])
async def get_user_dialogues(user_id: str, role_type: str = RoleTypes.HUMAN):
    """获取用户的活跃对话列表"""
    if role_type == RoleTypes.HUMAN:
        dialogues = await dialogue_service.get_active_dialogues(human_id=user_id)
    else:
        dialogues = await dialogue_service.get_active_dialogues(ai_id=user_id)
    
    return dialogues
