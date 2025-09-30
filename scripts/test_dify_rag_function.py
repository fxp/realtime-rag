#!/usr/bin/env python3
"""
独立测试脚本：测试 Dify RAG 调用功能
用于验证 run_dify_rag() 函数是否能正常工作
"""
import asyncio
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 读取配置
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
DIFY_TIMEOUT = float(os.getenv("DIFY_TIMEOUT", "60.0"))


async def run_dify_rag(
    query: str,
    user: str = "test-user",
    conversation_id: str | None = None,
) -> str:
    """调用 Dify Chat API 获取真实的 RAG 回答（阻塞模式）"""
    
    print(f"\n{'='*60}")
    print(f"测试 Dify RAG 调用")
    print(f"{'='*60}")
    
    # 检查 API Key 是否配置
    if not DIFY_API_KEY:
        return "❌ 错误：未配置 DIFY_API_KEY 环境变量。请设置后重启服务。"
    
    print(f"✓ API Key: {DIFY_API_KEY[:10]}...")
    print(f"✓ Base URL: {DIFY_BASE_URL}")
    print(f"✓ Timeout: {DIFY_TIMEOUT}s")
    print(f"✓ 查询: {query}")
    print(f"✓ 用户: {user}")
    print(f"{'='*60}\n")
    
    # 准备请求
    url = f"{DIFY_BASE_URL}/chat-messages"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "query": query,
        "user": user,
        "response_mode": "blocking",  # 使用阻塞模式
        "inputs": {},
    }
    
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    print("📤 发送请求到 Dify...")
    print(f"   URL: {url}")
    print(f"   Payload: {payload}\n")
    
    try:
        async with httpx.AsyncClient(timeout=DIFY_TIMEOUT) as client:
            print("⏳ 等待响应...\n")
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            print("📥 收到响应")
            print(f"{'─'*60}")
            
            # 根据官方文档提取 answer
            if result.get("event") == "message":
                answer = result.get("answer", "")
                message_id = result.get("message_id", "")
                conversation_id = result.get("conversation_id", "")
                
                # 显示元数据
                metadata = result.get("metadata", {})
                usage = metadata.get("usage", {})
                
                print(f"✅ 调用成功！")
                print(f"\n📝 消息信息:")
                print(f"   - 消息ID: {message_id}")
                print(f"   - 会话ID: {conversation_id}")
                
                if usage:
                    print(f"\n📊 使用统计:")
                    print(f"   - 提示词 Tokens: {usage.get('prompt_tokens', 0)}")
                    print(f"   - 完成 Tokens: {usage.get('completion_tokens', 0)}")
                    print(f"   - 总计 Tokens: {usage.get('total_tokens', 0)}")
                    if 'total_price' in usage:
                        print(f"   - 总价格: {usage.get('total_price')} {usage.get('currency', 'USD')}")
                    if 'latency' in usage:
                        print(f"   - 延迟: {usage.get('latency'):.2f}s")
                
                # 检索资源
                retriever_resources = metadata.get("retriever_resources", [])
                if retriever_resources:
                    print(f"\n🔍 检索到 {len(retriever_resources)} 个相关资源:")
                    for idx, resource in enumerate(retriever_resources, 1):
                        print(f"   [{idx}] {resource.get('document_name', 'Unknown')}")
                        print(f"       得分: {resource.get('score', 0):.4f}")
                        print(f"       数据集: {resource.get('dataset_name', 'Unknown')}")
                
                print(f"\n💬 回答内容:")
                print(f"{'─'*60}")
                print(answer)
                print(f"{'─'*60}")
                
                return answer if answer else "未获取到回答。"
            else:
                error_msg = f"Dify API 返回了意外的事件类型: {result.get('event')}"
                print(f"❌ {error_msg}")
                return error_msg
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Dify API HTTP 错误 {e.response.status_code}"
        print(f"❌ {error_msg}")
        print(f"   详情: {e.response.text}")
        return f"调用 RAG 服务失败：{error_msg}"
    
    except httpx.RequestError as e:
        error_msg = f"请求错误: {str(e)}"
        print(f"❌ {error_msg}")
        return f"调用 RAG 服务失败：{error_msg}"
    
    except Exception as e:
        error_msg = f"未知错误: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return f"调用 RAG 服务失败：{error_msg}"


async def run_tests():
    """运行一系列测试"""
    
    print("\n" + "="*60)
    print("Dify RAG 功能测试套件")
    print("="*60)
    
    test_cases = [
        {
            "name": "基础问答测试",
            "query": "你好，请介绍一下自己",
            "user": "test-user-1"
        },
        {
            "name": "知识问答测试",
            "query": "什么是 RAG？",
            "user": "test-user-2"
        },
        {
            "name": "中文问答测试",
            "query": "请问接下来要怎么安排推送上线？",
            "user": "test-user-3"
        }
    ]
    
    results = []
    
    for idx, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试 {idx}/{len(test_cases)}: {test['name']}")
        print(f"{'='*60}")
        
        answer = await run_dify_rag(
            query=test["query"],
            user=test["user"]
        )
        
        success = not answer.startswith("❌") and not answer.startswith("调用 RAG 服务失败")
        results.append({
            "name": test["name"],
            "success": success,
            "answer_length": len(answer)
        })
        
        # 等待一下避免请求过快
        if idx < len(test_cases):
            print("\n⏸️  等待 2 秒...")
            await asyncio.sleep(2)
    
    # 输出测试总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    for idx, result in enumerate(results, 1):
        status = "✅ 成功" if result["success"] else "❌ 失败"
        print(f"{idx}. {result['name']}: {status} (回答长度: {result['answer_length']})")
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    print(f"{'='*60}\n")


async def run_single_test():
    """运行单个快速测试"""
    query = input("请输入测试问题（直接回车使用默认问题）: ").strip()
    
    if not query:
        query = "你好，请介绍一下自己"
    
    answer = await run_dify_rag(
        query=query,
        user="interactive-test-user"
    )
    
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}\n")


def main():
    """主函数"""
    import sys
    
    print("\n" + "="*60)
    print("Dify RAG 调用测试工具")
    print("="*60)
    print("\n选择测试模式:")
    print("  1. 单个问题测试（交互式）")
    print("  2. 运行完整测试套件（3个测试）")
    print("  3. 快速测试（默认问题）")
    
    choice = input("\n请选择 (1/2/3, 默认 3): ").strip() or "3"
    
    try:
        if choice == "1":
            asyncio.run(run_single_test())
        elif choice == "2":
            asyncio.run(run_tests())
        elif choice == "3":
            print("\n运行快速测试...")
            asyncio.run(run_dify_rag("你好，请介绍一下自己", user="quick-test-user"))
        else:
            print("无效选择，运行默认测试...")
            asyncio.run(run_dify_rag("你好，请介绍一下自己", user="quick-test-user"))
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
