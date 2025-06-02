"""
SurrealDB数据库连接和操作
"""
import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime

import surrealdb
from surrealdb.ws import Surreal

from ..config import get_config


class Database:
    """SurrealDB数据库连接和操作"""
    
    def __init__(self):
        self.logger = logging.getLogger("Database")
        self.config = get_config()["database"]
        self.db_url = self.config["url"]
        self.db_user = self.config["user"]
        self.db_password = self.config["password"]
        self.db_namespace = self.config["namespace"]
        self.db_database = self.config["database"]
        self.client = None
        self.connected = False
    
    async def connect(self) -> bool:
        """
        连接数据库
        
        Returns:
            连接是否成功
        """
        try:
            # 如果已连接，先断开
            if self.client and self.connected:
                await self.disconnect()
            
            # 如果使用内存存储，不需要连接数据库
            if self.db_url == "memory":
                self.logger.info("Using memory storage, no database connection needed")
                self.connected = True
                return True
            
            # 连接数据库
            self.logger.info(f"Connecting to database: {self.db_url}")
            self.client = Surreal(self.db_url)
            await self.client.connect()
            
            # 登录
            await self.client.signin({"user": self.db_user, "pass": self.db_password})
            
            # 使用命名空间和数据库
            await self.client.use(self.db_namespace, self.db_database)
            
            self.connected = True
            self.logger.info("Database connected")
            return True
        
        except Exception as e:
            self.logger.error(f"Error connecting to database: {str(e)}")
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        断开数据库连接
        
        Returns:
            断开是否成功
        """
        try:
            if self.client and self.connected:
                await self.client.close()
                self.connected = False
                self.logger.info("Database disconnected")
            return True
        
        except Exception as e:
            self.logger.error(f"Error disconnecting from database: {str(e)}")
            return False
    
    async def ensure_connected(self) -> bool:
        """
        确保数据库已连接
        
        Returns:
            是否已连接
        """
        if not self.connected:
            return await self.connect()
        return True
    
    async def create(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建记录
        
        Args:
            table: 表名
            data: 数据
        
        Returns:
            创建的记录
        """
        try:
            # 如果使用内存存储，直接返回数据
            if self.db_url == "memory":
                return data
            
            # 确保已连接
            if not await self.ensure_connected():
                return None
            
            # 创建记录
            result = await self.client.create(table, data)
            
            if result and len(result) > 0:
                return result[0]
            return None
        
        except Exception as e:
            self.logger.error(f"Error creating record in {table}: {str(e)}")
            return None
    
    async def select(self, table: str, id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        查询记录
        
        Args:
            table: 表名
            id: 记录ID，如果为None则查询所有记录
        
        Returns:
            查询结果
        """
        try:
            # 如果使用内存存储，直接返回空列表
            if self.db_url == "memory":
                return []
            
            # 确保已连接
            if not await self.ensure_connected():
                return []
            
            # 查询记录
            if id:
                result = await self.client.select(f"{table}:{id}")
            else:
                result = await self.client.select(table)
            
            return result or []
        
        except Exception as e:
            self.logger.error(f"Error selecting from {table}: {str(e)}")
            return []
    
    async def update(self, table: str, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新记录
        
        Args:
            table: 表名
            id: 记录ID
            data: 数据
        
        Returns:
            更新后的记录
        """
        try:
            # 如果使用内存存储，直接返回数据
            if self.db_url == "memory":
                return data
            
            # 确保已连接
            if not await self.ensure_connected():
                return None
            
            # 更新记录
            result = await self.client.update(f"{table}:{id}", data)
            
            if result and len(result) > 0:
                return result[0]
            return None
        
        except Exception as e:
            self.logger.error(f"Error updating {table}:{id}: {str(e)}")
            return None
    
    async def delete(self, table: str, id: str) -> bool:
        """
        删除记录
        
        Args:
            table: 表名
            id: 记录ID
        
        Returns:
            是否删除成功
        """
        try:
            # 如果使用内存存储，直接返回成功
            if self.db_url == "memory":
                return True
            
            # 确保已连接
            if not await self.ensure_connected():
                return False
            
            # 删除记录
            await self.client.delete(f"{table}:{id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error deleting {table}:{id}: {str(e)}")
            return False
    
    async def query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行查询
        
        Args:
            query: 查询语句
            params: 查询参数
        
        Returns:
            查询结果
        """
        try:
            # 如果使用内存存储，直接返回空列表
            if self.db_url == "memory":
                return []
            
            # 确保已连接
            if not await self.ensure_connected():
                return []
            
            # 执行查询
            result = await self.client.query(query, params or {})
            
            return result or []
        
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            return []


# 创建数据库实例
db = Database()
