# Realtime RAG Prototype

This repository contains a minimal FastAPI-based WebSocket backend that accepts
real-time ASR text chunks, performs a lightweight question detection heuristic,
and returns a mocked Retrieval-Augmented Generation (RAG) answer when a
question-like utterance is detected.

## Features

- WebSocket endpoint at `/ws/realtime-asr` for streaming ASR chunks.
- Simple in-memory session state to accumulate final ASR segments.
- Heuristic question detection (punctuation and keyword based).
- Mocked RAG call that demonstrates the expected status/answer flow.
- Basic control commands (`pause`, `resume`, `stop`).

## Getting Started

1. **Install dependencies** (preferably inside a virtual environment):

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the service**:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Run the included test client** (optional):

   ```bash
   python scripts/ws_client.py --uri ws://localhost:8000/ws/realtime-asr
   ```

   The script replays a small sequence of ASR chunks and prints the
   server's responses so you can observe the end-to-end flow.

4. **Test with `websocat` or similar**:

   ```bash
   websocat ws://localhost:8000/ws/realtime-asr
   ```

   Example payloads:

   ```json
   {"type": "asr_chunk", "text": "你好，请问库存情况怎么样", "is_final": true}
   ```

   ```json
   {"type": "control", "action": "pause"}
   ```

The current implementation uses a mock RAG response. Integrate your preferred
LLM/RAG provider inside `run_mock_rag` in `app/main.py` when ready.
