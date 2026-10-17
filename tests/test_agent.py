"""Tests for app/agent.py — the tool surface and the stale[] wiring.

These run with NO FalkorDB and NO ANTHROPIC_API_KEY: app/graph.py is replaced by
a stub module and the Anthropic client by a scripted fake.  That keeps the two
things this file owns -- which tools the model can see, and how a tool's rows
become the frozen payload -- testable on a laptop that has neither.

Owner: Soham.
"""

from __future__ import annotations

import types

import pytest

from app import agent


# --------------------------------------------------------------------------- #
# A stub for app/graph.py: a TOOLS dict of name -> function, exactly the shape
# agent.call_tool reads.
# --------------------------------------------------------------------------- #

def _stub_graph() -> types.SimpleNamespace:
    def expertise(service: str) -> dict:
        return {
            "rows": [
                {"person": "Priya Sharma", "commits": 14, "latest": "2026-04-15",
                 "stale": True, "projects": ["p"], "detail": "14 commits [STALE]"},
                {"person": "Ravi Menon", "commits": 5, "latest": "2026-09-01",
                 "stale": False, "projects": ["p"], "detail": "5 commits"},
            ],
            "trail": [{"type": "Person", "name": "Priya Sharma", "detail": "d",
                       "date": "2026-04-15", "via_edge": "CONTRIBUTED_TO"}],
        }

    def owner_of(service: str) -> dict:
        return {"rows": [], "trail": []}

    return types.SimpleNamespace(TOOLS={"expertise": expertise, "owner_of": owner_of})


# --------------------------------------------------------------------------- #
# The tool surface must not drift from what graph.py actually implements.
# --------------------------------------------------------------------------- #

def test_tool_surface_matches_the_traversals_graph_publishes():
    """The described tools and graph.TOOLS must be the SAME set.

    This is the bug that made facts 16-20 unanswerable: 11 traversals existed in
    graph.TOOLS but only 4 had a description, and a traversal with no description
    is a tool the model can never call.  The reverse also matters -- a described
    tool with no function raises at call time -- so this checks both directions.
    """
    graph = pytest.importorskip("app.graph")
    described = {tool["name"] for tool in agent.TOOLS}
    assert set(graph.TOOLS) == described, (
        "app/agent.py and app/graph.py have drifted. "
        f"Undescribed traversals: {sorted(set(graph.TOOLS) - described)}; "
        f"described but not implemented: {sorted(described - set(graph.TOOLS))}"
    )


def test_every_described_tool_has_a_schema_shape():
    for tool in agent.TOOLS:
        assert tool["name"]
        assert tool["description"].strip()
        assert tool["input_schema"]["type"] == "object"


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #

def test_call_tool_dispatches_through_graph_tools(monkeypatch):
    monkeypatch.setattr(agent, "_load_graph_module", _stub_graph)
    result = agent.call_tool("expertise", {"service": "payments-gateway"})
    assert [r["person"] for r in result["rows"]] == ["Priya Sharma", "Ravi Menon"]
    assert result["trail"][0]["via_edge"] == "CONTRIBUTED_TO"


def test_call_tool_unknown_name_raises_with_the_published_list(monkeypatch):
    monkeypatch.setattr(agent, "_load_graph_module", _stub_graph)
    with pytest.raises(ValueError, match="expertise"):
        agent.call_tool("nope", {})


# --------------------------------------------------------------------------- #
# stale[] extraction — the real-mode bug: _trail() strips the markers, so this
# MUST read rows.
# --------------------------------------------------------------------------- #

def test_staleness_rows_pass_through_in_the_frozen_shape():
    rows = [
        {"type": "Document", "name": "payments-provider-eval-v3.md",
         "last_verified_at": "2026-03-18", "reason": "last verified 2026-03-18"},
    ]
    out = agent.extract_stale("staleness", rows)
    assert len(out) == 1
    assert set(out[0]) == {"type", "name", "reason", "last_verified_at"}
    assert out[0]["name"] == "payments-provider-eval-v3.md"


