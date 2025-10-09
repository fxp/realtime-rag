"""WebSocket 路由处理"""
from __future__ import annotations
import json
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
                await websocket.send_json({"type": "error", "code": "INVALID_JSON", "message": "Invalid JSON"})
                continue
            
            msg_type = payload.get("type")
            if not isinstance(msg_type, str):
                await websocket.send_json({"type": "error", "code": "INVALID_MESSAGE", "message": "Missing type"})
                continue
            
            client_session_id = payload.get("session_id")
            if isinstance(client_session_id, str) and client_session_id != session.session_id:
                session = SessionState(session_id=client_session_id)
            
            await websocket.send_json({"type": "ack", "received_type": msg_type, "session_id": session.session_id})
            
            if msg_type == "keepalive":
                continue
            elif msg_type == "control":
                if await handle_control(websocket, session, payload):
                    break
                continue
            elif msg_type == "asr_chunk":
                await handle_asr_chunk(websocket, session, payload)
            else:
                await websocket.send_json({"type": "error", "code": "UNSUPPORTED_TYPE", "message": f"Unsupported: {msg_type}"})
    except WebSocketDisconnect:
        pass

async def handle_control(websocket: WebSocket, session: SessionState, payload: Dict) -> bool:
    action = payload.get("action")
    if action == "pause":
        session.is_paused = True
        await websocket.send_json({"type": "status", "stage": "paused"})
    elif action == "resume":
        session.is_paused = False
        await websocket.send_json({"type": "status", "stage": "listening"})
    elif action == "stop":
        await websocket.send_json({"type": "status", "stage": "closed"})
        return True
    else:
        await websocket.send_json({"type": "error", "code": "UNKNOWN_ACTION", "message": "Unknown action"})
    return False

async def handle_asr_chunk(websocket: WebSocket, session: SessionState, payload: Dict) -> None:
    if session.is_paused:
        await websocket.send_json({"type": "status", "stage": "paused", "note": "Chunk ignored"})
        return
    
    text = payload.get("text")
    is_final = payload.get("is_final", False)
    
    if not isinstance(text, str):
        await websocket.send_json({"type": "error", "code": "INVALID_MESSAGE", "message": "text must be string"})
        return
    if not isinstance(is_final, bool):
        await websocket.send_json({"type": "error", "code": "INVALID_MESSAGE", "message": "is_final must be boolean"})
        return
    
    session.add_chunk(text, is_final=is_final)
    
    if not is_final:
        return
    
    if not session.looks_like_question():
        await websocket.send_json({"type": "status", "stage": "waiting_for_question", "note": "No question detected"})
        return
    
    question = session.aggregated_text
    await websocket.send_json({"type": "status", "stage": "analyzing", "question": question})
    await websocket.send_json({"type": "status", "stage": "querying_rag"})
    
    answer = await DifyClient.query(text=question, user=f"ws-user-{session.session_id}")
    
    chunks = stream_answer(answer)
    for idx, chunk in enumerate(chunks):
        await websocket.send_json({"type": "answer", "stream_index": idx, "content": chunk, "final": idx == len(chunks) - 1})
    
    await websocket.send_json({"type": "status", "stage": "idle"})
    session.reset()
