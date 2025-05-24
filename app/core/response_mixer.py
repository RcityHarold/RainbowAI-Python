"""
响应组装器（ResponseMixer）
整合插件内容、模型响应、插入模块形成最终消息
"""
from typing import Dict, Any, List, Optional, Union
import json
import logging
from datetime import datetime

from ..models.data_models import Message


class ResponseModifier:
    """响应修改器基类"""
    def __init__(self, modifier_id: str, description: str):
        self.modifier_id = modifier_id
        self.description = description
        self.logger = logging.getLogger(f"Modifier:{modifier_id}")
    
    def modify(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        修改响应内容
        
        Args:
            content: 原始响应内容
            metadata: 元数据
        
        Returns:
            修改后的响应内容
        """
        try:
            return self._modify_logic(content, metadata or {})
        except Exception as e:
            self.logger.error(f"Error in modifier {self.modifier_id}: {str(e)}")
            return content
    
    def _modify_logic(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        修改逻辑，子类需要实现此方法
        
        Args:
            content: 原始响应内容
            metadata: 元数据
        
        Returns:
            修改后的响应内容
        """
        raise NotImplementedError("Subclasses must implement _modify_logic method")


class EmotionModifier(ResponseModifier):
    """情感修饰器，根据指定情感调整响应语气"""
    def __init__(self):
        super().__init__(
            modifier_id="emotion",
            description="根据指定情感调整响应语气"
        )
        # 情感词汇映射
        self.emotion_phrases = {
            "happy": ["😊", "很高兴", "太棒了", "真不错"],
            "sad": ["😔", "遗憾", "难过", "希望能好转"],
            "excited": ["😃", "太棒了", "真是令人兴奋", "太精彩了"],
            "calm": ["😌", "平静", "安心", "放松"]
        }
    
    def _modify_logic(self, content: str, metadata: Dict[str, Any]) -> str:
        # 获取目标情感
        emotion = metadata.get("target_emotion", "neutral")
        if emotion == "neutral" or emotion not in self.emotion_phrases:
            return content
        
        # 获取情感词汇
        phrases = self.emotion_phrases[emotion]
        
        # 在内容末尾添加情感符号
        if content.endswith(("。", "！", "？", ".", "!", "?")):
            modified_content = content[:-1] + phrases[0] + content[-1]
        else:
            modified_content = content + phrases[0]
        
        return modified_content


class FormalityModifier(ResponseModifier):
    """正式度修饰器，调整响应的正式程度"""
    def __init__(self):
        super().__init__(
            modifier_id="formality",
            description="调整响应的正式程度"
        )
    
    def _modify_logic(self, content: str, metadata: Dict[str, Any]) -> str:
        # 获取目标正式度
        formality = metadata.get("formality", "neutral")
        
        if formality == "formal":
            # 替换口语化表达为正式表达
            replacements = {
                "我觉得": "我认为",
                "挺好的": "相当不错",
                "没问题": "没有问题",
                "行": "可以",
                "好的": "好的，我明白了"
            }
            
            modified_content = content
            for informal, formal in replacements.items():
                modified_content = modified_content.replace(informal, formal)
            
            return modified_content
        
        elif formality == "casual":
            # 替换正式表达为口语化表达
            replacements = {
                "我认为": "我觉得",
                "非常": "很",
                "请您": "请你",
                "可以": "行",
                "我理解": "我懂"
            }
            
            modified_content = content
            for formal, casual in replacements.items():
                modified_content = modified_content.replace(formal, casual)
            
            return modified_content
        
        else:
            # 保持原样
            return content


class ResponseMixer:
    """
    响应组装器
    整合插件内容、模型响应、插入模块形成最终消息
    """
    def __init__(self):
        self.modifiers: Dict[str, ResponseModifier] = {}
        self.logger = logging.getLogger("ResponseMixer")
        
        # 注册默认修饰器
        self.register_default_modifiers()
    
    def register_modifier(self, modifier: ResponseModifier):
        """
        注册响应修饰器
        
        Args:
            modifier: 修饰器实例
        """
        self.modifiers[modifier.modifier_id] = modifier
        self.logger.info(f"Registered modifier: {modifier.modifier_id}")
    
    def register_default_modifiers(self):
        """注册默认修饰器"""
        self.register_modifier(EmotionModifier())
        self.register_modifier(FormalityModifier())
    
    def mix_response(
        self,
        llm_response: str,
        tool_results: List[Dict[str, Any]] = None,
        plugins_output: List[Dict[str, Any]] = None,
        modifiers_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        混合响应
        
        Args:
            llm_response: LLM生成的原始响应
            tool_results: 工具调用结果列表
            plugins_output: 插件输出列表
            modifiers_config: 修饰器配置
        
        Returns:
            混合后的响应
        """
        self.logger.info("Mixing response")
        
        # 初始化最终响应
        final_response = llm_response
        
        # 处理工具结果
        if tool_results:
            self.logger.info(f"Processing {len(tool_results)} tool results")
            # 工具结果应该已经在LLM响应中体现，不需要额外处理
            # 但可以记录工具调用信息
            tool_ids = [result.get("tool_id") for result in tool_results]
            self.logger.info(f"Used tools: {', '.join(tool_ids)}")
        
        # 处理插件输出
        if plugins_output:
            self.logger.info(f"Processing {len(plugins_output)} plugin outputs")
            # 插入插件输出
            for plugin_output in plugins_output:
                plugin_id = plugin_output.get("plugin_id", "unknown")
                content = plugin_output.get("content", "")
                position = plugin_output.get("position", "append")
                
                if position == "prepend":
                    final_response = content + "\n\n" + final_response
                elif position == "append":
                    final_response = final_response + "\n\n" + content
                elif position == "replace":
                    final_response = content
                else:
                    self.logger.warning(f"Unknown plugin position: {position}")
        
        # 应用修饰器
        if modifiers_config:
            self.logger.info("Applying modifiers")
            for modifier_id, config in modifiers_config.items():
                if modifier_id in self.modifiers:
                    modifier = self.modifiers[modifier_id]
                    self.logger.info(f"Applying modifier: {modifier_id}")
                    final_response = modifier.modify(final_response, config)
        
        # 构建最终响应对象
        response_object = {
            "content": final_response,
            "original_content": llm_response,
            "tool_results": tool_results,
            "plugins_output": plugins_output,
            "modifiers_applied": list(modifiers_config.keys()) if modifiers_config else [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response_object
    
    def create_response_message(
        self,
        dialogue_id: str,
        session_id: str,
        turn_id: str,
        content: str,
        sender_id: str,
        metadata: Dict[str, Any] = None
    ) -> Message:
        """
        创建响应消息
        
        Args:
            dialogue_id: 对话ID
            session_id: 会话ID
            turn_id: 轮次ID
            content: 消息内容
            sender_id: 发送者ID
            metadata: 元数据
        
        Returns:
            消息对象
        """
        return Message(
            dialogue_id=dialogue_id,
            session_id=session_id,
            turn_id=turn_id,
            sender_role="ai",
            sender_id=sender_id,
            content=content,
            content_type="text",
            metadata=metadata or {}
        )
