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
from .constants import DialogueTypes, SessionTypes, ContentTypes, RoleTypes



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
            # 获取对话信息，用于对话类型路由
            from ..db.repositories import dialogue_repo
            dialogue = await dialogue_repo.get(message.dialogue_id)
            if not dialogue:
                self.logger.error(f"Dialogue not found: {message.dialogue_id}")
                raise ValueError(f"Dialogue not found: {message.dialogue_id}")
            
            # 根据对话类型路由到相应的处理逻辑
            return await self.route_by_dialogue_type(message, dialogue, stream_callback, history)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            # 发送错误通知
            if stream_callback:
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

    async def route_by_dialogue_type(self, message: Message, dialogue: Dialogue, stream_callback=None, history=None) -> Dict[str, Any]:
        """
        根据对话类型路由到相应的处理逻辑
        
        Args:
            message: 消息对象
            dialogue: 对话对象
            stream_callback: 流式响应回调函数
            history: 历史消息列表
        
        Returns:
            处理结果
        """
        dialogue_type = dialogue.dialogue_type
        
        # 根据对话类型路由
        if dialogue_type == DialogueTypes.HUMAN_AI:
            # 人类 ⇄ AI 私聊 (已实现)
            return await self.process_human_ai_dialogue(message, dialogue, stream_callback, history)
            
        elif dialogue_type == DialogueTypes.AI_SELF:
            # AI ⇄ 自我（自省/觉知）
            return await self.process_ai_self_dialogue(message, dialogue, stream_callback, history)
            
        elif dialogue_type == DialogueTypes.AI_AI:
            # AI ⇄ AI 对话
            return await self.process_ai_ai_dialogue(message, dialogue, stream_callback, history)
            
        elif dialogue_type == DialogueTypes.HUMAN_HUMAN_PRIVATE:
            # 人类 ⇄ 人类 私聊
            return await self.process_human_human_dialogue(message, dialogue, stream_callback, history)
            
        elif dialogue_type == DialogueTypes.HUMAN_HUMAN_GROUP:
            # 人类 ⇄ 人类 群聊
            return await self.process_human_human_group_dialogue(message, dialogue, stream_callback, history)
            
        elif dialogue_type == DialogueTypes.HUMAN_AI_GROUP:
            # 人类 ⇄ AI 群组 (LIO)
            return await self.process_human_ai_group_dialogue(message, dialogue, stream_callback, history)
            
        elif dialogue_type == DialogueTypes.AI_MULTI_HUMAN:
            # AI ⇄ 多人类 群组
            return await self.process_ai_multi_human_dialogue(message, dialogue, stream_callback, history)
            
        else:
            # 未知对话类型，使用默认处理逻辑
            self.logger.warning(f"Unknown dialogue type: {dialogue_type}, using default processing")
            return await self.process_human_ai_dialogue(message, dialogue, stream_callback, history)
    
    async def process_human_ai_dialogue(self, message: Message, dialogue: Dialogue, stream_callback=None, history=None) -> Dict[str, Any]:
        """处理人类 ⇄ AI 私聊"""
        # 现有的处理逻辑已经在process_message方法中实现
        # 这里可以直接复用process_message方法的核心逻辑
        
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
            if stream_callback:
                await stream_callback(response_content, False)
        
        self.logger.info(f"LLM response: {response_content[:50]}...")
        
        # 5. 检查是否需要工具调用
        tool_results = []
        if self._needs_tool(response_content):
            self.logger.info("Tool call needed")
            
            # 解析工具请求
            tool_request = self._parse_tool_request(response_content)
            
            # 发送工具调用通知
            if stream_callback:
                await stream_callback(
                    f"{response_content}\n\n[正在调用工具: {tool_request['tool']}]", 
                    False
                )
            
            # 调用工具
            tool_result = await self.tool_invoker.invoke_tool(
                tool_name=tool_request["tool"],
                parameters=tool_request["parameters"]
            )
            
            # 添加到结果列表
            tool_results.append({
                "tool": tool_request["tool"],
                "parameters": tool_request["parameters"],
                "result": tool_result
            })
            
            # 更新上下文，加入工具调用结果
            context = self._update_context_with_tool_result(context, tool_result)
            
            # 重新生成提示词
            prompt = self.context_builder.to_prompt_text(context)
            
            # 再次调用LLM
            response_content = ""
            async for chunk in self.llm_caller.stream_call(prompt):
                chunk_content = chunk.get("content", "")
                response_content += chunk_content
                
                # 发送流式响应
                if stream_callback:
                    await stream_callback(response_content, False)
        
        # 6. 组装响应
        response_object = self.response_mixer.mix_response(
            llm_response=response_content,
            tool_results=tool_results
        )
        
        # 发送完成通知
        if stream_callback:
            await stream_callback(response_object["content"], True)
        
        # 7. 返回结果
        return {
            "content": response_object["content"],
            "content_type": "text",  # 默认为文本
            "tool_results": tool_results,
            "ai_id": dialogue.ai_id or "ai-system",
            "metadata": {
                "tool_results": tool_results,
                "multimodal": multimodal_content is not None
            }
        }
    
    async def process_ai_self_dialogue(self, message: Message, dialogue: Dialogue, stream_callback=None, history=None) -> Dict[str, Any]:
        """处理 AI ⇄ 自我（自省/觉知）对话"""
        # 调用自省引擎处理
        from ..core.introspection_engine import introspection_engine
        
        self.logger.info(f"Processing AI self-reflection dialogue: {dialogue.id}")
        
        # 创建自省会话
        introspection_session = await introspection_engine.start_introspection_session(
            ai_id=dialogue.ai_id,
            session_type="self_reflection",
            trigger_source="dialogue",
            goal=message.content,
            metadata={
                "dialogue_id": dialogue.id,
                "message_id": message.id
            }
        )
        
        # 发送流式响应
        if stream_callback:
            await stream_callback("正在进行自我反思...", False)
        
        # 返回初始响应
        return {
            "content": "我正在进行自我反思，这可能需要一些时间。我会在完成后通知你。",
            "content_type": "text",
            "ai_id": dialogue.ai_id,
            "metadata": {
                "introspection_session_id": introspection_session.get("id"),
                "introspection_status": "processing"
            }
        }
    
    async def process_ai_ai_dialogue(self, message: Message, dialogue: Dialogue, stream_callback=None, history=None) -> Dict[str, Any]:
        """处理 AI ⇄ AI 对话"""
        # 调用多智能体协调器
        self.logger.info(f"Processing AI-AI dialogue: {dialogue.id}")
        
        # 获取参与的AI列表
        participant_ai_ids = dialogue.metadata.get("participant_ai_ids", [])
        if not participant_ai_ids:
            self.logger.error(f"No participant AIs found for AI-AI dialogue: {dialogue.id}")
            return {
                "content": "无法处理AI间对话，未找到参与的AI列表。",
                "content_type": "text",
                "ai_id": dialogue.ai_id,
                "error": "No participant AIs found"
            }
        
        # 这里应该调用多智能体协调器处理AI间对话
        # 简化实现，实际应该有更复杂的协调逻辑
        if stream_callback:
            await stream_callback("正在处理AI间对话...", False)
        
        # 返回简单响应
        return {
            "content": f"AI {dialogue.ai_id} 正在与 {', '.join(participant_ai_ids)} 进行对话。",
            "content_type": "text",
            "ai_id": dialogue.ai_id,
            "metadata": {
                "participant_ai_ids": participant_ai_ids
            }
        }
    
    async def process_human_human_dialogue(self, message: Message, dialogue: Dialogue, stream_callback=None, history=None) -> Dict[str, Any]:
        """处理人类 ⇄ 人类私聊"""
        # 实现人类间私聊的消息转发
        self.logger.info(f"Processing human-human dialogue: {dialogue.id}")
        
        # 获取接收者ID
        recipient_id = None
        if message.sender_id == dialogue.human_id:
            # 如果发送者是对话中的第一个人类，接收者是第二个人类
            recipient_id = dialogue.metadata.get("second_human_id")
        else:
            # 否则接收者是第一个人类
            recipient_id = dialogue.human_id
        
        if not recipient_id:
            self.logger.error(f"No recipient found for human-human dialogue: {dialogue.id}")
            return {
                "content": "无法转发消息，未找到接收者。",
                "content_type": "text",
                "error": "No recipient found"
            }
        
        # 通知接收者（实际实现应该通过WebSocket或其他通知机制）
        from ..services.notification_service import notification_service
        await notification_service.notify_message(recipient_id, message)
        
        # 返回确认消息
        return {
            "content": "消息已转发",
            "content_type": "text",
            "metadata": {
                "recipient_id": recipient_id
            }
        }
    
    async def process_human_human_group_dialogue(self, message: Message, dialogue: Dialogue, stream_callback=None, history=None) -> Dict[str, Any]:
        """处理人类 ⇄ 人类群聊"""
        # 实现群聊消息广播
        self.logger.info(f"Processing human-human group dialogue: {dialogue.id}")
        
        # 获取群组成员列表
        group_members = dialogue.metadata.get("group_members", [])
        if not group_members:
            self.logger.error(f"No group members found for group dialogue: {dialogue.id}")
            return {
                "content": "无法广播消息，未找到群组成员。",
                "content_type": "text",
                "error": "No group members found"
            }
        
        # 广播消息给所有成员（排除发送者自己）
        from ..services.notification_service import notification_service
        for member_id in group_members:
            if member_id != message.sender_id:
                await notification_service.notify_message(member_id, message)
        
        # 返回确认消息
        return {
            "content": f"消息已广播给{len(group_members)-1}位群组成员",
            "content_type": "text",
            "metadata": {
                "group_members": group_members,
                "broadcast_count": len(group_members) - 1
            }
        }
    
    async def process_human_ai_group_dialogue(self, message: Message, dialogue: Dialogue, stream_callback=None, history=None) -> Dict[str, Any]:
        """处理人类 ⇄ AI 群组 (LIO)对话"""
        # 实现LIO群组逻辑
        self.logger.info(f"Processing human-AI group (LIO) dialogue: {dialogue.id}")
        
        # 获取群组中的人类和AI成员
        human_members = dialogue.metadata.get("human_members", [])
        ai_members = dialogue.metadata.get("ai_members", [])
        
        if not human_members or not ai_members:
            self.logger.error(f"Missing members in LIO group: {dialogue.id}")
            return {
                "content": "无法处理LIO群组对话，成员信息不完整。",
                "content_type": "text",
                "error": "Incomplete member information"
            }
        
        # 根据发送者类型处理消息
        if message.sender_role == RoleTypes.HUMAN:
            # 人类发送的消息，需要AI响应
            # 这里可以复用人类-AI私聊的处理逻辑
            return await self.process_human_ai_dialogue(message, dialogue, stream_callback, history)
        else:
            # AI发送的消息，需要广播给人类成员
            from ..services.notification_service import notification_service
            for human_id in human_members:
                await notification_service.notify_message(human_id, message)
            
            return {
                "content": f"AI消息已广播给{len(human_members)}位人类成员",
                "content_type": "text",
                "ai_id": message.sender_id,
                "metadata": {
                    "human_members": human_members,
                    "broadcast_count": len(human_members)
                }
            }
    
    async def process_ai_multi_human_dialogue(self, message: Message, dialogue: Dialogue, stream_callback=None, history=None) -> Dict[str, Any]:
        """处理 AI ⇄ 多人类群组对话"""
        # 实现AI与多人类交互的逻辑
        self.logger.info(f"Processing AI-multi-human dialogue: {dialogue.id}")
        
        # 获取参与的人类列表
        human_participants = dialogue.metadata.get("human_participants", [])
        if not human_participants:
            self.logger.error(f"No human participants found for AI-multi-human dialogue: {dialogue.id}")
            return {
                "content": "无法处理AI与多人类对话，未找到人类参与者。",
                "content_type": "text",
                "ai_id": dialogue.ai_id,
                "error": "No human participants found"
            }
        
        # 根据发送者角色处理
        if message.sender_role == RoleTypes.HUMAN:
            # 人类发送的消息，AI需要响应
            # 可以复用人类-AI私聊的处理逻辑
            response = await self.process_human_ai_dialogue(message, dialogue, stream_callback, history)
            
            # 广播AI的响应给所有其他人类参与者
            from ..services.notification_service import notification_service
            for human_id in human_participants:
                if human_id != message.sender_id:
                    await notification_service.notify_ai_response(human_id, response, message.id)
            
            return response
        else:
            # AI主动发送的消息，广播给所有人类参与者
            from ..services.notification_service import notification_service
            for human_id in human_participants:
                await notification_service.notify_message(human_id, message)
            
            return {
                "content": f"AI消息已广播给{len(human_participants)}位人类参与者",
                "content_type": "text",
                "ai_id": dialogue.ai_id,
                "metadata": {
                    "human_participants": human_participants,
                    "broadcast_count": len(human_participants)
                }
            }