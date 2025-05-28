"""
自我反思引擎模块
提供AI自我反思、评估和改进能力
"""
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

from ..models.data_models import Message, Turn, Session, Dialogue
from ..db.repositories import introspection_repo
from .llm_caller import LLMCaller


class IntrospectionEngine:
    """自我反思引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger("IntrospectionEngine")
        self.llm_caller = LLMCaller()
    
    async def start_introspection_session(
        self,
        ai_id: str,
        session_type: str,
        trigger_source: str,
        goal: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        启动自我反思会话
        
        Args:
            ai_id: AI ID
            session_type: 会话类型（performance_review/error_analysis/improvement_planning）
            trigger_source: 触发来源（user_feedback/system_trigger/scheduled）
            goal: 反思目标
            metadata: 元数据
        
        Returns:
            创建的自我反思会话
        """
        try:
            # 创建自我反思会话记录
            introspection_session = {
                "id": f"introspection:{uuid.uuid4()}",
                "ai_id": ai_id,
                "session_type": session_type,
                "trigger_source": trigger_source,
                "goal": goal,
                "started_at": datetime.utcnow(),
                "steps": [],
                "summary": "",
                "metadata": metadata or {}
            }
            
            # 保存到数据库
            created_session = await introspection_repo.create(introspection_session)
            
            # 异步启动反思过程
            asyncio.create_task(self._run_introspection_process(created_session))
            
            return created_session
        
        except Exception as e:
            self.logger.error(f"启动自我反思会话失败: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def _run_introspection_process(self, session: Dict[str, Any]) -> None:
        """
        执行自我反思过程
        
        Args:
            session: 自我反思会话
        """
        try:
            steps = []
            session_type = session["session_type"]
            
            # 步骤1: 收集相关数据
            data_collection = await self._collect_relevant_data(session)
            steps.append({
                "step": "data_collection",
                "timestamp": datetime.utcnow().isoformat(),
                "result": data_collection
            })
            
            # 步骤2: 分析数据
            analysis = await self._analyze_data(session, data_collection)
            steps.append({
                "step": "analysis",
                "timestamp": datetime.utcnow().isoformat(),
                "result": analysis
            })
            
            # 步骤3: 生成见解
            insights = await self._generate_insights(session, analysis)
            steps.append({
                "step": "insights",
                "timestamp": datetime.utcnow().isoformat(),
                "result": insights
            })
            
            # 步骤4: 制定改进计划
            improvement_plan = await self._create_improvement_plan(session, insights)
            steps.append({
                "step": "improvement_plan",
                "timestamp": datetime.utcnow().isoformat(),
                "result": improvement_plan
            })
            
            # 步骤5: 总结反思结果
            summary = await self._summarize_introspection(session, steps)
            
            # 更新会话
            session["steps"] = steps
            session["summary"] = summary
            session["completed_at"] = datetime.utcnow()
            
            # 保存到数据库
            await introspection_repo.update(session)
            
            self.logger.info(f"自我反思会话完成: {session['id']}")
        
        except Exception as e:
            self.logger.error(f"执行自我反思过程失败: {str(e)}")
            # 更新会话状态为失败
            session["metadata"]["error"] = str(e)
            session["completed_at"] = datetime.utcnow()
            await introspection_repo.update(session)
    
    async def _collect_relevant_data(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """收集相关数据"""
        session_type = session["session_type"]
        ai_id = session["ai_id"]
        
        data = {
            "dialogues": [],
            "messages": [],
            "tool_calls": [],
            "performance_metrics": {}
        }
        
        if session_type == "performance_review":
            # 收集最近的对话和消息
            data["dialogues"] = await self._get_recent_dialogues(ai_id, limit=10)
            data["messages"] = await self._get_recent_messages(ai_id, limit=50)
            data["performance_metrics"] = await self._get_performance_metrics(ai_id)
        
        elif session_type == "error_analysis":
            # 收集错误相关的数据
            data["error_events"] = await self._get_error_events(ai_id, limit=20)
            data["failed_tool_calls"] = await self._get_failed_tool_calls(ai_id, limit=20)
        
        elif session_type == "improvement_planning":
            # 收集用于改进计划的数据
            data["user_feedback"] = await self._get_user_feedback(ai_id)
            data["performance_metrics"] = await self._get_performance_metrics(ai_id)
            data["previous_improvements"] = await self._get_previous_improvements(ai_id)
        
        return data
    
    async def _analyze_data(self, session: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据"""
        session_type = session["session_type"]
        
        # 构建分析提示词
        prompt = self._build_analysis_prompt(session_type, data)
        
        # 调用LLM进行分析
        result = await self.llm_caller.call(prompt)
        
        try:
            # 尝试解析JSON结果
            analysis = json.loads(result.get("content", "{}"))
        except json.JSONDecodeError:
            # 如果不是有效的JSON，使用原始内容
            analysis = {
                "raw_analysis": result.get("content", ""),
                "format_error": "无法解析为JSON格式"
            }
        
        return analysis
    
    async def _generate_insights(self, session: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成见解"""
        # 构建见解生成提示词
        prompt = self._build_insights_prompt(session, analysis)
        
        # 调用LLM生成见解
        result = await self.llm_caller.call(prompt)
        
        try:
            # 尝试解析JSON结果
            insights = json.loads(result.get("content", "{}"))
        except json.JSONDecodeError:
            # 如果不是有效的JSON，使用原始内容
            insights = {
                "raw_insights": result.get("content", ""),
                "format_error": "无法解析为JSON格式"
            }
        
        return insights
    
    async def _create_improvement_plan(self, session: Dict[str, Any], insights: Dict[str, Any]) -> Dict[str, Any]:
        """创建改进计划"""
        # 构建改进计划提示词
        prompt = self._build_improvement_plan_prompt(session, insights)
        
        # 调用LLM创建改进计划
        result = await self.llm_caller.call(prompt)
        
        try:
            # 尝试解析JSON结果
            plan = json.loads(result.get("content", "{}"))
        except json.JSONDecodeError:
            # 如果不是有效的JSON，使用原始内容
            plan = {
                "raw_plan": result.get("content", ""),
                "format_error": "无法解析为JSON格式"
            }
        
        return plan
    
    async def _summarize_introspection(self, session: Dict[str, Any], steps: List[Dict[str, Any]]) -> str:
        """总结反思结果"""
        # 构建总结提示词
        prompt = f"""
        请总结以下自我反思会话的结果:
        
        会话类型: {session['session_type']}
        反思目标: {session['goal']}
        
        数据收集结果: {json.dumps(steps[0]['result'], ensure_ascii=False)[:500]}...
        
        分析结果: {json.dumps(steps[1]['result'], ensure_ascii=False)[:500]}...
        
        见解: {json.dumps(steps[2]['result'], ensure_ascii=False)}
        
        改进计划: {json.dumps(steps[3]['result'], ensure_ascii=False)}
        
        请提供一个简洁的总结，包括主要发现、见解和改进方向。
        """
        
        # 调用LLM生成总结
        result = await self.llm_caller.call(prompt)
        
        return result.get("content", "无法生成总结")
    
    def _build_analysis_prompt(self, session_type: str, data: Dict[str, Any]) -> str:
        """构建分析提示词"""
        if session_type == "performance_review":
            return f"""
            请分析以下AI助手的性能数据，并提供详细的性能评估:
            
            对话数据: {json.dumps(data.get('dialogues', []), ensure_ascii=False)[:1000]}...
            
            消息数据: {json.dumps(data.get('messages', []), ensure_ascii=False)[:1000]}...
            
            性能指标: {json.dumps(data.get('performance_metrics', {}), ensure_ascii=False)}
            
            请分析以下几个方面:
            1. 响应质量和相关性
            2. 响应时间和效率
            3. 工具使用的适当性和有效性
            4. 对话流畅性和连贯性
            5. 整体用户体验
            
            请以JSON格式返回分析结果，包含以下字段:
            {{"response_quality": float, "response_relevance": float, "response_time": float, "tool_usage": float, "conversation_flow": float, "overall_score": float, "strengths": [string], "weaknesses": [string], "detailed_analysis": string}}
            """
        
        elif session_type == "error_analysis":
            return f"""
            请分析以下AI助手的错误事件和失败的工具调用，并提供详细的错误分析:
            
            错误事件: {json.dumps(data.get('error_events', []), ensure_ascii=False)}
            
            失败的工具调用: {json.dumps(data.get('failed_tool_calls', []), ensure_ascii=False)}
            
            请分析以下几个方面:
            1. 错误模式和频率
            2. 错误根本原因
            3. 错误影响和严重程度
            4. 可能的解决方案
            
            请以JSON格式返回分析结果，包含以下字段:
            {{"error_patterns": [string], "root_causes": [string], "severity": string, "impact": string, "potential_solutions": [string], "detailed_analysis": string}}
            """
        
        elif session_type == "improvement_planning":
            return f"""
            请分析以下AI助手的用户反馈、性能指标和以往改进，并提供改进方向分析:
            
            用户反馈: {json.dumps(data.get('user_feedback', []), ensure_ascii=False)}
            
            性能指标: {json.dumps(data.get('performance_metrics', {}), ensure_ascii=False)}
            
            以往改进: {json.dumps(data.get('previous_improvements', []), ensure_ascii=False)}
            
            请分析以下几个方面:
            1. 用户满意度和期望
            2. 性能瓶颈和限制
            3. 功能缺口和需求
            4. 改进优先级
            
            请以JSON格式返回分析结果，包含以下字段:
            {{"user_satisfaction": float, "performance_bottlenecks": [string], "feature_gaps": [string], "improvement_priorities": [string], "detailed_analysis": string}}
            """
        
        else:
            return f"""
            请分析以下AI助手的数据，并提供详细分析:
            
            数据: {json.dumps(data, ensure_ascii=False)[:2000]}...
            
            请提供全面的分析，包括优势、劣势和改进机会。
            
            请以JSON格式返回分析结果，包含以下字段:
            {{"strengths": [string], "weaknesses": [string], "opportunities": [string], "detailed_analysis": string}}
            """
    
    def _build_insights_prompt(self, session: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """构建见解生成提示词"""
        return f"""
        基于以下分析结果，请生成关于AI助手性能和能力的深入见解:
        
        反思目标: {session['goal']}
        
        分析结果: {json.dumps(analysis, ensure_ascii=False)}
        
        请提供以下几个方面的见解:
        1. 核心优势和差异化能力
        2. 关键改进领域
        3. 用户体验影响因素
        4. 长期发展方向
        
        请以JSON格式返回见解，包含以下字段:
        {{"core_strengths": [string], "improvement_areas": [string], "user_experience_factors": [string], "long_term_directions": [string], "key_insights": string}}
        """
    
    def _build_improvement_plan_prompt(self, session: Dict[str, Any], insights: Dict[str, Any]) -> str:
        """构建改进计划提示词"""
        return f"""
        基于以下见解，请为AI助手制定具体的改进计划:
        
        反思目标: {session['goal']}
        
        见解: {json.dumps(insights, ensure_ascii=False)}
        
        请提供以下几个方面的改进计划:
        1. 短期行动项目（1-2周内可实施）
        2. 中期改进目标（1-2个月）
        3. 长期发展方向（3-6个月）
        4. 关键性能指标和目标
        
        请以JSON格式返回改进计划，包含以下字段:
        {{"short_term_actions": [{{"action": string, "priority": string, "expected_impact": string}}], 
        "medium_term_goals": [string], 
        "long_term_directions": [string], 
        "key_metrics": [{{"metric": string, "current": string, "target": string}}],
        "implementation_notes": string}}
        """
    
    async def _get_recent_dialogues(self, ai_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的对话"""
        # 实际实现中应该从数据库查询
        # 这里返回模拟数据
        return [{"id": f"dialogue:{i}", "ai_id": ai_id, "created_at": datetime.utcnow().isoformat()} for i in range(limit)]
    
    async def _get_recent_messages(self, ai_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的消息"""
        # 实际实现中应该从数据库查询
        # 这里返回模拟数据
        return [{"id": f"message:{i}", "sender_id": ai_id if i % 2 == 0 else "user:1", "content": f"消息内容 {i}"} for i in range(limit)]
    
    async def _get_performance_metrics(self, ai_id: str) -> Dict[str, Any]:
        """获取性能指标"""
        # 实际实现中应该从监控系统获取
        # 这里返回模拟数据
        return {
            "average_response_time": 1.5,  # 秒
            "message_count": 1000,
            "dialogue_count": 200,
            "tool_usage_rate": 0.3,  # 30%的消息使用了工具
            "error_rate": 0.05,  # 5%的消息出现错误
            "user_satisfaction": 4.2  # 5分制
        }
    
    async def _get_error_events(self, ai_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取错误事件"""
        # 实际实现中应该从日志系统获取
        # 这里返回模拟数据
        return [{"id": f"error:{i}", "ai_id": ai_id, "error_type": "tool_call_error", "message": f"工具调用失败: {i}"} for i in range(limit)]
    
    async def _get_failed_tool_calls(self, ai_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取失败的工具调用"""
        # 实际实现中应该从数据库查询
        # 这里返回模拟数据
        return [{"id": f"tool_call:{i}", "tool_id": f"tool:{i%5}", "error": f"参数错误: {i}"} for i in range(limit)]
    
    async def _get_user_feedback(self, ai_id: str) -> List[Dict[str, Any]]:
        """获取用户反馈"""
        # 实际实现中应该从反馈系统获取
        # 这里返回模拟数据
        return [
            {"rating": 4, "comment": "回答很有帮助，但有时候响应较慢"},
            {"rating": 5, "comment": "非常满意，工具使用得很恰当"},
            {"rating": 3, "comment": "有时候回答不够准确，需要多次提问"}
        ]
    
    async def _get_previous_improvements(self, ai_id: str) -> List[Dict[str, Any]]:
        """获取以往的改进"""
        # 实际实现中应该从数据库查询
        # 这里返回模拟数据
        return [
            {"date": "2025-04-01", "area": "响应速度", "action": "优化上下文处理逻辑", "result": "响应时间减少20%"},
            {"date": "2025-03-15", "area": "工具使用", "action": "改进工具选择算法", "result": "工具使用准确率提高15%"}
        ]


# 创建全局自我反思引擎实例
introspection_engine = IntrospectionEngine()
