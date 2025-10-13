"""Regression tests for the standard realtime WebSocket workflow."""
from __future__ import annotations

import asyncio
from typing import List

import pytest
from fastapi.testclient import TestClient

from app.services.dify_client import DifyClient
from tests.helpers import perform_handshake


def test_standard_query_flow(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """The classic final-chunk question should trigger the normal analysis pipeline."""

    captured: List[str] = []

    async def fake_query(text: str, user: str = "", conversation_id: str | None = None) -> str:
        captured.append(text)
        await asyncio.sleep(0)
        return "标准流程回答"

    monkeypatch.setattr(DifyClient, "query", staticmethod(fake_query))

    with client.websocket_connect("/ws/realtime-asr") as ws:
        perform_handshake(ws)

        ws.send_json({"type": "asr_chunk", "text": "现在的测试进展怎么样?", "is_final": True})

        ack = ws.receive_json()
        assert ack["type"] == "ack"

        analyzing = ws.receive_json()
        assert analyzing["type"] == "status"
        assert analyzing["stage"] == "analyzing"
        assert analyzing["question"] == "现在的测试进展怎么样?"

        querying = ws.receive_json()
        assert querying["type"] == "status"
        assert querying["stage"] == "querying_rag"
        assert "mode" not in querying

        answer = ws.receive_json()
        assert answer["type"] == "answer"
        assert answer["final"] is True
        assert "标准流程回答" in answer["content"]

        idle = ws.receive_json()
        assert idle["type"] == "status"
        assert idle["stage"] == "idle"

    assert captured == ["现在的测试进展怎么样?"]


def test_standard_flow_handles_multiple_statements_before_question(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Multiple finalized statements should aggregate before triggering the question pipeline."""

    captured: List[str] = []

    async def fake_query(text: str, user: str = "", conversation_id: str | None = None) -> str:
        captured.append(text)
        await asyncio.sleep(0)
        return "综合回答"

    monkeypatch.setattr(DifyClient, "query", staticmethod(fake_query))

    with client.websocket_connect("/ws/realtime-asr") as ws:
        perform_handshake(ws)

        ws.send_json({"type": "asr_chunk", "text": "我们已经完成第一阶段", "is_final": True})

        ack_first = ws.receive_json()
        assert ack_first["type"] == "ack"

        waiting = ws.receive_json()
        assert waiting["type"] == "status"
        assert waiting["stage"] == "waiting_for_question"

        ws.send_json({"type": "asr_chunk", "text": "接下来该怎么办?", "is_final": True})

        ack_second = ws.receive_json()
        assert ack_second["type"] == "ack"

        analyzing = ws.receive_json()
        assert analyzing["type"] == "status"
        assert analyzing["stage"] == "analyzing"

        querying = ws.receive_json()
        assert querying["type"] == "status"
        assert querying["stage"] == "querying_rag"
        assert "mode" not in querying

        answer = ws.receive_json()
        assert answer["type"] == "answer"
        assert answer["final"] is True
        assert "综合回答" in answer["content"]

        idle = ws.receive_json()
        assert idle["type"] == "status"
        assert idle["stage"] == "idle"

    assert captured == ["我们已经完成第一阶段 接下来该怎么办?"]
