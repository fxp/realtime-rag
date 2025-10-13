"""Utility helpers shared across realtime WebSocket tests."""
from __future__ import annotations

from typing import Any


def perform_handshake(ws: Any) -> None:
    """Consume the initial ack and listening status messages from the server."""

    initial_ack = ws.receive_json()
    assert initial_ack["type"] == "ack"

    listening = ws.receive_json()
    assert listening["type"] == "status"
    assert listening["stage"] == "listening"
