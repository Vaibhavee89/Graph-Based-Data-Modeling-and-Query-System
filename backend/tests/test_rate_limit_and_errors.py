"""Tests for chat rate limiting and non-leaky error messages."""
from unittest.mock import Mock, patch

import networkx as nx
import pytest
from fastapi.testclient import TestClient

from app.core import rate_limit
from app.core.rate_limit import RateLimiter
from app.main import app
from app.routers.query import get_query_service
from app.schemas.query import QueryResponse
from app.services.query_service import QueryService


def test_limiter_blocks_after_limit_and_recovers():
    with patch("app.core.rate_limit.time.monotonic") as clock:
        clock.return_value = 0.0
        rl = RateLimiter(limit=2, window=60)
        assert rl.check("a") == 0
        assert rl.check("a") == 0
        assert rl.check("a") > 0          # third call blocked
        assert rl.check("b") == 0         # other clients unaffected
        clock.return_value = 61.0
        assert rl.check("a") == 0         # window passed


@pytest.fixture
def client():
    fake = Mock()
    fake.process_query.return_value = QueryResponse(success=True, answer="ok")
    app.dependency_overrides[get_query_service] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_chat_returns_429_when_limited(client):
    limiter = RateLimiter(limit=2, window=60)
    with patch.object(rate_limit, "_chat_limiter", limiter):
        assert client.post("/api/query/chat", json={"query": "x"}).status_code == 200
        assert client.post("/api/query/chat", json={"query": "x"}).status_code == 200
        r = client.post("/api/query/chat", json={"query": "x"})
    assert r.status_code == 429
    assert "Retry-After" in r.headers


def test_errors_do_not_leak_internal_details():
    svc = QueryService(Mock(), nx.DiGraph())
    svc.guardrail = Mock()
    svc.guardrail.validate_query.return_value = Mock(is_valid=True, reason="ok")
    svc._classify_intent = Mock(side_effect=RuntimeError("secret-db-password at host x"))
    resp = svc.process_query("how many orders")
    assert resp.success is False
    assert "secret" not in (resp.message or "") + (resp.answer or "")
