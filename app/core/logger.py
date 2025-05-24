"""
日志模块
用于记录系统操作和错误
"""
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

from ..config import get_config


class Logger:
    """日志记录器"""
    
    def __init__(self):
        self.config = get_config()["log"]
        self.level = self._get_log_level()
        self.file = self.config.get("file", "")
        
        # 配置日志
        self._configure_logging()
        
        # 创建日志记录器
        self.logger = logging.getLogger("RainbowAI")
    
    def _get_log_level(self) -> int:
        """获取日志级别"""
        level_str = self.config.get("level", "INFO").upper()
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels.get(level_str, logging.INFO)
    
    def _configure_logging(self):
        """配置日志"""
        # 创建日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(self.level)
        root_logger.addHandler(console_handler)
        
        # 如果配置了日志文件，创建文件处理器
        if self.file:
            # 确保日志目录存在
            log_dir = os.path.dirname(self.file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 创建文件处理器
            file_handler = logging.FileHandler(self.file)
            file_handler.setLevel(self.level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """记录日志"""
        # 添加时间戳
        kwargs["timestamp"] = datetime.utcnow().isoformat()
        
        # 格式化额外信息
        extra_info = ""
        if kwargs:
            extra_info = " " + json.dumps(kwargs, ensure_ascii=False)
        
        # 记录日志
        self.logger.log(level, message + extra_info)
    
    def log_dialogue_event(
        self,
        event_type: str,
        dialogue_id: Optional[str] = None,
        session_id: Optional[str] = None,
        turn_id: Optional[str] = None,
        message_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        actor_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ):
        """
        记录对话事件
        
        Args:
            event_type: 事件类型
            dialogue_id: 对话ID
            session_id: 会话ID
            turn_id: 轮次ID
            message_id: 消息ID
            actor_role: 操作者角色
            actor_id: 操作者ID
            event_data: 事件数据
        """
        self.info(
            f"Dialogue Event: {event_type}",
            event_type=event_type,
            dialogue_id=dialogue_id,
            session_id=session_id,
            turn_id=turn_id,
            message_id=message_id,
            actor_role=actor_role,
            actor_id=actor_id,
            event_data=event_data or {}
        )
    
    def log_api_request(
        self,
        method: str,
        path: str,
        client_ip: str,
        status_code: int,
        response_time: float,
        request_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        记录API请求
        
        Args:
            method: 请求方法
            path: 请求路径
            client_ip: 客户端IP
            status_code: 状态码
            response_time: 响应时间（毫秒）
            request_data: 请求数据
            error: 错误信息
        """
        log_level = logging.INFO
        if status_code >= 400:
            log_level = logging.ERROR
        
        self._log(
            log_level,
            f"API Request: {method} {path} - {status_code}",
            method=method,
            path=path,
            client_ip=client_ip,
            status_code=status_code,
            response_time=response_time,
            request_data=request_data or {},
            error=error
        )
    
    def log_tool_call(
        self,
        tool_id: str,
        dialogue_id: Optional[str] = None,
        turn_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
        execution_time: Optional[float] = None
    ):
        """
        记录工具调用
        
        Args:
            tool_id: 工具ID
            dialogue_id: 对话ID
            turn_id: 轮次ID
            parameters: 参数
            result: 结果
            success: 是否成功
            error: 错误信息
            execution_time: 执行时间（毫秒）
        """
        log_level = logging.INFO if success else logging.ERROR
        
        self._log(
            log_level,
            f"Tool Call: {tool_id} - {'Success' if success else 'Failed'}",
            tool_id=tool_id,
            dialogue_id=dialogue_id,
            turn_id=turn_id,
            parameters=parameters or {},
            result=result or {},
            success=success,
            error=error,
            execution_time=execution_time
        )


# 创建日志记录器实例
logger = Logger()
