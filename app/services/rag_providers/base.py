"""RAG/搜索系统基础抽象类"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class QueryResult:
    """查询结果数据类"""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    sources: Optional[list] = None
    usage: Optional[Dict[str, Any]] = None


class BaseRAGProvider(ABC):
    """RAG/搜索系统基础抽象类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化提供商
        
        Args:
            config: 提供商配置字典
        """
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置参数
        
        Raises:
            ValueError: 配置无效时抛出
        """
        pass
    
    @abstractmethod
    async def query(
        self, 
        text: str, 
        user: str = "default-user",
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> QueryResult:
        """执行查询
        
        Args:
            text: 查询文本
            user: 用户标识
            conversation_id: 会话ID（可选）
            **kwargs: 其他查询参数
            
        Returns:
            QueryResult: 查询结果
            
        Raises:
            Exception: 查询失败时抛出
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 服务是否可用
        """
        pass
    
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return self.__class__.__name__


class BaseSearchProvider(ABC):
    """搜索系统基础抽象类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化提供商
        
        Args:
            config: 提供商配置字典
        """
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置参数
        
        Raises:
            ValueError: 配置无效时抛出
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> QueryResult:
        """执行搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            **kwargs: 其他搜索参数
            
        Returns:
            QueryResult: 搜索结果
            
        Raises:
            Exception: 搜索失败时抛出
        """
        pass
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 服务是否可用
        """
        try:
            # 执行简单搜索测试
            await self.search("test", num_results=1)
            return True
        except Exception:
            return False
    
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return self.__class__.__name__


class RAGProviderFactory:
    """RAG 提供商工厂类"""
    
    _providers: Dict[str, type] = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type) -> None:
        """注册提供商
        
        Args:
            name: 提供商名称
            provider_class: 提供商类
        """
        cls._providers[name] = provider_class
    
    @classmethod
    def create_provider(cls, name: str, config: Dict[str, Any]) -> BaseRAGProvider:
        """创建提供商实例
        
        Args:
            name: 提供商名称
            config: 配置字典
            
        Returns:
            BaseRAGProvider: 提供商实例
            
        Raises:
            ValueError: 提供商不存在或配置无效
        """
        if name not in cls._providers:
            raise ValueError(f"Unknown provider: {name}")
        
        provider_class = cls._providers[name]
        return provider_class(config)
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """列出所有可用的提供商
        
        Returns:
            list[str]: 提供商名称列表
        """
        return list(cls._providers.keys())
