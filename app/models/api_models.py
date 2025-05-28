"""
API数据模型
定义API请求和响应的数据模型
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator


# 通用API响应模型
class APIResponse(BaseModel):
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")


# 对话相关模型
class DialogueCreate(BaseModel):
    dialogue_type: str = Field(..., description="对话类型")
    human_id: Optional[str] = Field(None, description="人类用户ID")
    ai_id: Optional[str] = Field(None, description="AI ID")
    relation_id: Optional[str] = Field(None, description="关系ID")
    title: str = Field(..., description="对话标题")
    description: Optional[str] = Field(None, description="对话描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class DialogueResponse(BaseModel):
    id: str = Field(..., description="对话ID")
    dialogue_type: str = Field(..., description="对话类型")
    human_id: Optional[str] = Field(None, description="人类用户ID")
    ai_id: Optional[str] = Field(None, description="AI ID")
    relation_id: Optional[str] = Field(None, description="关系ID")
    title: str = Field(..., description="对话标题")
    description: Optional[str] = Field(None, description="对话描述")
    created_at: datetime = Field(..., description="创建时间")
    is_active: bool = Field(..., description="是否活跃")
    last_activity_at: Optional[datetime] = Field(None, description="最后活动时间")
    sessions: List[str] = Field([], description="会话ID列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class DialogueListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    offset: int = Field(..., description="偏移量")
    limit: int = Field(..., description="限制数量")
    items: List[DialogueResponse] = Field(..., description="对话列表")


# 会话相关模型
class SessionCreate(BaseModel):
    dialogue_id: str = Field(..., description="对话ID")
    session_type: str = Field(..., description="会话类型")
    description: Optional[str] = Field(None, description="会话描述")
    created_by: Optional[str] = Field(None, description="创建者ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class SessionResponse(BaseModel):
    id: str = Field(..., description="会话ID")
    dialogue_id: str = Field(..., description="对话ID")
    session_type: str = Field(..., description="会话类型")
    start_at: datetime = Field(..., description="开始时间")
    end_at: Optional[datetime] = Field(None, description="结束时间")
    description: Optional[str] = Field(None, description="会话描述")
    created_by: Optional[str] = Field(None, description="创建者ID")
    turns: List[str] = Field([], description="轮次ID列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class SessionListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    offset: int = Field(..., description="偏移量")
    limit: int = Field(..., description="限制数量")
    items: List[SessionResponse] = Field(..., description="会话列表")


# 轮次相关模型
class TurnCreate(BaseModel):
    dialogue_id: str = Field(..., description="对话ID")
    session_id: str = Field(..., description="会话ID")
    initiator_role: str = Field(..., description="发起者角色")
    responder_role: str = Field(..., description="响应者角色")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class TurnResponse(BaseModel):
    id: str = Field(..., description="轮次ID")
    dialogue_id: str = Field(..., description="对话ID")
    session_id: str = Field(..., description="会话ID")
    initiator_role: str = Field(..., description="发起者角色")
    responder_role: str = Field(..., description="响应者角色")
    started_at: datetime = Field(..., description="开始时间")
    closed_at: Optional[datetime] = Field(None, description="结束时间")
    status: str = Field(..., description="状态")
    response_time: Optional[float] = Field(None, description="响应时间")
    messages: List[str] = Field([], description="消息ID列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class TurnListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    offset: int = Field(..., description="偏移量")
    limit: int = Field(..., description="限制数量")
    items: List[TurnResponse] = Field(..., description="轮次列表")


# 消息相关模型
class MessageCreate(BaseModel):
    dialogue_id: str = Field(..., description="对话ID")
    session_id: str = Field(..., description="会话ID")
    turn_id: str = Field(..., description="轮次ID")
    sender_role: str = Field(..., description="发送者角色")
    sender_id: Optional[str] = Field(None, description="发送者ID")
    content: str = Field(..., description="消息内容")
    content_type: str = Field("text", description="内容类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class MessageResponse(BaseModel):
    id: str = Field(..., description="消息ID")
    dialogue_id: str = Field(..., description="对话ID")
    session_id: str = Field(..., description="会话ID")
    turn_id: str = Field(..., description="轮次ID")
    sender_role: str = Field(..., description="发送者角色")
    sender_id: Optional[str] = Field(None, description="发送者ID")
    content: str = Field(..., description="消息内容")
    content_type: str = Field(..., description="内容类型")
    created_at: datetime = Field(..., description="创建时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class MessageListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    offset: int = Field(..., description="偏移量")
    limit: int = Field(..., description="限制数量")
    items: List[MessageResponse] = Field(..., description="消息列表")


# 工具调用相关模型
class ToolCallCreate(BaseModel):
    tool_id: str = Field(..., description="工具ID")
    dialogue_id: str = Field(..., description="对话ID")
    turn_id: str = Field(..., description="轮次ID")
    parameters: Dict[str, Any] = Field(..., description="参数")


class ToolCallResponse(BaseModel):
    id: str = Field(..., description="工具调用ID")
    tool_id: str = Field(..., description="工具ID")
    dialogue_id: str = Field(..., description="对话ID")
    turn_id: str = Field(..., description="轮次ID")
    parameters: Dict[str, Any] = Field(..., description="参数")
    result: Optional[Dict[str, Any]] = Field(None, description="结果")
    success: bool = Field(..., description="是否成功")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间")
    created_at: datetime = Field(..., description="创建时间")


class ToolCallListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    offset: int = Field(..., description="偏移量")
    limit: int = Field(..., description="限制数量")
    items: List[ToolCallResponse] = Field(..., description="工具调用列表")


# 媒体上传相关模型
class MediaUploadResponse(BaseModel):
    media_id: str = Field(..., description="媒体ID")
    file_name: str = Field(..., description="文件名")
    content_type: str = Field(..., description="内容类型")
    size: int = Field(..., description="文件大小")
    url: str = Field(..., description="访问URL")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


# WebSocket连接相关模型
class WebSocketMessage(BaseModel):
    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(..., description="消息数据")


# 自我反思相关模型
class IntrospectionSessionCreate(BaseModel):
    ai_id: str = Field(..., description="AI ID")
    session_type: str = Field(..., description="会话类型", example="performance_review")
    trigger_source: str = Field(..., description="触发来源", example="user_feedback")
    goal: str = Field(..., description="反思目标")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class IntrospectionSessionResponse(BaseModel):
    id: str = Field(..., description="会话ID")
    ai_id: str = Field(..., description="AI ID")
    session_type: str = Field(..., description="会话类型")
    trigger_source: str = Field(..., description="触发来源")
    goal: str = Field(..., description="反思目标")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    steps: List[Dict[str, Any]] = Field([], description="步骤")
    summary: Optional[str] = Field(None, description="总结")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class IntrospectionSessionListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    offset: int = Field(..., description="偏移量")
    limit: int = Field(..., description="限制数量")
    items: List[IntrospectionSessionResponse] = Field(..., description="自我反思会话列表")


# 多智能体协作相关模型
class AgentResponse(BaseModel):
    agent_id: str = Field(..., description="智能体ID")
    name: str = Field(..., description="名称")
    role: str = Field(..., description="角色")
    description: str = Field(..., description="描述")
    capabilities: List[str] = Field(..., description="能力")


class AgentListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    items: List[AgentResponse] = Field(..., description="智能体列表")


class CollaborationSessionCreate(BaseModel):
    task: str = Field(..., description="任务描述")
    agent_ids: List[str] = Field(..., description="参与协作的智能体ID列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class CollaborationSessionResponse(BaseModel):
    id: str = Field(..., description="会话ID")
    task: str = Field(..., description="任务描述")
    agent_ids: List[str] = Field(..., description="参与协作的智能体ID列表")
    initiator_id: Optional[str] = Field(None, description="发起者ID")
    created_at: datetime = Field(..., description="创建时间")
    status: str = Field(..., description="状态")
    dialogue_id: Optional[str] = Field(None, description="对话ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class CollaborationSessionListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    offset: int = Field(..., description="偏移量")
    limit: int = Field(..., description="限制数量")
    items: List[CollaborationSessionResponse] = Field(..., description="协作会话列表")


class CollaborationMessageCreate(BaseModel):
    content: str = Field(..., description="消息内容")
    target_agent_ids: Optional[List[str]] = Field(None, description="目标智能体ID列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class CollaborationMessageResponse(BaseModel):
    id: str = Field(..., description="消息ID")
    session_id: str = Field(..., description="会话ID")
    sender_id: str = Field(..., description="发送者ID")
    content: str = Field(..., description="消息内容")
    created_at: str = Field(..., description="创建时间")
    success: bool = Field(..., description="是否成功")


class CollaborationMessageListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    offset: int = Field(..., description="偏移量")
    limit: int = Field(..., description="限制数量")
    items: List[Dict[str, Any]] = Field(..., description="消息列表")


# 知识库集成相关模型
class KnowledgeBaseConnectorCreate(BaseModel):
    name: str = Field(..., description="连接器名称")
    type: str = Field(..., description="连接器类型", example="vector_db")
    api_url: str = Field(..., description="API URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    collection_name: Optional[str] = Field(None, description="集合名称")
    index_name: Optional[str] = Field(None, description="索引名称")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    embedding_model: Optional[str] = Field(None, description="嵌入模型")
    search_endpoint: Optional[str] = Field(None, description="搜索端点")
    document_endpoint: Optional[str] = Field(None, description="文档端点")
    headers: Optional[Dict[str, str]] = Field(None, description="请求头")


class KnowledgeBaseConnectorResponse(BaseModel):
    id: str = Field(..., description="连接器ID")
    name: str = Field(..., description="连接器名称")
    type: str = Field(..., description="连接器类型")
    config: Dict[str, Any] = Field(..., description="配置信息")


class KnowledgeBaseConnectorListResponse(BaseModel):
    total: int = Field(..., description="总数量")
    items: List[KnowledgeBaseConnectorResponse] = Field(..., description="连接器列表")


class KnowledgeBaseSearchResponse(BaseModel):
    query: str = Field(..., description="查询字符串")
    total_results: int = Field(..., description="总结果数")
    connector_count: int = Field(..., description="连接器数量")
    results: Dict[str, List[Dict[str, Any]]] = Field(..., description="搜索结果")


class KnowledgeBaseDocumentResponse(BaseModel):
    connector_id: str = Field(..., description="连接器ID")
    document_id: str = Field(..., description="文档ID")
    document: Dict[str, Any] = Field(..., description="文档内容")
