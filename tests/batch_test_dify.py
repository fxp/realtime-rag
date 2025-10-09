#!/usr/bin/env python3
"""
Dify API 批量压力测试
测试大量不同类型的查询，检测 Dify 返回值的稳定性和错误处理
"""
import asyncio
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import json

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.services.dify_client import DifyClient

# 加载环境变量
load_dotenv()

# 测试用例集合
TEST_CASES = [
    # === 基础问答测试 (10条) ===
    {"id": 1, "category": "基础问答", "query": "你好", "expected": "greeting"},
    {"id": 2, "category": "基础问答", "query": "你是谁？", "expected": "identity"},
    {"id": 3, "category": "基础问答", "query": "你能做什么？", "expected": "capability"},
    {"id": 4, "category": "基础问答", "query": "今天天气怎么样？", "expected": "info"},
    {"id": 5, "category": "基础问答", "query": "现在几点了？", "expected": "time"},
    {"id": 6, "category": "基础问答", "query": "谢谢", "expected": "thanks"},
    {"id": 7, "category": "基础问答", "query": "再见", "expected": "goodbye"},
    {"id": 8, "category": "基础问答", "query": "帮我一个忙", "expected": "help"},
    {"id": 9, "category": "基础问答", "query": "我很高兴", "expected": "emotion"},
    {"id": 10, "category": "基础问答", "query": "你好吗？", "expected": "greeting"},
    
    # === 知识问答测试 (15条) ===
    {"id": 11, "category": "知识问答", "query": "什么是人工智能？", "expected": "knowledge"},
    {"id": 12, "category": "知识问答", "query": "机器学习和深度学习有什么区别？", "expected": "knowledge"},
    {"id": 13, "category": "知识问答", "query": "RAG 是什么意思？", "expected": "knowledge"},
    {"id": 14, "category": "知识问答", "query": "解释一下 Transformer 模型", "expected": "knowledge"},
    {"id": 15, "category": "知识问答", "query": "什么是自然语言处理？", "expected": "knowledge"},
    {"id": 16, "category": "知识问答", "query": "Python 和 Java 哪个更好？", "expected": "knowledge"},
    {"id": 17, "category": "知识问答", "query": "如何学习编程？", "expected": "knowledge"},
    {"id": 18, "category": "知识问答", "query": "什么是区块链？", "expected": "knowledge"},
    {"id": 19, "category": "知识问答", "query": "云计算的优势是什么？", "expected": "knowledge"},
    {"id": 20, "category": "知识问答", "query": "大数据和数据分析的区别？", "expected": "knowledge"},
    {"id": 21, "category": "知识问答", "query": "什么是微服务架构？", "expected": "knowledge"},
    {"id": 22, "category": "知识问答", "query": "Docker 是什么？", "expected": "knowledge"},
    {"id": 23, "category": "知识问答", "query": "什么是 API？", "expected": "knowledge"},
    {"id": 24, "category": "知识问答", "query": "REST 和 GraphQL 的区别？", "expected": "knowledge"},
    {"id": 25, "category": "知识问答", "query": "什么是 WebSocket？", "expected": "knowledge"},
    
    # === 长文本测试 (5条) ===
    {"id": 26, "category": "长文本", "query": "请详细介绍一下人工智能的发展历史，包括从图灵测试到现代深度学习的演进过程，以及各个重要里程碑事件", "expected": "long_answer"},
    {"id": 27, "category": "长文本", "query": "能否详细说明一下如何从零开始构建一个完整的 Web 应用，包括前端、后端、数据库设计、部署等各个环节？", "expected": "long_answer"},
    {"id": 28, "category": "长文本", "query": "请解释云原生技术栈，包括容器化、Kubernetes、服务网格、DevOps 实践等相关概念和最佳实践", "expected": "long_answer"},
    {"id": 29, "category": "长文本", "query": "请介绍一下现代软件架构设计原则，包括 SOLID 原则、设计模式、架构模式以及如何在实际项目中应用", "expected": "long_answer"},
    {"id": 30, "category": "长文本", "query": "详细说明数据安全和隐私保护的重要性，以及在应用开发中应该遵循的安全最佳实践和相关法规要求", "expected": "long_answer"},
    
    # === 中英文混合测试 (5条) ===
    {"id": 31, "category": "中英混合", "query": "什么是 Machine Learning？", "expected": "mixed"},
    {"id": 32, "category": "中英混合", "query": "Please explain AI in Chinese", "expected": "mixed"},
    {"id": 33, "category": "中英混合", "query": "Python 的 list comprehension 怎么用？", "expected": "mixed"},
    {"id": 34, "category": "中英混合", "query": "What is the difference between 同步 and 异步？", "expected": "mixed"},
    {"id": 35, "category": "中英混合", "query": "解释一下 RESTful API 的设计原则", "expected": "mixed"},
    
    # === 特殊字符测试 (5条) ===
    {"id": 36, "category": "特殊字符", "query": "这是一个测试！@#$%^&*()", "expected": "special"},
    {"id": 37, "category": "特殊字符", "query": "1+1=? 2*2=?", "expected": "special"},
    {"id": 38, "category": "特殊字符", "query": "代码：print('Hello, World!')", "expected": "special"},
    {"id": 39, "category": "特殊字符", "query": "邮箱格式：test@example.com", "expected": "special"},
    {"id": 40, "category": "特殊字符", "query": "网址：https://www.example.com/path?key=value", "expected": "special"},
    
    # === 边界情况测试 (10条) ===
    {"id": 41, "category": "边界情况", "query": "?", "expected": "boundary"},
    {"id": 42, "category": "边界情况", "query": "a", "expected": "boundary"},
    {"id": 43, "category": "边界情况", "query": "   ", "expected": "boundary"},
    {"id": 44, "category": "边界情况", "query": "?" * 100, "expected": "boundary"},
    {"id": 45, "category": "边界情况", "query": "测试" * 50, "expected": "boundary"},
    {"id": 46, "category": "边界情况", "query": "123456789", "expected": "boundary"},
    {"id": 47, "category": "边界情况", "query": "...", "expected": "boundary"},
    {"id": 48, "category": "边界情况", "query": "!!!", "expected": "boundary"},
    {"id": 49, "category": "边界情况", "query": "呃呃呃", "expected": "boundary"},
    {"id": 50, "category": "边界情况", "query": "嗯？", "expected": "boundary"},
    
    # === 技术问题测试 (10条) ===
    {"id": 51, "category": "技术问题", "query": "如何优化数据库查询性能？", "expected": "tech"},
    {"id": 52, "category": "技术问题", "query": "什么时候应该使用 Redis 缓存？", "expected": "tech"},
    {"id": 53, "category": "技术问题", "query": "如何处理高并发场景？", "expected": "tech"},
    {"id": 54, "category": "技术问题", "query": "微服务之间如何通信？", "expected": "tech"},
    {"id": 55, "category": "技术问题", "query": "如何保证系统的高可用性？", "expected": "tech"},
    {"id": 56, "category": "技术问题", "query": "什么是 CAP 定理？", "expected": "tech"},
    {"id": 57, "category": "技术问题", "query": "如何实现负载均衡？", "expected": "tech"},
    {"id": 58, "category": "技术问题", "query": "消息队列的应用场景有哪些？", "expected": "tech"},
    {"id": 59, "category": "技术问题", "query": "如何进行性能测试？", "expected": "tech"},
    {"id": 60, "category": "技术问题", "query": "什么是 CI/CD？", "expected": "tech"},
]

