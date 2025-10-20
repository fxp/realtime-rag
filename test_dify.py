#!/usr/bin/env python3
"""Dify Provider 快速测试脚本"""

import asyncio
import sys
from app.services.rag_providers.dify import DifyProvider
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


async def test_basic_query():
    """测试基本查询"""
    print("=" * 50)
    print("测试 1: 基本查询")
    print("=" * 50)
    
    provider = DifyProvider({
        "api_key": os.getenv("DIFY_API_KEY"),
        "base_url": os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1"),
        "timeout": 30.0,
        "user": "test-user"
    })
    
    try:
        result = await provider.query("什么是人工智能？")
        print(f"\n✓ 查询成功!")
        print(f"\n答案: {result.content[:200]}...")
        print(f"\n会话ID: {result.metadata.get('conversation_id')}")
        print(f"消息ID: {result.metadata.get('message_id')}")
        
        if result.sources:
            print(f"\n来源数量: {len(result.sources)}")
            for i, source in enumerate(result.sources[:2], 1):
                print(f"  {i}. {source.get('title')} (分数: {source.get('score')})")
        
        if result.usage:
            print(f"\nToken使用: {result.usage}")
        
        return result.metadata.get('conversation_id')
    
    except Exception as e:
        print(f"\n✗ 查询失败: {e}")
        return None


async def test_stream_query():
    """测试流式查询"""
    print("\n\n" + "=" * 50)
    print("测试 2: 流式查询")
    print("=" * 50)
    
    provider = DifyProvider({
        "api_key": os.getenv("DIFY_API_KEY"),
        "base_url": os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1"),
        "timeout": 30.0,
        "user": "test-user"
    })
    
    try:
        print("\n流式答案:")
        print("-" * 50)
        
        async for chunk in provider.stream_query("解释一下机器学习"):
            print(chunk, end='', flush=True)
        
        print("\n" + "-" * 50)
        print("✓ 流式查询成功!")
        
    except Exception as e:
        print(f"\n✗ 流式查询失败: {e}")


async def test_multi_turn_conversation(conversation_id=None):
    """测试多轮对话"""
    print("\n\n" + "=" * 50)
    print("测试 3: 多轮对话")
    print("=" * 50)
    
    provider = DifyProvider({
        "api_key": os.getenv("DIFY_API_KEY"),
        "base_url": os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1"),
        "timeout": 30.0,
        "user": "test-user"
    })
    
    try:
        # 如果没有提供会话ID，先创建一个新会话
        if not conversation_id:
            print("\n第一轮: 什么是深度学习？")
            result1 = await provider.query("什么是深度学习？")
            conversation_id = result1.metadata.get('conversation_id')
            print(f"答案: {result1.content[:150]}...")
            print(f"会话ID: {conversation_id}")
        
        # 使用相同的会话ID进行第二轮对话
        print(f"\n第二轮: 它有哪些应用？（使用会话ID: {conversation_id}）")
        result2 = await provider.query(
            "它有哪些应用？",
            conversation_id=conversation_id
        )
        print(f"答案: {result2.content[:150]}...")
        
        print("\n✓ 多轮对话成功!")
        
    except Exception as e:
        print(f"\n✗ 多轮对话失败: {e}")


async def test_health_check():
    """测试健康检查"""
    print("\n\n" + "=" * 50)
    print("测试 4: 健康检查")
    print("=" * 50)
    
    provider = DifyProvider({
        "api_key": os.getenv("DIFY_API_KEY"),
        "base_url": os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1"),
        "timeout": 5.0,
        "user": "test-user"
    })
    
    try:
        is_healthy = await provider.health_check()
        
        if is_healthy:
            print("\n✓ Dify 服务健康")
        else:
            print("\n✗ Dify 服务不健康")
        
    except Exception as e:
        print(f"\n✗ 健康检查失败: {e}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("Dify Provider 测试")
    print("=" * 50)
    
    # 检查配置
    api_key = os.getenv("DIFY_API_KEY")
    if not api_key:
        print("\n错误: 未配置 DIFY_API_KEY")
        print("请在 .env 文件中配置:")
        print("  DIFY_API_KEY=your_dify_api_key")
        sys.exit(1)
    
    print(f"\n使用配置:")
    print(f"  API Key: {api_key[:20]}...")
    print(f"  Base URL: {os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1')}")
    
    # 运行测试
    conversation_id = await test_basic_query()
    await test_stream_query()
    
    if conversation_id:
        await test_multi_turn_conversation(conversation_id)
    else:
        await test_multi_turn_conversation()
    
    await test_health_check()
    
    print("\n\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试失败: {e}")
        import traceback
        traceback.print_exc()

