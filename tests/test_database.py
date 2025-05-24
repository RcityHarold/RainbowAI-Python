"""
数据库和存储库测试
"""
import pytest
import asyncio
from typing import Dict, Any, List

from app.db.database import Database, db
from app.db.repositories import (
    BaseRepository,
    MessageRepository,
    TurnRepository,
    SessionRepository,
    DialogueRepository,
    message_repo,
    turn_repo,
    session_repo,
    dialogue_repo
)
from app.models.data_models import Message, Turn, Session, Dialogue


@pytest.fixture
async def setup_db():
    """设置测试数据库连接"""
    # 使用内存数据库进行测试
    test_db = Database(url="memory")
    await test_db.connect()
    yield test_db
    # 清理数据库
    await test_db.disconnect()


@pytest.mark.asyncio
async def test_database_connection():
    """测试数据库连接"""
    # 使用内存数据库
    test_db = Database(url="memory")
    
    # 连接数据库
    connected = await test_db.connect()
    assert connected is True
    
    # 断开连接
    await test_db.disconnect()


@pytest.mark.asyncio
async def test_database_operations(setup_db):
    """测试数据库基本操作"""
    test_db = setup_db
    
    # 创建记录
    test_data = {"name": "test", "value": 123}
    result = await test_db.create("test", test_data)
    assert result is not None
    assert "id" in result
    
    # 获取记录
    record_id = result["id"]
    record = await test_db.select("test", record_id)
    assert record is not None
    assert record["name"] == "test"
    assert record["value"] == 123
    
    # 更新记录
    update_data = {"name": "updated", "value": 456}
    updated = await test_db.update("test", record_id, update_data)
    assert updated is True
    
    # 验证更新
    updated_record = await test_db.select("test", record_id)
    assert updated_record is not None
    assert updated_record["name"] == "updated"
    assert updated_record["value"] == 456
    
    # 删除记录
    deleted = await test_db.delete("test", record_id)
    assert deleted is True
    
    # 验证删除
    deleted_record = await test_db.select("test", record_id)
    assert deleted_record is None


@pytest.mark.asyncio
async def test_message_repository(setup_db):
    """测试消息存储库"""
    # 创建存储库
    repo = MessageRepository(setup_db)
    
    # 创建消息
    message = Message(
        content="测试消息",
        role="user",
        content_type="text",
        dialogue_id="test_dialogue",
        session_id="test_session",
        turn_id="test_turn"
    )
    
    # 保存消息
    created_message = await repo.create(message)
    assert created_message is not None
    assert created_message.id is not None
    assert created_message.content == "测试消息"
    
    # 获取消息
    retrieved_message = await repo.get(created_message.id)
    assert retrieved_message is not None
    assert retrieved_message.id == created_message.id
    assert retrieved_message.content == "测试消息"
    
    # 更新消息
    created_message.content = "更新的消息"
    updated = await repo.update(created_message)
    assert updated is True
    
    # 验证更新
    updated_message = await repo.get(created_message.id)
    assert updated_message is not None
    assert updated_message.content == "更新的消息"
    
    # 获取会话消息
    session_messages = await repo.get_by_session("test_session")
    assert len(session_messages) == 1
    assert session_messages[0].id == created_message.id
    
    # 获取轮次消息
    turn_messages = await repo.get_by_turn("test_turn")
    assert len(turn_messages) == 1
    assert turn_messages[0].id == created_message.id
    
    # 删除消息
    deleted = await repo.delete(created_message.id)
    assert deleted is True
    
    # 验证删除
    deleted_message = await repo.get(created_message.id)
    assert deleted_message is None


