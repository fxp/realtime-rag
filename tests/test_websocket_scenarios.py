#!/usr/bin/env python3
"""
WebSocket 场景测试脚本

根据 spec/protocols/realtime-websocket.md 规范编写的完整测试套件。
测试各种场景包括：连接、ASR文本处理、问题检测、控制消息等。
"""

import asyncio
import json
import sys
import time
from typing import List, Dict, Any, Optional
import websockets
from dataclasses import dataclass, field
from datetime import datetime
from colorama import init, Fore, Style

# 初始化颜色输出
init(autoreset=True)

# 配置
WS_URL = "ws://localhost:8000/ws/realtime-asr"
TIMEOUT = 30


@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: bool
    duration: float
    message: str = ""
    details: List[str] = field(default_factory=list)


@dataclass
class MessageLog:
    """消息日志"""
    timestamp: datetime
    direction: str  # "send" or "recv"
    message: Dict[str, Any]


class WebSocketTestClient:
    """WebSocket 测试客户端"""
    
    def __init__(self, url: str = WS_URL):
        self.url = url
        self.ws = None
        self.session_id = None
        self.message_log: List[MessageLog] = []
        self.received_messages: List[Dict] = []
        
    async def connect(self) -> bool:
        """建立连接"""
        try:
            self.ws = await websockets.connect(self.url)
            print(f"{Fore.GREEN}✓ 连接成功: {self.url}")
            return True
        except Exception as e:
            print(f"{Fore.RED}✗ 连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.ws:
            await self.ws.close()
            self.ws = None
    
    async def send_message(self, message: Dict[str, Any]):
        """发送消息"""
        self.message_log.append(MessageLog(
            timestamp=datetime.now(),
            direction="send",
            message=message
        ))
        await self.ws.send(json.dumps(message))
        print(f"{Fore.CYAN}→ 发送: {json.dumps(message, ensure_ascii=False)}")
    
    async def receive_message(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """接收消息"""
        try:
            message_str = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            message = json.loads(message_str)
            
            self.message_log.append(MessageLog(
                timestamp=datetime.now(),
                direction="recv",
                message=message
            ))
            self.received_messages.append(message)
            
            # 更新 session_id
            if "session_id" in message:
                self.session_id = message["session_id"]
            
            print(f"{Fore.YELLOW}← 接收: {json.dumps(message, ensure_ascii=False)}")
            return message
            
        except asyncio.TimeoutError:
            print(f"{Fore.RED}✗ 接收超时")
            return None
        except Exception as e:
            print(f"{Fore.RED}✗ 接收错误: {e}")
            return None
    
    async def wait_for_message_type(self, msg_type: str, timeout: float = 10.0) -> Optional[Dict]:
        """等待特定类型的消息"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            msg = await self.receive_message(timeout=1.0)
            if msg and msg.get("type") == msg_type:
                return msg
        
        return None
    
    async def wait_for_status(self, stage: str, timeout: float = 10.0) -> Optional[Dict]:
        """等待特定状态"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            msg = await self.receive_message(timeout=1.0)
            if msg and msg.get("type") == "status" and msg.get("stage") == stage:
                return msg
        
        return None
    
    async def collect_answer_chunks(self, timeout: float = 15.0) -> List[str]:
        """收集答案块"""
        chunks = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            msg = await self.receive_message(timeout=2.0)
            
            if msg and msg.get("type") == "answer":
                chunks.append(msg.get("content", ""))
                
                if msg.get("final"):
                    print(f"{Fore.GREEN}✓ 收到完整答案 ({len(chunks)} 块)")
                    break
        
        return chunks
    
    def print_message_log(self):
        """打印消息日志"""
        print(f"\n{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}消息日志 ({len(self.message_log)} 条)")
        print(f"{Fore.MAGENTA}{'='*60}")
        
        for log in self.message_log:
            direction = "→" if log.direction == "send" else "←"
            color = Fore.CYAN if log.direction == "send" else Fore.YELLOW
            timestamp = log.timestamp.strftime("%H:%M:%S.%f")[:-3]
            
            print(f"{color}{timestamp} {direction} {json.dumps(log.message, ensure_ascii=False)}")


class ScenarioTester:
    """场景测试器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
    
    async def run_test(self, name: str, test_func):
        """运行单个测试"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}测试: {name}")
        print(f"{Fore.CYAN}{'='*60}")
        
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            if result:
                self.results.append(TestResult(
                    name=name,
                    passed=True,
                    duration=duration,
                    message="测试通过"
                ))
                print(f"{Fore.GREEN}✓ 测试通过 ({duration:.2f}秒)")
            else:
                self.results.append(TestResult(
                    name=name,
                    passed=False,
                    duration=duration,
                    message="测试失败"
                ))
                print(f"{Fore.RED}✗ 测试失败 ({duration:.2f}秒)")
                
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                name=name,
                passed=False,
                duration=duration,
                message=f"异常: {str(e)}"
            ))
            print(f"{Fore.RED}✗ 测试异常: {e} ({duration:.2f}秒)")
    
    def print_summary(self):
        """打印测试摘要"""
        print(f"\n{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}测试摘要")
        print(f"{Fore.MAGENTA}{'='*60}\n")
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        total_duration = sum(r.duration for r in self.results)
        
        for result in self.results:
            status = f"{Fore.GREEN}✓" if result.passed else f"{Fore.RED}✗"
            print(f"{status} {result.name}: {result.message} ({result.duration:.2f}秒)")
        
        print(f"\n{Fore.CYAN}总计: {len(self.results)} 个测试")
        print(f"{Fore.GREEN}通过: {passed}")
        print(f"{Fore.RED}失败: {failed}")
        print(f"{Fore.CYAN}耗时: {total_duration:.2f}秒")
        
        if failed == 0:
            print(f"\n{Fore.GREEN}{'='*60}")
            print(f"{Fore.GREEN}所有测试通过! 🎉")
            print(f"{Fore.GREEN}{'='*60}")
        else:
            print(f"\n{Fore.RED}{'='*60}")
            print(f"{Fore.RED}有 {failed} 个测试失败")
            print(f"{Fore.RED}{'='*60}")


