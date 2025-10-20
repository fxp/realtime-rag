"""自定义RAG提供商实现"""

import httpx
from typing import Dict, Any, AsyncIterator
from .base import BaseRAGProvider
from app.models.batch_task import QueryResult
import logging

logger = logging.getLogger(__name__)


class CustomRAGProvider(BaseRAGProvider):
    """自定义RAG服务实现
    
    支持自定义RAG服务的提供商，可以对接任何符合标准接口的RAG服务。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化自定义RAG Provider
        
        Args:
            config: 配置，包含api_url、api_key、timeout等
        """
        super().__init__(config)
        self.api_url = config.get("api_url")
        self.api_key = config.get("api_key")
        self.timeout = config.get("timeout", 30.0)
        self.headers = config.get("headers", {})
        
        if not self.api_url:
            raise ValueError("Custom RAG Provider requires api_url in config")
        
        # 如果提供了API密钥，添加到headers
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def query(self, question: str, **kwargs) -> QueryResult:
        """查询自定义RAG服务
        
        Args:
            question: 用户问题
            **kwargs: 额外参数
            
        Returns:
            QueryResult: 查询结果
        """
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }
        
        payload = {
            "question": question,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # 尝试从不同的响应格式中提取内容
                content = (
                    data.get("answer") or 
                    data.get("content") or 
                    data.get("response") or
                    str(data)
                )
                
                return QueryResult(
                    content=content,
                    metadata={
                        "provider": self.name,
                        **data.get("metadata", {})
                    },
                    sources=data.get("sources"),
                    usage=data.get("usage")
                )
        except httpx.HTTPError as e:
            logger.error(f"Custom RAG query failed: {e}")
            raise Exception(f"自定义RAG查询失败: {str(e)}")
    
    async def stream_query(self, question: str, **kwargs) -> AsyncIterator[str]:
        """流式查询自定义RAG服务
        
        Args:
            question: 用户问题
            **kwargs: 额外参数
            
        Yields:
            str: 答案片段
        """
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }
        
        payload = {
            "question": question,
            "stream": True,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", self.api_url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            # 尝试解析JSON格式的流式响应
                            try:
                                import json
                                chunk = json.loads(line)
                                content = chunk.get("content") or chunk.get("delta") or ""
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                # 如果不是JSON，直接返回文本
                                yield line
        except httpx.HTTPError as e:
            logger.error(f"Custom RAG stream query failed: {e}")
            raise Exception(f"自定义RAG流式查询失败: {str(e)}")
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 服务是否可用
        """
        try:
            # 尝试发送一个健康检查请求
            health_url = self.config.get("health_url", f"{self.api_url}/health")
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url, headers=self.headers)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Custom RAG health check failed: {e}")
            return False
    
    @property
    def name(self) -> str:
        """提供商名称"""
        return "CustomRAGProvider"
