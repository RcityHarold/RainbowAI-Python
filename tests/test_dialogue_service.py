"""
对话服务测试
"""
import pytest
import asyncio
from typing import Dict, Any

from app.db.database import db
from app.db.repositories import dialogue_repo, session_repo, turn_repo, message_repo
from app.services.dialogue_service import DialogueService, dialogue_service
from app.models.data_models import Message, Dialogue, Session, Turn


@pytest.fixture
async def setup_db():
    """设置测试数据库连接"""
    # 使用内存数据库进行测试
    db.url = "memory"
    await db.connect()
    yield
    # 清理数据库
    await db.disconnect()


@pytest.fixture
def dialogue_service_instance():
    """创建对话服务实例"""
    return DialogueService(
        dialogue_repo=dialogue_repo,
        session_repo=session_repo,
        turn_repo=turn_repo,
        message_repo=message_repo
    )


@pytest.mark.asyncio
async def test_create_dialogue(setup_db, dialogue_service_instance):
    """测试创建对话"""
    # 创建对话
    dialogue = await dialogue_service_instance.create_dialogue(
        dialogue_type="chat",
        human_id="test_human",
        ai_id="test_ai",
        metadata={"test": "metadata"}
    )
    
    # 验证对话
    assert dialogue is not None
    assert dialogue.id is not None
    assert dialogue.dialogue_type == "chat"
    assert dialogue.human_id == "test_human"
    assert dialogue.ai_id == "test_ai"
    assert dialogue.metadata == {"test": "metadata"}
    assert dialogue.status == "active"
    
    # 从数据库获取对话
    db_dialogue = await dialogue_repo.get(dialogue.id)
    assert db_dialogue is not None
    assert db_dialogue.id == dialogue.id


@pytest.mark.asyncio
async def test_create_session(setup_db, dialogue_service_instance):
    """测试创建会话"""
    # 创建对话
    dialogue = await dialogue_service_instance.create_dialogue(
        dialogue_type="chat",
        human_id="test_human"
    )
    
    # 创建会话
    session = await dialogue_service_instance.create_session(
        dialogue_id=dialogue.id,
        session_type="normal",
        metadata={"test": "session"}
    )
    
    # 验证会话
    assert session is not None
    assert session.id is not None
    assert session.dialogue_id == dialogue.id
    assert session.session_type == "normal"
    assert session.metadata == {"test": "session"}
    assert session.status == "active"
    
    # 从数据库获取会话
    db_session = await session_repo.get(session.id)
    assert db_session is not None
    assert db_session.id == session.id


@pytest.mark.asyncio
async def test_create_turn(setup_db, dialogue_service_instance):
    """测试创建轮次"""
    # 创建对话和会话
    dialogue = await dialogue_service_instance.create_dialogue(dialogue_type="chat")
    session = await dialogue_service_instance.create_session(dialogue_id=dialogue.id)
    
    # 创建轮次
    turn = await dialogue_service_instance.create_turn(
        session_id=session.id,
        turn_index=1,
        metadata={"test": "turn"}
    )
    
    # 验证轮次
    assert turn is not None
    assert turn.id is not None
    assert turn.session_id == session.id
    assert turn.turn_index == 1
    assert turn.metadata == {"test": "turn"}
    
    # 从数据库获取轮次
    db_turn = await turn_repo.get(turn.id)
    assert db_turn is not None
    assert db_turn.id == turn.id


@pytest.mark.asyncio
async def test_process_message(setup_db, dialogue_service_instance, monkeypatch):
    """测试处理消息"""
    # 模拟对话核心处理
    async def mock_process_message(*args, **kwargs):
        # 创建响应消息
        response_message = Message(
            content="这是一个测试响应",
            role="assistant",
            content_type="text"
        )
        
        # 返回处理结果
        return {
            "dialogue": kwargs.get("dialogue") or Dialogue(dialogue_type="chat"),
            "session": kwargs.get("session") or Session(dialogue_id="test_dialogue"),
            "turn": kwargs.get("turn") or Turn(session_id="test_session"),
            "response_message": response_message
        }
    
    # 应用模拟
    from app.core.dialogue_core import dialogue_core
    monkeypatch.setattr(dialogue_core, "process_message", mock_process_message)
    
    # 创建输入消息
    input_message = Message(
        content="这是一个测试消息",
        role="user",
        content_type="text"
    )
    
    # 处理消息
    result = await dialogue_service_instance.process_message(input_message)
    
    # 验证结果
    assert result is not None
    assert "dialogue" in result
    assert "session" in result
    assert "turn" in result
    assert "response_message" in result
    assert result["response_message"].content == "这是一个测试响应"
    assert result["response_message"].role == "assistant"


@pytest.mark.asyncio
async def test_get_dialogue_history(setup_db, dialogue_service_instance):
    """测试获取对话历史"""
    # 创建对话和会话
    dialogue = await dialogue_service_instance.create_dialogue(dialogue_type="chat")
    session = await dialogue_service_instance.create_session(dialogue_id=dialogue.id)
    turn = await dialogue_service_instance.create_turn(session_id=session.id)
    
    # 创建消息
    message1 = Message(
        dialogue_id=dialogue.id,
        session_id=session.id,
        turn_id=turn.id,
        content="用户消息",
        role="user",
        content_type="text"
    )
    message2 = Message(
        dialogue_id=dialogue.id,
        session_id=session.id,
        turn_id=turn.id,
        content="AI响应",
        role="assistant",
        content_type="text"
    )
    
    # 保存消息
    await message_repo.create(message1)
    await message_repo.create(message2)
    
    # 获取对话历史
    messages = await dialogue_service_instance.get_dialogue_history(dialogue.id)
    
    # 验证历史
    assert messages is not None
    assert len(messages) == 2
    assert any(m.content == "用户消息" for m in messages)
    assert any(m.content == "AI响应" for m in messages)


@pytest.mark.asyncio
async def test_close_dialogue(setup_db, dialogue_service_instance):
    """测试关闭对话"""
    # 创建对话
    dialogue = await dialogue_service_instance.create_dialogue(dialogue_type="chat")
    
    # 关闭对话
    success = await dialogue_service_instance.close_dialogue(dialogue.id)
    
    # 验证关闭结果
    assert success is True
    
    # 获取对话并验证状态
    closed_dialogue = await dialogue_repo.get(dialogue.id)
    assert closed_dialogue is not None
    assert closed_dialogue.status == "closed"