# ============================================================================
# 测试场景
# ============================================================================

async def test_connection_and_initial_ack():
    """场景1: 测试连接和初始确认"""
    client = WebSocketTestClient()
    
    # 连接
    if not await client.connect():
        return False
    
    # 等待初始 ack
    ack = await client.wait_for_message_type("ack", timeout=5.0)
    if not ack:
        await client.disconnect()
        return False
    
    # 验证 session_id
    if not ack.get("session_id"):
        print(f"{Fore.RED}✗ 缺少 session_id")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 获得 session_id: {client.session_id}")
    
    # 等待初始状态
    status = await client.wait_for_status("listening")
    if not status:
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 进入 listening 状态")
    
    await client.disconnect()
    return True


async def test_keepalive():
    """场景2: 测试心跳消息"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    # 跳过初始消息
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 发送心跳
    await client.send_message({"type": "keepalive"})
    
    # 等待确认
    ack = await client.wait_for_message_type("ack", timeout=3.0)
    if not ack or ack.get("received_type") != "keepalive":
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 心跳确认成功")
    
    await client.disconnect()
    return True


async def test_asr_non_final_chunks():
    """场景3: 测试非最终化 ASR 文本块"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 发送非最终化文本块
    await client.send_message({
        "type": "asr_chunk",
        "text": "什么是",
        "is_final": False
    })
    
    # 等待确认
    ack = await client.wait_for_message_type("ack", timeout=3.0)
    if not ack or ack.get("received_type") != "asr_chunk":
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 非最终化文本块确认成功")
    
    await client.disconnect()
    return True


async def test_question_detection_and_rag():
    """场景4: 测试问题检测和 RAG 查询"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 发送问题
    await client.send_message({
        "type": "asr_chunk",
        "text": "什么是人工智能？",
        "is_final": True
    })
    
    # 等待确认
    await client.wait_for_message_type("ack")
    
    # 等待 analyzing 状态
    analyzing = await client.wait_for_status("analyzing", timeout=5.0)
    if not analyzing:
        print(f"{Fore.RED}✗ 未进入 analyzing 状态")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 进入 analyzing 状态")
    
    # 等待 querying_rag 状态
    querying = await client.wait_for_status("querying_rag", timeout=5.0)
    if not querying:
        print(f"{Fore.RED}✗ 未进入 querying_rag 状态")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 进入 querying_rag 状态")
    
    # 收集答案
    chunks = await client.collect_answer_chunks(timeout=20.0)
    if not chunks:
        print(f"{Fore.RED}✗ 未收到答案")
        await client.disconnect()
        return False
    
    answer = "".join(chunks)
    print(f"{Fore.GREEN}✓ 收到答案: {answer[:100]}...")
    
    # 等待 idle 状态
    idle = await client.wait_for_status("idle", timeout=5.0)
    if not idle:
        print(f"{Fore.RED}✗ 未进入 idle 状态")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 进入 idle 状态")
    
    await client.disconnect()
    return True


async def test_non_question_text():
    """场景5: 测试非问题文本"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 发送非问题文本
    await client.send_message({
        "type": "asr_chunk",
        "text": "今天天气不错",
        "is_final": True
    })
    
    await client.wait_for_message_type("ack")
    
    # 等待 waiting_for_question 状态
    waiting = await client.wait_for_status("waiting_for_question", timeout=5.0)
    if not waiting:
        print(f"{Fore.RED}✗ 未进入 waiting_for_question 状态")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 正确识别非问题文本")
    
    await client.disconnect()
    return True


