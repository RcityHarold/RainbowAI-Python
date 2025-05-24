"""
计算器工具
提供基本的数学计算功能
"""
import re
import math
import operator
from typing import Dict, Any, List, Optional, Union
from sympy import sympify, SympifyError

from ..base_tool import BaseTool, ToolResult, ToolError


class CalculatorTool(BaseTool):
    """计算器工具，提供基本的数学计算功能"""
    
    @property
    def tool_id(self) -> str:
        return "builtin.calculator"
    
    @property
    def display_name(self) -> str:
        return "计算器"
    
    @property
    def description(self) -> str:
        return "执行数学计算，支持基本运算和常用数学函数"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "expression": {
                "type": "string",
                "description": "要计算的数学表达式"
            }
        }
    
    @property
    def required_parameters(self) -> List[str]:
        return ["expression"]
    
    @property
    def category(self) -> str:
        return "utility"
    
    @property
    def tags(self) -> List[str]:
        return ["math", "calculator", "utility"]
    
    async def _execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """
        执行计算
        
        Args:
            parameters: 包含expression参数的字典
            context: 执行上下文
        
        Returns:
            计算结果
        """
        expression = parameters.get("expression", "").strip()
        
        if not expression:
            return ToolResult.error_result("表达式不能为空")
        
        try:
            # 使用sympy进行安全计算
            result = sympify(expression)
            
            # 转换为浮点数或整数
            if result.is_Integer:
                result = int(result)
            elif result.is_Float:
                result = float(result)
            
            return ToolResult.success_result(
                content=str(result),
                content_type="text",
                metadata={
                    "expression": expression,
                    "result": result
                }
            )
        
        except SympifyError as e:
            return ToolResult.error_result(f"无效的数学表达式: {str(e)}")
        
        except Exception as e:
            return ToolResult.error_result(f"计算错误: {str(e)}")
