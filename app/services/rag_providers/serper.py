"""Serper搜索提供商实现"""

import httpx
from typing import Dict, Any
from .base import BaseSearchProvider
from app.models.batch_task import QueryResult
import logging

logger = logging.getLogger(__name__)


class SerperProvider(BaseSearchProvider):
    """Serper搜索服务实现
    
    基于Serper API的搜索服务提供商。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Serper Provider
        
        Args:
            config: 配置，包含api_key、timeout等
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = "https://google.serper.dev"
        self.timeout = config.get("timeout", 10.0)
        
        if not self.api_key:
            raise ValueError("Serper Provider requires api_key in config")
    
    async def search(self, query: str, **kwargs) -> QueryResult:
        """执行搜索
        
        Args:
            query: 搜索查询
            **kwargs: 额外参数，如num、gl等
            
        Returns:
            QueryResult: 搜索结果
        """
        url = f"{self.base_url}/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": kwargs.get("num", 10),
            "gl": kwargs.get("gl", "us")
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # 提取搜索结果
                organic_results = data.get("organic", [])
                
                # 构建答案内容
                content_parts = []
                sources = []
                
                for idx, result in enumerate(organic_results[:5], 1):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    link = result.get("link", "")
                    
                    content_parts.append(f"{idx}. {title}\n{snippet}")
                    sources.append({
                        "title": title,
                        "url": link,
                        "snippet": snippet,
                        "position": idx
                    })
                
                content = "\n\n".join(content_parts)
                
                return QueryResult(
                    content=content,
                    metadata={
                        "provider": self.name,
                        "query": query,
                        "search_time": data.get("searchParameters", {}).get("time")
                    },
                    sources=sources,
                    usage={
                        "results_count": len(organic_results)
                    }
                )
        except httpx.HTTPError as e:
            logger.error(f"Serper search failed: {e}")
            raise Exception(f"Serper搜索失败: {str(e)}")
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 服务是否可用
        """
        try:
            # 执行一个简单的搜索测试
            await self.search("test", num=1)
            return True
        except Exception as e:
            logger.error(f"Serper health check failed: {e}")
            return False
    
    @property
    def name(self) -> str:
        """提供商名称"""
        return "SerperProvider"