@pytest.mark.asyncio
async def test_turn_repository(setup_db):
    """测试轮次存储库"""
    # 创建存储库
    repo = TurnRepository(setup_db)
    
    # 创建轮次
    turn = Turn(
        session_id="test_session",
        turn_index=1,
        metadata={"test": "metadata"}
    )
    
    # 保存轮次
    created_turn = await repo.create(turn)
    assert created_turn is not None
    assert created_turn.id is not None
    assert created_turn.session_id == "test_session"
    assert created_turn.turn_index == 1
    
    # 获取轮次
    retrieved_turn = await repo.get(created_turn.id)
    assert retrieved_turn is not None
    assert retrieved_turn.id == created_turn.id
    assert retrieved_turn.session_id == "test_session"
    
    # 更新轮次
    created_turn.metadata = {"updated": "metadata"}
    updated = await repo.update(created_turn)
    assert updated is True
    
    # 验证更新
    updated_turn = await repo.get(created_turn.id)
    assert updated_turn is not None
    assert updated_turn.metadata == {"updated": "metadata"}
    
    # 获取会话轮次
    session_turns = await repo.get_by_session("test_session")
    assert len(session_turns) == 1
    assert session_turns[0].id == created_turn.id
    
    # 删除轮次
    deleted = await repo.delete(created_turn.id)
    assert deleted is True
    
    # 验证删除
    deleted_turn = await repo.get(created_turn.id)
    assert deleted_turn is None


@pytest.mark.asyncio
async def test_session_repository(setup_db):
    """测试会话存储库"""
    # 创建存储库
    repo = SessionRepository(setup_db)
    
    # 创建会话
    session = Session(
        dialogue_id="test_dialogue",
        session_type="normal",
        status="active",
        metadata={"test": "metadata"}
    )
    
    # 保存会话
    created_session = await repo.create(session)
    assert created_session is not None
    assert created_session.id is not None
    assert created_session.dialogue_id == "test_dialogue"
    assert created_session.session_type == "normal"
    
    # 获取会话
    retrieved_session = await repo.get(created_session.id)
    assert retrieved_session is not None
    assert retrieved_session.id == created_session.id
    assert retrieved_session.dialogue_id == "test_dialogue"
    
    # 更新会话
    created_session.status = "closed"
    updated = await repo.update(created_session)
    assert updated is True
    
    # 验证更新
    updated_session = await repo.get(created_session.id)
    assert updated_session is not None
    assert updated_session.status == "closed"
    
    # 获取对话会话
    dialogue_sessions = await repo.get_by_dialogue("test_dialogue")
    assert len(dialogue_sessions) == 1
    assert dialogue_sessions[0].id == created_session.id
    
    # 删除会话
    deleted = await repo.delete(created_session.id)
    assert deleted is True
    
    # 验证删除
    deleted_session = await repo.get(created_session.id)
    assert deleted_session is None


@pytest.mark.asyncio
async def test_dialogue_repository(setup_db):
    """测试对话存储库"""
    # 创建存储库
    repo = DialogueRepository(setup_db)
    
    # 创建对话
    dialogue = Dialogue(
        dialogue_type="chat",
        human_id="test_human",
        ai_id="test_ai",
        status="active",
        metadata={"test": "metadata"}
    )
    
    # 保存对话
    created_dialogue = await repo.create(dialogue)
    assert created_dialogue is not None
    assert created_dialogue.id is not None
    assert created_dialogue.dialogue_type == "chat"
    assert created_dialogue.human_id == "test_human"
    assert created_dialogue.ai_id == "test_ai"
    
    # 获取对话
    retrieved_dialogue = await repo.get(created_dialogue.id)
    assert retrieved_dialogue is not None
    assert retrieved_dialogue.id == created_dialogue.id
    assert retrieved_dialogue.dialogue_type == "chat"
    
    # 更新对话
    created_dialogue.status = "closed"
    updated = await repo.update(created_dialogue)
    assert updated is True
    
    # 验证更新
    updated_dialogue = await repo.get(created_dialogue.id)
    assert updated_dialogue is not None
    assert updated_dialogue.status == "closed"
    
    # 获取用户对话
    human_dialogues = await repo.get_by_human("test_human")
    assert len(human_dialogues) == 1
    assert human_dialogues[0].id == created_dialogue.id
    
    # 获取AI对话
    ai_dialogues = await repo.get_by_ai("test_ai")
    assert len(ai_dialogues) == 1
    assert ai_dialogues[0].id == created_dialogue.id
    
    # 删除对话
    deleted = await repo.delete(created_dialogue.id)
    assert deleted is True
    
    # 验证删除
    deleted_dialogue = await repo.get(created_dialogue.id)
    assert deleted_dialogue is None
