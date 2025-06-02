"""
自省系统数据模型
定义自省会话和自省轮次的数据结构
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class IntrospectionTurnType(str, Enum):
    """自省轮次类型"""
    SELF_ANALYSIS = "self_analysis"
    EMOTION_TRACKING = "emotion_tracking"
    PERFORMANCE_REVIEW = "performance_review"
    ERROR_ANALYSIS = "error_analysis"
    KNOWLEDGE_ASSESSMENT = "knowledge_assessment"
    GOAL_SETTING = "goal_setting"
    IMPROVEMENT_PLANNING = "improvement_planning"


class MoodState(str, Enum):
    """AI情绪状态"""
    NEUTRAL = "neutral"
    CURIOUS = "curious"
    EXCITED = "excited"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    CONCERNED = "concerned"
    APOLOGETIC = "apologetic"
    REFLECTIVE = "reflective"
    DETERMINED = "determined"


class MoodShift(BaseModel):
    """情绪变化"""
    from_mood: MoodState
    to_mood: MoodState
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IntrospectionTurn(BaseModel):
    """自省轮次"""
    id: str
    session_id: str
    turn_type: IntrospectionTurnType
    question: str
    response: str
    insights: List[str] = []
    ai_mood_state: MoodState = MoodState.NEUTRAL
    mood_shift: Optional[MoodShift] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class SelfReflectionSession(BaseModel):
    """自省会话"""
    id: str
    ai_id: str
    session_type: str
    trigger_source: str
    goal: str
    turns: List[IntrospectionTurn] = []
    steps: List[Dict[str, Any]] = []
    summary: str = ""
    report: Dict[str, Any] = {}
    memory_entries: List[Dict[str, Any]] = []
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class IntrospectionReport(BaseModel):
    """自省报告"""
    session_id: str
    ai_id: str
    report_type: str
    summary: str
    key_insights: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]
    action_items: List[Dict[str, Any]]
    mood_analysis: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class MemoryEntry(BaseModel):
    """记忆条目"""
    id: str
    ai_id: str
    source_type: str
    source_id: str
    memory_type: str
    content: str
    importance: int
    tags: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}
