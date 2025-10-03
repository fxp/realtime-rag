import os
import json
from fastapi.testclient import TestClient

os.environ.setdefault("USE_MOCK_RAG", "1")

from app.main import app  # noqa: E402


client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_websocket_handshake_and_listening():
    with client.websocket_connect("/ws/realtime-asr") as ws:
        first = ws.receive_json()
        assert first["type"] == "ack"
        assert "session_id" in first

        second = ws.receive_json()
        assert second == {"type": "status", "stage": "listening"}


def test_waiting_for_question_then_answer_flow():
    with client.websocket_connect("/ws/realtime-asr") as ws:
        ws.receive_json()  # ack
        ws.receive_json()  # listening

        ws.send_json({"type": "asr_chunk", "text": "大家好，今天开会。", "is_final": True})
        ws.receive_json()  # ack
        status = ws.receive_json()
        assert status["type"] == "status"
        assert status["stage"] == "waiting_for_question"

        ws.send_json({"type": "asr_chunk", "text": "请问下一步怎么推进？", "is_final": True})
        ws.receive_json()  # ack
        analyzing = ws.receive_json()
        querying = ws.receive_json()
        assert analyzing["type"] == "status" and analyzing["stage"] == "analyzing"
        assert querying["type"] == "status" and querying["stage"] == "querying_rag"

        answers = []
        while True:
            msg = ws.receive_json()
            if msg["type"] == "answer":
                answers.append(msg)
                if msg["final"]:
                    break
        assert len(answers) >= 1
        idle = ws.receive_json()
        assert idle == {"type": "status", "stage": "idle"}


def test_control_pause_resume_and_stop():
    with client.websocket_connect("/ws/realtime-asr") as ws:
        ws.receive_json()  # ack
        ws.receive_json()  # listening

        ws.send_json({"type": "control", "action": "pause"})
        ws.receive_json()  # ack
        paused = ws.receive_json()
        assert paused == {"type": "status", "stage": "paused"}

        ws.send_json({"type": "asr_chunk", "text": "这条在暂停时应被忽略", "is_final": True})
        ws.receive_json()  # ack
        note = ws.receive_json()
        assert note["type"] == "status" and note["stage"] == "paused"

        ws.send_json({"type": "control", "action": "resume"})
        ws.receive_json()  # ack
        listening = ws.receive_json()
        assert listening == {"type": "status", "stage": "listening"}

        ws.send_json({"type": "control", "action": "stop"})
        ws.receive_json()  # ack
        closed = ws.receive_json()
        assert closed == {"type": "status", "stage": "closed"}


def test_invalid_json_error():
    with client.websocket_connect("/ws/realtime-asr") as ws:
        ws.receive_json()  # ack
        ws.receive_json()  # listening

        ws.send_text("not a json")
        err = ws.receive_json()
        assert err["type"] == "error"
        assert err["code"] == "INVALID_JSON"
