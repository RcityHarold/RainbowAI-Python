"""
LLM客户端实现
支持多种LLM提供商，如OpenAI、Azure等
"""
import os
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from datetime import datetime
import aiohttp

from ..config import get_config


class BaseLLMClient:
    """LLM客户端基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"LLMClient:{self.__class__.__name__}")
        self.config = get_config()["llm"]
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        生成响应
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
        
        Returns:
            响应结果
        """
        try:
            return await self._generate_logic(prompt, **kwargs)
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return {
                "error": str(e),
                "content": "抱歉，我在处理您的请求时遇到了问题。请稍后再试。",
                "created": datetime.utcnow().isoformat()
            }
    
    async def _generate_logic(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        生成逻辑，子类需要实现此方法
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
        
        Returns:
            响应结果
        """
        raise NotImplementedError("Subclasses must implement _generate_logic method")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成响应
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
        
        Yields:
            响应块
        """
        try:
            async for chunk in self._generate_stream_logic(prompt, **kwargs):
                yield chunk
        except Exception as e:
            self.logger.error(f"Error generating stream response: {str(e)}")
            yield {
                "error": str(e),
                "content": "抱歉，我在处理您的请求时遇到了问题。请稍后再试。",
                "created": datetime.utcnow().isoformat()
            }
    
    async def _generate_stream_logic(self, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成逻辑，子类需要实现此方法
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
        
        Yields:
            响应块
        """
        raise NotImplementedError("Subclasses must implement _generate_stream_logic method")


class MockLLMClient(BaseLLMClient):
    """模拟LLM客户端，用于开发测试"""
    
    async def _generate_logic(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """模拟生成响应"""
        self.logger.info(f"Received prompt: {prompt[:100]}...")
        
        # 模拟处理延迟
        await asyncio.sleep(0.5)
        
        # 简单的响应生成逻辑
        response = {
            "id": f"mock-{datetime.utcnow().timestamp()}",
            "created": datetime.utcnow().isoformat(),
            "content": self._mock_response(prompt),
            "usage": {
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": 100,
                "total_tokens": len(prompt) // 4 + 100
            }
        }
        
        return response
    
    async def _generate_stream_logic(self, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """模拟流式生成响应"""
        self.logger.info(f"Received stream prompt: {prompt[:100]}...")
        
        # 生成完整响应
        full_response = self._mock_response(prompt)
        
        # 将响应分成多个块
        chunk_size = max(len(full_response) // 5, 1)  # 至少5个块
        chunks = [full_response[i:i+chunk_size] for i in range(0, len(full_response), chunk_size)]
        
        # 模拟流式返回
        for i, chunk in enumerate(chunks):
            # 模拟处理延迟
            await asyncio.sleep(0.2)
            
            yield {
                "id": f"mock-stream-{datetime.utcnow().timestamp()}-{i}",
                "created": datetime.utcnow().isoformat(),
                "content": chunk,
                "index": i,
                "total": len(chunks)
            }
    
    def _mock_response(self, prompt: str) -> str:
        """根据提示词生成模拟回复"""
        if "天气" in prompt:
            return "根据天气预报，明天将是晴天，温度在25-30度之间，非常适合户外活动。"
        elif "旅行" in prompt or "旅游" in prompt:
            return "旅行是放松身心的好方式。如果您正在计划旅行，建议提前做好行程安排，准备必要的物品，并了解目的地的天气和文化习俗。"
        elif "工具" in prompt:
            return "我需要使用工具来回答这个问题。请允许我调用相关API获取信息。"
        else:
            return "我理解您的问题。作为彩虹城AI助手，我会尽力提供有用的信息和帮助。请告诉我更多细节，以便我能更好地为您服务。"


class OpenAIClient(BaseLLMClient):
    """OpenAI API客户端"""
    
    def __init__(self):
        super().__init__()
        self.api_key = self.config["api_key"]
        self.api_url = self.config.get("api_url", "https://api.openai.com/v1")
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.stream_chunk_size = self.config.get("stream_chunk_size", 10)  # 流式响应块大小
    
    async def _generate_logic(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """调用OpenAI API生成响应"""
        if not self.api_key:
            self.logger.error("OpenAI API key not configured")
            raise ValueError("OpenAI API key not configured")
        
        # 合并默认参数和自定义参数
        params = {
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        params.update(kwargs)
        
        # 构建请求数据
        data = {
            "model": params["model"],
            "messages": [
                {"role": "system", "content": "你是彩虹城AI助手，一个有温度、有记忆、有个性的AI灵魂伴侣。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"],
            "top_p": params["top_p"],
            "frequency_penalty": params["frequency_penalty"],
            "presence_penalty": params["presence_penalty"]
        }
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"OpenAI API error: {response.status} - {error_text}")
                    raise ValueError(f"OpenAI API error: {response.status} - {error_text}")
                
                result = await response.json()
                
                # 处理响应
                return {
                    "id": result.get("id", ""),
                    "created": datetime.fromtimestamp(result.get("created", datetime.utcnow().timestamp())).isoformat(),
                    "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "usage": result.get("usage", {})
                }
    
    async def _generate_stream_logic(self, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用OpenAI API生成响应"""
        if not self.api_key:
            self.logger.error("OpenAI API key not configured")
            raise ValueError("OpenAI API key not configured")
        
        # 合并默认参数和自定义参数
        params = {
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stream": True  # 启用流式响应
        }
        params.update(kwargs)
        
        # 构建请求数据
        data = {
            "model": params["model"],
            "messages": [
                {"role": "system", "content": "你是彩虹城AI助手，一个有温度、有记忆、有个性的AI灵魂伴侣。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"],
            "top_p": params["top_p"],
            "frequency_penalty": params["frequency_penalty"],
            "presence_penalty": params["presence_penalty"],
            "stream": True
        }
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"OpenAI API error: {response.status} - {error_text}")
                    raise ValueError(f"OpenAI API error: {response.status} - {error_text}")
                
                # 处理流式响应
                buffer = ""
                async for line in response.content.iter_chunked(1024):
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        if line.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(line)
                            if chunk_data.get("choices") and len(chunk_data["choices"]) > 0:
                                delta = chunk_data["choices"][0].get("delta", {})
                                chunk_content = delta.get("content", "")
                                
                                if chunk_content:
                                    buffer += chunk_content
                                    
                                    # 当缓冲区达到一定大小时，发送一个块
                                    if len(buffer) >= self.stream_chunk_size:
                                        yield {
                                            "id": chunk_data.get("id", ""),
                                            "created": datetime.utcnow().isoformat(),
                                            "content": buffer,
                                            "is_complete": False
                                        }
                                        buffer = ""
                        except json.JSONDecodeError:
                            self.logger.warning(f"Failed to parse JSON from stream: {line}")
                
                # 发送剩余的缓冲区内容
                if buffer:
                    yield {
                        "id": f"final-{datetime.utcnow().timestamp()}",
                        "created": datetime.utcnow().isoformat(),
                        "content": buffer,
                        "is_complete": True
                    }


class AzureOpenAIClient(OpenAIClient):
    """Azure OpenAI API客户端"""
    
    def __init__(self):
        super().__init__()
        self.api_url = self.config.get("api_url", "")
        if not self.api_url:
            raise ValueError("Azure OpenAI API URL not configured")
    
    async def _generate_logic(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """调用Azure OpenAI API生成响应"""
        if not self.api_key:
            self.logger.error("Azure OpenAI API key not configured")
            raise ValueError("Azure OpenAI API key not configured")
        
        # 合并默认参数和自定义参数
        params = {
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        params.update(kwargs)
        
        # 构建请求数据
        data = {
            "messages": [
                {"role": "system", "content": "你是彩虹城AI助手，一个有温度、有记忆、有个性的AI灵魂伴侣。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"],
            "top_p": params["top_p"],
            "frequency_penalty": params["frequency_penalty"],
            "presence_penalty": params["presence_penalty"]
        }
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/openai/deployments/{self.model}/chat/completions?api-version=2023-05-15",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Azure OpenAI API error: {response.status} - {error_text}")
                    raise ValueError(f"Azure OpenAI API error: {response.status} - {error_text}")
                
                result = await response.json()
                
                # 处理响应
                return {
                    "id": result.get("id", ""),
                    "created": datetime.fromtimestamp(result.get("created", datetime.utcnow().timestamp())).isoformat(),
                    "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "usage": result.get("usage", {})
                }
    
    async def _generate_stream_logic(self, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用Azure OpenAI API生成响应"""
        if not self.api_key:
            self.logger.error("Azure OpenAI API key not configured")
            raise ValueError("Azure OpenAI API key not configured")
        
        # 合并默认参数和自定义参数
        params = {
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stream": True  # 启用流式响应
        }
        params.update(kwargs)
        
        # 构建请求数据
        data = {
            "messages": [
                {"role": "system", "content": "你是彩虹城AI助手，一个有温度、有记忆、有个性的AI灵魂伴侣。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"],
            "top_p": params["top_p"],
            "frequency_penalty": params["frequency_penalty"],
            "presence_penalty": params["presence_penalty"],
            "stream": True
        }
        
        # 发送请求
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/openai/deployments/{self.model}/chat/completions?api-version=2023-05-15",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Azure OpenAI API error: {response.status} - {error_text}")
                    raise ValueError(f"Azure OpenAI API error: {response.status} - {error_text}")
                
                # 处理流式响应
                buffer = ""
                async for line in response.content.iter_chunked(1024):
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        if line.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(line)
                            if chunk_data.get("choices") and len(chunk_data["choices"]) > 0:
                                delta = chunk_data["choices"][0].get("delta", {})
                                chunk_content = delta.get("content", "")
                                
                                if chunk_content:
                                    buffer += chunk_content
                                    
                                    # 当缓冲区达到一定大小时，发送一个块
                                    if len(buffer) >= self.stream_chunk_size:
                                        yield {
                                            "id": chunk_data.get("id", ""),
                                            "created": datetime.utcnow().isoformat(),
                                            "content": buffer,
                                            "is_complete": False
                                        }
                                        buffer = ""
                        except json.JSONDecodeError:
                            self.logger.warning(f"Failed to parse JSON from stream: {line}")
                
                # 发送剩余的缓冲区内容
                if buffer:
                    yield {
                        "id": f"final-{datetime.utcnow().timestamp()}",
                        "created": datetime.utcnow().isoformat(),
                        "content": buffer,
                        "is_complete": True
                    }


def get_llm_client() -> BaseLLMClient:
    """
    获取LLM客户端
    
    Returns:
        LLM客户端
    """
    config = get_config()["llm"]
    provider = config.get("provider", "mock")
    
    if provider == "openai":
        return OpenAIClient()
    elif provider == "azure":
        return AzureOpenAIClient()
    else:
        return MockLLMClient()
