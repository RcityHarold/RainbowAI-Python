"""
LLM调用器（LLMCaller）
执行大模型API调用，支持链式推理、多轮生成
"""
from typing import Dict, Any, List, Optional, Union, Callable, AsyncGenerator
import json
import logging
from datetime import datetime
import asyncio
import uuid

from .llm_clients import get_llm_client


class LLMCaller:
    """
    LLM调用器
    负责执行大模型API调用，支持链式推理、多轮生成
    """
    
    def __init__(self, client=None):
        """
        初始LLM调用器
        
        Args:
            client: LLM客户端，如果为None则使用配置的LLM客户端
        """
        self.client = client or get_llm_client()
        self.logger = logging.getLogger("LLMCaller")
        self.default_params = {
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.95,
        }
    
    async def call(
        self,
        prompt: str,
        params: Dict[str, Any] = None,
        callback: Callable = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用LLM生成响应
        
        Args:
            prompt: 提示词
            params: 调用参数
            callback: 回调函数，用于处理响应
            stream: 是否使用流式响应
        
        Returns:
            LLM响应
        """
        # 合并默认参数和自定义参数
        call_params = {**self.default_params}
        if params:
            call_params.update(params)
        
        # 记录调用信息
        self.logger.info(f"Calling LLM with prompt length: {len(prompt)}")
        self.logger.debug(f"Prompt: {prompt[:200]}...")
        
        try:
            # 如果要求流式响应，使用流式生成
            if stream:
                # 收集所有流式响应并合并
                full_content = ""
                async for chunk in self.client.generate_stream(prompt, **call_params):
                    chunk_content = chunk.get("content", "")
                    full_content += chunk_content
                    
                    # 如果有回调函数，执行回调
                    if callback:
                        callback(chunk, full_content)
                
                # 构造完整响应
                response = {
                    "content": full_content,
                    "created": datetime.utcnow().isoformat(),
                    "id": str(uuid.uuid4())
                }
            else:
                # 正常调用LLM
                response = await self.client.generate(prompt, **call_params)
            
            # 记录响应
            self.logger.info(f"Received response with length: {len(response.get('content', ''))}")
            
            # 如果有回调函数且不是流式模式，执行回调
            if callback and not stream:
                callback(response)
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error calling LLM: {str(e)}")
            # 返回错误响应
            return {
                "error": str(e),
                "content": "抱歉，我在处理您的请求时遇到了问题。请稍后再试。",
                "created": datetime.utcnow().isoformat()
            }
    
    async def chain_of_thought(
        self,
        initial_prompt: str,
        max_steps: int = 3,
        thought_detector: Callable = None,
        final_answer_detector: Callable = None
    ) -> Dict[str, Any]:
        """
        执行思维链推理
        
        Args:
            initial_prompt: 初始提示词
            max_steps: 最大推理步数
            thought_detector: 思考检测函数，用于判断是否需要继续推理
            final_answer_detector: 最终答案检测函数，用于判断是否已得到最终答案
        
        Returns:
            最终响应
        """
        # 默认检测器
        if thought_detector is None:
            thought_detector = lambda resp: "我需要思考" in resp.get("content", "")
        
        if final_answer_detector is None:
            final_answer_detector = lambda resp: "最终答案" in resp.get("content", "")
        
        # 初始化推理链
        chain = []
        current_prompt = initial_prompt
        
        # 执行推理
        for step in range(max_steps):
            self.logger.info(f"Chain of thought step {step+1}/{max_steps}")
            
            # 调用LLM
            response = await self.call(current_prompt)
            chain.append(response)
            
            # 检查是否已得到最终答案
            if final_answer_detector(response):
                self.logger.info("Final answer detected, stopping chain")
                break
            
            # 检查是否需要继续推理
            if not thought_detector(response):
                self.logger.info("No further thought needed, stopping chain")
                break
            
            # 更新提示词，加入上一步的思考
            current_prompt = f"{current_prompt}\n\n思考过程: {response.get('content', '')}\n\n请继续推理，得出最终答案。"
        
        # 返回最终响应和完整推理链
        return {
            "final_response": chain[-1],
            "chain": chain,
            "steps": len(chain)
        }
    
    async def tool_augmented_generation(
        self,
        initial_prompt: str,
        tool_executor: Callable,
        tool_detection_keywords: List[str] = None,
        max_tool_calls: int = 3
    ) -> Dict[str, Any]:
        """
        工具增强生成
        
        Args:
            initial_prompt: 初始提示词
            tool_executor: 工具执行函数，接收工具调用请求，返回工具调用结果
            tool_detection_keywords: 工具调用检测关键词
            max_tool_calls: 最大工具调用次数
        
        Returns:
            最终响应和工具调用记录
        """
        if tool_detection_keywords is None:
            tool_detection_keywords = ["我需要使用工具", "调用工具", "使用API"]
        
        # 初始化
        tool_calls = []
        current_prompt = initial_prompt
        
        # 执行生成
        for step in range(max_tool_calls + 1):
            self.logger.info(f"Tool augmented generation step {step}/{max_tool_calls}")
            
            # 调用LLM
            response = await self.call(current_prompt)
            content = response.get("content", "")
            
            # 检查是否需要调用工具
            needs_tool = any(keyword in content for keyword in tool_detection_keywords)
            
            if not needs_tool or step == max_tool_calls:
                # 不需要工具或已达到最大调用次数，返回最终响应
                return {
                    "final_response": response,
                    "tool_calls": tool_calls,
                    "steps": step + 1
                }
            
            # 解析工具调用请求
            # 简化实现，实际应该有更复杂的解析逻辑
            tool_request = {
                "tool": content.split("我需要使用")[1].split("工具")[0].strip() if "我需要使用" in content else "unknown",
                "parameters": {}
            }
            
            # 执行工具调用
            tool_result = await tool_executor(tool_request)
            tool_calls.append({
                "request": tool_request,
                "result": tool_result
            })
            
            # 更新提示词，加入工具调用结果
            current_prompt = f"{current_prompt}\n\n工具调用结果: {json.dumps(tool_result, ensure_ascii=False)}\n\n请基于工具调用结果继续回答问题。"
        
        # 不应该到达这里
        return {
            "error": "Exceeded maximum tool calls without final response",
            "tool_calls": tool_calls
        }
    
    async def stream_call(
        self,
        prompt: str,
        params: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式调用LLM生成响应
        
        Args:
            prompt: 提示词
            params: 调用参数
        
        Yields:
            LLM响应块
        """
        # 合并默认参数和自定义参数
        call_params = {**self.default_params}
        if params:
            call_params.update(params)
        
        # 记录调用信息
        self.logger.info(f"Streaming LLM call with prompt length: {len(prompt)}")
        self.logger.debug(f"Prompt: {prompt[:200]}...")
        
        try:
            # 调用LLM流式生成
            async for chunk in self.client.generate_stream(prompt, **call_params):
                yield chunk
        
        except Exception as e:
            self.logger.error(f"Error in stream_call: {str(e)}")
            # 返回错误响应
            yield {
                "error": str(e),
                "content": "抱歉，我在处理您的请求时遇到了问题。请稍后再试。",
                "created": datetime.utcnow().isoformat()
            }
