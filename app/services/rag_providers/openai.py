"""OpenAI RAG提供商实现"""

import httpx
from typing import Dict, Any, AsyncIterator
from .base import BaseRAGProvider
from app.models.batch_task import QueryResult
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseRAGProvider):
    """OpenAI RAG服务实现
    
    基于OpenAI API的RAG服务提供商。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化OpenAI Provider
        
        Args:
            config: 配置，包含api_key、base_url、timeout等
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.openai.com")
        self.timeout = config.get("timeout", 30.0)
        self.default_model = config.get("model", "gpt-3.5-turbo")
        
        if not self.api_key:
            raise ValueError("OpenAI Provider requires api_key in config")
    
    async def query(self, question: str, **kwargs) -> QueryResult:
        """查询OpenAI
        
        Args:
            question: 用户问题
            **kwargs: 额外参数，如model、max_tokens等
            
        Returns:
            QueryResult: 查询结果
        """
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": kwargs.get("model", self.default_model),
            "messages": [
                {"role": "user", "content": question}
            ],
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return QueryResult(
                    content=content,
                    metadata={
                        "provider": self.name,
                        "model": data.get("model"),
                        "finish_reason": data.get("choices", [{}])[0].get("finish_reason")
                    },
                    usage=data.get("usage")
                )
        except httpx.HTTPError as e:
            logger.error(f"OpenAI query failed: {e}")
            raise Exception(f"OpenAI查询失败: {str(e)}")
    
    async def stream_query(self, question: str, **kwargs) -> AsyncIterator[str]:
        """流式查询OpenAI
        
        Args:
            question: 用户问题
            **kwargs: 额外参数
            
        Yields:
            str: 答案片段
        """
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": kwargs.get("model", self.default_model),
            "messages": [
                {"role": "user", "content": question}
            ],
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                import json
                                chunk = json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except httpx.HTTPError as e:
            logger.error(f"OpenAI stream query failed: {e}")
            raise Exception(f"OpenAI流式查询失败: {str(e)}")
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 服务是否可用
        """
        try:
            url = f"{self.base_url}/v1/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
    
    @property
    def name(self) -> str:
        """提供商名称"""
        return "OpenAIProvider"

