"""Unit tests for FastAPI Track B runtime."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import api.app as app_module


class _FakeCitation:
    def __init__(self, text: str, source: str = "") -> None:
        self.text = text
        self.source = source


class _FakeResponse:
    def __init__(self, *, content: str, citations: list[_FakeCitation], run_id: str) -> None:
        self.content = content
        self.citations = citations
        self.run_id = run_id


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app_module.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_endpoint_returns_agent_payload(monkeypatch) -> None:
    fake_agent = MagicMock()
    fake_agent.ask.return_value = _FakeResponse(
        content="Azure OpenAI can be deployed via portal.",
        citations=[
            _FakeCitation("[1] doc1", "azure-docs"),
            _FakeCitation("[2] doc2", "azure-docs"),
            _FakeCitation("[3] doc3", "arch-guide"),
        ],
        run_id="req-123",
    )

    app_module._get_agent.cache_clear()
    monkeypatch.setattr(app_module, "_get_agent", lambda: fake_agent)

    client = TestClient(app_module.app)
    response = client.post("/ask", json={"question": "How do I deploy Azure OpenAI?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("Azure OpenAI")
    assert body["run_id"] == "req-123"
    assert body["citations"] == ["azure-docs", "arch-guide"]
    fake_agent.ask.assert_called_once()


def test_ask_endpoint_validates_question() -> None:
    client = TestClient(app_module.app)
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422


def test_ask_endpoint_returns_500_on_unhandled_error(monkeypatch) -> None:
    fake_agent = MagicMock()
    fake_agent.ask.side_effect = RuntimeError("boom")

    app_module._get_agent.cache_clear()
    monkeypatch.setattr(app_module, "_get_agent", lambda: fake_agent)

    client = TestClient(app_module.app)
    response = client.post("/ask", json={"question": "test"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
