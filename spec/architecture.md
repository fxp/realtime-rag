# Architecture

## Overview

Realtime RAG is a FastAPI application that exposes a WebSocket endpoint for streaming automatic speech recognition (ASR) results, orchestrating question detection, and delegating question answering to the Dify Chat API. The system emphasises low-latency bidirectional communication with clients while maintaining a simple stateless backend that derives session state from messages.

## Goals

- Provide a resilient WebSocket service that can ingest streaming ASR transcripts.
- Detect finalized user questions and route them to a Retrieval Augmented Generation (RAG) backend.
- Stream responses back to the client in partial chunks for responsive user interfaces.
- Offer observability and graceful error handling around third-party API usage.

## Component Diagram

```
Client ──(WebSocket JSON)──> FastAPI Application ──(HTTP JSON)──> Dify Chat API
            ▲                        │
            │                        └──> SessionState / Text Utilities
            └────(streamed answers)───────────────────────────────────────
```

## Components

### FastAPI Application (`app/main.py`)
- Configures the FastAPI instance with metadata and health check routes.
- Validates environment configuration on startup.
- Includes the WebSocket router that hosts the realtime endpoint.

### WebSocket Router (`app/routers/websocket.py`)
- Manages WebSocket lifecycles: accepting connections, acknowledging messages, and handling disconnects.
- Maintains a `SessionState` instance per client to accumulate ASR chunks and track pause/resume controls.
- Delegates question answering to `DifyClient` once a final ASR chunk forms a question.
- Streams status updates, acknowledgements, partial answers, and errors back to the client.

### Session State (`app/models/session.py`)
- Represents the per-connection state machine.
- Buffers finalized ASR text and offers heuristics to decide when text resembles a question.
- Provides helpers to reset state after answers are delivered.

### Dify Client (`app/services/dify_client.py`)
- Wraps HTTPX asynchronous requests to the Dify Chat API.
- Adds authorization headers and optional conversation identifiers.
- Handles timeout, status, network, and unexpected error scenarios, returning human-readable messages for downstream streaming.

### Text Utilities (`app/services/text_utils.py`)
- Slices long Dify answers into manageable chunks for streaming delivery to the client.

## Runtime Behaviour

1. A client connects to the `/ws/realtime-asr` endpoint. The server acknowledges with a session identifier and enters the `listening` stage.
2. Clients stream ASR chunks via `asr_chunk` messages. Final chunks are accumulated in `SessionState`.
3. When a final chunk arrives and the aggregated text resembles a question, the router transitions into `analyzing`/`querying_rag` stages and invokes `DifyClient.query`.
4. Responses from Dify are split into segments by `stream_answer` and emitted as `answer` messages until completion.
5. After the answer is sent, the session reverts to the `idle` stage and awaits additional final chunks or control messages. Control actions (`pause`, `resume`, `stop`) adjust state transitions.

## Configuration

- Environment variables (via `.env`) control API credentials, endpoint base URL, timeout, WebSocket path, and metadata.
- Missing API credentials cause the service to respond with explicit error messages rather than failing silently.

## Error Handling & Resilience

- JSON parsing errors and unsupported message types produce structured error payloads for clients.
- Paused sessions explicitly acknowledge ignored chunks to keep client UIs synchronised.
- Dify request errors are logged and converted into textual responses so that the WebSocket stream remains consistent.

## Extensibility Considerations

- Additional message types can be introduced by extending the WebSocket router's dispatch logic while maintaining backward compatibility.
- Alternative RAG providers can be supported by swapping out `DifyClient` with an adapter implementing the same `query` interface.
- Multi-tenant authentication can be layered by associating session IDs with upstream credentials when accepting connections.