async def test_pause_resume():
    """场景6: 测试暂停和恢复"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 暂停
    await client.send_message({
        "type": "control",
        "action": "pause"
    })
    
    paused = await client.wait_for_status("paused", timeout=3.0)
    if not paused:
        print(f"{Fore.RED}✗ 未进入 paused 状态")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 成功暂停")
    
    # 在暂停状态下发送 ASR
    await client.send_message({
        "type": "asr_chunk",
        "text": "什么是机器学习？",
        "is_final": True
    })
    
    # 应该收到确认但标记为 paused
    ack = await client.wait_for_message_type("ack", timeout=3.0)
    if ack and ack.get("message") == "paused":
        print(f"{Fore.GREEN}✓ 暂停状态下正确忽略 ASR")
    
    # 恢复
    await client.send_message({
        "type": "control",
        "action": "resume"
    })
    
    resumed = await client.wait_for_status("listening", timeout=3.0)
    if not resumed:
        print(f"{Fore.RED}✗ 未恢复到 listening 状态")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 成功恢复")
    
    await client.disconnect()
    return True


async def test_instant_query():
    """场景7: 测试即时查询"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 先发送一个最终化文本
    await client.send_message({
        "type": "asr_chunk",
        "text": "解释一下深度学习",
        "is_final": True
    })
    
    await client.wait_for_message_type("ack")
    
    # 立即发送 instant_query
    await client.send_message({
        "type": "control",
        "action": "instant_query"
    })
    
    # 等待 instant_query 状态
    instant = await client.wait_for_status("instant_query", timeout=5.0)
    if not instant:
        print(f"{Fore.RED}✗ 未进入 instant_query 状态")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 进入 instant_query 状态")
    
    # 等待 querying_rag 状态（mode: instant）
    querying = await client.wait_for_status("querying_rag", timeout=5.0)
    if not querying or querying.get("mode") != "instant":
        print(f"{Fore.RED}✗ 查询模式不正确")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 进入 querying_rag (mode: instant)")
    
    # 收集答案
    chunks = await client.collect_answer_chunks(timeout=20.0)
    if not chunks:
        print(f"{Fore.RED}✗ 未收到答案")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 即时查询成功")
    
    await client.disconnect()
    return True


async def test_instant_query_without_final_text():
    """场景8: 测试没有最终化文本时的即时查询（应该失败）"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 直接发送 instant_query（没有先发送最终化文本）
    await client.send_message({
        "type": "control",
        "action": "instant_query"
    })
    
    # 应该收到错误
    error = await client.wait_for_message_type("error", timeout=3.0)
    if not error or error.get("code") != "NO_FINAL_ASR":
        print(f"{Fore.RED}✗ 未收到预期错误")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 正确返回 NO_FINAL_ASR 错误")
    
    await client.disconnect()
    return True


async def test_stop_command():
    """场景9: 测试停止命令"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 发送停止命令
    await client.send_message({
        "type": "control",
        "action": "stop"
    })
    
    # 等待 idle 状态
    idle = await client.wait_for_status("idle", timeout=3.0)
    if not idle:
        print(f"{Fore.RED}✗ 未进入 idle 状态")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 收到停止确认")
    
    await client.disconnect()
    return True


