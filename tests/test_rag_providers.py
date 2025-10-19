"""RAG 提供商测试"""
import asyncio
import pytest
from app.services.rag_providers.base import BaseRAGProvider, BaseSearchProvider, QueryResult
from app.services.rag_providers.dify import DifyProvider
from app.services.rag_providers.serper import SerperProvider
from app.services.rag_providers.custom import CustomRAGProvider, CustomSearchProvider
from app.services.rag_service import RAGService


class TestBaseRAGProvider:
    """测试基础 RAG 提供商抽象类"""
    
    def test_query_result_creation(self):
        """测试 QueryResult 创建"""
        result = QueryResult(
            content="测试内容",
            metadata={"test": "data"},
            sources=[{"title": "测试来源", "url": "http://test.com"}]
        )
        
        assert result.content == "测试内容"
        assert result.metadata == {"test": "data"}
        assert len(result.sources) == 1


class TestDifyProvider:
    """测试 Dify 提供商"""
    
    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        valid_config = {
            "api_key": "test-key",
            "base_url": "https://api.dify.ai/v1",
            "timeout": 60.0
        }
        provider = DifyProvider(valid_config)
        assert provider.config == valid_config
        
        # 无效配置 - 缺少 api_key
        with pytest.raises(ValueError):
            DifyProvider({"base_url": "https://api.dify.ai/v1"})
        
        # 无效配置 - 缺少 base_url
        with pytest.raises(ValueError):
            DifyProvider({"api_key": "test-key"})
    
    @pytest.mark.asyncio
    async def test_health_check_without_api_key(self):
        """测试无 API 密钥时的健康检查"""
        config = {
            "api_key": "",
            "base_url": "https://api.dify.ai/v1",
            "timeout": 60.0
        }
        provider = DifyProvider(config)
        # 应该返回 False，因为配置无效
        assert await provider.health_check() is False


class TestSerperProvider:
    """测试 Serper 提供商"""
    
    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        valid_config = {
            "api_key": "test-key",
            "timeout": 30.0
        }
        provider = SerperProvider(valid_config)
        assert provider.config == valid_config
        
        # 无效配置 - 缺少 api_key
        with pytest.raises(ValueError):
            SerperProvider({"timeout": 30.0})
    
    @pytest.mark.asyncio
    async def test_health_check_without_api_key(self):
        """测试无 API 密钥时的健康检查"""
        config = {
            "api_key": "",
            "timeout": 30.0
        }
        provider = SerperProvider(config)
        # 应该返回 False，因为配置无效
        assert await provider.health_check() is False


class TestCustomProviders:
    """测试自定义提供商"""
    
    def test_custom_rag_provider_config_validation(self):
        """测试自定义 RAG 提供商配置验证"""
        # 有效配置
        valid_config = {
            "api_key": "test-key",
            "base_url": "https://api.custom.com",
            "timeout": 60.0
        }
        provider = CustomRAGProvider(valid_config)
        assert provider.config == valid_config
        
        # 无效配置
        with pytest.raises(ValueError):
            CustomRAGProvider({"api_key": "test-key"})
    
    def test_custom_search_provider_config_validation(self):
        """测试自定义搜索提供商配置验证"""
        # 有效配置
        valid_config = {
            "api_key": "test-key",
            "base_url": "https://search.custom.com",
            "timeout": 30.0
        }
        provider = CustomSearchProvider(valid_config)
        assert provider.config == valid_config
        
        # 无效配置
        with pytest.raises(ValueError):
            CustomSearchProvider({"api_key": "test-key"})


class TestRAGService:
    """测试 RAG 服务管理器"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        config = {
            "rag": {
                "provider": "dify",
                "config": {
                    "api_key": "test-key",
                    "base_url": "https://api.dify.ai/v1",
                    "timeout": 60.0
                }
            },
            "search": {
                "provider": "serper",
                "config": {
                    "api_key": "test-key",
                    "timeout": 30.0
                }
            }
        }
        
        service = RAGService(config)
        assert service._rag_provider is not None
        assert service._search_provider is not None
    
    def test_service_without_providers(self):
        """测试无提供商的服务"""
        config = {}
        service = RAGService(config)
        assert service._rag_provider is None
        assert service._search_provider is None
        assert service.is_available() is False
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        config = {
            "rag": {
                "provider": "dify",
                "config": {
                    "api_key": "test-key",
                    "base_url": "https://api.dify.ai/v1",
                    "timeout": 60.0
                }
            }
        }
        
        service = RAGService(config)
        health_status = await service.health_check()
        
        assert "rag" in health_status
        assert isinstance(health_status["rag"], bool)
    
    def test_provider_info(self):
        """测试提供商信息"""
        config = {
            "rag": {
                "provider": "dify",
                "config": {
                    "api_key": "test-key",
                    "base_url": "https://api.dify.ai/v1",
                    "timeout": 60.0
                }
            }
        }
        
        service = RAGService(config)
        info = service.get_provider_info()
        
        assert "rag" in info
        assert info["rag"]["name"] == "DifyProvider"
        assert info["rag"]["type"] == "RAG"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
