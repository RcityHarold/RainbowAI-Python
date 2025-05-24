"""
搜索工具
提供网络搜索功能
"""
import json
import aiohttp
from typing import Dict, Any, List, Optional

from ...config import get_config
from ..base_tool import BaseTool, ToolResult, ToolError


class SearchTool(BaseTool):
    """搜索工具，提供网络搜索功能"""
    
    def __init__(self):
        super().__init__()
        config = get_config()
        self.api_key = config["tools"]["search_api_key"]
        self.api_url = "https://api.bing.microsoft.com/v7.0/search"
    
    @property
    def tool_id(self) -> str:
        return "builtin.search"
    
    @property
    def display_name(self) -> str:
        return "网络搜索"
    
    @property
    def description(self) -> str:
        return "搜索互联网上的信息，返回相关搜索结果"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "搜索查询词"
            },
            "count": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 5,
                "minimum": 1,
                "maximum": 10
            },
            "market": {
                "type": "string",
                "description": "搜索市场，例如zh-CN表示中国",
                "default": "zh-CN"
            }
        }
    
    @property
    def required_parameters(self) -> List[str]:
        return ["query"]
    
    @property
    def category(self) -> str:
        return "information"
    
    @property
    def tags(self) -> List[str]:
        return ["search", "information", "api"]
    
    @property
    def is_enabled(self) -> bool:
        return bool(self.api_key)
    
    async def _execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """
        执行搜索
        
        Args:
            parameters: 包含query、count和market参数的字典
            context: 执行上下文
        
        Returns:
            搜索结果
        """
        if not self.api_key:
            return ToolResult.error_result("未配置搜索API密钥")
        
        query = parameters.get("query", "").strip()
        count = int(parameters.get("count", 5))
        market = parameters.get("market", "zh-CN").strip()
        
        if not query:
            return ToolResult.error_result("搜索查询不能为空")
        
        # 构建请求头
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json"
        }
        
        # 构建查询参数
        query_params = {
            "q": query,
            "count": count,
            "mkt": market,
            "responseFilter": "webpages"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=query_params, headers=headers) as response:
                    if response.status != 200:
                        error_data = await response.text()
                        return ToolResult.error_result(f"搜索API错误: {error_data}")
                    
                    data = await response.json()
                    
                    # 提取搜索结果
                    web_pages = data.get("webPages", {}).get("value", [])
                    
                    if not web_pages:
                        return ToolResult.success_result(
                            content="未找到相关搜索结果",
                            content_type="text",
                            metadata={"query": query, "results": []}
                        )
                    
                    # 格式化搜索结果
                    results = []
                    for page in web_pages:
                        results.append({
                            "title": page.get("name", ""),
                            "url": page.get("url", ""),
                            "snippet": page.get("snippet", "")
                        })
                    
                    # 构建人类可读的搜索结果摘要
                    summary = f"搜索 \"{query}\" 的结果：\n\n"
                    for i, result in enumerate(results, 1):
                        summary += f"{i}. {result['title']}\n"
                        summary += f"   {result['snippet']}\n"
                        summary += f"   {result['url']}\n\n"
                    
                    return ToolResult.success_result(
                        content=summary.strip(),
                        content_type="text",
                        metadata={
                            "query": query,
                            "results": results,
                            "total_results": len(results)
                        }
                    )
        
        except aiohttp.ClientError as e:
            return ToolResult.error_result(f"网络请求错误: {str(e)}")
        
        except Exception as e:
            return ToolResult.error_result(f"搜索错误: {str(e)}")
