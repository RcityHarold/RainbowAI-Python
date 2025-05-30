"""
文本解析器模块

用于处理文本内容，提取摘要、实体和情感
"""
from typing import Dict, Any, List, Optional
import re

from ...core.logger import logger

class TextParser:
    """文本解析器"""
    
    def __init__(self):
        self.logger = logger
    
    async def parse(self, message) -> Dict[str, Any]:
        """
        解析文本内容
        
        Args:
            message: 消息对象
        
        Returns:
            解析结果
        """
        try:
            content = message.content
            
            # 提取实体（简单实现，实际应使用NLP模型）
            entities = self._extract_entities(content)
            
            # 分析情感（简单实现，实际应使用情感分析模型）
            emotion = self._analyze_sentiment(content)
            
            # 生成摘要（简单实现，实际应使用摘要生成模型）
            summary = self._generate_summary(content)
            
            return {
                "text_block": content,
                "semantic_tags": entities,
                "emotions": [emotion],
                "summary": summary,
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
        
        except Exception as e:
            self.logger.error(f"解析文本失败: {str(e)}")
            return {
                "text_block": str(message.content),
                "semantic_tags": [],
                "emotions": ["neutral"],
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
    
    async def parse_markdown(self, message) -> Dict[str, Any]:
        """
        解析Markdown内容
        
        Args:
            message: 消息对象
        
        Returns:
            解析结果
        """
        try:
            content = message.content
            
            # 将Markdown转换为纯文本（简单实现）
            plain_text = self._markdown_to_text(content)
            
            # 提取实体
            entities = self._extract_entities(plain_text)
            
            # 分析情感
            emotion = self._analyze_sentiment(plain_text)
            
            return {
                "text_block": plain_text,
                "original_markdown": content,
                "semantic_tags": entities,
                "emotions": [emotion],
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
        
        except Exception as e:
            self.logger.error(f"解析Markdown失败: {str(e)}")
            return {
                "text_block": str(message.content),
                "semantic_tags": [],
                "emotions": ["neutral"],
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        提取文本中的实体（简单实现）
        
        Args:
            text: 文本内容
        
        Returns:
            实体列表
        """
        # 简单实现，实际应使用NLP模型
        entities = []
        
        # 检测可能的主题词（简单实现）
        keywords = ["天气", "旅行", "工作", "学习", "健康", "娱乐", "技术", "科学", "艺术", "历史"]
        for keyword in keywords:
            if keyword in text:
                entities.append(keyword)
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        分析文本情感（简单实现）
        
        Args:
            text: 文本内容
        
        Returns:
            情感标签
        """
        # 简单实现，实际应使用情感分析模型
        positive_words = ["喜欢", "开心", "高兴", "快乐", "好", "优秀", "棒", "感谢", "谢谢"]
        negative_words = ["不喜欢", "难过", "伤心", "失望", "糟糕", "差", "坏", "讨厌", "生气"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _generate_summary(self, text: str) -> str:
        """
        生成文本摘要（简单实现）
        
        Args:
            text: 文本内容
        
        Returns:
            摘要
        """
        # 简单实现，实际应使用摘要生成模型
        if len(text) <= 100:
            return text
        
        # 简单截取前100个字符
        return text[:100] + "..."
    
    def _markdown_to_text(self, markdown: str) -> str:
        """
        将Markdown转换为纯文本
        
        Args:
            markdown: Markdown内容
        
        Returns:
            纯文本
        """
        # 移除标题标记
        text = re.sub(r'#+\s+', '', markdown)
        
        # 移除粗体和斜体标记
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # 移除链接，只保留链接文本
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        
        # 移除列表标记
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # 移除代码块
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # 移除行内代码
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        return text.strip()

# 创建全局文本解析器实例
text_parser = TextParser()