async def test_invalid_message():
    """场景10: 测试无效消息"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 发送无效 JSON
    try:
        await client.ws.send("invalid json {")
        error = await client.wait_for_message_type("error", timeout=3.0)
        
        if not error or error.get("code") != "INVALID_JSON":
            print(f"{Fore.RED}✗ 未收到 INVALID_JSON 错误")
            await client.disconnect()
            return False
        
        print(f"{Fore.GREEN}✓ 正确处理无效 JSON")
        
    except Exception as e:
        print(f"{Fore.RED}✗ 异常: {e}")
        await client.disconnect()
        return False
    
    await client.disconnect()
    return True


async def test_unsupported_message_type():
    """场景11: 测试不支持的消息类型"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 发送不支持的消息类型
    await client.send_message({
        "type": "unknown_type",
        "data": "test"
    })
    
    error = await client.wait_for_message_type("error", timeout=3.0)
    if not error or error.get("code") != "UNSUPPORTED_TYPE":
        print(f"{Fore.RED}✗ 未收到 UNSUPPORTED_TYPE 错误")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 正确处理不支持的消息类型")
    
    await client.disconnect()
    return True


async def test_multi_turn_conversation():
    """场景12: 测试多轮对话"""
    client = WebSocketTestClient()
    
    if not await client.connect():
        return False
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("listening")
    
    # 第一轮
    print(f"{Fore.CYAN}第一轮对话...")
    await client.send_message({
        "type": "asr_chunk",
        "text": "什么是机器学习？",
        "is_final": True
    })
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("analyzing")
    await client.wait_for_status("querying_rag")
    chunks1 = await client.collect_answer_chunks()
    await client.wait_for_status("idle")
    
    if not chunks1:
        print(f"{Fore.RED}✗ 第一轮查询失败")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 第一轮对话成功")
    
    # 第二轮
    print(f"{Fore.CYAN}第二轮对话...")
    await client.send_message({
        "type": "asr_chunk",
        "text": "深度学习和它有什么区别？",
        "is_final": True
    })
    
    await client.wait_for_message_type("ack")
    await client.wait_for_status("analyzing")
    await client.wait_for_status("querying_rag")
    chunks2 = await client.collect_answer_chunks()
    await client.wait_for_status("idle")
    
    if not chunks2:
        print(f"{Fore.RED}✗ 第二轮查询失败")
        await client.disconnect()
        return False
    
    print(f"{Fore.GREEN}✓ 第二轮对话成功")
    print(f"{Fore.GREEN}✓ 多轮对话测试通过")
    
    await client.disconnect()
    return True


# ============================================================================
# 主程序
# ============================================================================

async def main():
    """主测试函数"""
    print(f"{Fore.MAGENTA}")
    print("="*60)
    print("WebSocket 场景测试套件")
    print("="*60)
    print(f"{Style.RESET_ALL}")
    print(f"测试服务器: {WS_URL}")
    print(f"超时设置: {TIMEOUT}秒")
    print()
    
    # 检查服务器是否运行
    print(f"{Fore.CYAN}检查服务器连接...")
    test_client = WebSocketTestClient()
    if not await test_client.connect():
        print(f"{Fore.RED}错误: 无法连接到 WebSocket 服务器")
        print(f"{Fore.YELLOW}请确保服务器正在运行: ./run.sh 或 python -m app.main")
        return
    await test_client.disconnect()
    print(f"{Fore.GREEN}✓ 服务器连接正常\n")
    
    # 创建测试器
    tester = ScenarioTester()
    
    # 运行所有测试
    await tester.run_test("场景1: 连接和初始确认", test_connection_and_initial_ack)
    await tester.run_test("场景2: 心跳消息", test_keepalive)
    await tester.run_test("场景3: 非最终化 ASR 文本块", test_asr_non_final_chunks)
    await tester.run_test("场景4: 问题检测和 RAG 查询", test_question_detection_and_rag)
    await tester.run_test("场景5: 非问题文本", test_non_question_text)
    await tester.run_test("场景6: 暂停和恢复", test_pause_resume)
    await tester.run_test("场景7: 即时查询", test_instant_query)
    await tester.run_test("场景8: 无最终化文本的即时查询", test_instant_query_without_final_text)
    await tester.run_test("场景9: 停止命令", test_stop_command)
    await tester.run_test("场景10: 无效消息", test_invalid_message)
    await tester.run_test("场景11: 不支持的消息类型", test_unsupported_message_type)
    await tester.run_test("场景12: 多轮对话", test_multi_turn_conversation)
    
    # 打印摘要
    tester.print_summary()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


