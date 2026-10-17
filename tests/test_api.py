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


# --------------------------------------------------------------------------- #
# A backend failure must still be a well-formed stream, not a dropped socket.
# --------------------------------------------------------------------------- #

def test_backend_failure_yields_an_error_frame_then_done(client, monkeypatch):
    def boom(_question):
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Put it in .env")

    monkeypatch.setattr(main, "answer_question", boom)

    # Must NOT raise: the status is already committed to 200, so an escaping
    # exception is what produces the stuck spinner on the client.
    res = client.post("/ask", json={"question": "who owns payments-gateway?"})
    assert res.status_code == 200

    frames = _frames(res.text)
    assert frames[-1] == "[DONE]", "the client needs the sentinel even on failure"

    payload = json.loads(frames[-2])
    assert set(payload) == {"answer", "trail", "stale"}
    assert payload["trail"] == [] and payload["stale"] == []
    assert "ANTHROPIC_API_KEY" in payload["answer"]
    assert "could not answer" in payload["answer"]


def test_unexpected_backend_failure_still_streams_a_frame(client, monkeypatch):
    monkeypatch.setattr(
        main, "answer_question",
        lambda _q: (_ for _ in ()).throw(ValueError("graph returned garbage")),
    )

    res = client.post("/ask", json={"question": "anything"})
    frames = _frames(res.text)
    assert frames[-1] == "[DONE]"
    payload = json.loads(frames[-2])
    assert "ValueError" in payload["answer"]
    assert payload["trail"] == [] and payload["stale"] == []
