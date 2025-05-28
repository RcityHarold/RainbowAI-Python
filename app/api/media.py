"""
媒体处理API模块
提供多模态内容上传和处理功能
"""
import os
import base64
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..core.multimodal_handler import multimodal_handler
from ..core.logger import logger
from ..db.repositories import message_repo
from ..models.data_models import Message
from ..config import get_config

router = APIRouter()
config = get_config()


class Base64UploadRequest(BaseModel):
    """Base64上传请求"""
    base64_data: str = Field(..., description="Base64编码的媒体数据")
    filename: Optional[str] = Field(None, description="文件名")
    message_id: Optional[str] = Field(None, description="关联的消息ID")


@router.post("/api/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    message_id: Optional[str] = Form(None)
):
    """
    上传媒体文件
    支持图像、音频和视频
    """
    try:
        # 处理上传的文件
        result = await multimodal_handler.process_file(file.file, file.filename)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # 如果提供了消息ID，更新消息的元数据
        if message_id:
            await update_message_with_media(message_id, result)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传媒体文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传媒体文件失败: {str(e)}")


@router.post("/api/media/upload/base64")
async def upload_base64_media(request: Base64UploadRequest):
    """
    上传Base64编码的媒体数据
    支持图像、音频和视频
    """
    try:
        # 处理Base64编码的媒体数据
        result = await multimodal_handler.process_base64_media(
            request.base64_data,
            request.filename
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # 如果提供了消息ID，更新消息的元数据
        if request.message_id:
            await update_message_with_media(request.message_id, result)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传Base64媒体数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传Base64媒体数据失败: {str(e)}")


@router.get("/media/{category}/{filename}")
async def get_media(category: str, filename: str):
    """
    获取媒体文件
    """
    try:
        # 构建文件路径
        media_dir = config.get("MEDIA_STORAGE_PATH", "media")
        file_path = os.path.join(media_dir, category, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件未找到: {filename}")
        
        # 返回文件
        return FileResponse(file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取媒体文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取媒体文件失败: {str(e)}")


async def update_message_with_media(message_id: str, media_result: Dict[str, Any]):
    """
    使用媒体信息更新消息
    
    Args:
        message_id: 消息ID
        media_result: 媒体处理结果
    """
    try:
        # 获取消息
        message = await message_repo.get(message_id)
        if not message:
            logger.warning(f"消息未找到，无法更新媒体信息: {message_id}")
            return
        
        # 更新消息元数据
        if not message.metadata:
            message.metadata = {}
        
        # 添加媒体信息
        if "media" not in message.metadata:
            message.metadata["media"] = []
        
        media_info = {
            "url": media_result["url"],
            "mime_type": media_result["mime_type"],
            "category": media_result["category"],
            "filename": media_result["filename"],
            "size": media_result["size"],
            "metadata": media_result.get("metadata", {})
        }
        
        message.metadata["media"].append(media_info)
        
        # 更新内容类型（如果需要）
        if message.content_type == "text" and media_result["category"] in ["image", "audio", "video"]:
            message.content_type = f"multimodal/{media_result['category']}"
        
        # 保存更新后的消息
        await message_repo.update(message)
        
        logger.info(f"消息已更新媒体信息: {message_id}")
    
    except Exception as e:
        logger.error(f"更新消息媒体信息失败: {str(e)}")
        raise
