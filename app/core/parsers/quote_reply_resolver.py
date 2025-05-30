"""
引用回复解析器模块

用于处理引用回复，将引用内容补全插入结构化文本中
"""
from typing import Dict, Any, List, Optional, Tuple
import asyncio

from ...core.logger import logger

class QuoteReplyResolver:
    """引用回复解析器"""
    
    def __init__(self):
        self.logger = logger
        # 这里需要一个消息查询服务，用于根据消息ID获取消息内容
        # 实际实现时需要注入或导入相应的服务
        self.message_service = None
    
    async def parse(self, message) -> Dict[str, Any]:
        """
        解析引用回复
        
        Args:
            message: 消息对象
        
        Returns:
            解析结果
        """
        try:
            content = message.content
            content_meta = message.content_meta or {}
            
            # 获取引用的消息ID
            reply_to_id = content_meta.get("reply_to") or ""
            
            # 获取引用的消息内容
            quoted_content, quoted_sender = await self._get_quoted_message(reply_to_id)
            
            # 构建带引用的文本
            text_with_quote = self._build_text_with_quote(content, quoted_content, quoted_sender)
            
            # 提取引用上下文的关键信息
            quote_context = self._extract_quote_context(content, quoted_content)
            
            return {
                "text_block": text_with_quote,
                "original_text": content,
                "quoted_content": quoted_content,
                "quoted_sender": quoted_sender,
                "reply_to_id": reply_to_id,
                "quote_context": quote_context,
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
        
        except Exception as e:
            self.logger.error(f"解析引用回复失败: {str(e)}")
            return {
                "text_block": str(message.content),
                "original_text": str(message.content),
                "quoted_content": "",
                "quoted_sender": "",
                "reply_to_id": "",
                "quote_context": {},
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
    
    async def _get_quoted_message(self, message_id: str) -> Tuple[str, str]:
        """
        获取引用的消息内容
        
        Args:
            message_id: 消息ID
        
        Returns:
            (消息内容, 发送者)
        """
        # 实际实现时，应该从消息服务中获取消息内容
        # 这里简单模拟
        if not message_id:
            return "", ""
        
        if self.message_service:
            try:
                # 调用消息服务获取消息
                message = await self.message_service.get_message(message_id)
                return message.content, message.sender_role
            except Exception as e:
                self.logger.error(f"获取引用消息失败: {str(e)}")
        
        # 如果获取失败，返回空内容
        return "引用的消息内容不可用", "unknown"
    
    def _build_text_with_quote(self, content: str, quoted_content: str, quoted_sender: str) -> str:
        """
        构建带引用的文本
        
        Args:
            content: 原始内容
            quoted_content: 引用的内容
            quoted_sender: 引用内容的发送者
        
        Returns:
            带引用的文本
        """
        if not quoted_content:
            return content
        
        # 根据发送者角色选择不同的引用前缀
        if quoted_sender == "human":
            prefix = "引用用户的话："
        elif quoted_sender == "ai":
            prefix = "引用AI的话："
        else:
            prefix = "引用："
        
        # 构建引用文本
        quote_text = f"{prefix}"{quoted_content}"\n\n{content}"
        return quote_text
    
    def _extract_quote_context(self, content: str, quoted_content: str) -> Dict[str, Any]:
        """
        提取引用上下文的关键信息
        
        Args:
            content: 原始内容
            quoted_content: 引用的内容
        
        Returns:
            引用上下文的关键信息
        """
        # 简单实现，实际应该进行更复杂的语义分析
        return {
            "is_question_response": "?" in quoted_content,
            "is_continuation": len(content) > 3 * len(quoted_content),
            "is_clarification": "什么意思" in quoted_content or "不明白" in quoted_content,
            "is_agreement": "同意" in content or "赞成" in content,
            "is_disagreement": "不同意" in content or "反对" in content
        }

# 创建全局引用回复解析器实例
quote_reply_resolver = QuoteReplyResolver()
