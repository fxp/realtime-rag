"""Simple WebSocket client for manual integration testing.

This script connects to the realtime RAG WebSocket backend, replays a
predefined sequence of ASR chunks, and prints every message received from the
server. It helps validate the end-to-end flow without requiring a custom UI.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from typing import Iterable, List

import websockets


@dataclass
class AsrChunk:
    """Representation of a single ASR chunk to send to the backend."""

    text: str
    is_final: bool = True
    timestamp_ms: int | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "type": "asr_chunk",
            "text": self.text,
            "is_final": self.is_final,
        }
        if self.timestamp_ms is not None:
            payload["timestamp"] = self.timestamp_ms
        return payload


async def _send_sequence(ws: websockets.WebSocketClientProtocol, chunks: Iterable[AsrChunk]) -> None:
    """Send ASR chunks with small pauses to emulate streaming input."""

    for chunk in chunks:
        await ws.send(json.dumps(chunk.to_payload(), ensure_ascii=False))
        await asyncio.sleep(0.1)

    # Gracefully stop the session so the server can clean up state.
    await ws.send(json.dumps({"type": "control", "action": "stop"}))


async def _reader(ws: websockets.WebSocketClientProtocol) -> None:
    """Continuously print responses until the connection closes."""

    try:
        async for message in ws:
            print("<-", message)
    except websockets.ConnectionClosedOK:
        print("Connection closed by server.")
    except websockets.ConnectionClosedError as exc:  # pragma: no cover - depends on runtime
        print(f"Connection closed with error: {exc}")


def _build_default_sequence() -> List[AsrChunk]:
    """Create a short scenario that should trigger a mock RAG answer."""

    return [
        AsrChunk(text="大家好，今天我们复盘一下发布进展。"),
        AsrChunk(text="目前后台服务已经部署完成。"),
        AsrChunk(text="请问接下来要怎么安排推送上线？"),
    ]


async def run_client(uri: str, sequence: Iterable[AsrChunk]) -> None:
    """Run the client by connecting, launching the reader, and replaying chunks."""

    async with websockets.connect(uri) as ws:
        reader_task = asyncio.create_task(_reader(ws))
        await _send_sequence(ws, sequence)
        await reader_task


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test client for realtime RAG WebSocket service")
    parser.add_argument(
        "--uri",
        default="ws://127.0.0.1:8000/ws/realtime-asr",
        help="WebSocket endpoint to connect to (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sequence = _build_default_sequence()
    try:
        asyncio.run(run_client(args.uri, sequence))
    except KeyboardInterrupt:  # pragma: no cover - user initiated
        pass


if __name__ == "__main__":
    main()
