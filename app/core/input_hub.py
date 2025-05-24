"""
输入监听器（InputHub）
捕捉人类输入（含语音/文本/情绪等）
"""
from typing import Dict, Any, List, Optional, Union, Callable
import logging
import asyncio
import uuid
from datetime import datetime
import json

from ..models.data_models import Message


class InputProcessor:
    """输入处理器基类"""
    def __init__(self, processor_id: str, description: str):
        self.processor_id = processor_id
        self.description = description
        self.logger = logging.getLogger(f"InputProcessor:{processor_id}")
    
    async def process(self, input_data: Any) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            input_data: 输入数据
        
        Returns:
            处理结果
        """
        try:
            return await self._process_logic(input_data)
        except Exception as e:
            self.logger.error(f"Error in processor {self.processor_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processor_id": self.processor_id
            }
    
    async def _process_logic(self, input_data: Any) -> Dict[str, Any]:
        """
        处理逻辑，子类需要实现此方法
        
        Args:
            input_data: 输入数据
        
        Returns:
            处理结果
        """
        raise NotImplementedError("Subclasses must implement _process_logic method")


class TextProcessor(InputProcessor):
    """文本处理器"""
    def __init__(self):
        super().__init__(
            processor_id="text",
            description="处理文本输入"
        )
    
    async def _process_logic(self, input_data: str) -> Dict[str, Any]:
        """
        处理文本输入
        
        Args:
            input_data: 文本内容
        
        Returns:
            处理结果
        """
        # 简单的文本处理，实际项目可能需要更复杂的处理
        return {
            "success": True,
            "content": input_data,
            "content_type": "text",
            "metadata": {
                "length": len(input_data),
                "language": self._detect_language(input_data)
            }
        }
    
    def _detect_language(self, text: str) -> str:
        """
        检测文本语言
        
        Args:
            text: 文本内容
        
        Returns:
            语言代码
        """
        # 简化实现，实际应使用语言检测库
        if any("\u4e00" <= char <= "\u9fff" for char in text):
            return "zh"
        else:
            return "en"


class ImageProcessor(InputProcessor):
    """图像处理器"""
    def __init__(self):
        super().__init__(
            processor_id="image",
            description="处理图像输入"
        )
    
    async def _process_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理图像输入
        
        Args:
            input_data: 图像数据，包含url或base64
        
        Returns:
            处理结果
        """
        # 获取图像URL或base64
        image_url = input_data.get("url")
        image_base64 = input_data.get("base64")
        
        if not image_url and not image_base64:
            raise ValueError("Missing image url or base64 data")
        
        # 简化实现，实际项目应进行图像分析
        return {
            "success": True,
            "content": image_url or "base64_image_data",
            "content_type": "image",
            "metadata": {
                "caption": input_data.get("caption", "图像"),
                "source": "url" if image_url else "base64",
                "tags": input_data.get("tags", [])
            }
        }


class AudioProcessor(InputProcessor):
    """音频处理器"""
    def __init__(self):
        super().__init__(
            processor_id="audio",
            description="处理音频输入"
        )
    
    async def _process_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理音频输入
        
        Args:
            input_data: 音频数据，包含url或base64
        
        Returns:
            处理结果
        """
        # 获取音频URL或base64
        audio_url = input_data.get("url")
        audio_base64 = input_data.get("base64")
        
        if not audio_url and not audio_base64:
            raise ValueError("Missing audio url or base64 data")
        
        # 音频转文字（实际项目应使用语音识别API）
        transcription = input_data.get("transcription", "音频内容")
        
        return {
            "success": True,
            "content": audio_url or "base64_audio_data",
            "content_type": "audio",
            "metadata": {
                "transcription": transcription,
                "duration": input_data.get("duration", 0),
                "source": "url" if audio_url else "base64"
            }
        }


class InputHub:
    """
    输入监听器
    捕捉并处理各类输入
    """
    def __init__(self):
        self.processors: Dict[str, InputProcessor] = {}
        self.logger = logging.getLogger("InputHub")
        
        # 注册默认处理器
        self.register_default_processors()
    
    def register_processor(self, processor: InputProcessor):
        """
        注册输入处理器
        
        Args:
            processor: 处理器实例
        """
        self.processors[processor.processor_id] = processor
        self.logger.info(f"Registered processor: {processor.processor_id}")
    
    def register_default_processors(self):
        """注册默认处理器"""
        self.register_processor(TextProcessor())
        self.register_processor(ImageProcessor())
        self.register_processor(AudioProcessor())
    
    async def process_input(
        self,
        input_type: str,
        input_data: Any,
        user_id: str,
        dialogue_id: Optional[str] = None,
        session_id: Optional[str] = None,
        turn_id: Optional[str] = None
    ) -> Message:
        """
        处理输入
        
        Args:
            input_type: 输入类型
            input_data: 输入数据
            user_id: 用户ID
            dialogue_id: 对话ID
            session_id: 会话ID
            turn_id: 轮次ID
        
        Returns:
            消息对象
        """
        self.logger.info(f"Processing input of type: {input_type}")
        
        # 检查处理器是否存在
        if input_type not in self.processors:
            self.logger.error(f"Processor not found for input type: {input_type}")
            raise ValueError(f"Unsupported input type: {input_type}")
        
        # 获取处理器并处理输入
        processor = self.processors[input_type]
        result = await processor.process(input_data)
        
        if not result.get("success", False):
            self.logger.error(f"Error processing input: {result.get('error')}")
            raise RuntimeError(f"Error processing input: {result.get('error')}")
        
        # 创建消息对象
        message = Message(
            dialogue_id=dialogue_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            turn_id=turn_id or str(uuid.uuid4()),
            sender_role="human",
            sender_id=user_id,
            content=result["content"],
            content_type=result["content_type"],
            metadata=result.get("metadata", {})
        )
        
        self.logger.info(f"Created message: {message.id}")
        return message
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> Message:
        """
        处理Webhook输入
        
        Args:
            webhook_data: Webhook数据
        
        Returns:
            消息对象
        """
        # 解析Webhook数据
        input_type = webhook_data.get("type")
        input_data = webhook_data.get("data")
        user_id = webhook_data.get("user_id")
        dialogue_id = webhook_data.get("dialogue_id")
        session_id = webhook_data.get("session_id")
        turn_id = webhook_data.get("turn_id")
        
        if not input_type or not input_data or not user_id:
            self.logger.error("Missing required webhook data")
            raise ValueError("Missing required webhook data: type, data, user_id")
        
        # 处理输入
        return await self.process_input(
            input_type=input_type,
            input_data=input_data,
            user_id=user_id,
            dialogue_id=dialogue_id,
            session_id=session_id,
            turn_id=turn_id
        )
