#!/usr/bin/env python3
"""自定义提供商实现示例"""

import asyncio
from typing import Optional, Dict, Any
from app.services.rag_providers.base import BaseRAGProvider, BaseSearchProvider, QueryResult, RAGProviderFactory
from app.services.rag_service import RAGService


class MockRAGProvider(BaseRAGProvider):
    """模拟 RAG 提供商示例"""
    
    def _validate_config(self) -> None:
        """验证配置"""
        # 这个示例不需要特殊配置
        pass
    
    async def query(
        self, 
        text: str, 
        user: str = "default-user",
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> QueryResult:
        """模拟查询"""
        # 模拟一些处理时间
        await asyncio.sleep(0.1)
        
        # 根据问题生成模拟回答
        if "人工智能" in text or "AI" in text.upper():
            answer = "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"
        elif "机器学习" in text:
            answer = "机器学习是人工智能的一个子领域，它使计算机能够在没有明确编程的情况下学习和改进。"
        elif "深度学习" in text:
            answer = "深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的学习过程。"
        else:
            answer = f"这是一个关于'{text}'的模拟回答。在实际应用中，这里会调用真实的 RAG 服务。"
        
        # 添加一些元数据
        metadata = {
            "provider": "MockRAG",
            "processing_time": 0.1,
            "user": user,
            "conversation_id": conversation_id
        }
        
        # 模拟来源信息
        sources = [
            {
                "title": "模拟知识库文档",
                "url": "https://example.com/doc1",
                "relevance": 0.95
            },
            {
                "title": "相关技术文档",
                "url": "https://example.com/doc2", 
                "relevance": 0.87
            }
        ]
        
        return QueryResult(
            content=answer,
            metadata=metadata,
            sources=sources
        )
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


class MockSearchProvider(BaseSearchProvider):
    """模拟搜索提供商示例"""
    
    def _validate_config(self) -> None:
        """验证配置"""
        # 这个示例不需要特殊配置
        pass
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> QueryResult:
        """模拟搜索"""
        # 模拟一些处理时间
        await asyncio.sleep(0.2)
        
        # 生成模拟搜索结果
        mock_results = [
            {
                "title": f"搜索结果 1 - {query}",
                "url": "https://example.com/result1",
                "snippet": f"这是关于'{query}'的第一个搜索结果摘要。"
            },
            {
                "title": f"搜索结果 2 - {query}",
                "url": "https://example.com/result2", 
                "snippet": f"这是关于'{query}'的第二个搜索结果摘要。"
            },
            {
                "title": f"搜索结果 3 - {query}",
                "url": "https://example.com/result3",
                "snippet": f"这是关于'{query}'的第三个搜索结果摘要。"
            }
        ]
        
        # 构建回答内容
        content_parts = [f"**关于 '{query}' 的搜索结果:**"]
        
        for i, result in enumerate(mock_results[:num_results], 1):
            content_parts.append(f"{i}. **{result['title']}**\n   {result['snippet']}\n   {result['url']}")
        
        content = "\n\n".join(content_parts)
        
        # 构建元数据
        metadata = {
            "provider": "MockSearch",
            "query": query,
            "results_count": len(mock_results),
            "processing_time": 0.2
        }
        
        return QueryResult(
            content=content,
            metadata=metadata,
            sources=mock_results
        )


async def demo_custom_providers():
    """演示自定义提供商的使用"""
    
    print("=== 自定义提供商示例 ===\n")
    
    # 注册自定义提供商
    RAGProviderFactory.register_provider("mock_rag", MockRAGProvider)
    
    # 创建服务配置
    service_config = {
        "rag": {
            "provider": "mock_rag",
            "config": {}  # 模拟提供商不需要配置
        },
        "search": {
            "provider": "mock_search",
            "config": {}  # 模拟提供商不需要配置
        }
    }
    
    # 初始化 RAG 服务
    rag_service = RAGService(service_config)
    
    # 手动设置搜索提供商（因为 RAGService 目前只支持预定义的搜索提供商）
    rag_service._search_provider = MockSearchProvider({})
    
    print("✅ 自定义提供商已初始化")
    print(f"  - RAG: {rag_service._rag_provider.get_provider_name()}")
    print(f"  - Search: {rag_service._search_provider.get_provider_name()}")
    print()
    
    # 健康检查
    health_status = await rag_service.health_check()
    print("健康检查结果:")
    for service_type, status in health_status.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service_type}: {'健康' if status else '异常'}")
    print()
    
    # 测试 RAG 查询
    print("--- 测试 RAG 查询 ---")
    rag_questions = [
        "什么是人工智能？",
        "请解释机器学习的概念",
        "深度学习有哪些应用？"
    ]
    
    for question in rag_questions:
        print(f"问题: {question}")
        try:
            result = await rag_service.query(
                text=question,
                user="demo-user",
                use_search=False
            )
            print(f"回答: {result.content}")
            print(f"元数据: {result.metadata}")
            if result.sources:
                print(f"来源: {len(result.sources)} 个")
            print()
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            print()
    
    # 测试搜索查询
    print("--- 测试搜索查询 ---")
    search_queries = [
        "Python 最新版本特性",
        "机器学习最佳实践",
        "深度学习框架比较"
    ]
    
    for query in search_queries:
        print(f"搜索: {query}")
        try:
            result = await rag_service.query(
                text=query,
                user="demo-user",
                use_search=True
            )
            print(f"结果: {result.content}")
            print(f"元数据: {result.metadata}")
            if result.sources:
                print(f"来源: {len(result.sources)} 个")
            print()
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            print()


if __name__ == "__main__":
    asyncio.run(demo_custom_providers())
