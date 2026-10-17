"""Tests for app/main.py — the frozen /ask contract and CORS.

Runs against Ujwal's real fixture (mock/trail.json) through the mock branch, so
there is no FalkorDB and no API key involved.  tests/test_agent.py covers the
real branch's tool loop.

Owner: Soham.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture()
def client(monkeypatch):
    # Force the mock branch even if the developer's shell has USE_MOCK=0.
    monkeypatch.setattr(main, "USE_MOCK", True)
    return TestClient(main.app)


def _frames(text: str) -> list[str]:
    """Split an SSE body into its `data:` payloads."""
    return [
        line[len("data: "):]
        for line in text.splitlines()
        if line.startswith("data: ")
    ]


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["mock"] is True


def test_ask_streams_trail_then_answer_then_done(client):
    res = client.post("/ask", json={"question": "Who should I ask about the payments service?"})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")
    assert res.headers["cache-control"] == "no-cache"
    assert res.headers["x-accel-buffering"] == "no"

    frames = _frames(res.text)
    assert frames[-1] == "[DONE]"

    first = json.loads(frames[0])
    assert first["answer"] == ""
    assert set(first) == {"answer", "trail", "stale"}
    assert first["trail"] and first["stale"]

    last = json.loads(frames[-2])
    assert last["answer"]
    assert set(last) == {"answer", "trail", "stale"}


def test_ask_rejects_empty_question(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_unknown_question_does_not_borrow_another_case(client):
    res = client.post("/ask", json={"question": "what colour is the sky?"})
    last = json.loads(_frames(res.text)[-2])
    assert "no case" in last["answer"]
    assert last["trail"] == [] and last["stale"] == []


@pytest.mark.parametrize(
    "origin",
    ["http://localhost:5173", "http://127.0.0.1:5173"],
)
def test_cors_allows_both_vite_origins(client, origin):
    res = client.options(
        "/ask",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == origin
