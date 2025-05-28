"""
知识库集成模块
提供连接和查询外部知识库的能力
"""
import logging
import json
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime

import aiohttp
from fastapi import HTTPException

from ..config import settings


class KnowledgeBaseConnector:
    """知识库连接器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "未命名知识库")
        self.connector_type = "base"
        self.logger = logging.getLogger(f"KnowledgeBase:{self.name}")
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索知识库
        
        Args:
            query: 查询字符串
            limit: 结果数量限制
        
        Returns:
            搜索结果列表
        """
        raise NotImplementedError("子类必须实现search方法")
    
    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        获取文档详情
        
        Args:
            document_id: 文档ID
        
        Returns:
            文档详情
        """
        raise NotImplementedError("子类必须实现get_document方法")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态
        """
        raise NotImplementedError("子类必须实现health_check方法")


class VectorDBConnector(KnowledgeBaseConnector):
    """向量数据库连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connector_type = "vector_db"
        self.api_url = config.get("api_url", "")
        self.api_key = config.get("api_key", "")
        self.collection_name = config.get("collection_name", "")
        self.embedding_model = config.get("embedding_model", "text-embedding-ada-002")
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self.session
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索向量数据库"""
        try:
            session = await self._get_session()
            
            # 构建请求数据
            payload = {
                "query": query,
                "collection_name": self.collection_name,
                "limit": limit,
                "embedding_model": self.embedding_model
            }
            
            # 发送请求
            async with session.post(f"{self.api_url}/search", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"向量数据库搜索失败: {error_text}")
                    return []
                
                result = await response.json()
                return result.get("results", [])
        
        except Exception as e:
            self.logger.error(f"向量数据库搜索异常: {str(e)}")
            return []
    
    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """获取文档详情"""
        try:
            session = await self._get_session()
            
            # 发送请求
            async with session.get(f"{self.api_url}/documents/{document_id}", params={"collection_name": self.collection_name}) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"获取文档失败: {error_text}")
                    return {}
                
                return await response.json()
        
        except Exception as e:
            self.logger.error(f"获取文档异常: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            session = await self._get_session()
            
            # 发送请求
            async with session.get(f"{self.api_url}/health") as response:
                if response.status != 200:
                    return {"status": "error", "message": await response.text()}
                
                return {"status": "ok", "details": await response.json()}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}


class ElasticsearchConnector(KnowledgeBaseConnector):
    """Elasticsearch连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connector_type = "elasticsearch"
        self.api_url = config.get("api_url", "")
        self.api_key = config.get("api_key", "")
        self.index_name = config.get("index_name", "")
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"ApiKey {self.api_key}"
            
            auth = None
            if self.username and self.password:
                auth = aiohttp.BasicAuth(self.username, self.password)
            
            self.session = aiohttp.ClientSession(headers=headers, auth=auth)
        
        return self.session
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索Elasticsearch"""
        try:
            session = await self._get_session()
            
            # 构建搜索请求
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content", "summary^1.5"]
                    }
                },
                "size": limit
            }
            
            # 发送请求
            async with session.post(f"{self.api_url}/{self.index_name}/_search", json=search_body) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Elasticsearch搜索失败: {error_text}")
                    return []
                
                result = await response.json()
                hits = result.get("hits", {}).get("hits", [])
                
                # 格式化结果
                return [
                    {
                        "id": hit["_id"],
                        "score": hit["_score"],
                        "title": hit["_source"].get("title", ""),
                        "content": hit["_source"].get("content", ""),
                        "metadata": hit["_source"].get("metadata", {})
                    }
                    for hit in hits
                ]
        
        except Exception as e:
            self.logger.error(f"Elasticsearch搜索异常: {str(e)}")
            return []
    
    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """获取文档详情"""
        try:
            session = await self._get_session()
            
            # 发送请求
            async with session.get(f"{self.api_url}/{self.index_name}/_doc/{document_id}") as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"获取文档失败: {error_text}")
                    return {}
                
                result = await response.json()
                source = result.get("_source", {})
                
                return {
                    "id": result["_id"],
                    "title": source.get("title", ""),
                    "content": source.get("content", ""),
                    "metadata": source.get("metadata", {})
                }
        
        except Exception as e:
            self.logger.error(f"获取文档异常: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            session = await self._get_session()
            
            # 发送请求
            async with session.get(f"{self.api_url}/_cluster/health") as response:
                if response.status != 200:
                    return {"status": "error", "message": await response.text()}
                
                return {"status": "ok", "details": await response.json()}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}