def test_staleness_drops_edge_rows_that_are_outside_the_frozen_vocabulary():
    """Real-mode regression, from the live graph.

    staleness() returns 163 rows: 162 Document plus exactly one edge-level row
    {"type": "edge", "name": "CONTRIBUTED_TO"}.  mock/trail.json freezes
    stale[].type to {Person, Decision, Document, Message, Service, Project, Team},
    so "edge" is an undefined badge type -- the renderer styles by this value and
    has no rule for it.  graph.py's _trail() keeps edge rows out of the trail too,
    so such a row cannot badge a chip anyway.  The mock path never calls
    staleness(), which is why this only ever showed up against real data.
    """
    rows = [
        {"type": "edge", "name": "CONTRIBUTED_TO",
         "last_verified_at": "2026-04-15", "reason": "not re-verified since 2026-04-15"},
        {"type": "Document", "name": "payments-provider-eval-v3.md",
         "last_verified_at": "2026-03-18", "reason": "last verified 2026-03-18"},
    ]
    out = agent.extract_stale("staleness", rows)
    assert [s["name"] for s in out] == ["payments-provider-eval-v3.md"]


def test_every_emitted_stale_type_is_in_the_frozen_vocabulary():
    """No tool may put an unusable badge type on the wire."""
    stale = []
    stale += agent.extract_stale("staleness", [
        {"type": "edge", "name": "CONTRIBUTED_TO", "reason": "r", "last_verified_at": "d"},
        {"type": "Document", "name": "doc.md", "reason": "r", "last_verified_at": "d"},
    ])
    stale += agent.extract_stale("expertise", [
        {"person": "Priya Sharma", "latest": "2026-04-15", "stale": True, "detail": "d"},
    ])
    stale += agent.extract_stale("provenance", [
        {"id": "D-14", "status": "superseded", "date": "2026-03-18", "detail": "d"},
    ])
    assert stale, "the test must actually produce some stale items"
    assert {s["type"] for s in stale} <= agent.STALE_TYPES


def test_expertise_only_marks_the_stale_person():
    rows = [
        {"person": "Priya Sharma", "latest": "2026-04-15", "stale": True,
         "detail": "14 commits [STALE]"},
        {"person": "Ravi Menon", "latest": "2026-09-01", "stale": False,
         "detail": "5 commits"},
    ]
    out = agent.extract_stale("expertise", rows)
    assert out == [{
        "type": "Person", "name": "Priya Sharma",
        "reason": "14 commits [STALE]", "last_verified_at": "2026-04-15",
    }]


def test_provenance_marks_only_the_superseded_decision_not_the_current_one():
    """D-19 is active AND supersedes D-14; app/graph.py names that key
    `superseded_by`, which is inverted.  Only `status` may decide staleness, or
    the current decision gets badged as out of date."""
    rows = [
        {"id": "D-19", "status": "active", "superseded_by": "D-14",
         "date": "2026-05-06", "detail": "Dual provider [SUPERSEDES D-14]"},
        {"id": "D-14", "status": "superseded", "superseded_by": None,
         "date": "2026-03-18", "detail": "Single provider [SUPERSEDED]"},
    ]
    out = agent.extract_stale("provenance", rows)
    assert [s["name"] for s in out] == ["D-14"]


def test_tools_with_no_stale_semantics_return_nothing():
    assert agent.extract_stale("blast_radius", [{"service": "x"}]) == []


# --------------------------------------------------------------------------- #
# The whole loop, scripted, no network.
# --------------------------------------------------------------------------- #

class _Block:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Resp:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class _FakeClient:
    """Replays a fixed list of responses, one per messages.create call."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.messages = types.SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        return self._responses.pop(0)


def test_run_agent_returns_a_populated_trail_and_stale(monkeypatch):
    """Regression: stale[] used to be empty in real mode because it read trail[]."""
    monkeypatch.setattr(agent, "_load_graph_module", _stub_graph)
    responses = [
        _Resp([_Block(type="tool_use", id="t1", name="expertise",
                      input={"service": "payments-gateway"})], "tool_use"),
        _Resp([_Block(type="text", text="Ravi Menon now; Priya left.")], "end_turn"),
    ]
    monkeypatch.setattr(agent, "_client", lambda: _FakeClient(responses))

    result = agent.run_agent("Who should I ask about payments?")

    assert result["answer"] == "Ravi Menon now; Priya left."
    assert result["trail"][0]["via_edge"] == "CONTRIBUTED_TO"
    assert result["stale"], "real mode must populate stale[] from rows, not trail[]"
    assert result["stale"][0]["name"] == "Priya Sharma"