class TestResult:
    """测试结果记录"""
    def __init__(self, test_id, category, query, success, answer, error, duration):
        self.test_id = test_id
        self.category = category
        self.query = query
        self.success = success
        self.answer = answer
        self.error = error
        self.duration = duration
        self.has_error_in_answer = self._check_error_in_answer()
    
    def _check_error_in_answer(self):
        """检查答案中是否包含错误信息"""
        if not self.answer:
            return True
        error_keywords = ["错误", "失败", "Error", "error", "失败", "异常", "Exception"]
        return any(keyword in self.answer for keyword in error_keywords)


async def run_single_test(test_case: dict, test_num: int, total: int) -> TestResult:
    """运行单个测试用例"""
    test_id = test_case["id"]
    category = test_case["category"]
    query = test_case["query"]
    
    print(f"\n[{test_num}/{total}] 测试 #{test_id} - {category}")
    print(f"  查询: {query[:50]}{'...' if len(query) > 50 else ''}")
    
    start_time = time.time()
    
    try:
        answer = await DifyClient.query(
            text=query,
            user=f"batch-test-{test_id}"
        )
        duration = time.time() - start_time
        
        # 检查是否成功
        success = bool(answer) and not answer.startswith("错误") and not answer.startswith("调用 RAG 服务失败")
        
        print(f"  ✓ 耗时: {duration:.2f}s")
        print(f"  回答: {answer[:100]}{'...' if len(answer) > 100 else ''}")
        
        return TestResult(
            test_id=test_id,
            category=category,
            query=query,
            success=success,
            answer=answer,
            error=None,
            duration=duration
        )
    
    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        print(f"  ✗ 异常: {error_msg}")
        
        return TestResult(
            test_id=test_id,
            category=category,
            query=query,
            success=False,
            answer="",
            error=error_msg,
            duration=duration
        )


