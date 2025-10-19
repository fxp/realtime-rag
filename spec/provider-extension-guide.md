# 服务提供商扩展指南

## 概述

Realtime RAG 服务采用了抽象的提供商架构，支持轻松集成各种 RAG 和搜索服务。本指南详细说明如何添加新的服务提供商。

## 架构设计

### 核心抽象类

系统提供了两个基础抽象类：

1. **BaseRAGProvider**: RAG 服务提供商基类
2. **BaseSearchProvider**: 搜索服务提供商基类

### 统一接口

所有提供商都实现了统一的接口，确保：
- 一致的查询方法
- 标准化的结果格式
- 统一的错误处理
- 可配置的参数

## 实现 RAG 提供商

### 1. 创建提供商类

```python
from app.services.rag_providers.base import BaseRAGProvider, QueryResult
import httpx

class MyRAGProvider(BaseRAGProvider):
    """我的自定义 RAG 提供商"""
    
    def _validate_config(self) -> None:
        """验证配置参数"""
        required_fields = ["api_key", "endpoint"]
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise ValueError(f"MyRAG configuration missing required field: {field}")
    
    async def query(
        self, 
        text: str, 
        user: str = "default-user",
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> QueryResult:
        """执行查询"""
        # 实现具体的查询逻辑
        api_key = self.config["api_key"]
        endpoint = self.config["endpoint"]
        
        # 构建请求
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"query": text, "user": user}
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
        # 返回标准化结果
        return QueryResult(
            content=result.get("answer", ""),
            metadata=result.get("metadata", {}),
            sources=result.get("sources", [])
        )
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.query("test", user="health-check")
            return True
        except Exception:
            return False
```

### 2. 注册提供商

```python
from app.services.rag_providers.base import RAGProviderFactory

# 注册提供商
RAGProviderFactory.register_provider("my_rag", MyRAGProvider)
```

### 3. 配置提供商

```python
# 在配置中添加
config = {
    "rag": {
        "provider": "my_rag",
        "config": {
            "api_key": "your-api-key",
            "endpoint": "https://api.myrag.com/query",
            "timeout": 60.0
        }
    }
}
```

## 实现搜索提供商

### 1. 创建搜索提供商类

```python
from app.services.rag_providers.base import BaseSearchProvider, QueryResult
import httpx

class MySearchProvider(BaseSearchProvider):
    """我的自定义搜索提供商"""
    
    def _validate_config(self) -> None:
        """验证配置参数"""
        required_fields = ["api_key", "search_url"]
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise ValueError(f"MySearch configuration missing required field: {field}")
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> QueryResult:
        """执行搜索"""
        # 实现具体的搜索逻辑
        api_key = self.config["api_key"]
        search_url = self.config["search_url"]
        
        # 构建请求
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"q": query, "limit": num_results}
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.post(search_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        
        # 构建搜索结果
        results = result.get("results", [])
        content_parts = []
        
        if results:
            content_parts.append("**搜索结果:**")
            for i, item in enumerate(results[:5], 1):
                title = item.get("title", "")
                summary = item.get("summary", "")
                url = item.get("url", "")
                content_parts.append(f"{i}. **{title}**\n   {summary}\n   {url}")
        
        content = "\n\n".join(content_parts) if content_parts else "未找到相关信息。"
        
        # 构建来源信息
        sources = []
        for item in results:
            sources.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "summary": item.get("summary", "")
            })
        
        return QueryResult(
            content=content,
            metadata={"search_results_count": len(results)},
            sources=sources
        )
```

### 2. 集成到 RAG 服务

```python
# 在 rag_service.py 中添加
from .rag_providers.my_search import MySearchProvider

def _initialize_providers(self) -> None:
    # 初始化搜索提供商
    search_config = self.config.get("search", {})
    if search_config:
        provider_type = search_config.get("provider", "serper")
        provider_config = search_config.get("config", {})
        try:
            if provider_type == "my_search":
                self._search_provider = MySearchProvider(provider_config)
            # ... 其他提供商
        except Exception as e:
            print(f"Warning: Failed to initialize search provider {provider_type}: {e}")
```

