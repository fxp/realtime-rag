"""RAG 服务管理器"""
from __future__ import annotations
from typing import Optional, Dict, Any, Union
from .rag_providers.base import BaseRAGProvider, BaseSearchProvider, QueryResult, RAGProviderFactory
from .rag_providers.dify import DifyProvider
from .rag_providers.serper import SerperProvider
from .rag_providers.custom import CustomRAGProvider, CustomSearchProvider


class RAGService:
    """RAG 服务管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化 RAG 服务
        
        Args:
            config: 服务配置
        """
        self.config = config
        self._rag_provider: Optional[BaseRAGProvider] = None
        self._search_provider: Optional[BaseSearchProvider] = None
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """初始化提供商"""
        # 注册 RAG 提供商
        RAGProviderFactory.register_provider("dify", DifyProvider)
        RAGProviderFactory.register_provider("custom", CustomRAGProvider)
        
        # 初始化 RAG 提供商
        rag_config = self.config.get("rag", {})
        if rag_config:
            provider_type = rag_config.get("provider", "dify")
            provider_config = rag_config.get("config", {})
            try:
                self._rag_provider = RAGProviderFactory.create_provider(provider_type, provider_config)
            except Exception as e:
                print(f"Warning: Failed to initialize RAG provider {provider_type}: {e}")
        
        # 初始化搜索提供商
        search_config = self.config.get("search", {})
        if search_config:
            provider_type = search_config.get("provider", "serper")
            provider_config = search_config.get("config", {})
            try:
                if provider_type == "serper":
                    self._search_provider = SerperProvider(provider_config)
                elif provider_type == "custom":
                    self._search_provider = CustomSearchProvider(provider_config)
                else:
                    print(f"Warning: Unknown search provider: {provider_type}")
            except Exception as e:
                print(f"Warning: Failed to initialize search provider {provider_type}: {e}")
    
    async def query(
        self,
        text: str,
        user: str = "default-user",
        conversation_id: Optional[str] = None,
        use_search: bool = False,
        **kwargs
    ) -> QueryResult:
        """执行查询
        
        Args:
            text: 查询文本
            user: 用户标识
            conversation_id: 会话ID
            use_search: 是否使用搜索提供商
            **kwargs: 其他参数
            
        Returns:
            QueryResult: 查询结果
            
        Raises:
            Exception: 查询失败时抛出
        """
        if use_search and self._search_provider:
            return await self._search_provider.search(text, **kwargs)
        elif self._rag_provider:
            return await self._rag_provider.query(text, user, conversation_id, **kwargs)
        else:
            raise Exception("没有可用的 RAG 或搜索提供商")
    
    async def health_check(self) -> Dict[str, bool]:
        """健康检查
        
        Returns:
            Dict[str, bool]: 各提供商健康状态
        """
        status = {}
        
        if self._rag_provider:
            try:
                status["rag"] = await self._rag_provider.health_check()
            except Exception:
                status["rag"] = False
        else:
            status["rag"] = False
        
        if self._search_provider:
            try:
                status["search"] = await self._search_provider.health_check()
            except Exception:
                status["search"] = False
        else:
            status["search"] = False
        
        return status
    
    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息
        
        Returns:
            Dict[str, Any]: 提供商信息
        """
        info = {}
        
        if self._rag_provider:
            info["rag"] = {
                "name": self._rag_provider.get_provider_name(),
                "type": "RAG"
            }
        
        if self._search_provider:
            info["search"] = {
                "name": self._search_provider.get_provider_name(),
                "type": "Search"
            }
        
        return info
    
    def is_available(self) -> bool:
        """检查是否有可用的提供商
        
        Returns:
            bool: 是否有可用的提供商
        """
        return self._rag_provider is not None or self._search_provider is not None


# 全局 RAG 服务实例
_rag_service: Optional[RAGService] = None


def initialize_rag_service(config: Dict[str, Any]) -> RAGService:
    """初始化全局 RAG 服务
    
    Args:
        config: 服务配置
        
    Returns:
        RAGService: RAG 服务实例
    """
    global _rag_service
    _rag_service = RAGService(config)
    return _rag_service


def get_rag_service() -> Optional[RAGService]:
    """获取全局 RAG 服务实例
    
    Returns:
        Optional[RAGService]: RAG 服务实例，如果未初始化则返回 None
    """
    return _rag_service
