"""
多模态输入解析模块（MultiModalInputParser）
解析来自人类、AI或系统的多模态输入，将其转化为统一语义表示与结构化上下文片段
"""
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime
import json
import uuid

from ..models.data_models import Message


class SemanticBlock:
    """
    标准化语义块，用于上下文构建与推理
    """
    def __init__(
        self,
        text_block: str,
        semantic_tags: List[str] = None,
        emotions: List[str] = None,
        source_message_id: str = None,
        origin: str = None,
        timestamp: datetime = None
    ):
        self.text_block = text_block
        self.semantic_tags = semantic_tags or []
        self.emotions = emotions or []
        self.source_message_id = source_message_id
        self.origin = origin
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "text_block": self.text_block,
            "semantic_tags": self.semantic_tags,
            "emotions": self.emotions,
            "source_message_id": self.source_message_id,
            "origin": self.origin,
            "timestamp": self.timestamp.isoformat()
        }

    def __str__(self) -> str:
        return self.text_block


class ContentParser(ABC):
    """
    内容解析器基类
    """
    @abstractmethod
    def parse(self, message: Message) -> SemanticBlock:
        """解析消息内容，返回语义块"""
        pass


class TextParser(ContentParser):
    """
    文本解析器
    解析文本内容，提取情感、意图等
    """
    def parse(self, message: Message) -> SemanticBlock:
        if message.content_type != "text":
            raise ValueError(f"TextParser only supports 'text' content type, got {message.content_type}")
        
        # 简单实现，实际应用中可以接入NLP分析模块
        text = message.content
        
        # 提取情感（简化版）
        emotions = ["neutral"]
        if "开心" in text or "高兴" in text or "喜欢" in text:
            emotions = ["happy"]
        elif "伤心" in text or "难过" in text or "失望" in text:
            emotions = ["sad"]
        
        # 提取主题标签（简化版）
        semantic_tags = []
        if "天气" in text:
            semantic_tags.append("weather")
        if "旅行" in text or "旅游" in text:
            semantic_tags.append("travel")
        
        return SemanticBlock(
            text_block=text,
            semantic_tags=semantic_tags,
            emotions=emotions,
            source_message_id=message.id,
            origin=message.sender_role
        )


class ImageParser(ContentParser):
    """
    图像解析器
    解析图像内容，生成描述、提取主题等
    """
    def parse(self, message: Message) -> SemanticBlock:
        if message.content_type != "image":
            raise ValueError(f"ImageParser only supports 'image' content type, got {message.content_type}")
        
        # 简化实现，实际应用中应接入图像识别模型
        image_url = message.content
        caption = message.metadata.get("caption", "一张图片")
        
        # 构建语义块
        return SemanticBlock(
            text_block=f"[图片描述: {caption}]",
            semantic_tags=message.metadata.get("tags", []),
            emotions=message.metadata.get("visual_emotions", ["neutral"]),
            source_message_id=message.id,
            origin=message.sender_role
        )


class ToolOutputParser(ContentParser):
    """
    工具输出解析器
    将工具调用结果转化为自然语言
    """
    def parse(self, message: Message) -> SemanticBlock:
        if message.content_type != "tool_output":
            raise ValueError(f"ToolOutputParser only supports 'tool_output' content type, got {message.content_type}")
        
        # 解析工具输出（假设为JSON字符串）
        try:
            tool_output = json.loads(message.content)
            tool_name = tool_output.get("tool", "未知工具")
            result = tool_output.get("result", {})
            
            # 根据工具类型生成不同的自然语言描述
            if tool_name == "weather":
                city = result.get("city", "未知城市")
                temp = result.get("temp", "未知温度")
                condition = result.get("condition", "未知天气状况")
                text_block = f"根据天气查询，{city}的温度是{temp}度，天气状况为{condition}。"
            else:
                # 通用工具输出处理
                text_block = f"工具 {tool_name} 返回结果: {str(result)}"
            
            return SemanticBlock(
                text_block=text_block,
                semantic_tags=[tool_name],
                emotions=["neutral"],
                source_message_id=message.id,
                origin="system"
            )
        except json.JSONDecodeError:
            # 非JSON格式，直接使用原始内容
            return SemanticBlock(
                text_block=f"工具返回结果: {message.content}",
                semantic_tags=["tool_output"],
                emotions=["neutral"],
                source_message_id=message.id,
                origin="system"
            )


class MultiModalInputParser:
    """
    多模态输入解析器
    整合各类解析器，处理不同类型的输入
    """
    def __init__(self):
        self.parsers = {
            "text": TextParser(),
            "image": ImageParser(),
            "tool_output": ToolOutputParser(),
            # 可扩展更多类型的解析器
        }
    
    def parse(self, message: Message) -> SemanticBlock:
        """
        解析消息，返回标准化语义块
        """
        content_type = message.content_type
        
        if content_type in self.parsers:
            return self.parsers[content_type].parse(message)
        else:
            # 默认处理：将未知类型转为文本描述
            return SemanticBlock(
                text_block=f"[{content_type}类型内容]: {message.content[:100]}...",
                semantic_tags=[content_type],
                emotions=["neutral"],
                source_message_id=message.id,
                origin=message.sender_role
            )
    
    def register_parser(self, content_type: str, parser: ContentParser):
        """
        注册新的内容解析器
        """
        self.parsers[content_type] = parser
