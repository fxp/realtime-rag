"""WebSocket 路由处理"""
from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from typing import Dict
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.session import SessionState
from app.services.dify_client import DifyClient
from app.services.text_utils import stream_answer

router = APIRouter()


@router.websocket("/ws/realtime-asr")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    send_lock = asyncio.Lock()
    initial_session_id = str(uuid4())
    session = SessionState(session_id=initial_session_id)
    await send_json_locked(websocket, send_lock, {"type": "ack", "message": "connected", "session_id": session.session_id})
    await send_json_locked(websocket, send_lock, {"type": "status", "stage": "listening"})

    try:
        while True:
            message = await websocket.receive_text()
            try:
                payload: Dict[str, object] = json.loads(message)
            except json.JSONDecodeError:
                await send_json_locked(websocket, send_lock, {"type": "error", "code": "INVALID_JSON", "message": "Invalid JSON"})
                continue

            msg_type = payload.get("type")
            if not isinstance(msg_type, str):
                await send_json_locked(websocket, send_lock, {"type": "error", "code": "INVALID_MESSAGE", "message": "Missing type"})
                continue

            client_session_id = payload.get("session_id")
            if isinstance(client_session_id, str) and client_session_id != session.session_id:
                await cancel_current_query(session, websocket, send_lock, reason="session_switch")
                session = SessionState(session_id=client_session_id)

            await send_json_locked(websocket, send_lock, {"type": "ack", "received_type": msg_type, "session_id": session.session_id})

            if msg_type == "keepalive":
                continue
            if msg_type == "control":
                if await handle_control(websocket, session, payload, send_lock):
                    break
                continue
            if msg_type == "asr_chunk":
                await handle_asr_chunk(websocket, session, payload, send_lock)
                continue

            await send_json_locked(websocket, send_lock, {"type": "error", "code": "UNSUPPORTED_TYPE", "message": f"Unsupported: {msg_type}"})
    except WebSocketDisconnect:
        pass
    finally:
        if session.current_query_task and not session.current_query_task.done():
            session.current_query_task.cancel()
            with suppress(asyncio.CancelledError):
                await session.current_query_task


async def handle_control(websocket: WebSocket, session: SessionState, payload: Dict, send_lock: asyncio.Lock) -> bool:
    action = payload.get("action")
    if action == "pause":
        session.is_paused = True
        await send_json_locked(websocket, send_lock, {"type": "status", "stage": "paused"})
    elif action == "resume":
        session.is_paused = False
        await send_json_locked(websocket, send_lock, {"type": "status", "stage": "listening"})
    elif action == "stop":
        await cancel_current_query(session, websocket, send_lock, reason="stop")
        await send_json_locked(websocket, send_lock, {"type": "status", "stage": "closed"})
        return True
    elif action == "instant_query":
        if not session.last_final_text:
            await send_json_locked(websocket, send_lock, {"type": "error", "code": "NO_FINAL_ASR", "message": "No finalized ASR chunk to query"})
            return False
        await cancel_current_query(session, websocket, send_lock, reason="instant_query")
        await start_query_task(session, websocket, send_lock, session.last_final_text, mode="instant")
    else:
        await send_json_locked(websocket, send_lock, {"type": "error", "code": "UNKNOWN_ACTION", "message": "Unknown action"})
    return False


async def handle_asr_chunk(websocket: WebSocket, session: SessionState, payload: Dict, send_lock: asyncio.Lock) -> None:
    if session.is_paused:
        await send_json_locked(websocket, send_lock, {"type": "status", "stage": "paused", "note": "Chunk ignored"})
        return

    text = payload.get("text")
    is_final = payload.get("is_final", False)

    if not isinstance(text, str):
        await send_json_locked(websocket, send_lock, {"type": "error", "code": "INVALID_MESSAGE", "message": "text must be string"})
        return
    if not isinstance(is_final, bool):
        await send_json_locked(websocket, send_lock, {"type": "error", "code": "INVALID_MESSAGE", "message": "is_final must be boolean"})
        return

    session.add_chunk(text, is_final=is_final)

    if not is_final:
        return

    if session.has_active_query:
        await send_json_locked(websocket, send_lock, {"type": "status", "stage": "waiting_for_question", "note": "RAG query already running"})
        return

    if not session.looks_like_question():
        await send_json_locked(websocket, send_lock, {"type": "status", "stage": "waiting_for_question", "note": "No question detected"})
        return

    question = session.aggregated_text.strip()
    if not question:
        await send_json_locked(websocket, send_lock, {"type": "error", "code": "EMPTY_QUESTION", "message": "Final ASR chunk is empty"})
        return

    await start_query_task(session, websocket, send_lock, question, mode="standard")


async def send_json_locked(websocket: WebSocket, lock: asyncio.Lock, payload: Dict) -> None:
    async with lock:
        await websocket.send_json(payload)


async def cancel_current_query(session: SessionState, websocket: WebSocket, lock: asyncio.Lock, *, reason: str) -> None:
    task = session.current_query_task
    if not task or task.done():
        session.current_query_task = None
        return

    await send_json_locked(websocket, lock, {"type": "status", "stage": "interrupting", "note": reason})
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    session.current_query_task = None


async def start_query_task(session: SessionState, websocket: WebSocket, lock: asyncio.Lock, question: str, *, mode: str) -> None:
    question = question.strip()
    if not question:
        await send_json_locked(websocket, lock, {"type": "error", "code": "EMPTY_QUESTION", "message": "Final ASR chunk is empty"})
        return

    if session.current_query_task and not session.current_query_task.done():
        # 不允许同时存在两个查询任务
        await send_json_locked(websocket, lock, {"type": "status", "stage": "waiting_for_question", "note": "Query already in progress"})
        return

    async def runner() -> None:
        await perform_query(session, websocket, lock, question, mode=mode)

    task = asyncio.create_task(runner())
    session.current_query_task = task


async def perform_query(session: SessionState, websocket: WebSocket, lock: asyncio.Lock, question: str, *, mode: str) -> None:
    try:
        if mode == "instant":
            await send_json_locked(websocket, lock, {"type": "status", "stage": "instant_query", "question": question})
        else:
            await send_json_locked(websocket, lock, {"type": "status", "stage": "analyzing", "question": question})

        querying_payload = {"type": "status", "stage": "querying_rag"}
        if mode == "instant":
            querying_payload["mode"] = "instant"
        await send_json_locked(websocket, lock, querying_payload)

        answer = await DifyClient.query(text=question, user=f"ws-user-{session.session_id}")
        chunks = stream_answer(answer)
        for idx, chunk in enumerate(chunks):
            await send_json_locked(
                websocket,
                lock,
                {"type": "answer", "stream_index": idx, "content": chunk, "final": idx == len(chunks) - 1},
            )

        await send_json_locked(websocket, lock, {"type": "status", "stage": "idle"})
        session.reset()
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # pragma: no cover - unexpected runtime failure
        await send_json_locked(websocket, lock, {"type": "error", "code": "SERVER_ERROR", "message": str(exc)})
    finally:
        session.current_query_task = None
