#!/usr/bin/env python3
"""快速验证修复效果 - 只测试之前失败的案例"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
from app.services.dify_client import DifyClient

load_dotenv()

# 之前失败的案例
FAILED_CASES = [
    "云计算的优势是什么？",  # 之前5.32s超时
    "REST和GraphQL的区别？",  # 之前5.33s超时
    "请详细介绍一下人工智能的发展历史",  # 长文本，之前5.33s超时
]

async def main():
    print("\n" + "="*60)
    print("快速验证 - 测试之前失败的案例")
    print("="*60)
    print(f"超时设置: 30秒")
    print(f"测试数量: {len(FAILED_CASES)}")
    print("="*60 + "\n")
    
    success = 0
    for idx, query in enumerate(FAILED_CASES, 1):
        print(f"[{idx}/{len(FAILED_CASES)}] 测试: {query[:40]}...")
        answer = await DifyClient.query(text=query, user=f"verify-{idx}")
        
        is_success = not answer.startswith("调用 RAG 服务失败")
        if is_success:
            success += 1
            print(f"  ✅ 成功: {answer[:80]}...")
        else:
            print(f"  ❌ 失败: {answer}")
        print()
    
    print("="*60)
    print(f"结果: {success}/{len(FAILED_CASES)} 成功")
    print(f"成功率: {success/len(FAILED_CASES)*100:.1f}%")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
