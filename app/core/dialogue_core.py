"""
对话调度器（DialogueCore）
路由到不同对话类型的处理流
"""
from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
import uuid
from datetime import datetime

from ..models.data_models import Message, Turn, Session, Dialogue
from .input_parser import MultiModalInputParser, SemanticBlock
from .context_builder import ContextBuilder
from .llm_caller import LLMCaller
from .tool_invoker import ToolInvoker
from .response_mixer import ResponseMixer


class DialogueCore:
    """
    对话调度器
    负责协调各模块，处理完整对话流程
    """
    def __init__(self):
        self.logger = logging.getLogger("DialogueCore")
        self.input_parser = MultiModalInputParser()
        self.context_builder = ContextBuilder()
        self.llm_caller = LLMCaller()
        self.tool_invoker = ToolInvoker()
        self.response_mixer = ResponseMixer()
    
    async def process_message(
        self,
        message: Message,
        dialogue: Optional[Dialogue] = None,
        session: Optional[Session] = None,
        turn: Optional[Turn] = None
    ) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message: 消息对象
            dialogue: 对话对象，如果为None则创建新对话
            session: 会话对象，如果为None则创建新会话
            turn: 轮次对象，如果为None则创建新轮次
        
        Returns:
            处理结果，包含响应消息和更新的对话/会话/轮次对象
        """
        self.logger.info(f"Processing message: {message.id}")
        
        # 1. 创建或获取对话、会话、轮次
        dialogue, session, turn = await self._ensure_dialogue_context(
            message, dialogue, session, turn
        )
        
        # 2. 解析输入
        semantic_block = self.input_parser.parse(message)
        self.logger.info(f"Parsed input: {semantic_block.text_block[:50]}...")
        
        # 3. 构建上下文
        context = self.context_builder.build_context(
            dialogue_id=dialogue.id,
            current_turn=turn,
            current_message=message,
            semantic_block=semantic_block
        )
        prompt = self.context_builder.to_prompt_text(context)
        
        # 4. 调用LLM
        llm_response = await self.llm_caller.call(prompt)
        llm_content = llm_response.get("content", "")
        self.logger.info(f"LLM response: {llm_content[:50]}...")
        
        # 5. 检查是否需要工具调用
        tool_results = []
        if self._needs_tool(llm_content):
            self.logger.info("Tool call needed")
            
            # 解析工具请求
            tool_request = self._parse_tool_request(llm_content)
            
            # 调用工具
            tool_result = await self.tool_invoker.invoke_tool(
                tool_id=tool_request["tool"],
                parameters=tool_request["parameters"]
            )
            tool_results.append(tool_result.to_dict())
            
            # 更新上下文并再次调用LLM
            updated_context = self._update_context_with_tool_result(context, tool_result)
            updated_prompt = self.context_builder.to_prompt_text(updated_context)
            
            llm_response = await self.llm_caller.call(updated_prompt)
            llm_content = llm_response.get("content", "")
            self.logger.info(f"Updated LLM response: {llm_content[:50]}...")
        
        # 6. 组装响应
        response_object = self.response_mixer.mix_response(
            llm_response=llm_content,
            tool_results=tool_results
        )
        
        # 7. 创建响应消息
        response_message = self.response_mixer.create_response_message(
            dialogue_id=dialogue.id,
            session_id=session.id,
            turn_id=turn.id,
            content=response_object["content"],
            sender_id="ai-system",  # 实际应使用配置的AI ID
            metadata={
                "original_content": response_object["original_content"],
                "tool_results": tool_results,
                "modifiers_applied": response_object["modifiers_applied"]
            }
        )
        
        # 8. 更新轮次状态
        turn.messages.append(response_message.id)
        turn.status = "responded"
        turn.closed_at = datetime.utcnow()
        
        # 9. 返回结果
        return {
            "dialogue": dialogue,
            "session": session,
            "turn": turn,
            "input_message": message,
            "response_message": response_message,
            "context": context,
            "tool_results": tool_results
        }
    
    async def _ensure_dialogue_context(
        self,
        message: Message,
        dialogue: Optional[Dialogue] = None,
        session: Optional[Session] = None,
        turn: Optional[Turn] = None
    ) -> tuple:
        """
        确保对话上下文存在
        如果不存在则创建新的对话/会话/轮次
        
        Args:
            message: 消息对象
            dialogue: 对话对象
            session: 会话对象
            turn: 轮次对象
        
        Returns:
            对话、会话、轮次对象元组
        """
        # 创建新对话
        if dialogue is None:
            dialogue = Dialogue(
                dialogue_type="human_ai",
                human_id=message.sender_id if message.sender_role == "human" else None,
                ai_id=None  # 实际应使用配置的AI ID
            )
            self.logger.info(f"Created new dialogue: {dialogue.id}")
        
        # 创建新会话
        if session is None:
            session = Session(
                dialogue_id=dialogue.id,
                session_type="dialogue",
                created_by=message.sender_role
            )
            dialogue.sessions.append(session.id)
            self.logger.info(f"Created new session: {session.id}")
        
        # 创建新轮次
        if turn is None:
            turn = Turn(
                dialogue_id=dialogue.id,
                session_id=session.id,
                initiator_role=message.sender_role,
                responder_role="ai" if message.sender_role == "human" else "human"
            )
            session.turns.append(turn.id)
            self.logger.info(f"Created new turn: {turn.id}")
        
        # 添加消息到轮次
        if message.id not in turn.messages:
            turn.messages.append(message.id)
        
        # 更新对话最后活动时间
        dialogue.last_activity_at = datetime.utcnow()
        
        return dialogue, session, turn
    
    def _needs_tool(self, llm_content: str) -> bool:
        """
        检查LLM响应是否需要工具调用
        
        Args:
            llm_content: LLM响应内容
        
        Returns:
            是否需要工具调用
        """
        # 简化实现，检查关键词
        tool_keywords = [
            "我需要使用工具",
            "需要查询",
            "调用API",
            "使用工具"
        ]
        
        return any(keyword in llm_content for keyword in tool_keywords)
    
    def _parse_tool_request(self, llm_content: str) -> Dict[str, Any]:
        """
        解析工具请求
        
        Args:
            llm_content: LLM响应内容
        
        Returns:
            工具请求字典，包含tool和parameters
        """
        # 简化实现，实际应使用更复杂的解析逻辑
        tool_request = {
            "tool": "unknown",
            "parameters": {}
        }
        
        # 检查是否需要天气工具
        if "天气" in llm_content:
            tool_request["tool"] = "weather"
            
            # 提取城市参数
            city = "北京"  # 默认城市
            if "城市" in llm_content:
                # 简单提取城市名
                city_start = llm_content.find("城市") + 2
                city_end = llm_content.find("的天气")
                if city_end > city_start:
                    city = llm_content[city_start:city_end].strip()
            
            tool_request["parameters"] = {"city": city}
        
        # 检查是否需要搜索工具
        elif "搜索" in llm_content:
            tool_request["tool"] = "search"
            
            # 提取查询参数
            query = "默认查询"  # 默认查询
            if "搜索" in llm_content:
                # 简单提取查询词
                query_start = llm_content.find("搜索") + 2
                query_end = len(llm_content)
                query = llm_content[query_start:query_end].strip()
            
            tool_request["parameters"] = {"query": query}
        
        return tool_request
    
    def _update_context_with_tool_result(
        self,
        context: Dict[str, Any],
        tool_result: Any
    ) -> Dict[str, Any]:
        """
        使用工具结果更新上下文
        
        Args:
            context: 原始上下文
            tool_result: 工具调用结果
        
        Returns:
            更新后的上下文
        """
        # 复制原始上下文
        updated_context = context.copy()
        
        # 将工具结果转换为文本
        tool_result_text = tool_result.to_text()
        
        # 更新当前输入，加入工具结果
        current_input = updated_context["current_input"]
        current_input["text"] = current_input["text"] + f"\n\n工具调用结果: {tool_result_text}\n\n请基于以上工具结果回答问题。"
        
        return updated_context