## 配置管理

### 环境变量配置

```bash
# .env 文件
RAG_PROVIDER=my_rag
SEARCH_PROVIDER=my_search

# 自定义 RAG 配置
MY_RAG_API_KEY=your-api-key
MY_RAG_ENDPOINT=https://api.myrag.com/query
MY_RAG_TIMEOUT=60.0

# 自定义搜索配置
MY_SEARCH_API_KEY=your-search-api-key
MY_SEARCH_URL=https://api.mysearch.com/search
MY_SEARCH_TIMEOUT=30.0
```

### 配置类扩展

```python
# 在 config.py 中扩展
class Config:
    # 自定义提供商配置
    MY_RAG_API_KEY: str = os.getenv("MY_RAG_API_KEY", "")
    MY_RAG_ENDPOINT: str = os.getenv("MY_RAG_ENDPOINT", "")
    MY_RAG_TIMEOUT: float = float(os.getenv("MY_RAG_TIMEOUT", "60.0"))
    
    MY_SEARCH_API_KEY: str = os.getenv("MY_SEARCH_API_KEY", "")
    MY_SEARCH_URL: str = os.getenv("MY_SEARCH_URL", "")
    MY_SEARCH_TIMEOUT: float = float(os.getenv("MY_SEARCH_TIMEOUT", "30.0"))
    
    @classmethod
    def get_rag_config(cls) -> Dict[str, Any]:
        """获取 RAG 服务配置"""
        if cls.RAG_PROVIDER == "my_rag":
            return {
                "provider": "my_rag",
                "config": {
                    "api_key": cls.MY_RAG_API_KEY,
                    "endpoint": cls.MY_RAG_ENDPOINT,
                    "timeout": cls.MY_RAG_TIMEOUT
                }
            }
        # ... 其他提供商
        return {}
    
    @classmethod
    def get_search_config(cls) -> Dict[str, Any]:
        """获取搜索服务配置"""
        if cls.SEARCH_PROVIDER == "my_search":
            return {
                "provider": "my_search",
                "config": {
                    "api_key": cls.MY_SEARCH_API_KEY,
                    "search_url": cls.MY_SEARCH_URL,
                    "timeout": cls.MY_SEARCH_TIMEOUT
                }
            }
        # ... 其他提供商
        return {}
```

## 测试提供商

### 单元测试

```python
import pytest
from app.services.rag_providers.my_rag import MyRAGProvider

class TestMyRAGProvider:
    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        valid_config = {
            "api_key": "test-key",
            "endpoint": "https://api.myrag.com/query",
            "timeout": 60.0
        }
        provider = MyRAGProvider(valid_config)
        assert provider.config == valid_config
        
        # 无效配置
        with pytest.raises(ValueError):
            MyRAGProvider({"api_key": "test-key"})
    
    @pytest.mark.asyncio
    async def test_query(self):
        """测试查询功能"""
        config = {
            "api_key": "test-key",
            "endpoint": "https://api.myrag.com/query",
            "timeout": 60.0
        }
        provider = MyRAGProvider(config)
        
        # 模拟查询（需要 mock httpx 请求）
        result = await provider.query("测试问题")
        assert isinstance(result, QueryResult)
        assert result.content is not None
```

### 集成测试

```python
import pytest
from app.services.rag_service import RAGService

class TestRAGServiceWithMyProvider:
    @pytest.mark.asyncio
    async def test_my_rag_provider_integration(self):
        """测试自定义 RAG 提供商集成"""
        config = {
            "rag": {
                "provider": "my_rag",
                "config": {
                    "api_key": "test-key",
                    "endpoint": "https://api.myrag.com/query",
                    "timeout": 60.0
                }
            }
        }
        
        service = RAGService(config)
        assert service._rag_provider is not None
        assert service.is_available() is True
        
        # 测试健康检查
        health_status = await service.health_check()
        assert "rag" in health_status
```

## 最佳实践

### 1. 错误处理

