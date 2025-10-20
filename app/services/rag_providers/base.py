"""RAG和搜索提供商的基础抽象类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator
from app.models.batch_task import QueryResult


class BaseRAGProvider(ABC):
    """RAG提供商基础抽象类
    
    定义RAG服务提供商的标准接口。所有RAG提供商必须实现这些方法。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化RAG提供商
        
        Args:
            config: 提供商配置，包含API密钥、端点等
        """
        self.config = config
    
    @abstractmethod
    async def query(self, question: str, **kwargs) -> QueryResult:
        """查询RAG服务
        
        Args:
            question: 用户问题
            **kwargs: 额外的查询参数
            
        Returns:
            QueryResult: 标准化的查询结果
            
        Raises:
            Exception: 查询失败时抛出异常
        """
        pass
    
    @abstractmethod
    async def stream_query(self, question: str, **kwargs) -> AsyncIterator[str]:
        """流式查询RAG服务
        
        Args:
            question: 用户问题
            **kwargs: 额外的查询参数
            
        Yields:
            str: 流式返回的答案片段
            
        Raises:
            Exception: 查询失败时抛出异常
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 如果服务可用返回True，否则返回False
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        pass
    
    @property
    def provider_type(self) -> str:
        """提供商类型"""
        return "RAG"


class BaseSearchProvider(ABC):
    """搜索提供商基础抽象类
    
    定义搜索服务提供商的标准接口。所有搜索提供商必须实现这些方法。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化搜索提供商
        
        Args:
            config: 提供商配置，包含API密钥、端点等
        """
        self.config = config
    
    @abstractmethod
    async def search(self, query: str, **kwargs) -> QueryResult:
        """执行搜索
        
        Args:
            query: 搜索查询
            **kwargs: 额外的搜索参数
            
        Returns:
            QueryResult: 标准化的搜索结果
            
        Raises:
            Exception: 搜索失败时抛出异常
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 如果服务可用返回True，否则返回False
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        pass
    
    @property
    def provider_type(self) -> str:
        """提供商类型"""
        return "Search"
