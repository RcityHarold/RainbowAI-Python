"""
中间件模块
用于处理请求和响应
"""
import time
import uuid
import json
import traceback
from typing import Callable, Dict, Any
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from .core.logger import logger
from .config import get_config


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件，记录请求和响应"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID，用于全链路跟踪
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = request.client.host if request.client else "unknown"
        headers = dict(request.headers)
        
        # 移除敏感信息
        if "authorization" in headers:
            headers["authorization"] = "[REDACTED]"
        if "api-key" in headers:
            headers["api-key"] = "[REDACTED]"
        
        # 尝试获取请求体
        request_body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                # 保存原始请求体
                body_bytes = await request.body()
                request_body = body_bytes.decode()
                
                # 尝试解析JSON
                try:
                    request_data = json.loads(request_body)
                except json.JSONDecodeError:
                    request_data = {"raw": "[non-json content]"}
            except Exception:
                request_data = {"error": "Could not read request body"}
        else:
            request_data = {}
        
        # 记录请求开始
        logger.info(
            f"API Request Started: {method} {path}",
            request_id=request_id,
            method=method,
            path=path,
            query_params=query_params,
            client_ip=client_ip,
            headers=headers,
            request_data=request_data
        )
        
        # 处理请求
        try:
            # 调用下一个中间件或路由处理程序
            response = await call_next(request)
            
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000  # 毫秒
            
            # 获取响应信息
            status_code = response.status_code
            response_headers = dict(response.headers)
            
            # 尝试获取响应体
            response_body = None
            if "content-type" in response_headers and "application/json" in response_headers["content-type"].lower():
                # 保存原始响应
                original_response_body = b""
                async for chunk in response.body_iterator:
                    original_response_body += chunk
                
                # 重新构建响应
                response = Response(
                    content=original_response_body,
                    status_code=status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                
                # 尝试解析响应体
                try:
                    response_body = original_response_body.decode()
                    response_data = json.loads(response_body)
                except Exception:
                    response_data = {"raw": "[could not parse response]"}
            else:
                response_data = {"content_type": response.media_type or "unknown"}
            
            # 记录请求完成日志
            logger.log_api_request(
                method=method,
                path=path,
                client_ip=client_ip,
                status_code=status_code,
                response_time=response_time,
                request_data=request_data
            )
            
            # 记录请求结束
            logger.info(
                f"API Request Completed: {method} {path} - {status_code}",
                request_id=request_id,
                method=method,
                path=path,
                status_code=status_code,
                response_time=response_time,
                response_headers=response_headers,
                response_data=response_data
            )
            
            return response
        
        except Exception as e:
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000  # 毫秒
            
            # 记录错误日志
            error_detail = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            
            logger.error(
                f"API Request Failed: {method} {path} - {type(e).__name__}: {str(e)}",
                request_id=request_id,
                method=method,
                path=path,
                error=error_detail,
                response_time=response_time,
                request_data=request_data
            )
            
            logger.log_api_request(
                method=method,
                path=path,
                client_ip=client_ip,
                status_code=500,
                response_time=response_time,
                request_data=request_data,
                error=str(e)
            )
            
            # 重新抛出异常，让FastAPI处理
            raise


def setup_middleware(app: FastAPI):
    """设置中间件"""
    # 获取配置
    config = get_config()
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config["cors"]["origins"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加日志中间件
    app.add_middleware(LoggingMiddleware)
