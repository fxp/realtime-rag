#!/usr/bin/env python3
"""RAG 服务使用示例"""

import asyncio
import os
from app.services.rag_service import RAGService
from app.config import config


async def main():
    """演示 RAG 服务的使用"""
    
    print("=== RAG 服务示例 ===\n")
    
    # 获取服务配置
    service_config = config.get_service_config()
    print("服务配置:")
    print(f"  RAG 提供商: {config.RAG_PROVIDER}")
    print(f"  搜索提供商: {config.SEARCH_PROVIDER}")
    print()
    
    # 初始化 RAG 服务
    rag_service = RAGService(service_config)
    
    # 检查服务可用性
    if not rag_service.is_available():
        print("❌ 没有可用的服务提供商")
        return
    
    print("✅ RAG 服务已初始化")
    
    # 显示提供商信息
    provider_info = rag_service.get_provider_info()
    for service_type, info in provider_info.items():
        print(f"  - {service_type}: {info['name']} ({info['type']})")
    print()
    
    # 健康检查
    print("执行健康检查...")
    health_status = await rag_service.health_check()
    for service_type, status in health_status.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service_type}: {'健康' if status else '异常'}")
    print()
    
    # 测试查询
    test_questions = [
        "什么是人工智能？",
        "搜索最新的 Python 3.12 特性",
        "请解释一下机器学习的基本概念"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"--- 测试查询 {i} ---")
        print(f"问题: {question}")
        
        try:
            # 检测是否应该使用搜索服务
            use_search = any(keyword in question.lower() for keyword in ["搜索", "查找", "找", "search", "find", "lookup"])
            
            result = await rag_service.query(
                text=question,
                user="example-user",
                use_search=use_search
            )
            
            print(f"回答: {result.content[:200]}{'...' if len(result.content) > 200 else ''}")
            
            if result.metadata:
                print(f"元数据: {result.metadata}")
            
            if result.sources:
                print(f"来源数量: {len(result.sources)}")
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
        
        print()


if __name__ == "__main__":
    # 设置环境变量（示例）
    os.environ.setdefault("RAG_PROVIDER", "dify")
    os.environ.setdefault("SEARCH_PROVIDER", "serper")
    # 注意：需要设置实际的 API 密钥才能正常工作
    
    asyncio.run(main())
