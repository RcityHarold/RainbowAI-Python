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
import random

from ..models.data_models import Message, Turn, Session, Dialogue
from ..models.introspection_models import (
    IntrospectionTurn, IntrospectionTurnType, SelfReflectionSession,
    MoodState, MoodShift, IntrospectionReport, MemoryEntry
)
from ..db.repositories.introspection_repo import introspection_repo
from .llm_caller import LLMCaller
from .memory_manager import memory_manager


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
            session_id = f"introspection_session:{uuid.uuid4()}"
            introspection_session = SelfReflectionSession(
                id=session_id,
                ai_id=ai_id,
                session_type=session_type,
                trigger_source=trigger_source,
                goal=goal,
                started_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # 保存到数据库
            session_dict = introspection_session.dict()
            created_session = await introspection_repo["create_session"](session_dict)
            
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
            session_id = session["id"]
            ai_id = session["ai_id"]
            
            # 初始情绪状态设置
            current_mood = MoodState.REFLECTIVE
            
            # 步骤1: 收集相关数据
            data_collection = await self._collect_relevant_data(session)
            steps.append({
                "step": "data_collection",
                "timestamp": datetime.utcnow().isoformat(),
                "result": data_collection
            })
            
            # 创建第一个自省轮次 - 数据收集
            await self._create_introspection_turn(
                session_id=session_id,
                turn_type=IntrospectionTurnType.SELF_ANALYSIS,
                question="收集了哪些数据用于自我反思？",
                response=f"收集了{len(data_collection)}项数据，包括最近对话、性能指标和用户反馈。",
                ai_mood_state=current_mood
            )
            
            # 步骤2: 分析数据
            analysis = await self._analyze_data(session, data_collection)
            steps.append({
                "step": "analysis",
                "timestamp": datetime.utcnow().isoformat(),
                "result": analysis
            })
            
            # 更新情绪状态 - 分析后可能变得更加专注或担忧
            new_mood = random.choice([MoodState.CURIOUS, MoodState.CONCERNED])
            mood_shift = MoodShift(
                from_mood=current_mood,
                to_mood=new_mood,
                reason="数据分析过程中发现了一些需要关注的模式"
            )
            current_mood = new_mood
            
            # 创建第二个自省轮次 - 数据分析
            await self._create_introspection_turn(
                session_id=session_id,
                turn_type=IntrospectionTurnType.PERFORMANCE_REVIEW,
                question="数据分析显示了哪些模式和趋势？",
                response=f"分析显示: {analysis.get('summary', '无摘要')}",
                ai_mood_state=current_mood,
                mood_shift=mood_shift.dict()
            )
            
            # 步骤3: 生成见解
            insights = await self._generate_insights(session, analysis)
            steps.append({
                "step": "insights",
                "timestamp": datetime.utcnow().isoformat(),
                "result": insights
            })
            
            # 更新情绪状态 - 获得见解后可能变得更加自信或不确定
            new_mood = random.choice([MoodState.CONFIDENT, MoodState.UNCERTAIN])
            mood_shift = MoodShift(
                from_mood=current_mood,
                to_mood=new_mood,
                reason="从数据中生成见解，评估自身表现"
            )
            current_mood = new_mood
            
            # 创建第三个自省轮次 - 见解生成
            insight_items = insights.get("key_insights", [])
            insight_text = "\n".join([f"- {item}" for item in insight_items[:3]])
            await self._create_introspection_turn(
                session_id=session_id,
                turn_type=IntrospectionTurnType.KNOWLEDGE_ASSESSMENT,
                question="从数据分析中得出了哪些关键见解？",
                response=f"关键见解:\n{insight_text}",
                ai_mood_state=current_mood,
                mood_shift=mood_shift.dict(),
                insights=insight_items
            )
            
            # 步骤4: 制定改进计划
            improvement_plan = await self._create_improvement_plan(session, insights)
            steps.append({
                "step": "improvement_plan",
                "timestamp": datetime.utcnow().isoformat(),
                "result": improvement_plan
            })
            
            # 更新情绪状态 - 制定计划后变得更加坚定
            new_mood = MoodState.DETERMINED
            mood_shift = MoodShift(
                from_mood=current_mood,
                to_mood=new_mood,
                reason="制定了明确的改进计划，准备采取行动"
            )
            current_mood = new_mood
            
            # 创建第四个自省轮次 - 改进计划
            plan_items = improvement_plan.get("short_term_actions", [])
            plan_text = "\n".join([f"- {item.get('action')}" for item in plan_items[:3]])
            await self._create_introspection_turn(
                session_id=session_id,
                turn_type=IntrospectionTurnType.IMPROVEMENT_PLANNING,
                question="制定了哪些具体的改进计划？",
                response=f"短期行动计划:\n{plan_text}",
                ai_mood_state=current_mood,
                mood_shift=mood_shift.dict()
            )
            
            # 步骤5: 总结反思结果
            summary = await self._summarize_introspection(session, steps)
            
            # 生成自省报告
            report = await self._generate_introspection_report(session, steps, summary, current_mood)
            
            # 生成记忆条目
            memory_entries = await self._generate_memory_entries(session, insights, improvement_plan)
            
            # 更新会话
            session["steps"] = steps
            session["summary"] = summary
            session["report"] = report
            session["memory_entries"] = [entry.get("id") for entry in memory_entries]
            session["completed_at"] = datetime.utcnow()
            
            # 保存到数据库
            await introspection_repo["update_session"](session["id"], session)
            
            self.logger.info(f"自我反思过程完成: {session['id']}")
            
        except Exception as e:
            self.logger.error(f"执行自我反思过程失败: {str(e)}")
            # 更新会话状态为失败
            session["error"] = str(e)
            await introspection_repo["update_session"](session["id"], session)
    
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
        try:
            # 提取各步骤的关键结果
            data_collection = next((s["result"] for s in steps if s["step"] == "data_collection"), {})
            analysis = next((s["result"] for s in steps if s["step"] == "analysis"), {})
            insights = next((s["result"] for s in steps if s["step"] == "insights"), {})
            improvement_plan = next((s["result"] for s in steps if s["step"] == "improvement_plan"), {})
            
            # 构建总结提示词
            prompt = f"""
            请总结以下自我反思过程的结果:
            
            反思目标: {session['goal']}
            数据分析: {json.dumps(analysis.get('summary', {}), ensure_ascii=False)}
            关键见解: {json.dumps(insights.get('key_insights', []), ensure_ascii=False)}
            改进计划: {json.dumps(improvement_plan.get('short_term_actions', []), ensure_ascii=False)}
            
            请提供一个简洁的总结，包括主要发现、见解和改进方向。
            """
            
            # 调用LLM生成总结
            response = await self.llm_caller.call(prompt)
            summary = response.get("content", "")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"总结反思结果失败: {str(e)}")
            return f"总结生成失败: {str(e)}"
    
    async def _create_introspection_turn(self, session_id: str, turn_type: IntrospectionTurnType, 
                                     question: str, response: str, ai_mood_state: MoodState,
                                     mood_shift: Optional[Dict[str, Any]] = None, insights: List[str] = None) -> Dict[str, Any]:
        """创建自省轮次"""
        try:
            turn_id = f"introspection_turn:{uuid.uuid4()}"
            turn = IntrospectionTurn(
                id=turn_id,
                session_id=session_id,
                turn_type=turn_type,
                question=question,
                response=response,
                insights=insights or [],
                ai_mood_state=ai_mood_state,
                mood_shift=mood_shift,
                created_at=datetime.utcnow()
            )
            
            # 保存到数据库
            turn_dict = turn.dict()
            created_turn = await introspection_repo["create_turn"](turn_dict)
            
            return created_turn
            
        except Exception as e:
            self.logger.error(f"创建自省轮次失败: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_introspection_report(self, session: Dict[str, Any], steps: List[Dict[str, Any]], 
                                         summary: str, current_mood: MoodState) -> Dict[str, Any]:
        """生成自省报告"""
        try:
            # 提取各步骤的关键结果
            insights = next((s["result"] for s in steps if s["step"] == "insights"), {})
            improvement_plan = next((s["result"] for s in steps if s["step"] == "improvement_plan"), {})
            analysis = next((s["result"] for s in steps if s["step"] == "analysis"), {})
            
            # 创建报告
            report = IntrospectionReport(
                session_id=session["id"],
                ai_id=session["ai_id"],
                report_type=session["session_type"],
                summary=summary,
                key_insights=insights.get("key_insights", []),
                strengths=insights.get("strengths", []),
                areas_for_improvement=insights.get("areas_for_improvement", []),
                action_items=improvement_plan.get("short_term_actions", []),
                mood_analysis={
                    "final_mood": current_mood.value,
                    "mood_progression": ["reflective", "concerned", "uncertain", "determined"],
                    "emotional_stability": "stable"
                },
                performance_metrics=analysis.get("performance_metrics", {}),
                created_at=datetime.utcnow()
            )
            
            # 保存到数据库
            report_dict = report.dict()
            created_report = await introspection_repo["create_report"](report_dict)
            
            return created_report
            
        except Exception as e:
            self.logger.error(f"生成自省报告失败: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_memory_entries(self, session: Dict[str, Any], insights: Dict[str, Any], 
                                   improvement_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成记忆条目"""
        try:
            memory_entries = []
            ai_id = session["ai_id"]
            
            # 从见解生成记忆
            if "key_insights" in insights:
                for idx, insight in enumerate(insights["key_insights"]):
                    memory_entry = MemoryEntry(
                        id=f"memory_entry:{uuid.uuid4()}",
                        ai_id=ai_id,
                        source_type="introspection",
                        source_id=session["id"],
                        memory_type="insight",
                        content=insight,
                        importance=5 - min(idx, 4),  # 重要性递减
                        tags=["introspection", "insight", session["session_type"]],
                        created_at=datetime.utcnow()
                    )
                    
                    # 保存到数据库
                    entry_dict = memory_entry.dict()
                    created_entry = await introspection_repo["create_memory_entry"](entry_dict)
                    memory_entries.append(created_entry)
            
            # 从改进计划生成记忆
            if "short_term_actions" in improvement_plan:
                for idx, action in enumerate(improvement_plan["short_term_actions"]):
                    memory_entry = MemoryEntry(
                        id=f"memory_entry:{uuid.uuid4()}",
                        ai_id=ai_id,
                        source_type="introspection",
                        source_id=session["id"],
                        memory_type="action_item",
                        content=action.get("action", ""),
                        importance=5 - min(idx, 4),  # 重要性递减
                        tags=["introspection", "action_item", action.get("priority", "medium")],
                        created_at=datetime.utcnow()
                    )
                    
                    # 保存到数据库
                    entry_dict = memory_entry.dict()
                    created_entry = await introspection_repo["create_memory_entry"](entry_dict)
                    memory_entries.append(created_entry)
            
            return memory_entries
            
        except Exception as e:
            self.logger.error(f"生成记忆条目失败: {str(e)}")
            return []


# 创建全局自我反思引擎实例
introspection_engine = IntrospectionEngine()
