"""Dify Chat API 测试客户端

这个脚本用于测试连接到 Dify 的 Chat 应用，支持流式和非流式响应。
基于官方文档: https://docs.dify.ai/api-reference/chat/send-chat-message

使用方法:
    python scripts/dify_workflow_client.py --api-key YOUR_API_KEY --query "你的问题"
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, Optional

import httpx


class DifyChatClient:
    """Dify Chat API 客户端（基于官方文档）"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.dify.ai/v1",
        timeout: float = 60.0,
    ) -> None:
        """
        初始化 Dify 客户端
        
        Args:
            api_key: Dify API 密钥
            base_url: API 基础 URL
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def send_chat_message(
        self,
        query: str,
        user: str = "test-user",
        inputs: Optional[Dict[str, Any]] = None,
        response_mode: str = "streaming",
        conversation_id: Optional[str] = None,
        files: Optional[list] = None,
        auto_generate_name: bool = True,
    ) -> None:
        """
        发送聊天消息到 Dify Chat 应用
        
        Args:
            query: 用户输入/问题内容（必需）
            user: 用户标识符，应用内唯一（必需）
            inputs: 应用定义的各种变量值，键值对格式
            response_mode: 响应模式，"streaming" 或 "blocking"
            conversation_id: 会话ID，用于继续上一个对话
            files: 文件列表（用于支持 Vision 的模型）
            auto_generate_name: 是否自动生成对话标题
        """
        if inputs is None:
            inputs = {}
        
        # 准备请求负载（根据官方文档）
        payload = {
            "query": query,
            "user": user,
            "response_mode": response_mode,
            "inputs": inputs,
            "auto_generate_name": auto_generate_name,
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        if files:
            payload["files"] = files

        print(f"\n{'='*60}")
        print(f"发送消息到 Dify Chat API")
        print(f"{'='*60}")
        print(f"查询: {query}")
        print(f"响应模式: {response_mode}")
        print(f"用户: {user}")
        if conversation_id:
            print(f"会话ID: {conversation_id}")
        if inputs:
            print(f"输入变量: {json.dumps(inputs, ensure_ascii=False)}")
        if files:
            print(f"文件数量: {len(files)}")
        print(f"{'='*60}\n")

        try:
            if response_mode == "streaming":
                await self._run_streaming(payload)
            else:
                await self._run_blocking(payload)
        except httpx.HTTPStatusError as e:
            print(f"\n❌ HTTP 错误: {e.response.status_code}")
            print(f"错误详情: {e.response.text}")
        except httpx.RequestError as e:
            print(f"\n❌ 请求错误: {e}")
        except Exception as e:
            print(f"\n❌ 未知错误: {e}")

    async def _run_streaming(self, payload: Dict[str, Any]) -> None:
        """处理流式响应（根据官方文档的 SSE 格式）"""
        url = f"{self.base_url}/chat-messages"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                url,
                headers=self.headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                
                print("开始接收流式响应...\n")
                print(f"{'─'*60}")
                
                full_answer = ""
                event_count = 0
                conversation_id = None
                message_id = None
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    # Dify 流式响应格式: data: {json}
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        try:
                            data = json.loads(data_str)
                            event_count += 1
                            
                            # 根据官方文档处理不同的事件类型
                            event_type = data.get("event")
                            
                            if event_type == "message":
                                # 完整消息事件（blocking 模式）
                                full_answer = data.get("answer", "")
                                conversation_id = data.get("conversation_id")
                                message_id = data.get("message_id")
                                print(f"\n💬 完整消息: {full_answer}")
                            
                            elif event_type == "message_end":
                                # 消息结束事件
                                metadata = data.get("metadata", {})
                                conversation_id = data.get("conversation_id")
                                message_id = data.get("id")
                                print(f"\n{'─'*60}")
                                print("✅ 消息完成")
                                if metadata:
                                    usage = metadata.get("usage", {})
                                    if usage:
                                        print(f"\n📊 使用统计:")
                                        print(f"  - 提示词 tokens: {usage.get('prompt_tokens', 0)}")
                                        print(f"  - 完成 tokens: {usage.get('completion_tokens', 0)}")
                                        print(f"  - 总计 tokens: {usage.get('total_tokens', 0)}")
                                        if 'total_price' in usage:
                                            print(f"  - 总价格: {usage.get('total_price')} {usage.get('currency', 'USD')}")
                            
                            elif event_type == "agent_thought":
                                # Agent 思考过程
                                thought = data.get("thought", "")
                                if thought:
                                    print(f"\n🤔 思考: {thought}")
                            
                            elif event_type == "agent_message" or event_type == "message_replace":
                                # Agent 消息或消息替换
                                answer = data.get("answer", "")
                                if answer:
                                    print(answer, end="", flush=True)
                                    full_answer += answer
                            
                            elif event_type == "error":
                                # 错误事件
                                print(f"\n❌ 错误: {data.get('message', '未知错误')}")
                                print(f"   状态码: {data.get('status', 'N/A')}")
                            
                            elif event_type == "ping":
                                # 心跳事件，忽略
                                pass
                            
                            else:
                                # 其他未知事件类型，打印出来
                                await self._handle_stream_event(data, event_count)
                                
                        except json.JSONDecodeError:
                            print(f"⚠️  无法解析 JSON: {data_str}")
                
                print(f"\n{'─'*60}")
                print(f"总共接收到 {event_count} 个事件")
                if conversation_id:
                    print(f"会话ID: {conversation_id}")
                if message_id:
                    print(f"消息ID: {message_id}")
                if full_answer:
                    print(f"\n完整回答:\n{full_answer}")

    async def _run_blocking(self, payload: Dict[str, Any]) -> None:
        """处理阻塞式响应（根据官方文档）"""
        url = f"{self.base_url}/chat-messages"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            
            result = response.json()
            print("收到响应:\n")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 根据官方文档提取关键信息
            if result.get("event") == "message":
                print(f"\n{'─'*60}")
                print(f"💬 回答: {result.get('answer', '')}")
                print(f"📝 消息ID: {result.get('message_id')}")
                print(f"🔗 会话ID: {result.get('conversation_id')}")
                
                # 显示元数据
                metadata = result.get("metadata", {})
                if metadata:
                    usage = metadata.get("usage", {})
                    if usage:
                        print(f"\n📊 使用统计:")
                        print(f"  - 提示词 tokens: {usage.get('prompt_tokens', 0)}")
                        print(f"  - 完成 tokens: {usage.get('completion_tokens', 0)}")
                        print(f"  - 总计 tokens: {usage.get('total_tokens', 0)}")
                        if 'total_price' in usage:
                            print(f"  - 总价格: {usage.get('total_price')} {usage.get('currency', 'USD')}")
                    
                    # 显示检索资源
                    retriever_resources = metadata.get("retriever_resources", [])
                    if retriever_resources:
                        print(f"\n🔍 检索到 {len(retriever_resources)} 个相关资源:")
                        for idx, resource in enumerate(retriever_resources, 1):
                            print(f"  [{idx}] {resource.get('document_name', 'Unknown')}")
                            print(f"      得分: {resource.get('score', 0):.4f}")
                            print(f"      数据集: {resource.get('dataset_name', 'Unknown')}")

    async def _handle_stream_event(self, event: Dict[str, Any], event_num: int) -> None:
        """处理单个流式事件（用于未知事件类型）"""
        event_type = event.get("event", "unknown")
        print(f"ℹ️  [{event_num}] {event_type}: {json.dumps(event, ensure_ascii=False, indent=2)}")

    async def get_conversations(self, user: str = "test-user", limit: int = 20) -> None:
        """获取会话列表"""
        url = f"{self.base_url}/conversations"
        params = {
            "user": user,
            "limit": limit,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                result = response.json()
                print("会话列表:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"获取会话列表失败: {e}")
    
    async def stop_message(self, task_id: str, user: str = "test-user") -> None:
        """停止消息生成"""
        url = f"{self.base_url}/chat-messages/{task_id}/stop"
        payload = {"user": user}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                result = response.json()
                print("停止消息生成:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"停止消息失败: {e}")


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Dify Chat API 测试客户端（基于官方文档）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python scripts/dify_workflow_client.py --api-key YOUR_KEY --query "你好"
  
  # 使用阻塞模式
  python scripts/dify_workflow_client.py --api-key YOUR_KEY --query "你好" --blocking
  
  # 自定义 API 地址
  python scripts/dify_workflow_client.py --api-key YOUR_KEY --base-url http://localhost:5001/v1 --query "测试"
  
  # 传递输入变量
  python scripts/dify_workflow_client.py --api-key YOUR_KEY --query "分析" --inputs '{"var1": "value1"}'
  
  # 多轮对话
  python scripts/dify_workflow_client.py --api-key YOUR_KEY --query "继续" --conversation-id CONV_ID
        """,
    )
    
    parser.add_argument(
        "--api-key",
        required=True,
        help="Dify API 密钥 (必需)",
    )
    
    parser.add_argument(
        "--base-url",
        default="https://api.dify.ai/v1",
        help="Dify API 基础 URL (默认: %(default)s)",
    )
    
    parser.add_argument(
        "--query",
        "-q",
        required=True,
        help="要发送给 workflow 的查询文本 (必需)",
    )
    
    parser.add_argument(
        "--user",
        default="test-user",
        help="用户标识符 (默认: %(default)s)",
    )
    
    parser.add_argument(
        "--inputs",
        type=str,
        help="额外的输入参数，JSON 格式，例如: '{\"key\": \"value\"}'",
    )
    
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="使用阻塞模式而不是流式模式",
    )
    
    parser.add_argument(
        "--conversation-id",
        help="会话ID，用于多轮对话",
    )
    
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="请求超时时间（秒）(默认: %(default)s)",
    )
    
    parser.add_argument(
        "--list-conversations",
        action="store_true",
        help="列出会话历史后退出",
    )
    
    parser.add_argument(
        "--files",
        type=str,
        help="文件列表（JSON 格式），用于 Vision 模型",
    )
    
    parser.add_argument(
        "--no-auto-name",
        action="store_true",
        help="不自动生成会话标题",
    )
    
    return parser.parse_args()


async def main() -> None:
    """主函数"""
    args = parse_args()
    
    # 解析额外的输入参数
    inputs = None
    if args.inputs:
        try:
            inputs = json.loads(args.inputs)
        except json.JSONDecodeError:
            print(f"错误: 无法解析 --inputs 参数为 JSON: {args.inputs}", file=sys.stderr)
            sys.exit(1)
    
    # 解析文件列表
    files = None
    if args.files:
        try:
            files = json.loads(args.files)
        except json.JSONDecodeError:
            print(f"错误: 无法解析 --files 参数为 JSON: {args.files}", file=sys.stderr)
            sys.exit(1)
    
    # 创建客户端
    client = DifyChatClient(
        api_key=args.api_key,
        base_url=args.base_url,
        timeout=args.timeout,
    )
    
    # 如果只是列出会话
    if args.list_conversations:
        await client.get_conversations(user=args.user)
        return
    
    # 发送聊天消息
    response_mode = "blocking" if args.blocking else "streaming"
    await client.send_chat_message(
        query=args.query,
        user=args.user,
        inputs=inputs,
        response_mode=response_mode,
        conversation_id=args.conversation_id,
        files=files,
        auto_generate_name=not args.no_auto_name,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n中断执行")
        sys.exit(0)

