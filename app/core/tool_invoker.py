"""
工具调度器（ToolInvoker）
接入外部API工具模块，获取信息、分析处理结果等
"""
from typing import Dict, Any, List, Optional, Union, Callable
import json
import asyncio
import uuid
from datetime import datetime

from ..models.data_models import Message
from ..tools import BaseTool, ToolResult, ToolError, tool_registry
from ..core.logger import logger


# 注意：这个类已经被移动到 app.tools.base_tool 模块中
# 这里保留一个兼容类，用于兼容旧版代码
class ToolResultLegacy:
    """工具调用结果（兼容旧版）"""
    def __init__(
        self,
        tool_id: str,
        success: bool,
        data: Any = None,
        error: str = None,
        execution_time: float = None
    ):
        self.tool_id = tool_id
        self.success = success
        self.data = data
        self.error = error
        self.execution_time = execution_time
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "tool_id": self.tool_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    def to_text(self) -> str:
        """转换为文本格式，用于插入上下文"""
        if not self.success:
            return f"工具 {self.tool_id} 调用失败: {self.error}"
        
        if isinstance(self.data, dict):
            # 字典类型，格式化输出
            result_parts = []
            for key, value in self.data.items():
                result_parts.append(f"{key}: {value}")
            return f"工具 {self.tool_id} 返回结果:\n" + "\n".join(result_parts)
        else:
            # 其他类型，直接转字符串
            return f"工具 {self.tool_id} 返回结果: {self.data}"


# 注意：这个类已经被移动到 app.tools.base_tool 模块中
# 这里保留一个兼容类，用于兼容旧版代码
class BaseToolLegacy:
    """工具基类（兼容旧版）"""
    def __init__(self, tool_id: str, description: str):
        self.tool_id = tool_id
        self.description = description
        self.logger = logger
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResultLegacy:
        """
        执行工具调用
        
        Args:
            parameters: 工具调用参数
        
        Returns:
            工具调用结果
        """
        start_time = datetime.utcnow().timestamp()
        
        try:
            # 执行工具逻辑
            result = await self._execute_logic(parameters)
            execution_time = datetime.utcnow().timestamp() - start_time
            
            return ToolResultLegacy(
                tool_id=self.tool_id,
                success=True,
                data=result,
                execution_time=execution_time
            )
        
        except Exception as e:
            self.logger.error(f"Error executing tool {self.tool_id}: {str(e)}")
            execution_time = datetime.utcnow().timestamp() - start_time
            
            return ToolResultLegacy(
                tool_id=self.tool_id,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _execute_logic(self, parameters: Dict[str, Any]) -> Any:
        """
        执行工具逻辑，子类需要实现此方法
        
        Args:
            parameters: 工具调用参数
        
        Returns:
            执行结果
        """
        raise NotImplementedError("子类必须实现此方法")


class ToolInvoker:
    """
    工具调度器
    负责管理和调用各种工具
    """
    def __init__(self):
        # 使用全局工具注册表
        self.tool_registry = tool_registry
        
        # 发现并注册内置工具
        self.discover_tools()
    
    def discover_tools(self):
        """发现并注册工具"""
        try:
            # 发现内置工具
            count = self.tool_registry.discover_tools("app.tools.builtin")
            logger.info(f"发现并注册了 {count} 个内置工具")
        except Exception as e:
            logger.error(f"发现工具时发生错误: {str(e)}")
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用工具列表
        
        Returns:
            工具列表
        """
        return self.tool_registry.list_tools(enabled_only=True)
    
    def get_tool_categories(self) -> List[str]:
        """
        获取工具类别
        
        Returns:
            类别列表
        """
        return self.tool_registry.get_categories()
    
    async def invoke_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ToolResult:
        """
        调用工具
        
        Args:
            tool_id: 工具ID
            parameters: 工具调用参数
            context: 执行上下文
        
        Returns:
            工具调用结果
        """
        return await self.tool_registry.execute_tool(tool_id, parameters, context)
    
    async def process_tool_request(
        self,
        message: Message
    ) -> Optional[ToolResult]:
        """
        处理工具请求消息
        
        Args:
            message: 消息对象, 应为tool_request类型
        
        Returns:
            工具调用结果，如果消息不是工具请求则返回None
        """
        if message.content_type != "tool_request":
            return None
        
        try:
            # 解析工具请求
            request = json.loads(message.content)
            tool_id = request.get("tool")
            parameters = request.get("parameters", {})
            
            # 准备上下文
            context = {
                "dialogue_id": message.dialogue_id,
                "session_id": message.session_id,
                "turn_id": message.turn_id,
                "message_id": message.id
            }
            
            # 调用工具
            return await self.invoke_tool(tool_id, parameters, context)
        
        except json.JSONDecodeError:
            logger.error(f"无效的工具请求格式: {message.content}")
            return ToolResult.error_result("无效的工具请求格式")
        
        except Exception as e:
            logger.error(f"处理工具请求时发生错误: {str(e)}")
            return ToolResult.error_result(f"处理工具请求时发生错误: {str(e)}")
