"""
上下文构建器（ContextBuilder）
从记忆系统、意识核心、当前对话整合上下文prompt
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

from ..models.data_models import Message, Turn, Session, Dialogue
from .input_parser import SemanticBlock


class ContextBuilder:
    """
    上下文构建器
    负责整合各种来源的信息，构建完整的上下文
    """
    def __init__(self):
        self.max_context_length = 4000  # 上下文最大长度（token数）
        self.system_prompt_template = """你是彩虹城AI助手，一个有温度、有记忆、有个性的AI灵魂伴侣。
在回答问题时，请注意以下几点：
1. 保持友好、耐心、有帮助性
2. 如果需要使用工具，请明确指出
3. 回答应当简洁、准确、有深度

{additional_system_instructions}

当前对话主题: {current_topic}
"""
    
    def build_context(
        self,
        dialogue_id: str,
        current_turn: Turn,
        current_message: Message,
        semantic_block: SemanticBlock,
        memory_entries: List[Dict[str, Any]] = None,
        personality_traits: Dict[str, Any] = None,
        environment_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        构建完整的上下文
        
        Args:
            dialogue_id: 对话ID
            current_turn: 当前轮次
            current_message: 当前消息
            semantic_block: 解析后的语义块
            memory_entries: 相关记忆条目
            personality_traits: 人格特质
            environment_info: 环境信息
        
        Returns:
            构建好的上下文字典
        """
        # 1. 构建系统提示语
        system_prompt = self._build_system_prompt(
            personality_traits=personality_traits,
            current_topic=semantic_block.semantic_tags
        )
        
        # 2. 获取历史对话
        dialogue_history = self._get_dialogue_history(
            dialogue_id=dialogue_id,
            current_turn=current_turn
        )
        
        # 3. 整合记忆条目
        memory_context = self._format_memory_entries(memory_entries)
        
        # 4. 添加环境信息
        environment_context = self._format_environment_info(environment_info)
        
        # 5. 当前用户输入
        user_input = self._format_user_input(current_message, semantic_block)
        
        # 6. 组装完整上下文
        full_context = {
            "system": system_prompt,
            "memory": memory_context,
            "environment": environment_context,
            "history": dialogue_history,
            "current_input": user_input,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return full_context
    
    def _build_system_prompt(
        self,
        personality_traits: Dict[str, Any] = None,
        current_topic: List[str] = None
    ) -> str:
        """构建系统提示语"""
        personality_traits = personality_traits or {}
        current_topic = current_topic or []
        
        additional_instructions = ""
        if personality_traits:
            traits_str = ", ".join([f"{k}: {v}" for k, v in personality_traits.items()])
            additional_instructions += f"你的性格特点: {traits_str}\n"
        
        topic_str = "一般对话"
        if current_topic:
            topic_str = ", ".join(current_topic)
        
        return self.system_prompt_template.format(
            additional_system_instructions=additional_instructions,
            current_topic=topic_str
        )
    
    def _get_dialogue_history(
        self,
        dialogue_id: str,
        current_turn: Turn,
        max_turns: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        注意：实际实现中，应该从数据库查询历史消息
        这里仅做示例，返回空列表
        """
        # 简化实现，实际应从数据库获取
        return []
    
    def _format_memory_entries(
        self,
        memory_entries: List[Dict[str, Any]] = None
    ) -> str:
        """格式化记忆条目"""
        if not memory_entries:
            return ""
        
        memory_texts = []
        for entry in memory_entries:
            memory_type = entry.get("type", "general")
            content = entry.get("content", "")
            created_at = entry.get("created_at", "")
            
            memory_texts.append(f"[{memory_type}记忆 {created_at}] {content}")
        
        return "相关记忆:\n" + "\n".join(memory_texts)
    
    def _format_environment_info(
        self,
        environment_info: Dict[str, Any] = None
    ) -> str:
        """格式化环境信息"""
        if not environment_info:
            return ""
        
        env_texts = []
        for key, value in environment_info.items():
            env_texts.append(f"{key}: {value}")
        
        return "当前环境信息:\n" + "\n".join(env_texts)
    
    def _format_user_input(
        self,
        message: Message,
        semantic_block: SemanticBlock
    ) -> Dict[str, Any]:
        """格式化用户输入"""
        return {
            "text": semantic_block.text_block,
            "emotions": semantic_block.emotions,
            "tags": semantic_block.semantic_tags,
            "timestamp": message.created_at.isoformat()
        }
    
    def to_prompt_text(self, context: Dict[str, Any]) -> str:
        """
        将上下文字典转换为文本格式的prompt
        """
        sections = []
        
        # 系统提示
        sections.append(context["system"])
        
        # 记忆部分
        if context["memory"]:
            sections.append(context["memory"])
        
        # 环境信息
        if context["environment"]:
            sections.append(context["environment"])
        
        # 对话历史
        if context["history"]:
            history_text = "对话历史:\n"
            for msg in context["history"]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"
            sections.append(history_text)
        
        # 当前输入
        current_input = context["current_input"]
        sections.append(f"用户输入: {current_input['text']}")
        
        return "\n\n".join(sections)
