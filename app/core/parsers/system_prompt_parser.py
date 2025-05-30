"""
系统提示解析器模块

用于处理系统提示，参与system instruction合成
"""
from typing import Dict, Any, List, Optional
import re

from ...core.logger import logger

class SystemPromptParser:
    """系统提示解析器"""
    
    def __init__(self):
        self.logger = logger
        # 系统提示类型
        self.prompt_types = {
            "system_instruction": "系统指令",
            "context_hint": "上下文提示",
            "tool_suggestion": "工具建议",
            "memory_recall": "记忆回溯",
            "personality_guidance": "人格引导",
            "error_handling": "错误处理"
        }
    
    async def parse(self, message) -> Dict[str, Any]:
        """
        解析系统提示
        
        Args:
            message: 消息对象
        
        Returns:
            解析结果
        """
        try:
            content = message.content
            content_meta = message.content_meta or {}
            
            # 如果内容是字典，提取文本和类型
            if isinstance(content, dict):
                prompt_text = content.get("text", "")
                prompt_type = content.get("type", "system_instruction")
            else:
                # 否则假设内容是文本
                prompt_text = str(content)
                prompt_type = content_meta.get("type", "system_instruction")
            
            # 获取提示类型的显示名称
            prompt_type_display = self.prompt_types.get(prompt_type, "系统提示")
            
            # 提取指令意图（简单实现）
            instruction_intent = self._extract_instruction_intent(prompt_text, prompt_type)
            
            # 提取关键指令（简单实现）
            key_directives = self._extract_key_directives(prompt_text)
            
            # 构建系统提示文本
            system_text = f"{prompt_type_display}: {prompt_text}"
            
            return {
                "text_block": system_text,
                "prompt_text": prompt_text,
                "prompt_type": prompt_type,
                "instruction_intent": instruction_intent,
                "key_directives": key_directives,
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
        
        except Exception as e:
            self.logger.error(f"解析系统提示失败: {str(e)}")
            return {
                "text_block": str(message.content),
                "prompt_text": str(message.content),
                "prompt_type": "system_instruction",
                "instruction_intent": "unknown",
                "key_directives": [],
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
    
    def _extract_instruction_intent(self, text: str, prompt_type: str) -> str:
        """
        提取指令意图
        
        Args:
            text: 提示文本
            prompt_type: 提示类型
        
        Returns:
            指令意图
        """
        # 根据提示类型和文本内容判断意图
        if prompt_type == "system_instruction":
            if "请" in text or "回答" in text:
                return "request_response"
            elif "不要" in text or "避免" in text:
                return "constraint"
            elif "记住" in text or "注意" in text:
                return "reminder"
            else:
                return "general_instruction"
        elif prompt_type == "context_hint":
            return "provide_context"
        elif prompt_type == "tool_suggestion":
            return "suggest_tool"
        elif prompt_type == "memory_recall":
            return "recall_memory"
        elif prompt_type == "personality_guidance":
            return "guide_personality"
        elif prompt_type == "error_handling":
            return "handle_error"
        else:
            return "unknown"
    
    def _extract_key_directives(self, text: str) -> List[str]:
        """
        提取关键指令
        
        Args:
            text: 提示文本
        
        Returns:
            关键指令列表
        """
        # 简单实现，实际应使用更复杂的NLP技术
        directives = []
        
        # 尝试按句子分割
        sentences = re.split(r'[。！？.!?]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 检查是否包含指令性词语
            directive_words = ["请", "必须", "应该", "需要", "记住", "注意", "不要", "避免"]
            if any(word in sentence for word in directive_words):
                directives.append(sentence)
        
        # 如果没有找到明确的指令，使用整个文本
        if not directives and text.strip():
            directives.append(text.strip())
        
        return directives

# 创建全局系统提示解析器实例
system_prompt_parser = SystemPromptParser()
