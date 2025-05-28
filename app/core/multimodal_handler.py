"""
多模态内容处理模块
用于处理图像、音频等多媒体内容
"""
import os
import base64
import uuid
import magic
import asyncio
from typing import Dict, Any, Optional, List, Tuple, BinaryIO
from pathlib import Path
from io import BytesIO
from PIL import Image
from pydub import AudioSegment

from ..core.logger import logger
from ..config import get_config


class MultimodalHandler:
    """多模态内容处理器"""
    
    def __init__(self):
        self.config = get_config()
        self.media_dir = self.config.get("MEDIA_STORAGE_PATH", "media")
        self.allowed_image_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        self.allowed_audio_types = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/webm"]
        self.allowed_video_types = ["video/mp4", "video/webm", "video/ogg"]
        
        # 确保媒体目录存在
        os.makedirs(self.media_dir, exist_ok=True)
        os.makedirs(os.path.join(self.media_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.media_dir, "audio"), exist_ok=True)
        os.makedirs(os.path.join(self.media_dir, "video"), exist_ok=True)
    
    def get_mime_type(self, file_content: bytes) -> str:
        """
        获取文件MIME类型
        
        Args:
            file_content: 文件内容
        
        Returns:
            MIME类型
        """
        mime = magic.Magic(mime=True)
        return mime.from_buffer(file_content)
    
    def is_valid_media_type(self, mime_type: str) -> bool:
        """
        检查是否为有效的媒体类型
        
        Args:
            mime_type: MIME类型
        
        Returns:
            是否有效
        """
        return (
            mime_type in self.allowed_image_types or
            mime_type in self.allowed_audio_types or
            mime_type in self.allowed_video_types
        )
    
    def get_media_category(self, mime_type: str) -> str:
        """
        获取媒体类别
        
        Args:
            mime_type: MIME类型
        
        Returns:
            媒体类别 (image/audio/video)
        """
        if mime_type in self.allowed_image_types:
            return "image"
        elif mime_type in self.allowed_audio_types:
            return "audio"
        elif mime_type in self.allowed_video_types:
            return "video"
        else:
            return "unknown"
    
    async def process_base64_media(self, base64_data: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        处理Base64编码的媒体数据
        
        Args:
            base64_data: Base64编码的媒体数据
            filename: 文件名（可选）
        
        Returns:
            处理结果
        """
        try:
            # 解码Base64数据
            if "," in base64_data:
                # 处理data URL格式 (e.g., "data:image/jpeg;base64,...")
                _, base64_data = base64_data.split(",", 1)
            
            file_content = base64.b64decode(base64_data)
            
            # 获取MIME类型
            mime_type = self.get_mime_type(file_content)
            
            # 检查媒体类型
            if not self.is_valid_media_type(mime_type):
                return {
                    "success": False,
                    "error": f"不支持的媒体类型: {mime_type}"
                }
            
            # 获取媒体类别
            category = self.get_media_category(mime_type)
            
            # 生成文件名
            if not filename:
                extension = mime_type.split("/")[1]
                filename = f"{uuid.uuid4()}.{extension}"
            
            # 保存文件
            file_path = os.path.join(self.media_dir, category, filename)
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 处理特定类型的媒体
            metadata = {}
            if category == "image":
                metadata = await self.process_image(BytesIO(file_content))
            elif category == "audio":
                metadata = await self.process_audio(BytesIO(file_content), mime_type)
            
            # 生成URL
            url = f"/media/{category}/{filename}"
            
            return {
                "success": True,
                "file_path": file_path,
                "url": url,
                "mime_type": mime_type,
                "category": category,
                "filename": filename,
                "size": len(file_content),
                "metadata": metadata
            }
        
        except Exception as e:
            logger.error(f"处理媒体数据失败: {str(e)}")
            return {
                "success": False,
                "error": f"处理媒体数据失败: {str(e)}"
            }
    
    async def process_file(self, file: BinaryIO, filename: str) -> Dict[str, Any]:
        """
        处理上传的文件
        
        Args:
            file: 文件对象
            filename: 文件名
        
        Returns:
            处理结果
        """
        try:
            # 读取文件内容
            file_content = await asyncio.to_thread(file.read)
            
            # 获取MIME类型
            mime_type = self.get_mime_type(file_content)
            
            # 检查媒体类型
            if not self.is_valid_media_type(mime_type):
                return {
                    "success": False,
                    "error": f"不支持的媒体类型: {mime_type}"
                }
            
            # 获取媒体类别
            category = self.get_media_category(mime_type)
            
            # 生成文件名
            if not filename:
                extension = mime_type.split("/")[1]
                filename = f"{uuid.uuid4()}.{extension}"
            else:
                # 确保文件名是安全的
                filename = os.path.basename(filename)
                # 如果没有扩展名，添加扩展名
                if "." not in filename:
                    extension = mime_type.split("/")[1]
                    filename = f"{filename}.{extension}"
            
            # 保存文件
            file_path = os.path.join(self.media_dir, category, filename)
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 处理特定类型的媒体
            metadata = {}
            if category == "image":
                metadata = await self.process_image(BytesIO(file_content))
            elif category == "audio":
                metadata = await self.process_audio(BytesIO(file_content), mime_type)
            
            # 生成URL
            url = f"/media/{category}/{filename}"
            
            return {
                "success": True,
                "file_path": file_path,
                "url": url,
                "mime_type": mime_type,
                "category": category,
                "filename": filename,
                "size": len(file_content),
                "metadata": metadata
            }
        
        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            return {
                "success": False,
                "error": f"处理文件失败: {str(e)}"
            }
    
    async def process_image(self, image_data: BytesIO) -> Dict[str, Any]:
        """
        处理图像数据
        
        Args:
            image_data: 图像数据
        
        Returns:
            图像元数据
        """
        try:
            # 使用Pillow处理图像
            image = await asyncio.to_thread(Image.open, image_data)
            
            # 获取图像信息
            width, height = image.size
            format_name = image.format
            mode = image.mode
            
            return {
                "width": width,
                "height": height,
                "format": format_name,
                "mode": mode,
                "aspect_ratio": round(width / height, 2) if height > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"处理图像失败: {str(e)}")
            return {}
    
    async def process_audio(self, audio_data: BytesIO, mime_type: str) -> Dict[str, Any]:
        """
        处理音频数据
        
        Args:
            audio_data: 音频数据
            mime_type: MIME类型
        
        Returns:
            音频元数据
        """
        try:
            # 确定音频格式
            format_map = {
                "audio/mpeg": "mp3",
                "audio/wav": "wav",
                "audio/ogg": "ogg",
                "audio/webm": "webm"
            }
            format_name = format_map.get(mime_type, "mp3")
            
            # 使用pydub处理音频
            audio = await asyncio.to_thread(AudioSegment.from_file, audio_data, format=format_name)
            
            # 获取音频信息
            duration_seconds = len(audio) / 1000.0
            channels = audio.channels
            sample_width = audio.sample_width
            frame_rate = audio.frame_rate
            
            return {
                "duration": duration_seconds,
                "channels": channels,
                "sample_width": sample_width,
                "frame_rate": frame_rate,
                "format": format_name
            }
        
        except Exception as e:
            logger.error(f"处理音频失败: {str(e)}")
            return {}


# 创建全局多模态处理器实例
multimodal_handler = MultimodalHandler()
