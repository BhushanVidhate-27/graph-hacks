"""
app/main.py — the frozen HTTP contract: FastAPI + SSE.

Owner: Soham.  Rule 12: every line is explainable, so there is no extra
abstraction between the route and the stream.

The contract (soham.md §3, frozen — do NOT rename a field after 15:00 Day 1,
because Ujwal's renderer is already building against these exact keys):

    POST /ask  { question }  ->  SSE stream of { answer, trail[], stale[] }

        trail[] = [ { type, name, detail, date, via_edge }, ... ]
        stale[] = [ { type, name, reason, last_verified_at }, ... ]

    GET /health

Design rule for this file (soham.md §4, "S2"): EVERY mock lives behind ONE
function with ONE clearly marked fake branch.  When the real graph lands we
delete the fake branch and change nothing else.  Scattering mock literals
through the handlers is how you end up grepping at 22:00.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

load_dotenv()

# --------------------------------------------------------------------------- #
# The one switch that flips mocks -> real graph
# --------------------------------------------------------------------------- #
#
# USE_MOCK=1 (default)  -> read Ujwal's single fixture, mock/trail.json
# USE_MOCK=0            -> call app/agent.py, which calls app/graph.py
#
# Default stays 1 on purpose: the graph is Bhushan's and may be late, and the
# frontend must never be blocked on it (that is the whole point of S2).
USE_MOCK = os.getenv("USE_MOCK", "1") == "1"

# mock/ belongs to Ujwal.  We READ it, we never EDIT it (soham.md §4).  It is
# the executable spec: if this file and the contract disagree, this file wins at
# runtime and the bug lands on Ujwal's Saturday, so we follow the fixture's shape.
# MOCK_TRAIL_PATH lets a test point at a copy without touching the real fixture.
MOCK_PATH = Path(
    os.getenv(
        "MOCK_TRAIL_PATH",
        str(Path(__file__).resolve().parent.parent / "mock" / "trail.json"),
    )
)


# --------------------------------------------------------------------------- #
# Pydantic models — "take real data through pydantic models so the shapes
# cannot drift" (soham.md §15).  If a field is misspelled here, FastAPI errors
# loudly instead of silently shipping a broken key to the renderer.
# --------------------------------------------------------------------------- #


class Ask(BaseModel):
    """Request body for POST /ask."""

    question: str = Field(min_length=1, max_length=500)


class TrailItem(BaseModel):
    """One chip in the provenance trail.

    `via_edge` is the edge label BETWEEN chips.  It is what makes the trail a
    proof chain instead of decoration — never drop it (soham.md §3).
    """

    type: str
    name: str
    detail: str
    date: str
    via_edge: str


class StaleItem(BaseModel):
    """One ⚠ badge — a fact we can no longer trust."""

    type: str
    name: str
    reason: str
    last_verified_at: str


class Answer(BaseModel):
    """The complete payload.  Every SSE event carries ALL THREE keys, even when
    one of them is still empty, so the frontend never has to guess whether a
    missing key means 'not yet' or 'nothing found'."""

    answer: str
    trail: list[TrailItem]
    stale: list[StaleItem]


# --------------------------------------------------------------------------- #
# The single mock seam
# --------------------------------------------------------------------------- #


def _read_mock(question: str) -> dict[str, Any]:
    """Load Ujwal's fixture and build the frozen payload for `question`.

    Ujwal's fixture is the executable spec (soham.md §3), so we follow ITS shape
    rather than the one this file first guessed.  Cases live under "cases", and
    each case carries its own `question` to match on.  `answer` is an array of
    short strings so the frontend can test a token streamer; the fixture's own
    shape_notes say the backend joins it, so we join.

    Anything unexpected raises with the path in the message, because a silent
    fallback here would look like an empty graph and that is a different bug.
    """
    if not MOCK_PATH.exists():
        raise FileNotFoundError(
            f"{MOCK_PATH} is missing. That file is Ujwal's single shared fixture "
            "(mock/trail.json) and both the frontend and this fake branch read it. "
            "Ping Ujwal — do not create a second mock set."
        )

    data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
    return _to_payload(_select_case(data, question))


def _select_case(data: Any, question: str) -> dict[str, Any]:
    """Pick the fixture case for `question` (by question text, then by case id).

    We code to the fixture's actual shape.  If that shape changes we fail loudly
    instead of silently guessing a new one — a silent mismatch here would surface
    as an empty graph, which is a different bug with a different owner.
    """
    cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(cases, dict):
        raise KeyError(
            f"{MOCK_PATH} has no 'cases' object. Ujwal's fixture changed shape — "
            "check with him rather than guessing the new one here."
        )

    for case in cases.values():  # match on the question text the case carries
        if isinstance(case, dict) and case.get("question") == question:
            return case
    if isinstance(cases.get(question), dict):  # ... or on a case id like "demo"
        return cases[question]

    # No case for this question. Say so plainly rather than borrowing another
    # case's answer — a confident off-topic answer is the bug we are avoiding.
    return {
        "answer": (
            "This is the mock API and mock/trail.json has no case for that "
            "question. Add one there (Ujwal owns the fixture) or ask one of the "
            "demo questions."
        ),
        "trail": [],
        "stale": [],
    }


def _to_payload(case: dict[str, Any]) -> dict[str, Any]:
    """Reshape one fixture case into the frozen payload.

    One real difference from the wire contract: the fixture stores `answer` as an
    array of short strings, and the contract says a string. The fixture's own
    shape_notes say the backend joins it, so we join.
    """
    answer = case.get("answer", "")
    if isinstance(answer, list):
        answer = "".join(str(part) for part in answer)
    return {
        "answer": answer,
        "trail": case.get("trail") or [],
        "stale": case.get("stale") or [],
    }


def answer_question(question: str) -> dict[str, Any]:
    """THE seam.  Mocks in, real graph out — one branch, one line to delete.

    soham.md §4 sketches this as `get_trail(question)`; it returns the whole
    frozen payload because that keeps exactly ONE fake branch in the file
    instead of one per field.
    """
    if USE_MOCK:
        # ------------------------------------------------------------------ #
        # FAKE BRANCH — delete this whole `if` at Gate 2.                     #
        # ------------------------------------------------------------------ #
        raw = _read_mock(question)
        payload = Answer.model_validate(raw)
        return payload.model_dump()
        # ------------------------------------------------------------------ #
        # END FAKE BRANCH                                                     #
        # ------------------------------------------------------------------ #

    # REAL BRANCH.  app/agent.py picks the tools and runs the traversals;
    # app/graph.py holds the only Cypher.  This file builds no query strings.
    from app.agent import run_agent

    return Answer.model_validate(run_agent(question)).model_dump()


# --------------------------------------------------------------------------- #
# SSE
# --------------------------------------------------------------------------- #
#
# THE ONE GOTCHA (soham.md §8):
#   Native EventSource is GET-only.  Our contract is POST /ask, so EventSource
#   does NOT work.  The client MUST use fetch() + response.body.getReader():
#
#       const res = await fetch("/ask", {
#         method: "POST",
#         headers: { "Content-Type": "application/json" },
#         body: JSON.stringify({ question }),
#       });
#       const reader = res.body.getReader();
#       // ... decode each chunk, split on "\n\n", JSON.parse the "data: " line.
#
#   If Ujwal builds against EventSource it works right up until Gate 2 and then
#   fails with no useful error.


def _sse(payload: dict[str, Any]) -> str:
    """Format one Server-Sent Event frame.

    The SSE wire format is `data: <line>\\n\\n`.  We JSON-encode the payload so
    newlines inside an answer can never break the framing.
    """
    return f"data: {json.dumps(payload, default=str)}\n\n"


def stream_answer(question: str) -> Iterator[str]:
    """Yield the trail first, then the answer.

    Order matters for the demo: the chips (trail + stale) render as soon as the
    first frame lands, so the UI shows its evidence before the prose arrives.
    Every frame keeps all three canonical keys.
    """
    result = answer_question(question)

    # Frame 1 — the evidence.  Answer is empty on purpose: nothing is claimed yet.
    yield _sse({"answer": "", "trail": result["trail"], "stale": result["stale"]})

    # Frame 2 — the prose, tied to the frame above.
    yield _sse(result)

    # Frame 3 — an explicit terminator.  The client should not have to infer
    # "done" from a closed socket, which is ambiguous with a dropped connection.
    yield "data: [DONE]\n\n"


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #

app = FastAPI(title="Helio company brain", version="0.1.0")

# CORS: the frontend dev server runs on 5173.  Port 3000 is the FalkorDB
# Browser, not the Node dev server — allowing it would be a copy-paste bug.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness + which branch we are on.  Bhushan's deploy hits this."""
    return {"status": "ok", "mock": USE_MOCK}


@app.post("/ask")
def ask(req: Ask) -> StreamingResponse:
    """Frozen contract: POST /ask -> SSE stream of {answer, trail[], stale[]}."""
    return StreamingResponse(
        stream_answer(req.question),
        media_type="text/event-stream",
        headers={
            # Proxies buffer a naive stream into one lump: it works on
            # localhost and dies behind a real proxy.  Without the second
            # header the demo works locally and breaks in production, and it
            # reads as a bug in this code (soham.md §8).
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":  # python -m app.main
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
