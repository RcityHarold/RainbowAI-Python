"""
多模态输入解析模块

用于解析来自人类、AI或系统的多模态输入，将其转化为统一语义表示与结构化上下文片段，
供后续上下文构建与语义推理使用。
"""
from typing import Dict, Any, Optional, List, Union
import json
import asyncio
from dataclasses import dataclass
from enum import Enum

from ..core.logger import logger
from ..core.multimodal_handler import multimodal_handler
from .parsers import (
    text_parser,
    image_parser,
    audio_parser,
    tool_output_parser,
    quote_reply_resolver,
    system_prompt_parser,
    integration_manager
)

class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    TOOL_OUTPUT = "tool_output"
    PROMPT = "prompt"
    MARKDOWN = "markdown"
    QUOTE_REPLY = "quote_reply"

@dataclass
class Message:
    """消息基本结构"""
    message_id: str
    dialogue_id: str
    turn_id: str
    sender_role: str  # "human" / "ai" / "system"
    content_type: str
    content: Any
    content_meta: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

class MultiModalInputParser:
    """多模态输入解析器"""
    
    def __init__(self):
        self.logger = logger
        self.text_parser = text_parser
        self.image_parser = image_parser
        self.audio_parser = audio_parser
        self.tool_output_parser = tool_output_parser
        self.quote_reply_resolver = quote_reply_resolver
        self.system_prompt_parser = system_prompt_parser
        self.integration_manager = integration_manager
    
    async def parse(self, message: Message) -> Dict[str, Any]:
        """
        解析多模态消息
        
        Args:
            message: 消息对象
        
        Returns:
            统一上下文格式
        """
        try:
            content_type = message.content_type
            
            if content_type == ContentType.TEXT.value:
                return await self.text_parser.parse(message)
            elif content_type == ContentType.IMAGE.value:
                return await self.image_parser.parse(message)
            elif content_type == ContentType.AUDIO.value:
                return await self.audio_parser.parse(message)
            elif content_type == ContentType.TOOL_OUTPUT.value:
                return await self.tool_output_parser.parse(message)
            elif content_type == ContentType.PROMPT.value:
                return await self.system_prompt_parser.parse(message)
            elif content_type == ContentType.MARKDOWN.value:
                return await self.text_parser.parse_markdown(message)
            elif content_type == ContentType.QUOTE_REPLY.value:
                return await self.quote_reply_resolver.parse(message)
            else:
                # 默认作为文本处理
                self.logger.warning(f"未知内容类型: {content_type}，将作为文本处理")
                return await self.text_parser.parse(message)
        
        except Exception as e:
            self.logger.error(f"解析消息失败: {str(e)}")
            # 返回一个基本的结构，避免系统崩溃
            return {
                "text_block": str(message.content),
                "semantic_tags": [],
                "emotions": ["neutral"],
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
    
    async def parse_mixed_content(self, messages: List[Message]) -> Dict[str, Any]:
        """
        解析混合内容消息（如同时包含文本和图像的消息）
        
        Args:
            messages: 消息对象列表
        
        Returns:
            整合后的解析结果
        """
        try:
            # 分别解析每个消息
            parsed_results = []
            for message in messages:
                result = await self.parse(message)
                parsed_results.append(result)
            
            # 使用整合管理器整合结果
            integrated_result = await self.integration_manager.integrate(parsed_results)
            return integrated_result
        
        except Exception as e:
            self.logger.error(f"解析混合内容失败: {str(e)}")
            # 返回一个基本的结构，避免系统崩溃
            return {
                "text_block": "混合内容",
                "semantic_tags": [],
                "emotions": ["neutral"],
                "modalities": ["mixed"],
                "error": str(e)
            }

# 创建全局多模态输入解析器实例
multimodal_input_parser = MultiModalInputParser()
