#!/usr/bin/env python3
"""
简单的 Dify API 测试脚本
用于快速验证 Dify API 连接和功能
"""
import asyncio
import sys
import time
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.services.dify_client import DifyClient

# 加载环境变量
load_dotenv()


async def test_single_query(query: str, test_name: str = "测试"):
    """
    测试单个查询
    
    参数:
        query: 查询文本
        test_name: 测试名称
    
    返回:
        (是否成功, 耗时, 回答)
    """
    print(f"\n{'='*60}")
    print(f"📝 {test_name}")
    print(f"{'='*60}")
    print(f"问题: {query}")
    print(f"等待响应...")
    
    start_time = time.time()
    
    try:
        # 调用 Dify API
        answer = await DifyClient.query(text=query, user="simple-test")
        duration = time.time() - start_time
        
        # 检查是否成功
        is_success = bool(answer) and not answer.startswith("调用 RAG 服务失败")
        
        # 显示结果
        if is_success:
            print(f"✅ 成功 (耗时: {duration:.2f}秒)")
            print(f"回答: {answer[:200]}{'...' if len(answer) > 200 else ''}")
        else:
            print(f"❌ 失败 (耗时: {duration:.2f}秒)")
            print(f"错误: {answer}")
        
        return is_success, duration, answer
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ 异常 (耗时: {duration:.2f}秒)")
        print(f"错误信息: {str(e)}")
        return False, duration, str(e)


async def run_simple_tests():
    """运行简单的测试用例集"""
    print("\n" + "="*60)
    print("🚀 Dify API 简单测试")
    print("="*60)
    
    # 定义测试用例
    test_cases = [
        ("你好", "问候测试"),
        ("什么是人工智能？", "知识问答测试"),
        ("Python和Java有什么区别？", "对比问答测试"),
    ]
    
    results = []
    
    # 逐个运行测试
    for query, test_name in test_cases:
        success, duration, answer = await test_single_query(query, test_name)
        results.append({
            "test_name": test_name,
            "query": query,
            "success": success,
            "duration": duration,
            "answer": answer
        })
        
        # 延迟1秒避免请求过快
        await asyncio.sleep(1)
    
    # 显示总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    avg_duration = sum(r["duration"] for r in results) / total_count
    
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count} ({success_count/total_count*100:.1f}%)")
    print(f"失败: {total_count - success_count}")
    print(f"平均耗时: {avg_duration:.2f}秒")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败")
        print("\n失败的测试:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['test_name']}: {r['query']}")
    
    print("="*60)
    
    return success_count == total_count


async def interactive_test():
    """交互式测试模式"""
    print("\n" + "="*60)
    print("💬 交互式测试模式")
    print("="*60)
    print("输入问题进行测试，输入 'quit' 或 'exit' 退出")
    print("="*60 + "\n")
    
    while True:
        try:
            # 读取用户输入
            query = input("请输入问题: ").strip()
            
            # 检查退出命令
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见！")
                break
            
            # 跳过空输入
            if not query:
                continue
            
            # 运行测试
            await test_single_query(query, "交互式测试")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except EOFError:
            print("\n\n👋 再见！")
            break


def print_usage():
    """打印使用说明"""
    print("""
使用方法:
    python scripts/simple_dify_test.py [模式]

模式:
    (无参数)    运行预设的简单测试用例
    interactive 进入交互式测试模式
    custom "你的问题"  测试自定义问题

示例:
    # 运行预设测试
    python scripts/simple_dify_test.py
    
    # 交互式测试
    python scripts/simple_dify_test.py interactive
    
    # 测试自定义问题
    python scripts/simple_dify_test.py custom "什么是机器学习？"
""")


async def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode in ['help', '-h', '--help']:
            print_usage()
            return
        elif mode == 'interactive':
            await interactive_test()
            return
        elif mode == 'custom':
            if len(sys.argv) < 3:
                print("❌ 错误: 请提供要测试的问题")
                print("示例: python scripts/simple_dify_test.py custom \"什么是AI？\"")
                return
            query = sys.argv[2]
            await test_single_query(query, "自定义测试")
            return
        else:
            print(f"❌ 未知模式: {mode}")
            print_usage()
            return
    
    # 默认运行简单测试
    await run_simple_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