```python
async def query(self, text: str, **kwargs) -> QueryResult:
    """执行查询"""
    try:
        # 查询逻辑
        pass
    except httpx.TimeoutException as e:
        raise Exception(f"请求超时: {e}") from e
    except httpx.HTTPStatusError as e:
        raise Exception(f"HTTP 错误 {e.response.status_code}: {e.response.text}") from e
    except httpx.RequestError as e:
        raise Exception(f"网络错误: {e}") from e
    except Exception as e:
        raise Exception(f"未知错误: {e}") from e
```

### 2. 配置验证

```python
def _validate_config(self) -> None:
    """验证配置参数"""
    required_fields = ["api_key", "endpoint"]
    optional_fields = ["timeout", "max_tokens"]
    
    # 检查必需字段
    for field in required_fields:
        if field not in self.config or not self.config[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # 设置默认值
    for field, default_value in optional_fields.items():
        if field not in self.config:
            self.config[field] = default_value
```

### 3. 日志记录

```python
import logging

logger = logging.getLogger(__name__)

async def query(self, text: str, **kwargs) -> QueryResult:
    """执行查询"""
    logger.info(f"Executing query with {self.__class__.__name__}")
    
    try:
        # 查询逻辑
        result = await self._perform_query(text, **kwargs)
        logger.info(f"Query successful, returned {len(result.content)} characters")
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise
```

### 4. 性能优化

```python
import asyncio
from functools import lru_cache

class MyRAGProvider(BaseRAGProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None
    
    async def _get_client(self):
        """获取或创建 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.get("timeout", 60.0)
            )
        return self._client
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
```

## 部署注意事项

### 1. 依赖管理

```python
# requirements.txt
httpx>=0.27.0
aiohttp>=3.8.0  # 如果需要 aiohttp 客户端
```

### 2. 环境变量

```bash
# 生产环境配置
export RAG_PROVIDER=my_rag
export MY_RAG_API_KEY=production-api-key
export MY_RAG_ENDPOINT=https://api.myrag.com/v1/query
export MY_RAG_TIMEOUT=120.0
```

### 3. 监控和日志

```python
# 添加监控指标
from prometheus_client import Counter, Histogram

query_counter = Counter('rag_queries_total', 'Total RAG queries', ['provider'])
query_duration = Histogram('rag_query_duration_seconds', 'RAG query duration', ['provider'])

async def query(self, text: str, **kwargs) -> QueryResult:
    """执行查询"""
    start_time = time.time()
    provider_name = self.__class__.__name__
    
    try:
        result = await self._perform_query(text, **kwargs)
        query_counter.labels(provider=provider_name).inc()
        return result
    finally:
        query_duration.labels(provider=provider_name).observe(time.time() - start_time)
```

## 示例：集成 OpenAI API

```python
import openai
from app.services.rag_providers.base import BaseRAGProvider, QueryResult

class OpenAIProvider(BaseRAGProvider):
    """OpenAI RAG 提供商"""
    
    def _validate_config(self) -> None:
        """验证配置"""
        required_fields = ["api_key", "model"]
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise ValueError(f"OpenAI configuration missing required field: {field}")
    
    async def query(
        self, 
        text: str, 
        user: str = "default-user",
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> QueryResult:
        """执行 OpenAI 查询"""
        api_key = self.config["api_key"]
        model = self.config["model"]
        
        # 设置 OpenAI API 密钥
        openai.api_key = api_key
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=[
                    {"role": "user", "content": text}
                ],
                max_tokens=self.config.get("max_tokens", 1000),
                temperature=self.config.get("temperature", 0.7)
            )
            
            answer = response.choices[0].message.content
            
            return QueryResult(
                content=answer,
                metadata={
                    "model": model,
                    "usage": response.usage.to_dict()
                }
            )
        
        except Exception as e:
            raise Exception(f"OpenAI API 调用失败: {e}") from e
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.query("test", user="health-check")
            return True
        except Exception:
            return False
```

这个扩展指南提供了完整的框架来添加新的 RAG 和搜索提供商，确保系统的灵活性和可扩展性。
