"""Minimal realtime RAG WebSocket prototype."""
from __future__ import annotations

import asyncio
import json
from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="Realtime RAG Prototype")


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


async def run_mock_rag(query: str) -> str:
    """Simulate a RAG backend response."""
    await asyncio.sleep(0.1)
    return (
        "这是一个模拟回答，用于展示系统流程。"\
        f" 根据你的问题“{query}”，建议稍后接入真正的 RAG 服务。"
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
    session = SessionState(session_id=str(uuid4()))
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

            answer = await run_mock_rag(question)
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
