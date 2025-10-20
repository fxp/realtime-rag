"""RAG服务管理器"""

from typing import Dict, Any, Optional, AsyncIterator
from app.services.rag_providers.base import BaseRAGProvider, BaseSearchProvider
from app.services.rag_providers import (
    ContextProvider, OpenAIProvider, SerperProvider, CustomRAGProvider, DifyProvider
)
from app.models.batch_task import QueryResult
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """RAG服务管理器
    
    统一管理RAG和搜索服务提供商，提供统一的查询接口。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化RAG服务
        
        Args:
            config: 服务配置，包含RAG和搜索提供商的配置
        """
        self.config = config
        self.rag_provider: Optional[BaseRAGProvider] = None
        self.search_provider: Optional[BaseSearchProvider] = None
        
        # 初始化RAG提供商
        rag_config = config.get("rag", {})
        if rag_config:
            self._init_rag_provider(rag_config)
        
        # 初始化搜索提供商
        search_config = config.get("search", {})
        if search_config:
            self._init_search_provider(search_config)
    
    def _init_rag_provider(self, config: Dict[str, Any]) -> None:
        """初始化RAG提供商
        
        Args:
            config: RAG提供商配置
        """
        provider_type = config.get("provider", "").lower()
        
        try:
            if provider_type == "context":
                self.rag_provider = ContextProvider(config)
            elif provider_type == "openai":
                self.rag_provider = OpenAIProvider(config)
            elif provider_type == "dify":
                self.rag_provider = DifyProvider(config)
            elif provider_type == "custom":
                self.rag_provider = CustomRAGProvider(config)
            else:
                logger.warning(f"Unknown RAG provider type: {provider_type}")
        except Exception as e:
            logger.error(f"Failed to initialize RAG provider: {e}")
    
    def _init_search_provider(self, config: Dict[str, Any]) -> None:
        """初始化搜索提供商
        
        Args:
            config: 搜索提供商配置
        """
        provider_type = config.get("provider", "").lower()
        
        try:
            if provider_type == "serper":
                self.search_provider = SerperProvider(config)
            else:
                logger.warning(f"Unknown search provider type: {provider_type}")
        except Exception as e:
            logger.error(f"Failed to initialize search provider: {e}")
    
    async def query(self, question: str, use_search: bool = False, **kwargs) -> QueryResult:
        """执行查询
        
        Args:
            question: 用户问题
            use_search: 是否使用搜索服务（如果检测到搜索关键词）
            **kwargs: 额外参数
            
        Returns:
            QueryResult: 查询结果
            
        Raises:
            Exception: 如果查询失败或没有可用的提供商
        """
        # 自动检测是否需要使用搜索
        if not use_search:
            use_search = self._should_use_search(question)
        
        # 优先使用搜索服务
        if use_search and self.search_provider:
            logger.info(f"Using search provider for question: {question}")
            return await self.search_provider.search(question, **kwargs)
        
        # 使用RAG服务
        if self.rag_provider:
            logger.info(f"Using RAG provider for question: {question}")
            return await self.rag_provider.query(question, **kwargs)
        
        raise Exception("没有可用的RAG或搜索服务提供商")
    
    async def stream_query(self, question: str, **kwargs) -> AsyncIterator[str]:
        """流式查询
        
        Args:
            question: 用户问题
            **kwargs: 额外参数
            
        Yields:
            str: 答案片段
            
        Raises:
            Exception: 如果查询失败或没有可用的RAG提供商
        """
        if not self.rag_provider:
            raise Exception("没有可用的RAG服务提供商")
        
        logger.info(f"Streaming query for question: {question}")
        async for chunk in self.rag_provider.stream_query(question, **kwargs):
            yield chunk
    
    def _should_use_search(self, question: str) -> bool:
        """判断是否应该使用搜索服务
        
        检测问题中是否包含搜索相关的关键词。
        
        Args:
            question: 用户问题
            
        Returns:
            bool: 如果应该使用搜索返回True
        """
        search_keywords = [
            '搜索', '查找', '找', '搜', 'search', 'find', 'look up',
            '最新', '新闻', 'latest', 'news', 'recent',
            '天气', 'weather', '股票', 'stock'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in search_keywords)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        result = {
            "rag": False,
            "search": False,
            "providers": {}
        }
        
        # 检查RAG提供商
        if self.rag_provider:
            try:
                result["rag"] = await self.rag_provider.health_check()
                result["providers"]["rag"] = {
                    "name": self.rag_provider.name,
                    "type": self.rag_provider.provider_type,
                    "status": result["rag"]
                }
            except Exception as e:
                logger.error(f"RAG provider health check failed: {e}")
        
        # 检查搜索提供商
        if self.search_provider:
            try:
                result["search"] = await self.search_provider.health_check()
                result["providers"]["search"] = {
                    "name": self.search_provider.name,
                    "type": self.search_provider.provider_type,
                    "status": result["search"]
                }
            except Exception as e:
                logger.error(f"Search provider health check failed: {e}")
        
        return result
    
    @property
    def is_available(self) -> bool:
        """检查是否有可用的服务提供商
        
        Returns:
            bool: 如果有任何可用的提供商返回True
        """
        return self.rag_provider is not None or self.search_provider is not None
