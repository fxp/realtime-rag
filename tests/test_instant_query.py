import asyncio
from typing import List

import pytest
from fastapi.testclient import TestClient

from app.services.dify_client import DifyClient
from tests.helpers import perform_handshake


def test_instant_query_triggers_immediate_rag_call(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: List[str] = []

    async def fake_query(text: str, user: str = "", conversation_id: str | None = None) -> str:
        captured.append(text)
        await asyncio.sleep(0)
        return "即时回答"

    monkeypatch.setattr(DifyClient, "query", staticmethod(fake_query))

    with client.websocket_connect("/ws/realtime-asr") as ws:
        perform_handshake(ws)

        ws.send_json({"type": "asr_chunk", "text": "这是测试命令", "is_final": True})
        ack = ws.receive_json()
        assert ack["type"] == "ack"
        status = ws.receive_json()
        assert status["type"] == "status"
        assert status["stage"] == "waiting_for_question"

        ws.send_json({"type": "control", "action": "instant_query"})
        ack = ws.receive_json()
        assert ack["type"] == "ack"

        instant = ws.receive_json()
        assert instant["stage"] == "instant_query"
        assert instant["question"] == "这是测试命令"

        querying = ws.receive_json()
        assert querying["stage"] == "querying_rag"
        assert querying.get("mode") == "instant"

        answer = ws.receive_json()
        assert answer["type"] == "answer"
        assert answer["final"] is True
        assert "即时回答" in answer["content"]

        idle = ws.receive_json()
        assert idle["stage"] == "idle"

    assert captured == ["这是测试命令"]


def test_instant_query_cancels_active_query(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[str] = []
    flags = {"cancelled": False}

    async def fake_query(text: str, user: str = "", conversation_id: str | None = None) -> str:
        calls.append(text)
        if len(calls) == 1:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                flags["cancelled"] = True
                raise
            return "不会返回"
        return "新的回答"

    monkeypatch.setattr(DifyClient, "query", staticmethod(fake_query))

    with client.websocket_connect("/ws/realtime-asr") as ws:
        perform_handshake(ws)

        ws.send_json({"type": "asr_chunk", "text": "请问现在的进度?", "is_final": True})
        ack = ws.receive_json()
        assert ack["type"] == "ack"

        analyzing = ws.receive_json()
        assert analyzing["stage"] == "analyzing"
        querying = ws.receive_json()
        assert querying["stage"] == "querying_rag"

        ws.send_json({"type": "control", "action": "instant_query"})
        ack = ws.receive_json()
        assert ack["type"] == "ack"

        interrupting = ws.receive_json()
        assert interrupting["stage"] == "interrupting"

        instant = ws.receive_json()
        assert instant["stage"] == "instant_query"
        querying_instant = ws.receive_json()
        assert querying_instant["stage"] == "querying_rag"
        assert querying_instant.get("mode") == "instant"

        answer = ws.receive_json()
        assert answer["type"] == "answer"
        assert answer["final"] is True
        idle = ws.receive_json()
        assert idle["stage"] == "idle"

    assert flags["cancelled"] is True
    assert calls[0] == "请问现在的进度?"
    assert calls[1] == "请问现在的进度?"
