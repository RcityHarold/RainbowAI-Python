"""
实时通信API模块
提供WebSocket连接和实时消息推送功能
"""
import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core.websocket_manager import websocket_manager
from ..core.logger import logger
from ..services.dialogue_service import dialogue_service
from ..models.data_models import Message
from ..db.repositories import message_repo

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = None,
    dialogue_id: Optional[str] = None
):
    """
    WebSocket连接端点
    支持用户和对话的实时通信
    """
    # 生成连接ID
    connection_id = str(uuid.uuid4())
    
    try:
        # 建立连接
        await websocket_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            dialogue_id=dialogue_id
        )
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connection_established",
            "connection_id": connection_id,
            "user_id": user_id,
            "dialogue_id": dialogue_id
        })
        
        # 持续接收消息
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                
                # 解析消息
                try:
                    message_data = json.loads(data)
                    message_type = message_data.get("type", "unknown")
                    
                    # 处理不同类型的消息
                    if message_type == "ping":
                        # 心跳消息
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": message_data.get("timestamp")
                        })
                    
                    elif message_type == "typing":
                        # 用户正在输入
                        if dialogue_id:
                            # 广播给对话中的其他用户
                            typing_message = {
                                "type": "typing",
                                "user_id": user_id,
                                "dialogue_id": dialogue_id,
                                "is_typing": message_data.get("is_typing", True)
                            }
                            await websocket_manager.send_to_dialogue(typing_message, dialogue_id)
                    
                    else:
                        # 未知消息类型
                        await websocket.send_json({
                            "type": "error",
                            "message": f"未知消息类型: {message_type}"
                        })
                
                except json.JSONDecodeError:
                    # 消息格式错误
                    await websocket.send_json({
                        "type": "error",
                        "message": "消息格式错误，请发送有效的JSON"
                    })
            
            except WebSocketDisconnect:
                # 连接断开
                break
    
    except Exception as e:
        logger.error(f"WebSocket连接错误: {str(e)}")
    
    finally:
        # 断开连接
        websocket_manager.disconnect(connection_id)


@router.post("/api/notify/message")
async def notify_new_message(message_id: str):
    """
    通知新消息
    当有新消息时，通过WebSocket推送给相关用户
    """
    try:
        # 获取消息
        message = await message_repo.get(message_id)
        if not message:
            raise HTTPException(status_code=404, detail=f"消息未找到: {message_id}")
        
        # 构建通知消息
        notification = {
            "type": "new_message",
            "message_id": message.id,
            "dialogue_id": message.dialogue_id,
            "session_id": message.session_id,
            "turn_id": message.turn_id,
            "sender_role": message.sender_role,
            "content_type": message.content_type,
            "created_at": message.created_at.isoformat()
        }
        
        # 推送给对话中的所有用户
        await websocket_manager.send_to_dialogue(notification, message.dialogue_id)
        
        return {"success": True, "message": "通知已发送"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送消息通知失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发送消息通知失败: {str(e)}")


@router.post("/api/notify/dialogue_update")
async def notify_dialogue_update(dialogue_id: str, update_type: str):
    """
    通知对话更新
    当对话状态变更时，通过WebSocket推送给相关用户
    """
    try:
        # 构建通知消息
        notification = {
            "type": "dialogue_update",
            "dialogue_id": dialogue_id,
            "update_type": update_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 推送给对话中的所有用户
        await websocket_manager.send_to_dialogue(notification, dialogue_id)
        
        return {"success": True, "message": "通知已发送"}
    
    except Exception as e:
        logger.error(f"发送对话更新通知失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发送对话更新通知失败: {str(e)}")


@router.post("/api/notify/stream_response")
async def stream_response(
    dialogue_id: str,
    session_id: str,
    turn_id: str,
    content: str,
    is_complete: bool = False
):
    """
    流式响应
    用于实时推送AI生成的内容
    """
    try:
        # 构建流式响应消息
        stream_message = {
            "type": "stream_response",
            "dialogue_id": dialogue_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "content": content,
            "is_complete": is_complete,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 推送给对话中的所有用户
        await websocket_manager.send_to_dialogue(stream_message, dialogue_id)
        
        return {"success": True, "message": "流式响应已发送"}
    
    except Exception as e:
        logger.error(f"发送流式响应失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发送流式响应失败: {str(e)}")
