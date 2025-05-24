"""
工具基础类
定义工具接口和基本功能
"""
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field

from ..core.logger import logger


class ToolResult(BaseModel):
    """工具执行结果"""
    
    success: bool = Field(True, description="执行是否成功")
    content: Any = Field(None, description="结果内容")
    content_type: str = Field("text", description="内容类型，如text、json、image等")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "content": self.content,
            "content_type": self.content_type,
            "error": self.error,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def success_result(cls, content: Any, content_type: str = "text", metadata: Dict[str, Any] = None) -> "ToolResult":
        """创建成功结果"""
        return cls(
            success=True,
            content=content,
            content_type=content_type,
            error=None,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_result(cls, error: str, metadata: Dict[str, Any] = None) -> "ToolResult":
        """创建错误结果"""
        return cls(
            success=False,
            content=None,
            content_type="text",
            error=error,
            metadata=metadata or {}
        )


class ToolError(Exception):
    """工具执行错误"""
    
    def __init__(self, message: str, metadata: Dict[str, Any] = None):
        self.message = message
        self.metadata = metadata or {}
        super().__init__(message)


class BaseTool(ABC):
    """工具基础类"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "未提供描述"
    
    @property
    @abstractmethod
    def tool_id(self) -> str:
        """工具ID，全局唯一"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """工具显示名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """工具版本"""
        pass
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """工具参数定义"""
        return {}
    
    @property
    def required_parameters(self) -> List[str]:
        """必需参数列表"""
        return []
    
    @property
    def category(self) -> str:
        """工具类别"""
        return "general"
    
    @property
    def tags(self) -> List[str]:
        """工具标签"""
        return []
    
    @property
    def is_enabled(self) -> bool:
        """工具是否启用"""
        return True
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        # 检查必需参数
        for param in self.required_parameters:
            if param not in parameters:
                raise ToolError(f"缺少必需参数: {param}")
        
        # 返回验证后的参数
        return parameters
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        """
        执行工具
        
        Args:
            parameters: 工具参数
            context: 执行上下文
        
        Returns:
            执行结果
        """
        context = context or {}
        
        # 记录工具调用
        logger.log_tool_call(
            tool_id=self.tool_id,
            dialogue_id=context.get("dialogue_id"),
            turn_id=context.get("turn_id"),
            parameters=parameters,
            execution_time=0,  # 将在执行后更新
            success=True  # 将在执行后更新
        )
        
        try:
            # 验证参数
            validated_params = self.validate_parameters(parameters)
            
            # 执行工具逻辑
            start_time = asyncio.get_event_loop().time()
            result = await self._execute(validated_params, context)
            end_time = asyncio.get_event_loop().time()
            
            # 计算执行时间（毫秒）
            execution_time = (end_time - start_time) * 1000
            
            # 更新工具调用日志
            logger.log_tool_call(
                tool_id=self.tool_id,
                dialogue_id=context.get("dialogue_id"),
                turn_id=context.get("turn_id"),
                parameters=parameters,
                result=result.to_dict() if result else None,
                success=result.success if result else False,
                execution_time=execution_time
            )
            
            return result
        
        except ToolError as e:
            # 记录工具错误
            logger.log_tool_call(
                tool_id=self.tool_id,
                dialogue_id=context.get("dialogue_id"),
                turn_id=context.get("turn_id"),
                parameters=parameters,
                success=False,
                error=str(e)
            )
            
            return ToolResult.error_result(str(e), e.metadata)
        
        except Exception as e:
            # 记录未预期错误
            error_message = f"工具执行错误: {str(e)}"
            logger.error(error_message)
            
            logger.log_tool_call(
                tool_id=self.tool_id,
                dialogue_id=context.get("dialogue_id"),
                turn_id=context.get("turn_id"),
                parameters=parameters,
                success=False,
                error=error_message
            )
            
            return ToolResult.error_result(error_message)
    
    @abstractmethod
    async def _execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """
        执行工具逻辑
        
        Args:
            parameters: 验证后的工具参数
            context: 执行上下文
        
        Returns:
            执行结果
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tool_id": self.tool_id,
            "name": self.display_name,
            "description": self.description,
            "version": self.version,
            "parameters": self.parameters,
            "required_parameters": self.required_parameters,
            "category": self.category,
            "tags": self.tags,
            "is_enabled": self.is_enabled
        }
