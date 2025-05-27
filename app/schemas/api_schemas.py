"""
API请求和响应的模式定义
"""
from typing import Dict, Any, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel
from datetime import datetime

from ..models.data_models import Message, Turn, Session, Dialogue
from ..tools.base_tool import ToolResult


class InputRequest(BaseModel):
    """输入请求"""
    type: str = Field(..., description="输入类型，如text、image、audio等")
    data: Any = Field(..., description="输入数据")
    user_id: str = Field(..., description="用户ID")
    dialogue_id: Optional[str] = Field(None, description="对话ID，如果为空则创建新对话")
    session_id: Optional[str] = Field(None, description="会话ID，如果为空则创建新会话")
    turn_id: Optional[str] = Field(None, description="轮次ID，如果为空则创建新轮次")

    class Config:
        schema_extra = {
            "example": {
                "type": "text",
                "data": "明天北京的天气如何？",
                "user_id": "user-001",
                "dialogue_id": None,
                "session_id": None,
                "turn_id": None
            }
        }


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str = Field(..., description="消息ID")
    status: str = Field(..., description="状态，如processing、completed、error等")
    content: str = Field(..., description="消息内容")
    content_type: str = Field(..., description="内容类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

    class Config:
        schema_extra = {
            "example": {
                "message_id": "msg-uuid-123",
                "status": "completed",
                "content": "明天北京天气晴朗，气温20-28度。",
                "content_type": "text",
                "metadata": {
                    "emotion": "neutral",
                    "tool_used": "weather"
                }
            }
        }


class DialogueResponse(BaseModel):
    """对话响应"""
    dialogue: Dialogue
    sessions: List[Session] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "dialogue": {
                    "id": "dlg-uuid-001",
                    "dialogue_type": "human_ai",
                    "human_id": "user-001",
                    "ai_id": "ai-cleora",
                    "created_at": "2025-05-13T10:00:00Z",
                    "is_active": True,
                    "last_activity_at": "2025-05-13T15:00:00Z",
                    "sessions": ["sess-uuid-001", "sess-uuid-002"]
                },
                "sessions": [
                    {
                        "id": "sess-uuid-001",
                        "dialogue_id": "dlg-uuid-001",
                        "session_type": "dialogue",
                        "start_at": "2025-05-13T10:00:00Z",
                        "end_at": "2025-05-13T11:00:00Z",
                        "description": "天气查询对话",
                        "created_by": "human",
                        "turns": ["turn-uuid-001", "turn-uuid-002"]
                    }
                ]
            }
        }


# 通用分页和筛选模型
T = TypeVar('T')

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, description="页码，从1开始")
    page_size: int = Field(20, description="每页数量")
    
    @validator('page')
    def page_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('页码必须大于等于1')
        return v
    
    @validator('page_size')
    def page_size_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('每页数量必须大于等于1')
        if v > 100:
            raise ValueError('每页数量不能超过100')
        return v


class PaginatedResponse(GenericModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    
    @validator('total_pages', pre=True, always=True)
    def compute_total_pages(cls, v, values):
        if 'total' in values and 'page_size' in values and values['page_size'] > 0:
            return (values['total'] + values['page_size'] - 1) // values['page_size']
        return v or 0


class DialogueFilterParams(BaseModel):
    """对话筛选参数"""
    human_id: Optional[str] = Field(None, description="人类用户ID")
    ai_id: Optional[str] = Field(None, description="AI ID")
    dialogue_type: Optional[str] = Field(None, description="对话类型")
    status: Optional[str] = Field(None, description="状态，如active、closed等")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    search_text: Optional[str] = Field(None, description="搜索文本")


class SessionFilterParams(BaseModel):
    """会话筛选参数"""
    dialogue_id: Optional[str] = Field(None, description="对话 ID")
    session_type: Optional[str] = Field(None, description="会话类型")
    status: Optional[str] = Field(None, description="状态")
    created_by: Optional[str] = Field(None, description="创建者")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class MessageFilterParams(BaseModel):
    """消息筛选参数"""
    dialogue_id: Optional[str] = Field(None, description="对话 ID")
    session_id: Optional[str] = Field(None, description="会话 ID")
    turn_id: Optional[str] = Field(None, description="轮次 ID")
    role: Optional[str] = Field(None, description="角色，如user、assistant等")
    content_type: Optional[str] = Field(None, description="内容类型")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    search_text: Optional[str] = Field(None, description="搜索文本")


class ToolRequestSchema(BaseModel):
    """工具请求模式"""
    tool_id: str = Field(..., description="工具ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    
    class Config:
        schema_extra = {
            "example": {
                "tool_id": "builtin.weather",
                "parameters": {
                    "city": "北京",
                    "units": "metric"
                }
            }
        }


class ToolResponseSchema(BaseModel):
    """工具响应模式"""
    tool_id: str = Field(..., description="工具ID")
    success: bool = Field(..., description="是否成功")
    content: Optional[Any] = Field(None, description="结果内容")
    content_type: str = Field(..., description="内容类型")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @classmethod
    def from_tool_result(cls, tool_result: ToolResult) -> 'ToolResponseSchema':
        return cls(
            tool_id=tool_result.tool_id if hasattr(tool_result, 'tool_id') else "",
            success=tool_result.success,
            content=tool_result.content,
            content_type=tool_result.content_type,
            error=tool_result.error,
            metadata=tool_result.metadata
        )


class NewDialogueRequest(BaseModel):
    """新建对话请求"""
    dialogue_type: str = Field("human_ai", description="对话类型，默认为human_ai")
    human_id: Optional[str] = Field(None, description="人类用户ID")
    ai_id: Optional[str] = Field(None, description="AI ID")
    title: Optional[str] = Field(None, description="对话标题")
    description: Optional[str] = Field(None, description="对话描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

    class Config:
        schema_extra = {
            "example": {
                "dialogue_type": "human_ai",
                "human_id": "user-001",
                "ai_id": "ai-cleora",
                "title": "天气查询对话",
                "description": "关于明天北京天气的对话",
                "metadata": {
                    "tags": ["天气", "北京"],
                    "priority": "normal"
                }
            }
        }


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str = Field(..., description="错误详情")

    class Config:
        schema_extra = {
            "example": {
                "detail": "Resource not found"
            }
        }
