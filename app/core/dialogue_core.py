"""
对话调度器（DialogueCore）
路由到不同对话类型的处理流
"""
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable
import logging
import asyncio
import uuid
import json
from datetime import datetime

from ..models.data_models import Message, Turn, Session, Dialogue
from .input_parser import MultiModalInputParser, SemanticBlock
from .context_builder import ContextBuilder
from .llm_caller import LLMCaller
from .tool_invoker import ToolInvoker
from .response_mixer import ResponseMixer
from .multimodal_handler import multimodal_handler
from ..services.notification_service import notification_service


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
        history: List[Message] = None,
        stream_callback: Optional[Callable[[str, bool], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message: 消息对象
            history: 历史消息列表
            stream_callback: 流式响应回调函数
        
        Returns:
            处理结果
        """
        self.logger.info(f"Processing message: {message.id}")
        
        # 如果没有提供流式响应回调，使用默认的通知服务
        if stream_callback is None:
            async def default_stream_callback(content: str, is_complete: bool):
                await notification_service.send_stream_response(
                    dialogue_id=message.dialogue_id,
                    session_id=message.session_id,
                    turn_id=message.turn_id,
                    content=content,
                    is_complete=is_complete
                )
            stream_callback = default_stream_callback
        
        try:
            # 1. 处理多模态内容
            multimodal_content = None
            if message.content_type.startswith("multimodal/") and message.metadata and "media" in message.metadata:
                # 提取多模态内容
                multimodal_content = self._process_multimodal_content(message)
            
            # 2. 解析输入
            semantic_block = self.input_parser.parse(message)
            self.logger.info(f"Parsed input: {semantic_block.text_block[:50]}...")
            
            # 3. 构建上下文
            context = self.context_builder.build_context(
                message=message,
                history=history,
                multimodal_content=multimodal_content
            )
            prompt = self.context_builder.to_prompt_text(context)
            
            # 4. 调用LLM（流式响应）
            response_content = ""
            async for chunk in self.llm_caller.stream_call(prompt):
                chunk_content = chunk.get("content", "")
                response_content += chunk_content
                
                # 发送流式响应
                await stream_callback(response_content, False)
            
            self.logger.info(f"LLM response: {response_content[:50]}...")
            
            # 5. 检查是否需要工具调用
            tool_results = []
            if self._needs_tool(response_content):
                self.logger.info("Tool call needed")
                
                # 解析工具请求
                tool_request = self._parse_tool_request(response_content)
                
                # 发送工具调用通知
                await stream_callback(
                    f"{response_content}\n\n[正在调用工具: {tool_request['tool']}]", 
                    False
                )
                
                # 调用工具
                tool_result = await self.tool_invoker.invoke_tool(
                    tool_id=tool_request["tool"],
                    parameters=tool_request["parameters"]
                )
                tool_results.append(tool_result.to_dict())
                
                # 更新上下文并再次调用LLM
                updated_context = self._update_context_with_tool_result(context, tool_result)
                updated_prompt = self.context_builder.to_prompt_text(updated_context)
                
                # 发送工具结果通知
                await stream_callback(
                    f"{response_content}\n\n[工具结果: {tool_result.to_text()}]\n\n[正在生成最终回复...]", 
                    False
                )
                
                # 再次调用LLM（流式响应）
                final_response = ""
                async for chunk in self.llm_caller.stream_call(updated_prompt):
                    chunk_content = chunk.get("content", "")
                    final_response += chunk_content
                    
                    # 发送流式响应
                    await stream_callback(
                        f"{response_content}\n\n[工具结果: {tool_result.to_text()}]\n\n{final_response}", 
                        False
                    )
                
                response_content = final_response
                self.logger.info(f"Final response: {response_content[:50]}...")
            
            # 6. 组装响应
            response_object = self.response_mixer.mix_response(
                llm_response=response_content,
                tool_results=tool_results
            )
            
            # 发送完成通知
            await stream_callback(response_object["content"], True)
            
            # 7. 返回结果
            return {
                "content": response_object["content"],
                "content_type": "text",  # 默认为文本
                "tool_results": tool_results,
                "ai_id": "ai-system",  # 实际应使用配置的AI ID
                "metadata": {
                    "tool_results": tool_results,
                    "multimodal": multimodal_content is not None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            # 发送错误通知
            await stream_callback(f"处理消息时发生错误: {str(e)}", True)
            
            # 返回错误结果
            return {
                "content": f"处理消息时发生错误: {str(e)}",
                "content_type": "text",
                "tool_results": [],
                "ai_id": "ai-system",
                "metadata": {
                    "error": str(e)
                }
            }
    
    def _process_multimodal_content(self, message: Message) -> Dict[str, Any]:
        """
        处理多模态内容
        
        Args:
            message: 消息对象
        
        Returns:
            处理结果
        """
        try:
            # 提取媒体信息
            media_info = message.metadata.get("media", [])
            if not media_info:
                return None
            
            result = {
                "type": message.content_type.split("/")[1],  # 例如 "image", "audio", "video"
                "items": []
            }
            
            # 处理每个媒体项
            for item in media_info:
                media_item = {
                    "url": item.get("url", ""),
                    "mime_type": item.get("mime_type", ""),
                    "category": item.get("category", ""),
                    "metadata": item.get("metadata", {})
                }
                result["items"].append(media_item)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing multimodal content: {str(e)}")
            return None
    
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
