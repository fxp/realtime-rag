"""Minimal realtime RAG WebSocket prototype."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Realtime RAG Prototype")

# Dify API 配置（从 .env 文件或环境变量读取）
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
DIFY_TIMEOUT = float(os.getenv("DIFY_TIMEOUT", "60.0"))

# 启动时显示配置信息
if DIFY_API_KEY:
    print(f"✓ Dify API 已配置: {DIFY_API_KEY[:10]}...")
    print(f"✓ Base URL: {DIFY_BASE_URL}")
else:
    print("⚠️  警告: DIFY_API_KEY 未配置，RAG 功能将无法使用")


class SessionState:
    """Track per-connection conversation state."""

    QUESTION_HINTS = {"?", "吗", "呢", "怎么", "为何", "为什么", "请问", "多少", "哪", "怎么做"}

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.final_chunks: List[str] = []
        self.is_paused: bool = False

    def add_chunk(self, text: str, is_final: bool) -> None:
        if is_final:
            self.final_chunks.append(text.strip())

    @property
    def aggregated_text(self) -> str:
        return " ".join(chunk for chunk in self.final_chunks if chunk)

    def reset(self) -> None:
        self.final_chunks.clear()

    def looks_like_question(self) -> bool:
        text = self.aggregated_text
        if not text:
            return False
        lowered = text.lower()
        if any(token in lowered for token in ("what", "why", "how", "when", "where", "?")):
            return True
        return any(hint in text for hint in self.QUESTION_HINTS)


async def run_dify_rag(
    query: str,
    user: str = "websocket-user",
    conversation_id: Optional[str] = None,
) -> str:
    """调用 Dify Chat API 获取真实的 RAG 回答（阻塞模式）"""
    
    # 检查 API Key 是否配置
    if not DIFY_API_KEY:
        return "错误：未配置 DIFY_API_KEY 环境变量。请设置后重启服务。"
    
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
    
    try:
        async with httpx.AsyncClient(timeout=DIFY_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # 根据官方文档提取 answer
            if result.get("event") == "message":
                answer = result.get("answer", "")
                
                # 可选：记录元数据用于调试
                metadata = result.get("metadata", {})
                usage = metadata.get("usage", {})
                if usage:
                    print(f"[Dify RAG] Tokens: {usage.get('total_tokens', 0)}, "
                          f"Price: {usage.get('total_price', 0)} {usage.get('currency', 'USD')}")
                
                return answer if answer else "未获取到回答。"
            else:
                return f"Dify API 返回了意外的事件类型: {result.get('event')}"
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Dify API HTTP 错误 {e.response.status_code}: {e.response.text}"
        print(f"[Dify RAG Error] {error_msg}")
        return f"调用 RAG 服务失败：{error_msg}"
    
    except httpx.RequestError as e:
        error_msg = f"请求错误: {str(e)}"
        print(f"[Dify RAG Error] {error_msg}")
        return f"调用 RAG 服务失败：{error_msg}"
    
    except Exception as e:
        error_msg = f"未知错误: {str(e)}"
        print(f"[Dify RAG Error] {error_msg}")
        return f"调用 RAG 服务失败：{error_msg}"


async def run_mock_rag(query: str) -> str:
    """Simulate a RAG backend response."""
    await asyncio.sleep(0.1)
    return (
        f"这是一个模拟回答，用于展示系统流程。"
        f"根据你的问题「{query}」，建议稍后接入真正的 RAG 服务。"
    )


def stream_answer(answer: str, max_chunk_size: int = 120) -> List[str]:
    """Split long answers into smaller chunks for streaming."""
    chunks: List[str] = []
    current = []
    current_len = 0
    for part in answer.split():
        part_len = len(part) + 1  # include space
        if current_len + part_len > max_chunk_size and current:
            chunks.append(" ".join(current))
            current = [part]
            current_len = len(part)
        else:
            current.append(part)
            current_len += part_len
    if current:
        chunks.append(" ".join(current))
    if not chunks:
        chunks.append(answer)
    return chunks


@app.websocket("/ws/realtime-asr")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    # 初始会话ID，如果客户端提供了session_id则使用客户端的
    initial_session_id = str(uuid4())
    session = SessionState(session_id=initial_session_id)
    await websocket.send_json({"type": "ack", "message": "connected", "session_id": session.session_id})
    await websocket.send_json({"type": "status", "stage": "listening"})

    try:
        while True:
            message = await websocket.receive_text()
            try:
                payload: Dict[str, object] = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "code": "INVALID_JSON",
                    "message": "Payload must be valid JSON text.",
                })
                continue

            msg_type = payload.get("type")
            if not isinstance(msg_type, str):
                await websocket.send_json({
                    "type": "error",
                    "code": "INVALID_MESSAGE",
                    "message": "Missing or invalid 'type' field.",
                })
                continue

            # 检查客户端是否提供了session_id
            client_session_id = payload.get("session_id")
            if isinstance(client_session_id, str) and client_session_id != session.session_id:
                # 如果客户端提供了不同的session_id，更新会话
                session = SessionState(session_id=client_session_id)
            
            await websocket.send_json({
                "type": "ack",
                "received_type": msg_type,
                "session_id": session.session_id,
            })

            if msg_type == "keepalive":
                continue

            if msg_type == "control":
                action = payload.get("action")
                if action == "pause":
                    session.is_paused = True
                    await websocket.send_json({"type": "status", "stage": "paused"})
                elif action == "resume":
                    session.is_paused = False
                    await websocket.send_json({"type": "status", "stage": "listening"})
                elif action == "stop":
                    await websocket.send_json({"type": "status", "stage": "closed"})
                    break
                else:
                    await websocket.send_json({
                        "type": "error",
                        "code": "UNKNOWN_ACTION",
                        "message": "Supported actions: pause, resume, stop.",
                    })
                continue

            if msg_type != "asr_chunk":
                await websocket.send_json({
                    "type": "error",
                    "code": "UNSUPPORTED_TYPE",
                    "message": "Expected message type 'asr_chunk'.",
                })
                continue

            if session.is_paused:
                await websocket.send_json({
                    "type": "status",
                    "stage": "paused",
                    "note": "Chunk received while paused; ignoring.",
                })
                continue

            text = payload.get("text")
            is_final = payload.get("is_final", False)
            if not isinstance(text, str):
                await websocket.send_json({
                    "type": "error",
                    "code": "INVALID_MESSAGE",
                    "message": "'text' field must be a string.",
                })
                continue
            if not isinstance(is_final, bool):
                await websocket.send_json({
                    "type": "error",
                    "code": "INVALID_MESSAGE",
                    "message": "'is_final' field must be a boolean.",
                })
                continue

            session.add_chunk(text, is_final=is_final)

            if not is_final:
                continue

            if not session.looks_like_question():
                await websocket.send_json({
                    "type": "status",
                    "stage": "waiting_for_question",
                    "note": "No question detected in final chunk.",
                })
                continue

            question = session.aggregated_text
            await websocket.send_json({"type": "status", "stage": "analyzing", "question": question})
            await websocket.send_json({"type": "status", "stage": "querying_rag"})

            # 使用真实的 Dify RAG 调用
            # 如果需要使用模拟调用，可以切换为 run_mock_rag(question)
            answer = await run_dify_rag(
                query=question,
                user=f"ws-user-{session.session_id}",
                conversation_id=None,  # 可以传入 session.session_id 来支持多轮对话
            )
            chunks = stream_answer(answer)
            for idx, chunk in enumerate(chunks):
                await websocket.send_json({
                    "type": "answer",
                    "stream_index": idx,
                    "content": chunk,
                    "final": idx == len(chunks) - 1,
                })
            await websocket.send_json({"type": "status", "stage": "idle"})
            session.reset()
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":  # pragma: no cover - manual launch helper
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
