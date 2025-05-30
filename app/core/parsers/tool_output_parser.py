"""
工具输出解析器模块

用于将工具输出转化为自然语言片段
"""
from typing import Dict, Any, List, Optional
import json

from ...core.logger import logger

class ToolOutputParser:
    """工具输出解析器"""
    
    def __init__(self):
        self.logger = logger
        # 工具类型到自然语言模板的映射
        self.tool_templates = {
            "weather": "天气查询结果：{city}的天气是{condition}，温度{temp}度，{rain_desc}。",
            "search": "搜索结果：{summary}",
            "database": "数据库查询结果：{result_summary}",
            "calculator": "计算结果：{expression} = {result}",
            "translation": "翻译结果：{translated_text}",
            "reminder": "已设置提醒：{reminder_text}，时间：{time}"
        }
    
    async def parse(self, message) -> Dict[str, Any]:
        """
        解析工具输出内容
        
        Args:
            message: 消息对象
        
        Returns:
            解析结果
        """
        try:
            content = message.content
            
            # 如果内容是字符串形式的JSON，尝试解析
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    # 如果不是有效的JSON，保持原样
                    pass
            
            # 提取工具类型和结果
            tool_type = self._extract_tool_type(content)
            tool_result = self._extract_tool_result(content)
            
            # 将工具结果转化为自然语言
            text_block = self._tool_result_to_text(tool_type, tool_result)
            
            # 提取关键信息（简单实现）
            key_info = self._extract_key_info(tool_type, tool_result)
            
            return {
                "text_block": text_block,
                "tool_type": tool_type,
                "tool_result": tool_result,
                "key_info": key_info,
                "semantic_tags": [tool_type] if tool_type else [],
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
        
        except Exception as e:
            self.logger.error(f"解析工具输出失败: {str(e)}")
            return {
                "text_block": str(message.content),
                "tool_type": "unknown",
                "tool_result": {},
                "key_info": {},
                "semantic_tags": [],
                "source_message_id": message.message_id,
                "origin": message.sender_role,
                "timestamp": message.created_at
            }
    
    def _extract_tool_type(self, content: Any) -> str:
        """
        提取工具类型
        
        Args:
            content: 工具输出内容
        
        Returns:
            工具类型
        """
        if isinstance(content, dict):
            # 尝试从字典中提取工具类型
            return content.get("tool", "") or content.get("type", "") or content.get("tool_type", "")
        return ""
    
    def _extract_tool_result(self, content: Any) -> Dict[str, Any]:
        """
        提取工具结果
        
        Args:
            content: 工具输出内容
        
        Returns:
            工具结果
        """
        if isinstance(content, dict):
            # 尝试从字典中提取工具结果
            result = content.get("result", {}) or content.get("data", {}) or content
            if isinstance(result, dict):
                return result
            return {"value": result}
        return {"value": content}
    
    def _tool_result_to_text(self, tool_type: str, tool_result: Dict[str, Any]) -> str:
        """
        将工具结果转化为自然语言
        
        Args:
            tool_type: 工具类型
            tool_result: 工具结果
        
        Returns:
            自然语言描述
        """
        # 如果有对应的模板，使用模板格式化
        if tool_type in self.tool_templates:
            try:
                # 尝试使用模板格式化
                if tool_type == "weather":
                    return self.tool_templates[tool_type].format(
                        city=tool_result.get("city", "未知城市"),
                        condition=tool_result.get("condition", "未知"),
                        temp=tool_result.get("temp", "未知"),
                        rain_desc="有雨" if tool_result.get("rain", False) else "无雨"
                    )
                elif tool_type == "search":
                    return self.tool_templates[tool_type].format(
                        summary=tool_result.get("summary", "未找到相关信息")
                    )
                elif tool_type == "database":
                    return self.tool_templates[tool_type].format(
                        result_summary=tool_result.get("summary", "无结果")
                    )
                elif tool_type == "calculator":
                    return self.tool_templates[tool_type].format(
                        expression=tool_result.get("expression", ""),
                        result=tool_result.get("result", "")
                    )
                elif tool_type == "translation":
                    return self.tool_templates[tool_type].format(
                        translated_text=tool_result.get("text", "")
                    )
                elif tool_type == "reminder":
                    return self.tool_templates[tool_type].format(
                        reminder_text=tool_result.get("text", ""),
                        time=tool_result.get("time", "")
                    )
            except KeyError as e:
                self.logger.warning(f"工具结果缺少必要字段: {str(e)}")
            except Exception as e:
                self.logger.warning(f"格式化工具结果失败: {str(e)}")
        
        # 如果没有对应的模板或格式化失败，返回通用描述
        if isinstance(tool_result, dict):
            # 将字典转换为字符串
            try:
                return f"工具结果: {json.dumps(tool_result, ensure_ascii=False)}"
            except:
                pass
        
        # 最后的备选方案
        return f"工具 '{tool_type}' 的结果: {str(tool_result)}"
    
    def _extract_key_info(self, tool_type: str, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取关键信息
        
        Args:
            tool_type: 工具类型
            tool_result: 工具结果
        
        Returns:
            关键信息
        """
        # 根据工具类型提取不同的关键信息
        key_info = {}
        
        if tool_type == "weather":
            key_info = {
                "city": tool_result.get("city"),
                "temperature": tool_result.get("temp"),
                "condition": tool_result.get("condition"),
                "has_rain": tool_result.get("rain", False)
            }
        elif tool_type == "search":
            key_info = {
                "query": tool_result.get("query"),
                "summary": tool_result.get("summary"),
                "source": tool_result.get("source")
            }
        # 可以根据需要添加更多工具类型的处理
        
        # 移除None值
        return {k: v for k, v in key_info.items() if v is not None}

# 创建全局工具输出解析器实例
tool_output_parser = ToolOutputParser()
