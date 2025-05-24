"""
天气工具
提供天气查询功能
"""
import json
import aiohttp
from typing import Dict, Any, List, Optional

from ...config import get_config
from ..base_tool import BaseTool, ToolResult, ToolError


class WeatherTool(BaseTool):
    """天气工具，提供天气查询功能"""
    
    def __init__(self):
        super().__init__()
        config = get_config()
        self.api_key = config["tools"]["weather_api_key"]
        self.api_url = "https://api.openweathermap.org/data/2.5/weather"
    
    @property
    def tool_id(self) -> str:
        return "builtin.weather"
    
    @property
    def display_name(self) -> str:
        return "天气查询"
    
    @property
    def description(self) -> str:
        return "查询指定城市的天气信息，包括温度、湿度、风速等"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "city": {
                "type": "string",
                "description": "城市名称，可以是中文或英文"
            },
            "country_code": {
                "type": "string",
                "description": "国家代码，例如CN表示中国（可选）"
            },
            "units": {
                "type": "string",
                "description": "温度单位，metric表示摄氏度，imperial表示华氏度",
                "enum": ["metric", "imperial"],
                "default": "metric"
            }
        }
    
    @property
    def required_parameters(self) -> List[str]:
        return ["city"]
    
    @property
    def category(self) -> str:
        return "information"
    
    @property
    def tags(self) -> List[str]:
        return ["weather", "information", "api"]
    
    @property
    def is_enabled(self) -> bool:
        return bool(self.api_key)
    
    async def _execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """
        执行天气查询
        
        Args:
            parameters: 包含city、country_code和units参数的字典
            context: 执行上下文
        
        Returns:
            天气查询结果
        """
        if not self.api_key:
            return ToolResult.error_result("未配置天气API密钥")
        
        city = parameters.get("city", "").strip()
        country_code = parameters.get("country_code", "").strip()
        units = parameters.get("units", "metric").strip()
        
        if not city:
            return ToolResult.error_result("城市名称不能为空")
        
        # 构建查询参数
        query_params = {
            "q": f"{city},{country_code}" if country_code else city,
            "appid": self.api_key,
            "units": units,
            "lang": "zh_cn"  # 使用中文返回结果
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=query_params) as response:
                    if response.status != 200:
                        error_data = await response.text()
                        return ToolResult.error_result(f"天气API错误: {error_data}")
                    
                    data = await response.json()
                    
                    # 提取有用的天气信息
                    weather_info = {
                        "city": data.get("name", city),
                        "country": data.get("sys", {}).get("country", country_code),
                        "weather": data.get("weather", [{}])[0].get("description", "未知"),
                        "temperature": data.get("main", {}).get("temp", 0),
                        "feels_like": data.get("main", {}).get("feels_like", 0),
                        "humidity": data.get("main", {}).get("humidity", 0),
                        "pressure": data.get("main", {}).get("pressure", 0),
                        "wind_speed": data.get("wind", {}).get("speed", 0),
                        "wind_direction": data.get("wind", {}).get("deg", 0),
                        "clouds": data.get("clouds", {}).get("all", 0),
                        "timestamp": data.get("dt", 0)
                    }
                    
                    # 构建人类可读的天气描述
                    temp_unit = "°C" if units == "metric" else "°F"
                    weather_description = (
                        f"{weather_info['city']}的天气：{weather_info['weather']}，"
                        f"温度{weather_info['temperature']}{temp_unit}，"
                        f"体感温度{weather_info['feels_like']}{temp_unit}，"
                        f"湿度{weather_info['humidity']}%，"
                        f"风速{weather_info['wind_speed']}m/s"
                    )
                    
                    return ToolResult.success_result(
                        content=weather_description,
                        content_type="text",
                        metadata=weather_info
                    )
        
        except aiohttp.ClientError as e:
            return ToolResult.error_result(f"网络请求错误: {str(e)}")
        
        except Exception as e:
            return ToolResult.error_result(f"天气查询错误: {str(e)}")
