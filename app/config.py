"""
配置文件
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 应用配置
APP_NAME = "RainbowAI对话管理系统"
APP_VERSION = "0.1.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# 数据库配置
DB_URL = os.getenv("DB_URL", "memory")  # 默认使用内存存储
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAMESPACE = os.getenv("DB_NAMESPACE", "rainbow")
DB_DATABASE = os.getenv("DB_DATABASE", "dialogue")

# LLM配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")  # mock, openai, azure
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# 对话配置
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
RESPONSE_WINDOW_HOURS = int(os.getenv("RESPONSE_WINDOW_HOURS", "3"))
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "1"))

# 工具配置
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "")

# CORS配置
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# 媒体存储配置
MEDIA_STORAGE_PATH = os.getenv("MEDIA_STORAGE_PATH", "media")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))  # 默认10MB
ALLOWED_MEDIA_TYPES = os.getenv("ALLOWED_MEDIA_TYPES", "image,audio,video").split(",")

# 获取完整配置
def get_config() -> Dict[str, Any]:
    """获取完整配置"""
    return {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "debug": DEBUG
        },
        "server": {
            "host": HOST,
            "port": PORT
        },
        "database": {
            "url": DB_URL,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "namespace": DB_NAMESPACE,
            "database": DB_DATABASE
        },
        "llm": {
            "provider": LLM_PROVIDER,
            "api_key": LLM_API_KEY,
            "api_url": LLM_API_URL,
            "model": LLM_MODEL
        },
        "dialogue": {
            "max_context_length": MAX_CONTEXT_LENGTH,
            "response_window_hours": RESPONSE_WINDOW_HOURS,
            "session_timeout_hours": SESSION_TIMEOUT_HOURS
        },
        "tools": {
            "weather_api_key": WEATHER_API_KEY,
            "search_api_key": SEARCH_API_KEY
        },
        "log": {
            "level": LOG_LEVEL,
            "file": LOG_FILE
        },
        "cors": {
            "origins": CORS_ORIGINS
        },
        "media": {
            "storage_path": MEDIA_STORAGE_PATH,
            "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
            "allowed_types": ALLOWED_MEDIA_TYPES
        }
    }

# 创建settings对象，供其他模块导入
class Settings:
    """配置设置类"""
    def __init__(self):
        # 应用配置
        self.APP_NAME = APP_NAME
        self.APP_VERSION = APP_VERSION
        self.DEBUG = DEBUG
        
        # 服务器配置
        self.HOST = HOST
        self.PORT = PORT
        
        # 数据库配置
        self.DB_URL = DB_URL
        self.DB_USER = DB_USER
        self.DB_PASSWORD = DB_PASSWORD
        self.DB_NAMESPACE = DB_NAMESPACE
        self.DB_DATABASE = DB_DATABASE
        
        # LLM配置
        self.LLM_PROVIDER = LLM_PROVIDER
        self.LLM_API_KEY = LLM_API_KEY
        self.LLM_API_URL = LLM_API_URL
        self.LLM_MODEL = LLM_MODEL
        
        # 对话配置
        self.MAX_CONTEXT_LENGTH = MAX_CONTEXT_LENGTH
        self.RESPONSE_WINDOW_HOURS = RESPONSE_WINDOW_HOURS
        self.SESSION_TIMEOUT_HOURS = SESSION_TIMEOUT_HOURS
        
        # 工具配置
        self.WEATHER_API_KEY = WEATHER_API_KEY
        self.SEARCH_API_KEY = SEARCH_API_KEY
        
        # 日志配置
        self.LOG_LEVEL = LOG_LEVEL
        self.LOG_FILE = LOG_FILE
        
        # CORS配置
        self.CORS_ORIGINS = CORS_ORIGINS
        
        # 媒体存储配置
        self.MEDIA_STORAGE_PATH = MEDIA_STORAGE_PATH
        self.MAX_UPLOAD_SIZE_MB = MAX_UPLOAD_SIZE_MB
        self.ALLOWED_MEDIA_TYPES = ALLOWED_MEDIA_TYPES
        
        # 知识库配置
        self.DEFAULT_KNOWLEDGE_BASES = []

# 创建全局settings实例
settings = Settings()
