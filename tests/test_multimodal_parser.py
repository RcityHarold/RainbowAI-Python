"""
测试多模态输入解析器
"""
import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.multimodal_input_parser import (
    MultiModalInputParser, 
    Message, 
    ContentType
)

async def test_text_parser():
    """测试文本解析器"""
    parser = MultiModalInputParser()
    
    # 创建文本消息
    message = Message(
        message_id="test-message-1",
        dialogue_id="test-dialogue-1",
        turn_id="test-turn-1",
        sender_role="human",
        content_type=ContentType.TEXT.value,
        content="我今天感觉很开心，因为天气很好，我计划去旅行。",
        created_at=datetime.now().isoformat()
    )
    
    # 解析消息
    result = await parser.parse(message)
    
    # 打印结果
    print("\n=== 文本解析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

async def test_image_parser():
    """测试图像解析器"""
    parser = MultiModalInputParser()
    
    # 创建图像消息
    message = Message(
        message_id="test-message-2",
        dialogue_id="test-dialogue-1",
        turn_id="test-turn-1",
        sender_role="human",
        content_type=ContentType.IMAGE.value,
        content="http://example.com/test-image.jpg",
        content_meta={
            "caption": "一张美丽的风景照",
            "width": 800,
            "height": 600,
            "format": "jpg"
        },
        created_at=datetime.now().isoformat()
    )
    
    # 解析消息
    result = await parser.parse(message)
    
    # 打印结果
    print("\n=== 图像解析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

async def test_audio_parser():
    """测试音频解析器"""
    parser = MultiModalInputParser()
    
    # 创建音频消息
    message = Message(
        message_id="test-message-3",
        dialogue_id="test-dialogue-1",
        turn_id="test-turn-1",
        sender_role="human",
        content_type=ContentType.AUDIO.value,
        content="http://example.com/test-audio.mp3",
        content_meta={
            "duration": 120,
            "format": "mp3",
            "transcription": "这是一段测试音频的转录文本，包含了一些情感表达。"
        },
        created_at=datetime.now().isoformat()
    )
    
    # 解析消息
    result = await parser.parse(message)
    
    # 打印结果
    print("\n=== 音频解析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

async def test_tool_output_parser():
    """测试工具输出解析器"""
    parser = MultiModalInputParser()
    
    # 创建工具输出消息
    message = Message(
        message_id="test-message-4",
        dialogue_id="test-dialogue-1",
        turn_id="test-turn-1",
        sender_role="system",
        content_type=ContentType.TOOL_OUTPUT.value,
        content=json.dumps({
            "tool": "weather",
            "result": {
                "city": "北京",
                "temp": 25,
                "condition": "晴朗"
            }
        }),
        created_at=datetime.now().isoformat()
    )
    
    # 解析消息
    result = await parser.parse(message)
    
    # 打印结果
    print("\n=== 工具输出解析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

async def test_mixed_content():
    """测试混合内容解析"""
    parser = MultiModalInputParser()
    
    # 创建多个不同类型的消息
    messages = [
        Message(
            message_id="test-message-5-1",
            dialogue_id="test-dialogue-1",
            turn_id="test-turn-1",
            sender_role="human",
            content_type=ContentType.TEXT.value,
            content="这是我今天拍的照片，天气很好。",
            created_at=datetime.now().isoformat()
        ),
        Message(
            message_id="test-message-5-2",
            dialogue_id="test-dialogue-1",
            turn_id="test-turn-1",
            sender_role="human",
            content_type=ContentType.IMAGE.value,
            content="http://example.com/test-image-2.jpg",
            content_meta={
                "caption": "阳光明媚的公园",
                "width": 1200,
                "height": 800,
                "format": "jpg"
            },
            created_at=datetime.now().isoformat()
        ),
        Message(
            message_id="test-message-5-3",
            dialogue_id="test-dialogue-1",
            turn_id="test-turn-1",
            sender_role="human",
            content_type=ContentType.AUDIO.value,
            content="http://example.com/test-audio-2.mp3",
            content_meta={
                "duration": 30,
                "format": "mp3",
                "transcription": "这是我在公园录制的鸟叫声，非常悦耳。"
            },
            created_at=datetime.now().isoformat()
        )
    ]
    
    # 解析混合内容
    result = await parser.parse_mixed_content(messages)
    
    # 打印结果
    print("\n=== 混合内容解析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

async def test_quote_reply_resolver():
    """测试引用回复解析器"""
    parser = MultiModalInputParser()
    
    # 创建引用回复消息
    message = Message(
        message_id="test-message-6",
        dialogue_id="test-dialogue-1",
        turn_id="test-turn-1",
        sender_role="human",
        content_type=ContentType.QUOTE_REPLY.value,
        content="我同意你的观点",
        content_meta={
            "reply_to": "original-message-id",
            "quoted_content": "我认为这个方案很好",
            "quoted_sender": "ai"
        },
        created_at=datetime.now().isoformat()
    )
    
    # 解析消息
    result = await parser.parse(message)
    
    # 打印结果
    print("\n=== 引用回复解析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

async def test_system_prompt_parser():
    """测试系统提示解析器"""
    parser = MultiModalInputParser()
    
    # 创建系统提示消息
    message = Message(
        message_id="test-message-7",
        dialogue_id="test-dialogue-1",
        turn_id="test-turn-1",
        sender_role="system",
        content_type=ContentType.SYSTEM_PROMPT.value,
        content="请以专业的语气回答用户的问题",
        content_meta={
            "type": "system_instruction",
            "priority": "high"
        },
        created_at=datetime.now().isoformat()
    )
    
    # 解析消息
    result = await parser.parse(message)
    
    # 打印结果
    print("\n=== 系统提示解析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

async def run_all_tests():
    """运行所有测试"""
    print("开始测试多模态输入解析器...")
    
    await test_text_parser()
    await test_image_parser()
    await test_audio_parser()
    await test_tool_output_parser()
    await test_mixed_content()
    await test_quote_reply_resolver()
    await test_system_prompt_parser()
    
    print("\n所有测试完成！")

if __name__ == "__main__":
    # 运行所有测试
    asyncio.run(run_all_tests())