async def run_batch_tests(test_cases: list, delay: float = 1.0):
    """批量运行测试"""
    print("="*80)
    print(f"开始批量测试 - 共 {len(test_cases)} 条测试用例")
    print("="*80)
    
    results = []
    total = len(test_cases)
    
    for idx, test_case in enumerate(test_cases, 1):
        result = await run_single_test(test_case, idx, total)
        results.append(result)
        
        # 延迟避免请求过快
        if idx < total:
            await asyncio.sleep(delay)
    
    return results


def generate_report(results: list):
    """生成测试报告"""
    print("\n" + "="*80)
    print("测试报告")
    print("="*80)
    
    # 统计数据
    total = len(results)
    success_count = sum(1 for r in results if r.success)
    failed_count = total - success_count
    error_in_answer_count = sum(1 for r in results if r.has_error_in_answer)
    
    avg_duration = sum(r.duration for r in results) / total if total > 0 else 0
    max_duration = max(r.duration for r in results) if results else 0
    min_duration = min(r.duration for r in results) if results else 0
    
    # 按类别统计
    categories = {}
    for r in results:
        if r.category not in categories:
            categories[r.category] = {"total": 0, "success": 0, "failed": 0}
        categories[r.category]["total"] += 1
        if r.success:
            categories[r.category]["success"] += 1
        else:
            categories[r.category]["failed"] += 1
    
    # 打印总体统计
    print(f"\n📊 总体统计:")
    print(f"  - 测试总数: {total}")
    print(f"  - 成功: {success_count} ({success_count/total*100:.1f}%)")
    print(f"  - 失败: {failed_count} ({failed_count/total*100:.1f}%)")
    print(f"  - 回答中包含错误信息: {error_in_answer_count}")
    
    print(f"\n⏱️  性能统计:")
    print(f"  - 平均耗时: {avg_duration:.2f}s")
    print(f"  - 最快: {min_duration:.2f}s")
    print(f"  - 最慢: {max_duration:.2f}s")
    
    # 按类别统计
    print(f"\n📋 分类统计:")
    for category, stats in sorted(categories.items()):
        success_rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  - {category}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
    
    # 失败案例
    failed_results = [r for r in results if not r.success]
    if failed_results:
        print(f"\n❌ 失败案例 ({len(failed_results)} 条):")
        for r in failed_results[:10]:  # 只显示前10条
            print(f"  - #{r.test_id} [{r.category}] {r.query[:40]}...")
            print(f"    原因: {r.error or r.answer[:50]}")
    
    # 包含错误信息的回答
    error_answers = [r for r in results if r.has_error_in_answer and r.success]
    if error_answers:
        print(f"\n⚠️  回答中包含错误关键词 ({len(error_answers)} 条):")
        for r in error_answers[:10]:
            print(f"  - #{r.test_id} [{r.category}] {r.query[:40]}...")
            print(f"    回答: {r.answer[:80]}...")
    
    # 保存详细报告到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path(__file__).parent / f"test_report_{timestamp}.json"
    
    report_data = {
        "timestamp": timestamp,
        "summary": {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "error_in_answer": error_in_answer_count,
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "min_duration": min_duration,
        },
        "categories": categories,
        "results": [
            {
                "id": r.test_id,
                "category": r.category,
                "query": r.query,
                "success": r.success,
                "answer": r.answer,
                "error": r.error,
                "duration": r.duration,
                "has_error_in_answer": r.has_error_in_answer,
            }
            for r in results
        ]
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已保存: {report_file}")
    
    return success_count == total


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("Dify API 批量压力测试")
    print("="*80)
    print(f"测试用例数量: {len(TEST_CASES)}")
    print(f"测试类别: {len(set(t['category'] for t in TEST_CASES))} 种")
    print("="*80)
    
    # 检查配置
    if not os.getenv("DIFY_API_KEY"):
        print("❌ 错误: 未配置 DIFY_API_KEY")
        return
    
    # 运行测试
    results = await run_batch_tests(TEST_CASES, delay=0.5)
    
    # 生成报告
    all_success = generate_report(results)
    
    print("\n" + "="*80)
    if all_success:
        print("✅ 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请查看详细报告")
    print("="*80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
