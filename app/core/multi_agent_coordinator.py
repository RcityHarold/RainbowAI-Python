"""
多智能体协作系统模块
提供多个AI代理之间的协作和通信能力
"""
import logging
import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime

from ..models.data_models import Message, Dialogue
from ..db.repositories import dialogue_repo, message_repo
from .llm_caller import LLMCaller


class Agent:
    """智能体代理"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        description: str,
        capabilities: List[str],
        system_prompt: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.capabilities = capabilities
        self.system_prompt = system_prompt
        self.metadata = metadata or {}
        self.llm_caller = LLMCaller()
        self.logger = logging.getLogger(f"Agent:{agent_id}")
    
    async def process_message(
        self,
        message: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message: 消息内容
            context: 上下文信息
        
        Returns:
            处理结果
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(message, context)
            
            # 调用LLM
            response = await self.llm_caller.call(prompt)
            
            # 解析响应
            parsed_response = self._parse_response(response.get("content", ""))
            
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "role": self.role,
                "content": parsed_response.get("content", ""),
                "actions": parsed_response.get("actions", []),
                "thoughts": parsed_response.get("thoughts", ""),
                "created_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"处理消息失败: {str(e)}")
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "role": self.role,
                "content": f"处理消息时发生错误: {str(e)}",
                "error": str(e),
                "created_at": datetime.utcnow().isoformat()
            }
    
    def _build_prompt(self, message: Dict[str, Any], context: Dict[str, Any]) -> str:
        """构建提示词"""
        # 基础系统提示词
        system_prompt = self.system_prompt
        
        # 添加代理信息
        agent_info = f"""
        你是 {self.name}，一个{self.role}。
        
        你的职责和能力:
        {self.description}
        
        你可以使用的能力:
        {', '.join(self.capabilities)}
        """
        
        # 添加协作信息
        collaboration_info = f"""
        你正在与其他代理协作解决问题。当前对话中的其他代理包括:
        {self._format_other_agents(context.get('agents', []))}
        
        当前任务:
        {context.get('task', '未指定任务')}
        """
        
        # 添加对话历史
        history = self._format_history(context.get('history', []))
        
        # 添加当前消息
        current_message = f"""
        当前消息:
        发送者: {message.get('sender_name', '未知')} ({message.get('sender_role', '未知')})
        内容: {message.get('content', '')}
        """
        
        # 添加响应格式说明
        response_format = """
        请以JSON格式返回你的响应，包含以下字段:
        {
            "thoughts": "你的内部思考过程，不会展示给其他代理",
            "content": "你的实际回复内容，将展示给其他代理",
            "actions": [
                {
                    "type": "工具调用/信息请求/任务分配",
                    "target": "目标代理ID或'all'",
                    "content": "行动的具体内容"
                }
            ]
        }
        """
        
        # 组合完整提示词
        prompt = f"{system_prompt}\n\n{agent_info}\n\n{collaboration_info}\n\n{history}\n\n{current_message}\n\n{response_format}"
        
        return prompt
    
    def _format_other_agents(self, agents: List[Dict[str, Any]]) -> str:
        """格式化其他代理信息"""
        if not agents:
            return "无其他代理"
        
        formatted = []
        for agent in agents:
            if agent.get("agent_id") != self.agent_id:
                formatted.append(f"- {agent.get('name', '未知')} ({agent.get('role', '未知')}): {agent.get('description', '无描述')}")
        
        return "\n".join(formatted) if formatted else "无其他代理"
    
    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """格式化对话历史"""
        if not history:
            return "无对话历史"
        
        formatted = ["对话历史:"]
        for msg in history:
            sender = f"{msg.get('sender_name', '未知')} ({msg.get('sender_role', '未知')})"
            content = msg.get('content', '')
            formatted.append(f"{sender}: {content}")
        
        return "\n".join(formatted)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """解析响应"""
        try:
            # 尝试解析JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果不是有效的JSON，提取内容
            return {
                "content": response_text,
                "thoughts": "无法解析JSON格式的思考",
                "actions": []
            }


class MultiAgentCoordinator:
    """多智能体协作协调器"""
    
    def __init__(self):
        self.logger = logging.getLogger("MultiAgentCoordinator")
        self.agents: Dict[str, Agent] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(self, agent: Agent) -> None:
        """
        注册智能体
        
        Args:
            agent: 智能体对象
        """
        self.agents[agent.agent_id] = agent
        self.logger.info(f"已注册智能体: {agent.name} ({agent.agent_id})")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        获取智能体
        
        Args:
            agent_id: 智能体ID
        
        Returns:
            智能体对象
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有智能体
        
        Returns:
            智能体列表
        """
        return [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "description": agent.description,
                "capabilities": agent.capabilities
            }
            for agent in self.agents.values()
        ]
    
    async def create_collaboration_session(
        self,
        task: str,
        agent_ids: List[str],
        initiator_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建协作会话
        
        Args:
            task: 任务描述
            agent_ids: 参与协作的智能体ID列表
            initiator_id: 发起者ID
            metadata: 元数据
        
        Returns:
            创建的协作会话
        """
        try:
            # 验证所有智能体都已注册
            for agent_id in agent_ids:
                if agent_id not in self.agents:
                    raise ValueError(f"智能体未注册: {agent_id}")
            
            # 创建会话ID
            session_id = f"collab:{uuid.uuid4()}"
            
            # 创建协作会话
            session = {
                "id": session_id,
                "task": task,
                "agent_ids": agent_ids,
                "initiator_id": initiator_id,
                "created_at": datetime.utcnow(),
                "status": "active",
                "messages": [],
                "metadata": metadata or {}
            }
            
            # 保存会话
            self.sessions[session_id] = session
            
            # 创建对话记录
            dialogue = await self._create_dialogue_record(session)
            session["dialogue_id"] = dialogue.id
            
            # 发送任务分配消息
            await self.send_system_message(
                session_id=session_id,
                content=f"任务: {task}",
                metadata={"type": "task_assignment"}
            )
            
            return session
        
        except Exception as e:
            self.logger.error(f"创建协作会话失败: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def send_message(
        self,
        session_id: str,
        sender_id: str,
        content: str,
        target_agent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送消息
        
        Args:
            session_id: 会话ID
            sender_id: 发送者ID
            content: 消息内容
            target_agent_ids: 目标智能体ID列表
            metadata: 元数据
        
        Returns:
            发送结果
        """
        try:
            # 验证会话存在
            session = self.sessions.get(session_id)
            if not session:
                raise ValueError(f"会话不存在: {session_id}")
            
            # 验证发送者是会话成员
            sender_agent = self.agents.get(sender_id)
            if not sender_agent and sender_id != "user" and not sender_id.startswith("system:"):
                raise ValueError(f"发送者不是会话成员: {sender_id}")
            
            # 确定发送者信息
            sender_name = "用户"
            sender_role = "user"
            if sender_agent:
                sender_name = sender_agent.name
                sender_role = sender_agent.role
            elif sender_id.startswith("system:"):
                sender_name = "系统"
                sender_role = "system"
            
            # 创建消息
            message = {
                "id": f"message:{uuid.uuid4()}",
                "session_id": session_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "sender_role": sender_role,
                "content": content,
                "target_agent_ids": target_agent_ids or [],
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # 添加到会话消息列表
            session["messages"].append(message)
            
            # 创建消息记录
            await self._create_message_record(message, session["dialogue_id"])
            
            # 如果有目标智能体，则触发处理
            if target_agent_ids:
                asyncio.create_task(self._process_message_by_agents(message, session, target_agent_ids))
            else:
                # 否则，所有智能体都处理
                asyncio.create_task(self._process_message_by_all_agents(message, session))
            
            return {
                "success": True,
                "message_id": message["id"]
            }
        
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def send_system_message(
        self,
        session_id: str,
        content: str,
        target_agent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送系统消息
        
        Args:
            session_id: 会话ID
            content: 消息内容
            target_agent_ids: 目标智能体ID列表
            metadata: 元数据
        
        Returns:
            发送结果
        """
        return await self.send_message(
            session_id=session_id,
            sender_id="system:coordinator",
            content=content,
            target_agent_ids=target_agent_ids,
            metadata=metadata
        )
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取会话消息
        
        Args:
            session_id: 会话ID
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            消息列表
        """
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        messages = session.get("messages", [])
        # 按时间排序
        messages.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 应用分页
        return messages[offset:offset+limit]
    
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """
        关闭会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            关闭结果
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                raise ValueError(f"会话不存在: {session_id}")
            
            # 更新状态
            session["status"] = "closed"
            session["closed_at"] = datetime.utcnow()
            
            # 发送会话结束通知
            await self.send_system_message(
                session_id=session_id,
                content="协作会话已结束",
                metadata={"type": "session_closed"}
            )
            
            return {
                "success": True,
                "session_id": session_id
            }
        
        except Exception as e:
            self.logger.error(f"关闭会话失败: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def _process_message_by_agents(
        self,
        message: Dict[str, Any],
        session: Dict[str, Any],
        target_agent_ids: List[str]
    ) -> None:
        """处理消息（指定智能体）"""
        for agent_id in target_agent_ids:
            if agent_id in self.agents and agent_id in session["agent_ids"]:
                agent = self.agents[agent_id]
                await self._process_message_by_agent(message, session, agent)
    
    async def _process_message_by_all_agents(
        self,
        message: Dict[str, Any],
        session: Dict[str, Any]
    ) -> None:
        """处理消息（所有智能体）"""
        for agent_id in session["agent_ids"]:
            if agent_id in self.agents and agent_id != message["sender_id"]:
                agent = self.agents[agent_id]
                await self._process_message_by_agent(message, session, agent)
    
    async def _process_message_by_agent(
        self,
        message: Dict[str, Any],
        session: Dict[str, Any],
        agent: Agent
    ) -> None:
        """单个智能体处理消息"""
        try:
            # 构建上下文
            context = self._build_agent_context(session, agent.agent_id)
            
            # 代理处理消息
            response = await agent.process_message(message, context)
            
            # 发送代理响应
            await self.send_message(
                session_id=session["id"],
                sender_id=agent.agent_id,
                content=response["content"],
                metadata={
                    "thoughts": response.get("thoughts", ""),
                    "actions": response.get("actions", [])
                }
            )
            
            # 处理代理的行动
            await self._process_agent_actions(response.get("actions", []), session, agent)
        
        except Exception as e:
            self.logger.error(f"智能体处理消息失败: {str(e)}")
            # 发送错误通知
            await self.send_system_message(
                session_id=session["id"],
                content=f"智能体 {agent.name} 处理消息时发生错误: {str(e)}",
                metadata={"type": "error", "agent_id": agent.agent_id}
            )
    
    def _build_agent_context(self, session: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """构建代理上下文"""
        # 获取会话消息历史
        messages = session.get("messages", [])
        
        # 获取会话中的所有代理
        agents = []
        for aid in session["agent_ids"]:
            if aid in self.agents:
                agent = self.agents[aid]
                agents.append({
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "role": agent.role,
                    "description": agent.description
                })
        
        return {
            "session_id": session["id"],
            "task": session["task"],
            "agents": agents,
            "history": messages[-20:] if len(messages) > 20 else messages,  # 最近20条消息
            "metadata": session.get("metadata", {})
        }
    
    async def _process_agent_actions(
        self,
        actions: List[Dict[str, Any]],
        session: Dict[str, Any],
        agent: Agent
    ) -> None:
        """处理代理的行动"""
        for action in actions:
            action_type = action.get("type", "")
            target = action.get("target", "")
            content = action.get("content", "")
            
            if action_type == "工具调用":
                # 处理工具调用
                await self._handle_tool_call(action, session, agent)
            
            elif action_type == "信息请求":
                # 处理信息请求
                await self._handle_information_request(action, session, agent)
            
            elif action_type == "任务分配":
                # 处理任务分配
                await self._handle_task_assignment(action, session, agent)
    
    async def _handle_tool_call(
        self,
        action: Dict[str, Any],
        session: Dict[str, Any],
        agent: Agent
    ) -> None:
        """处理工具调用"""
        # 实际实现中，这里应该调用工具系统
        # 这里简化为发送系统消息
        await self.send_system_message(
            session_id=session["id"],
            content=f"工具调用结果: {action.get('content', '')}",
            target_agent_ids=[agent.agent_id],
            metadata={"type": "tool_result", "tool": action.get("tool", "")}
        )
    
    async def _handle_information_request(
        self,
        action: Dict[str, Any],
        session: Dict[str, Any],
        agent: Agent
    ) -> None:
        """处理信息请求"""
        target = action.get("target", "")
        content = action.get("content", "")
        
        if target == "all":
            # 向所有代理发送信息请求
            await self.send_message(
                session_id=session["id"],
                sender_id=agent.agent_id,
                content=f"信息请求: {content}",
                metadata={"type": "information_request"}
            )
        elif target in self.agents:
            # 向特定代理发送信息请求
            await self.send_message(
                session_id=session["id"],
                sender_id=agent.agent_id,
                content=f"信息请求: {content}",
                target_agent_ids=[target],
                metadata={"type": "information_request"}
            )
    
    async def _handle_task_assignment(
        self,
        action: Dict[str, Any],
        session: Dict[str, Any],
        agent: Agent
    ) -> None:
        """处理任务分配"""
        target = action.get("target", "")
        content = action.get("content", "")
        
        if target == "all":
            # 向所有代理分配任务
            await self.send_message(
                session_id=session["id"],
                sender_id=agent.agent_id,
                content=f"任务分配: {content}",
                metadata={"type": "task_assignment"}
            )
        elif target in self.agents:
            # 向特定代理分配任务
            await self.send_message(
                session_id=session["id"],
                sender_id=agent.agent_id,
                content=f"任务分配: {content}",
                target_agent_ids=[target],
                metadata={"type": "task_assignment"}
            )
    
    async def _create_dialogue_record(self, session: Dict[str, Any]) -> Dialogue:
        """创建对话记录"""
        # 创建对话对象
        dialogue = Dialogue(
            dialogue_type="multi_agent_collaboration",
            title=f"多智能体协作: {session['task'][:30]}...",
            description=session["task"],
            metadata={
                "collaboration_session_id": session["id"],
                "agent_ids": session["agent_ids"],
                "initiator_id": session.get("initiator_id")
            }
        )
        
        # 保存到数据库
        return await dialogue_repo.create(dialogue)
    
    async def _create_message_record(self, message: Dict[str, Any], dialogue_id: str) -> Message:
        """创建消息记录"""
        # 创建消息对象
        msg = Message(
            dialogue_id=dialogue_id,
            sender_role=message["sender_role"],
            sender_id=message["sender_id"],
            content=message["content"],
            content_type="text",
            metadata={
                "collaboration_message_id": message["id"],
                "sender_name": message.get("sender_name"),
                "target_agent_ids": message.get("target_agent_ids", []),
                **message.get("metadata", {})
            }
        )
        
        # 保存到数据库
        return await message_repo.create(msg)


# 创建全局多智能体协作协调器实例
multi_agent_coordinator = MultiAgentCoordinator()


# 预定义一些常用智能体
def create_default_agents():
    """创建默认智能体"""
    # 研究助手
    research_agent = Agent(
        agent_id="agent:research",
        name="研究助手",
        role="信息收集和分析专家",
        description="专注于收集、验证和分析信息，提供深入的研究结果和数据支持。",
        capabilities=["web_search", "document_analysis", "fact_checking"],
        system_prompt="你是一个专业的研究助手，擅长信息收集、验证和分析。你的回答应该基于事实，提供可靠的信息来源，并进行深入分析。"
    )
    
    # 创意顾问
    creative_agent = Agent(
        agent_id="agent:creative",
        name="创意顾问",
        role="创意和头脑风暴专家",
        description="专注于生成创新想法、解决方案和创意内容，擅长头脑风暴和创意思维。",
        capabilities=["brainstorming", "idea_generation", "creative_writing"],
        system_prompt="你是一个富有创造力的顾问，擅长生成新颖的想法和创意解决方案。你的回答应该展现创新思维，提供多样化的视角和可能性。"
    )
    
    # 逻辑分析师
    logic_agent = Agent(
        agent_id="agent:logic",
        name="逻辑分析师",
        role="逻辑推理和批判性思维专家",
        description="专注于逻辑分析、批判性思维和结构化推理，擅长评估论点和解决复杂问题。",
        capabilities=["logical_analysis", "critical_thinking", "argument_evaluation"],
        system_prompt="你是一个严谨的逻辑分析师，擅长结构化思考和批判性分析。你的回答应该展现清晰的逻辑，指出潜在的谬误，并提供严谨的推理过程。"
    )
    
    # 协调员
    coordinator_agent = Agent(
        agent_id="agent:coordinator",
        name="协调员",
        role="团队协调和项目管理专家",
        description="专注于协调团队合作、管理项目进度和整合不同观点，擅长组织和规划。",
        capabilities=["task_management", "team_coordination", "progress_tracking"],
        system_prompt="你是一个高效的协调员，擅长组织团队合作和管理项目。你的回答应该帮助团队保持专注，明确任务分工，并推动项目向前发展。"
    )
    
    # 注册智能体
    multi_agent_coordinator.register_agent(research_agent)
    multi_agent_coordinator.register_agent(creative_agent)
    multi_agent_coordinator.register_agent(logic_agent)
    multi_agent_coordinator.register_agent(coordinator_agent)


# 初始化默认智能体
create_default_agents()
