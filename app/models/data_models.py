"""
数据结构定义：Message、Turn、Session、Dialogue
基于彩虹城AI对话管理系统四层数据结构
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid.uuid4())


class Message(BaseModel):
    """
    消息模型 - 最小信息单位
    支持多模态内容（文本、图片、音频、工具输出等）
    """
    id: str = Field(default_factory=generate_uuid)
    dialogue_id: str
    session_id: str
    turn_id: str
    sender_role: str  # 'human' | 'ai' | 'system'
    sender_id: Optional[str] = None
    content: str
    content_type: str  # 'text' | 'image' | 'audio' | 'tool_output' | 'prompt' | ...
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "id": "msg-uuid-123",
                "dialogue_id": "dlg-uuid-000",
                "session_id": "sess-uuid-789",
                "turn_id": "turn-uuid-456",
                "sender_role": "ai",
                "sender_id": "ai-entity-999",
                "content": "明天新加坡38度，不需要带伞。",
                "content_type": "text",
                "created_at": "2025-05-13T14:22:00Z",
                "metadata": {
                    "emotion": "calm",
                    "intent": "inform",
                    "tool_used": None
                }
            }
        }


class Turn(BaseModel):
    """
    轮次模型 - 意图交互单元
    定义了发起者、回应者、响应窗口、状态等
    """
    id: str = Field(default_factory=generate_uuid)
    dialogue_id: str
    session_id: str
    initiator_role: str  # 'human' | 'ai' | 'system'
    responder_role: str  # 'human' | 'ai' | 'system'
    started_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    status: str = "open"  # 'open' | 'responded' | 'unresponded'
    response_time: Optional[float] = None  # seconds
    messages: List[str] = Field(default_factory=list)  # 消息ID列表
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "id": "turn-uuid-003",
                "dialogue_id": "dlg-uuid-001",
                "session_id": "sess-uuid-002",
                "initiator_role": "ai",
                "responder_role": "human",
                "started_at": "2025-05-13T15:00:00Z",
                "closed_at": None,
                "status": "open",
                "response_time": None,
                "messages": ["msg-uuid-001", "msg-uuid-002"],
                "metadata": {
                    "expected_window_minutes": 180
                }
            }
        }


class Session(BaseModel):
    """
    会话模型 - 上下文段落
    自动分段（如对话超时）或AI自省任务
    """
    id: str = Field(default_factory=generate_uuid)
    dialogue_id: str
    session_type: str  # 'dialogue' | 'self_reflection'
    start_at: datetime = Field(default_factory=datetime.utcnow)
    end_at: Optional[datetime] = None
    description: Optional[str] = None
    created_by: str  # 'system' | 'ai' | 'human'
    turns: List[str] = Field(default_factory=list)  # 轮次ID列表
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "id": "sess-uuid-002",
                "dialogue_id": "dlg-uuid-001",
                "session_type": "dialogue",
                "start_at": "2025-05-13T15:00:00Z",
                "end_at": None,
                "description": "讨论新加坡旅行计划",
                "created_by": "system",
                "turns": ["turn-uuid-001", "turn-uuid-002"],
                "metadata": {
                    "topic_tags": ["travel", "weather"]
                }
            }
        }


class Dialogue(BaseModel):
    """
    对话模型 - 唯一主线容器
    聚合所有Session，支持人类-AI、AI自省、LIO群聊等多种模式
    """
    id: str = Field(default_factory=generate_uuid)
    dialogue_type: str  # 'human_ai' | 'ai_self' | 'lio_group' | 'human_human'
    human_id: Optional[str] = None
    ai_id: Optional[str] = None
    relation_id: Optional[str] = None
    title: Optional[str] = None  # 对话标题
    description: Optional[str] = None  # 对话描述
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    sessions: List[str] = Field(default_factory=list)  # 会话ID列表
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "id": "dlg-uuid-001",
                "dialogue_type": "human_ai",
                "human_id": "user-001",
                "ai_id": "ai-cleora",
                "relation_id": None,
                "title": "新加坡旅行计划",
                "description": "讨论新加坡旅行的天气、景点和行程安排",
                "created_at": "2025-05-13T10:00:00Z",
                "is_active": True,
                "last_activity_at": "2025-05-13T15:00:00Z",
                "sessions": ["sess-uuid-001", "sess-uuid-002"],
                "metadata": {
                    "topic_tags": ["travel", "weather"],
                    "context_mode": "1v1"
                }
            }
        }