class WebAPIConnector(KnowledgeBaseConnector):
    """Web API连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connector_type = "web_api"
        self.api_url = config.get("api_url", "")
        self.api_key = config.get("api_key", "")
        self.search_endpoint = config.get("search_endpoint", "/search")
        self.document_endpoint = config.get("document_endpoint", "/documents")
        self.headers = config.get("headers", {})
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索Web API"""
        try:
            session = await self._get_session()
            
            # 构建请求参数
            params = {
                "query": query,
                "limit": limit
            }
            
            # 发送请求
            async with session.get(f"{self.api_url}{self.search_endpoint}", params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Web API搜索失败: {error_text}")
                    return []
                
                result = await response.json()
                return result.get("results", [])
        
        except Exception as e:
            self.logger.error(f"Web API搜索异常: {str(e)}")
            return []
    
    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """获取文档详情"""
        try:
            session = await self._get_session()
            
            # 发送请求
            async with session.get(f"{self.api_url}{self.document_endpoint}/{document_id}") as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"获取文档失败: {error_text}")
                    return {}
                
                return await response.json()
        
        except Exception as e:
            self.logger.error(f"获取文档异常: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            session = await self._get_session()
            
            # 发送请求
            async with session.get(f"{self.api_url}/health") as response:
                if response.status != 200:
                    return {"status": "error", "message": await response.text()}
                
                return {"status": "ok", "details": await response.json()}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}


