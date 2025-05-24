"""
工具注册表
用于管理和调用各种工具
"""
import importlib
import pkgutil
from typing import Dict, Any, List, Type, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor

from .base_tool import BaseTool, ToolResult
from ..core.logger import logger


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    def register(self, tool: BaseTool) -> None:
        """
        注册工具
        
        Args:
            tool: 工具实例
        """
        if not isinstance(tool, BaseTool):
            raise TypeError(f"工具必须是BaseTool的实例，而不是{type(tool)}")
        
        tool_id = tool.tool_id
        if tool_id in self._tools:
            logger.warning(f"工具ID '{tool_id}' 已存在，将被覆盖")
        
        self._tools[tool_id] = tool
        logger.info(f"工具 '{tool_id}' 已注册")
    
    def unregister(self, tool_id: str) -> bool:
        """
        注销工具
        
        Args:
            tool_id: 工具ID
        
        Returns:
            是否成功注销
        """
        if tool_id in self._tools:
            del self._tools[tool_id]
            logger.info(f"工具 '{tool_id}' 已注销")
            return True
        
        logger.warning(f"工具 '{tool_id}' 不存在，无法注销")
        return False
    
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """
        获取工具
        
        Args:
            tool_id: 工具ID
        
        Returns:
            工具实例，如果不存在则返回None
        """
        return self._tools.get(tool_id)
    
    def list_tools(self, category: Optional[str] = None, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        列出工具
        
        Args:
            category: 工具类别，如果为None则列出所有类别
            enabled_only: 是否只列出已启用的工具
        
        Returns:
            工具列表
        """
        tools = []
        
        for tool in self._tools.values():
            if enabled_only and not tool.is_enabled:
                continue
            
            if category and tool.category != category:
                continue
            
            tools.append(tool.to_dict())
        
        return tools
    
    def get_categories(self) -> List[str]:
        """
        获取所有工具类别
        
        Returns:
            类别列表
        """
        categories = set()
        
        for tool in self._tools.values():
            if tool.is_enabled:
                categories.add(tool.category)
        
        return sorted(list(categories))
    
    async def execute_tool(self, tool_id: str, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> ToolResult:
        """
        执行工具
        
        Args:
            tool_id: 工具ID
            parameters: 工具参数
            context: 执行上下文
        
        Returns:
            执行结果
        """
        tool = self.get_tool(tool_id)
        if not tool:
            error_message = f"工具 '{tool_id}' 不存在"
            logger.error(error_message)
            return ToolResult.error_result(error_message)
        
        if not tool.is_enabled:
            error_message = f"工具 '{tool_id}' 已禁用"
            logger.error(error_message)
            return ToolResult.error_result(error_message)
        
        try:
            return await tool.execute(parameters, context)
        except Exception as e:
            error_message = f"执行工具 '{tool_id}' 时发生错误: {str(e)}"
            logger.error(error_message)
            return ToolResult.error_result(error_message)
    
    def discover_tools(self, package_path: str) -> int:
        """
        自动发现并注册工具
        
        Args:
            package_path: 工具包路径，例如 'app.tools.builtin'
        
        Returns:
            注册的工具数量
        """
        count = 0
        package = importlib.import_module(package_path)
        
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
            if is_pkg:
                # 如果是包，递归搜索
                count += self.discover_tools(name)
            else:
                try:
                    # 导入模块
                    module = importlib.import_module(name)
                    
                    # 查找模块中的工具类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        # 检查是否是BaseTool的子类（不包括BaseTool本身）
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseTool) and 
                            attr is not BaseTool):
                            
                            try:
                                # 实例化工具并注册
                                tool = attr()
                                self.register(tool)
                                count += 1
                            except Exception as e:
                                logger.error(f"实例化工具 '{attr_name}' 时发生错误: {str(e)}")
                
                except Exception as e:
                    logger.error(f"导入模块 '{name}' 时发生错误: {str(e)}")
        
        return count


# 创建全局工具注册表实例
tool_registry = ToolRegistry()
