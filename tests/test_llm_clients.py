"""
LLM客户端测试
"""
import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock

from app.core.llm_clients import (
    BaseLLMClient,
    MockLLMClient,
    OpenAILLMClient,
    AzureLLMClient,
    get_llm_client
)


@pytest.fixture
def mock_response():
    """模拟LLM响应"""
    return {
        "id": "test-response-id",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-3.5-turbo",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "这是一个测试响应"
                },
                "finish_reason": "stop",
                "index": 0
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.mark.asyncio
async def test_mock_llm_client():
    """测试模拟LLM客户端"""
    # 创建客户端
    client = MockLLMClient()
    
    # 发送消息
    response = await client.send_message(
        messages=[{"role": "user", "content": "测试消息"}],
        model="gpt-3.5-turbo"
    )
    
    # 验证响应
    assert response is not None
    assert "content" in response
    assert "role" in response
    assert response["role"] == "assistant"
    assert isinstance(response["content"], str)


@pytest.mark.asyncio
async def test_openai_llm_client(mock_response):
    """测试OpenAI LLM客户端"""
    # 模拟aiohttp.ClientSession.post
    with patch("aiohttp.ClientSession.post") as mock_post:
        # 设置模拟响应
        mock_context = MagicMock()
        mock_context.__aenter__.return_value.status = 200
        mock_context.__aenter__.return_value.json = MagicMock(
            return_value=asyncio.Future()
        )
        mock_context.__aenter__.return_value.json.return_value.set_result(mock_response)
        mock_post.return_value = mock_context
        
        # 创建客户端
        client = OpenAILLMClient(api_key="test_key")
        
        # 发送消息
        response = await client.send_message(
            messages=[{"role": "user", "content": "测试消息"}],
            model="gpt-3.5-turbo"
        )
        
        # 验证响应
        assert response is not None
        assert response["role"] == "assistant"
        assert response["content"] == "这是一个测试响应"
        
        # 验证调用
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["url"] == "https://api.openai.com/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer test_key"
        assert json.loads(kwargs["json"]["messages"][0]["content"]) == "测试消息"


@pytest.mark.asyncio
async def test_azure_llm_client(mock_response):
    """测试Azure LLM客户端"""
    # 模拟aiohttp.ClientSession.post
    with patch("aiohttp.ClientSession.post") as mock_post:
        # 设置模拟响应
        mock_context = MagicMock()
        mock_context.__aenter__.return_value.status = 200
        mock_context.__aenter__.return_value.json = MagicMock(
            return_value=asyncio.Future()
        )
        mock_context.__aenter__.return_value.json.return_value.set_result(mock_response)
        mock_post.return_value = mock_context
        
        # 创建客户端
        client = AzureLLMClient(
            api_key="test_key",
            api_url="https://test-azure-endpoint.openai.azure.com"
        )
        
        # 发送消息
        response = await client.send_message(
            messages=[{"role": "user", "content": "测试消息"}],
            model="gpt-3.5-turbo"
        )
        
        # 验证响应
        assert response is not None
        assert response["role"] == "assistant"
        assert response["content"] == "这是一个测试响应"
        
        # 验证调用
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "https://test-azure-endpoint.openai.azure.com" in kwargs["url"]
        assert kwargs["headers"]["api-key"] == "test_key"
        assert json.loads(kwargs["json"]["messages"][0]["content"]) == "测试消息"


def test_get_llm_client():
    """测试获取LLM客户端"""
    # 测试获取模拟客户端
    client = get_llm_client("mock")
    assert isinstance(client, MockLLMClient)
    
    # 测试获取OpenAI客户端
    client = get_llm_client("openai", api_key="test_key")
    assert isinstance(client, OpenAILLMClient)
    
    # 测试获取Azure客户端
    client = get_llm_client("azure", api_key="test_key", api_url="test_url")
    assert isinstance(client, AzureLLMClient)
    
    # 测试获取未知客户端（应返回模拟客户端）
    client = get_llm_client("unknown")
    assert isinstance(client, MockLLMClient)