class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger("KnowledgeBaseManager")
        self.connectors: Dict[str, KnowledgeBaseConnector] = {}
        self.connector_types = {
            "vector_db": VectorDBConnector,
            "elasticsearch": ElasticsearchConnector,
            "web_api": WebAPIConnector
        }
    
    def register_connector(self, config: Dict[str, Any]) -> str:
        """
        注册知识库连接器
        
        Args:
            config: 连接器配置
        
        Returns:
            连接器ID
        """
        try:
            connector_type = config.get("type", "")
            if connector_type not in self.connector_types:
                raise ValueError(f"不支持的连接器类型: {connector_type}")
            
            # 生成连接器ID
            connector_id = config.get("id", f"kb:{uuid.uuid4()}")
            
            # 创建连接器实例
            connector_class = self.connector_types[connector_type]
            connector = connector_class(config)
            
            # 注册连接器
            self.connectors[connector_id] = connector
            self.logger.info(f"已注册知识库连接器: {connector.name} ({connector_id})")
            
            return connector_id
        
        except Exception as e:
            self.logger.error(f"注册知识库连接器失败: {str(e)}")
            raise
    
    def get_connector(self, connector_id: str) -> Optional[KnowledgeBaseConnector]:
        """
        获取知识库连接器
        
        Args:
            connector_id: 连接器ID
        
        Returns:
            连接器实例
        """
        return self.connectors.get(connector_id)
    
    def list_connectors(self) -> List[Dict[str, Any]]:
        """
        列出所有知识库连接器
        
        Returns:
            连接器列表
        """
        return [
            {
                "id": connector_id,
                "name": connector.name,
                "type": connector.connector_type,
                "config": {
                    k: v for k, v in connector.config.items()
                    if k not in ["api_key", "password"]  # 排除敏感信息
                }
            }
            for connector_id, connector in self.connectors.items()
        ]
    
    def remove_connector(self, connector_id: str) -> bool:
        """
        移除知识库连接器
        
        Args:
            connector_id: 连接器ID
        
        Returns:
            是否成功移除
        """
        if connector_id in self.connectors:
            del self.connectors[connector_id]
            self.logger.info(f"已移除知识库连接器: {connector_id}")
            return True
        return False
    
    async def search_all(self, query: str, limit_per_connector: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        搜索所有知识库
        
        Args:
            query: 查询字符串
            limit_per_connector: 每个连接器的结果数量限制
        
        Returns:
            所有连接器的搜索结果
        """
        results = {}
        tasks = []
        
        # 创建所有连接器的搜索任务
        for connector_id, connector in self.connectors.items():
            task = asyncio.create_task(self._search_connector(connector_id, connector, query, limit_per_connector))
            tasks.append(task)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
        # 收集结果
        for task in tasks:
            connector_id, connector_results = task.result()
            if connector_results:
                results[connector_id] = connector_results
        
        return results
    
    async def _search_connector(
        self,
        connector_id: str,
        connector: KnowledgeBaseConnector,
        query: str,
        limit: int
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """单个连接器搜索"""
        try:
            results = await connector.search(query, limit)
            return connector_id, results
        except Exception as e:
            self.logger.error(f"连接器 {connector_id} 搜索失败: {str(e)}")
            return connector_id, []
    
    async def search(
        self,
        connector_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索特定知识库
        
        Args:
            connector_id: 连接器ID
            query: 查询字符串
            limit: 结果数量限制
        
        Returns:
            搜索结果
        """
        connector = self.get_connector(connector_id)
        if not connector:
            raise HTTPException(status_code=404, detail=f"知识库连接器不存在: {connector_id}")
        
        return await connector.search(query, limit)
    
    async def get_document(
        self,
        connector_id: str,
        document_id: str
    ) -> Dict[str, Any]:
        """
        获取文档详情
        
        Args:
            connector_id: 连接器ID
            document_id: 文档ID
        
        Returns:
            文档详情
        """
        connector = self.get_connector(connector_id)
        if not connector:
            raise HTTPException(status_code=404, detail=f"知识库连接器不存在: {connector_id}")
        
        document = await connector.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"文档不存在: {document_id}")
        
        return document
    
    async def check_health(self, connector_id: str) -> Dict[str, Any]:
        """
        检查知识库健康状态
        
        Args:
            connector_id: 连接器ID
        
        Returns:
            健康状态
        """
        connector = self.get_connector(connector_id)
        if not connector:
            raise HTTPException(status_code=404, detail=f"知识库连接器不存在: {connector_id}")
        
        return await connector.health_check()
    
    async def check_all_health(self) -> Dict[str, Dict[str, Any]]:
        """
        检查所有知识库健康状态
        
        Returns:
            所有连接器的健康状态
        """
        results = {}
        tasks = []
        
        # 创建所有连接器的健康检查任务
        for connector_id, connector in self.connectors.items():
            task = asyncio.create_task(self._check_connector_health(connector_id, connector))
            tasks.append(task)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
        # 收集结果
        for task in tasks:
            connector_id, health_status = task.result()
            results[connector_id] = health_status
        
        return results
    
    async def _check_connector_health(
        self,
        connector_id: str,
        connector: KnowledgeBaseConnector
    ) -> Tuple[str, Dict[str, Any]]:
        """单个连接器健康检查"""
        try:
            health_status = await connector.health_check()
            return connector_id, health_status
        except Exception as e:
            self.logger.error(f"连接器 {connector_id} 健康检查失败: {str(e)}")
            return connector_id, {"status": "error", "message": str(e)}


# 创建全局知识库管理器实例
kb_manager = KnowledgeBaseManager()


# 注册默认知识库连接器
def register_default_connectors():
    """注册默认知识库连接器"""
    # 如果配置了默认知识库
    if hasattr(settings, 'DEFAULT_KNOWLEDGE_BASES') and settings.DEFAULT_KNOWLEDGE_BASES:
        for kb_config in settings.DEFAULT_KNOWLEDGE_BASES:
            try:
                kb_manager.register_connector(kb_config)
            except Exception as e:
                logging.error(f"注册默认知识库连接器失败: {str(e)}")


# 初始化默认知识库连接器
register_default_connectors()
