"""Shared pytest fixtures for realtime RAG tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient instance for WebSocket integration tests."""
    with TestClient(app) as test_client:
        yield test_client
