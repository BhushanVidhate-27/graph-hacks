"""1000 data-driven test cases for the Helio company brain.

These are GENERATED from the loaded graph and the frozen contract, not
hand-written one by one.  The point is breadth with real assertions: every case
names the exact property it checks, so a failure tells you what broke.

Coverage (see CASES at the bottom; the group name is the first element):

  alias            loose human phrase -> real service node, and the
                   anti-fabrication rule: resolving must NEVER invent a node
  owner_of         all 20 services
  blast_radius     all 20 services (dedup, acyclicity, depth, edge label)
  expertise        all 20 services (volume + recency shape)
  sla_of           all 20 services
  provenance       all 40 projects (decision + evidence shape)
  current_team     all 100 people (current vs departed)
  on_call          all 5 teams
  decisions_about  every decision retrievable by a word from its own summary
  zero_dependents  each of the 10 known answers is really in the list
  staleness        edge + document staleness shape
  invariants       every tool: dict / rows / trail / count / JSON / trail keys /
                   every trail value is a string (the frozen contract)
  vocab            every tool: frozen via_edge + type vocabularies, never blank
  garbage          8 string tools against 10 hostile strings (incl. injection)
  fakeservice      20 unknown services x 4 tools: honest empty, no invention
  groundtruth      the 20 hand-written facts in GROUND_TRUTH.md (+ addendum)
  api              /health, /ask SSE, validation, CORS, failure frames
  agent            the model-facing tool surface in app/agent.py

Requires a running FalkorDB (app/graph.py) with the Helio graph loaded, and the
frozen fixture at mock/trail.json.  No ANTHROPIC_API_KEY is used: the API cases
run through the mock branch and the /health + validation paths.

Owner: Soham.
"""

from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from app import agent, graph, main

# --------------------------------------------------------------------------- #
# Frozen vocabularies (mock/trail.json -> via_edge_vocabulary, shape_notes)
# --------------------------------------------------------------------------- #

VIA_EDGES = frozenset(
    {
        "CONTRIBUTED_TO",
        "OWNED_BY",
        "EVIDENCED_BY",
        "SUPERSEDES",
        "MENTIONS",
        "HAS_DEPENDENT",
        "DEPENDS_ON",
        "MEMBER_OF",
        "ON_CALL",
    }
)
TYPES = frozenset(
    {"Person", "Decision", "Document", "Message", "Service", "Project", "Team"}
)
TRAIL_KEYS = frozenset({"type", "name", "detail", "date", "via_edge"})

# Fact 18 — the real, hand-written list of services with zero inbound dependents.
ZERO_DEPENDENT_SERVICES = frozenset(
    {
        "admin-bff",
        "config-service",
        "mobile-bff",
        "notifications",
        "recommendation",
        "search-index",
        "session-store",
        "settlement-batch",
        "web-frontend",
        "webhook-relay",
    }
)

# Fact 5 — what breaks if payments-gateway dies.
PAYMENTS_BLAST = {
    "checkout-api": 1,
    "config-service": 1,
    "dispute-service": 1,
    "mobile-bff": 1,
    "notifications": 1,
    "webhook-relay": 1,
    "fraud-scoring": 2,
    "recommendation": 3,
}


# --------------------------------------------------------------------------- #
# Graph inventory, read once at collection time.
# --------------------------------------------------------------------------- #

def _q(cypher: str) -> list[tuple]:
    return [tuple(r) for r in graph._graph().query(cypher).result_set]


SERVICES = sorted(r[0] for r in _q("MATCH (s:Service) RETURN s.name"))
TEAMS = sorted(r[0] for r in _q("MATCH (t:Team) RETURN t.name"))
PEOPLE = sorted(r[0] for r in _q("MATCH (p:Person) RETURN p.name"))
PROJECTS = sorted(r[0] for r in _q("MATCH (p:Project) RETURN p.name"))
DECISION_ROWS = sorted(
    (r[0], r[1] or "") for r in _q("MATCH (d:Decision) RETURN d.id, d.summary")
)
DECISIONS = [d for d, _ in DECISION_ROWS]

_MIG = _q("MATCH (d:Decision {id: 'D-19'})-[:ABOUT]->(p:Project) RETURN p.name")
MIGRATION_PROJECT = _MIG[0][0] if _MIG else PROJECTS[0]

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# --------------------------------------------------------------------------- #
# Group: alias — 21 input forms per service, resolving must never fabricate.
# --------------------------------------------------------------------------- #

def _alias_forms(s: str) -> list[tuple[str, str | None]]:
    """(input, expected) pairs.  expected=None means 'only assert no invention'."""
    spaced = s.replace("-", " ")
    return [
        (s, s),
        (s.upper(), s),
        (f"the {s}", s),
        (f"{s} service", s),
        (spaced, s),
        (s.replace("-", "_"), s),
        (f"{spaced} service", s),
        (f"{spaced} svc", s),
        ("The " + spaced.title() + " Service", s),
        (f"{s} svc", s),
        (f"{s}-service", s),
        (f"our {s}", s),
        ("the " + spaced.upper() + " SERVICE", s),
        (s.upper() + " SERVICE", s),
        (f"  {s}  ", s),
        (s.replace("-", ""), None),
        (s.split("-")[0], None),
        (spaced.title(), s),
        (s.upper().replace("-", " "), s),
        (s.replace("-", "_") + " service", s),
        (f"{spaced} thing", s),
    ]


def _alias_pool() -> list[tuple[str, str, str | None]]:
    per = [_alias_forms(s) for s in SERVICES]
    n_forms = len(per[0])
    pool: list[tuple[str, str, str | None]] = []
    for j in range(n_forms):                 # form-major, so every form is used
        for i, s in enumerate(SERVICES):
            inp, exp = per[i][j]
            pool.append((s, inp, exp))
    return pool


def _check_alias(payload, _mp) -> None:
    s, inp, exp = payload
    resolved, exact = graph.resolve_service(inp)
    if exp is not None:
        assert resolved == exp, f"{inp!r} resolved to {resolved!r}, expected {exp!r}"
        # `exact` is True only when the caller literally passed the node's name.
        assert exact == (inp == exp), f"exact flag wrong for {inp!r}"
    else:
        assert resolved in SERVICES or resolved == inp, (
            f"{inp!r} invented the node {resolved!r}"
        )


# --------------------------------------------------------------------------- #
# Group: per-service tool sweeps
# --------------------------------------------------------------------------- #

def _check_owner_of(service, _mp) -> None:
    r = graph.owner_of(service)
    assert r["service"] == service
    assert r["count"] == len(r["rows"])
    for row in r["rows"]:
        assert set(row) == {"team"}
        assert row["team"] in TEAMS
    for tr in r["trail"]:
        assert set(tr) == TRAIL_KEYS
        assert tr["type"] == "Team"
        assert tr["via_edge"] == "OWNED_BY"


def _check_blast_radius(service, _mp) -> None:
    r = graph.blast_radius(service)
    assert r["service"] == service
    assert r["count"] == len(r["rows"])
    deps = [row["service"] for row in r["rows"]]
    assert len(deps) == len(set(deps)), "blast radius returned a duplicate"
    assert service not in deps, "a service is in its own blast radius"
    for row in r["rows"]:
        assert row["depth"] >= 1
        assert row["service"] in SERVICES
    for tr in r["trail"]:
        assert set(tr) == TRAIL_KEYS
        assert tr["type"] == "Service"
        assert tr["via_edge"] == "HAS_DEPENDENT"


def _check_expertise(service, _mp) -> None:
    r = graph.expertise(service)
    assert r["service"] == service
    assert r["count"] == len(r["rows"])
    for row in r["rows"]:
        assert row["detail"]
        if row["person"] == "current owner (per decision)":
            assert row["commits"] is None
            assert row["stale"] is False
        else:
            assert isinstance(row["commits"], int) and row["commits"] >= 1
            assert _DATE.match(row["latest"]), row["latest"]
            assert isinstance(row["stale"], bool)
            assert isinstance(row["projects"], list)
    for tr in r["trail"]:
        assert set(tr) == TRAIL_KEYS
        assert tr["type"] in TYPES
        assert tr["via_edge"] in {"CONTRIBUTED_TO", "EVIDENCED_BY"}


def _check_sla_of(service, _mp) -> None:
    r = graph.sla_of(service)
    assert r["service"] == service
    assert r["count"] == len(r["rows"])
    for row in r["rows"]:
        assert set(row) == {"sla"}
        assert isinstance(row["sla"], str) and row["sla"].strip()
    for tr in r["trail"]:
        assert set(tr) == TRAIL_KEYS
        assert tr["via_edge"] == "OWNED_BY"


def _check_provenance(project, _mp) -> None:
    r = graph.provenance(project)
    assert r["project"] == project
    assert r["count"] == len(r["rows"])
    for row in r["rows"]:
        assert set(row) == {
            "id", "summary", "date", "status", "evidence",
            "superseded_by", "supersedes_summary", "detail",
        }
        assert re.match(r"^D-\d+$", row["id"]), row["id"]
        assert isinstance(row["evidence"], list)
    for tr in r["trail"]:
        assert set(tr) == TRAIL_KEYS
        assert tr["type"] in TYPES
        assert tr["via_edge"] in VIA_EDGES


def _check_current_team(person, _mp) -> None:
    r = graph.current_team(person)
    assert r["person"] == person
    assert r["count"] == len(r["rows"])
    for row in r["rows"]:
        assert set(row) == {"team", "valid_to"}
        assert row["team"] in TEAMS
        assert not row["valid_to"], "current membership carries a valid_to"
    for row in r["departed"]:
        assert set(row) == {"team", "valid_to"}
        assert row["team"] in TEAMS
        assert row["valid_to"], "departed membership has no valid_to"
    for tr in r["trail"]:
        assert set(tr) == TRAIL_KEYS
        assert tr["via_edge"] == "MEMBER_OF"


def _check_on_call(team, _mp) -> None:
    r = graph.on_call(team)
    assert r["team"] == team
    assert r["count"] == len(r["rows"])
    assert r["on_call"] == [x["person"] for x in r["rows"] if x["on_call"]]
    assert r["rotation_not_on_call"] == [
        x["person"] for x in r["rows"] if not x["on_call"]
    ]
    for row in r["rows"]:
        assert isinstance(row["on_call"], bool)
        if row["on_call"]:
            assert isinstance(row["week_start"], str) and _DATE.match(row["week_start"]), (
                f"{row['person']} is on call for {team} but week_start is "
                f"{row['week_start']!r}. The ON_CALL edge carries week_start/"
                "on_call_week; app/graph.py reads m.on_call_week (a node property "
                "that does not exist) instead of binding the edge."
            )
        else:
            assert row["week_start"] is None
    for tr in r["trail"]:
        assert set(tr) == TRAIL_KEYS
        assert tr["via_edge"] == "ON_CALL"


def _check_decisions_about(payload, _mp) -> None:
    keyword, required_id, expected_count = payload
    r = graph.decisions_about(keyword)
    assert r["keyword"] == keyword
    assert r["trail"] == []
    assert r["count"] == len(r["rows"])
    ids = [row["id"] for row in r["rows"]]
    for row in r["rows"]:
        assert set(row) == {"id", "summary", "date"}
        assert row["id"] in DECISIONS
    if required_id is not None:
        assert required_id in ids, f"{required_id} not found by {keyword!r}"
    if expected_count is not None:
        assert r["count"] == expected_count


def _check_zero_dependents(service, _mp) -> None:
    r = graph.zero_dependents()
    assert service in [row["name"] for row in r["rows"]]


def _check_staleness(_payload, _mp) -> None:
    r = graph.staleness()
    assert _DATE.match(r["cutoff"]), r["cutoff"]
    assert r["count"] == len(r["rows"])
    assert r["count"] >= 1
    for row in r["rows"]:
        assert {"type", "name", "last_verified_at", "reason"} <= set(row)
        assert _DATE.match(row["last_verified_at"]), row["last_verified_at"]
    for tr in r["trail"]:
        assert set(tr) == TRAIL_KEYS
        assert tr["type"] == "Document"
        assert tr["via_edge"] == "EVIDENCED_BY"


# --------------------------------------------------------------------------- #
# Group: invariants + vocab — applied to every tool
# --------------------------------------------------------------------------- #

_TOOL_CALLS = {
    "blast_radius": lambda: graph.blast_radius("payments-gateway"),
    "expertise": lambda: graph.expertise("payments-gateway"),
    "provenance": lambda: graph.provenance(MIGRATION_PROJECT),
    "staleness": lambda: graph.staleness(),
    "owner_of": lambda: graph.owner_of("payments-gateway"),
    "decisions_about": lambda: graph.decisions_about("provider"),
    "zero_dependents": lambda: graph.zero_dependents(),
    "sla_of": lambda: graph.sla_of("payments-gateway"),
    "current_team": lambda: graph.current_team("Ravi Menon"),
    "on_call": lambda: graph.on_call("Ledger"),
}


def _check_invariant(payload, _mp) -> None:
    tool, idx = payload
    res = _TOOL_CALLS[tool]()
    if idx == 0:
        assert isinstance(res, dict)
    elif idx == 1:
        assert isinstance(res.get("rows"), list)
    elif idx == 2:
        assert isinstance(res.get("trail"), list)
    elif idx == 3:
        assert res["count"] == len(res["rows"])
    elif idx == 4:
        json.dumps(res, default=str)          # must be serialisable to the wire
    elif idx == 5:
        for tr in res["trail"]:
            assert set(tr) == TRAIL_KEYS
    elif idx == 6:
        # The frozen contract: every trail value is a string (date may be "").
        # A None here fails Answer.model_validate on the real /ask path.
        for tr in res["trail"]:
            for key in TRAIL_KEYS:
                assert isinstance(tr[key], str), (
                    f"{tool}: trail row has {key}={tr[key]!r} "
                    f"({type(tr[key]).__name__}), expected str"
                )
    else:  # pragma: no cover
        raise AssertionError(f"unknown invariant {idx}")


def _check_vocab(payload, _mp) -> None:
    tool, idx = payload
    trail = _TOOL_CALLS[tool]()["trail"]
    if idx == 0:
        assert all(tr["via_edge"] in VIA_EDGES for tr in trail)
    elif idx == 1:
        assert all(tr["type"] in TYPES for tr in trail)
    elif idx == 2:
        assert all(tr["via_edge"] != "" for tr in trail), "a chip lost its edge"
    else:  # pragma: no cover
        raise AssertionError(f"unknown vocab check {idx}")


# --------------------------------------------------------------------------- #
# Group: garbage + fake services — honesty under hostile / unknown input
# --------------------------------------------------------------------------- #

_STRING_TOOLS = [
    "blast_radius", "expertise", "owner_of", "sla_of",
    "provenance", "current_team", "on_call", "decisions_about",
]

_GARBAGE = [
    "",
    "   ",
    "\t\n",
    "'; MATCH (n) DETACH DELETE n //",
    "x' OR '1'='1",
    "%",
    "🐍🚀",
    "a" * 300,
    "NULL",
    "payments-gateway' RETURN 1 //",
]

_ECHO_KEY = {
    "blast_radius": "service",
    "expertise": "service",
    "owner_of": "service",
    "sla_of": "service",
    "provenance": "project",
    "current_team": "person",
    "on_call": "team",
    "decisions_about": "keyword",
}


def _check_garbage(payload, _mp) -> None:
    tool, junk = payload
    res = getattr(graph, tool)(junk)          # must not raise (params are bound)
    assert isinstance(res, dict)
    assert res["count"] == len(res["rows"])
    echoed = res[_ECHO_KEY[tool]]
    if tool in {"blast_radius", "expertise", "owner_of", "sla_of"}:
        assert echoed in SERVICES or echoed == junk, f"invented service {echoed!r}"
    else:
        assert echoed == junk


def _check_fake_service(payload, _mp) -> None:
    tool, name = payload
    res = getattr(graph, tool)(name)
    assert res["service"] == name
    assert res["count"] == 0, f"{name} unexpectedly matched rows"
    assert res["rows"] == []
    assert res["trail"] == []


# --------------------------------------------------------------------------- #
# Group: GROUND_TRUTH.md — the hand-written facts
# --------------------------------------------------------------------------- #

def _prov_rows(project: str) -> dict[str, dict]:
    return {row["id"]: row for row in graph.provenance(project)["rows"]}


def _gt_owner_payments(_p, _mp):
    r = graph.owner_of("payments-gateway")
    assert [row["team"] for row in r["rows"]] == ["Platform"]


def _gt_owner_ledger(_p, _mp):
    r = graph.owner_of("ledger-core")
    assert "Ledger" in [row["team"] for row in r["rows"]]


def _gt_owner_fraud(_p, _mp):
    r = graph.owner_of("fraud-scoring")
    assert "Risk" in [row["team"] for row in r["rows"]]


def _gt_config_unowned(_p, _mp):
    r = graph.owner_of("config-service")
    assert r["count"] == 0
    assert r["rows"] == []


def _gt_blast_count(_p, _mp):
    assert graph.blast_radius("payments-gateway")["count"] == 8


def _gt_blast_names(_p, _mp):
    got = {row["service"] for row in graph.blast_radius("payments-gateway")["rows"]}
    assert got == set(PAYMENTS_BLAST)


def _gt_blast_depths(_p, _mp):
    got = {row["service"]: row["depth"]
           for row in graph.blast_radius("payments-gateway")["rows"]}
    assert got == PAYMENTS_BLAST


def _gt_blast_cross_team(_p, _mp):
    rows = graph.blast_radius("payments-gateway")["rows"]
    assert sum(1 for row in rows if row["cross_team"]) == 6


def _gt_blast_no_upstream(_p, _mp):
    deps = {row["service"] for row in graph.blast_radius("payments-gateway")["rows"]}
    assert "ledger-core" not in deps


def _gt_blast_no_settlement(_p, _mp):
    deps = {row["service"] for row in graph.blast_radius("payments-gateway")["rows"]}
    assert "settlement-batch" not in deps


def _gt_priya_top_volume(_p, _mp):
    rows = [r for r in graph.expertise("payments-gateway")["rows"]
            if r["commits"] is not None]
    top = max(rows, key=lambda r: r["commits"])
    assert top["person"] == "Priya Sharma"
    assert max(r["commits"] for r in rows) == 14


def _gt_priya_stale(_p, _mp):
    row = next(r for r in graph.expertise("payments-gateway")["rows"]
               if r["person"] == "Priya Sharma")
    assert row["commits"] == 14
    assert row["latest"] == "2026-04-15"
    assert row["stale"] is True


def _gt_oncall_diego(_p, _mp):
    assert graph.on_call("Ledger")["on_call"] == ["Diego Alvarez"]


def _gt_oncall_ravi_not(_p, _mp):
    assert "Ravi Menon" in graph.on_call("Ledger")["rotation_not_on_call"]


def _gt_prov_has_both(_p, _mp):
    rows = _prov_rows(MIGRATION_PROJECT)
    assert "D-14" in rows and "D-19" in rows


def _gt_d14_superseded(_p, _mp):
    assert _prov_rows(MIGRATION_PROJECT)["D-14"]["status"] == "superseded"


def _gt_d19_supersedes(_p, _mp):
    assert _prov_rows(MIGRATION_PROJECT)["D-19"]["superseded_by"] == "D-14"


def _gt_pricing_zero(_p, _mp):
    r = graph.decisions_about("pricing")
    assert r["count"] == 0
    assert r["rows"] == []


def _gt_zero_dependents_set(_p, _mp):
    r = graph.zero_dependents()
    assert r["count"] == 10
    assert {row["name"] for row in r["rows"]} == set(ZERO_DEPENDENT_SERVICES)


def _gt_aisha_departed(_p, _mp):
    r = graph.current_team("Aisha Khan")
    assert r["count"] == 0
    assert r["rows"] == []
    assert any(d["valid_to"] == "2026-06-30" for d in r["departed"])


def _gt_dispute_sla_empty(_p, _mp):
    r = graph.sla_of("dispute-service")
    assert r["count"] == 0
    assert r["rows"] == []


def _gt_stale_provider_doc(_p, _mp):
    names = [row["name"] for row in graph.staleness()["rows"]]
    assert any("payments-provider-eval" in (n or "") for n in names)


def _gt_provider_has_d19(_p, _mp):
    ids = [row["id"] for row in graph.decisions_about("provider")["rows"]]
    assert "D-19" in ids


def _gt_ravi_is_platform(_p, _mp):
    r = graph.current_team("Ravi Menon")
    assert "Platform" in [row["team"] for row in r["rows"]]


_GROUND_TRUTH = {
    "owner_payments_is_platform": _gt_owner_payments,
    "owner_ledger_is_ledger": _gt_owner_ledger,
    "owner_fraud_is_risk": _gt_owner_fraud,
    "config_service_unowned": _gt_config_unowned,
    "blast_count_is_8": _gt_blast_count,
    "blast_names": _gt_blast_names,
    "blast_depths": _gt_blast_depths,
    "blast_cross_team_is_6": _gt_blast_cross_team,
    "blast_excludes_ledger_core": _gt_blast_no_upstream,
    "blast_excludes_settlement_batch": _gt_blast_no_settlement,
    "priya_tops_volume": _gt_priya_top_volume,
    "priya_14_commits_stale": _gt_priya_stale,
    "oncall_ledger_diego": _gt_oncall_diego,
    "oncall_ledger_ravi_not_called": _gt_oncall_ravi_not,
    "provenance_has_d14_d19": _gt_prov_has_both,
    "d14_superseded": _gt_d14_superseded,
    "d19_supersedes_d14": _gt_d19_supersedes,
    "pricing_returns_zero": _gt_pricing_zero,
    "zero_dependents_exact_set": _gt_zero_dependents_set,
    "aisha_departed_2026_06_30": _gt_aisha_departed,
    "dispute_sla_empty": _gt_dispute_sla_empty,
    "staleness_flags_provider_doc": _gt_stale_provider_doc,
    "provider_has_d19": _gt_provider_has_d19,
    "ravi_current_team_platform": _gt_ravi_is_platform,
}


def _check_ground_truth(key, mp) -> None:
    _GROUND_TRUTH[key](None, mp)


# --------------------------------------------------------------------------- #
# Group: api — /health, /ask SSE, validation, CORS, failure frames
# --------------------------------------------------------------------------- #

_FIXTURE_QUESTIONS = [
    "Who knows about the payments service, what breaks if it goes down, "
    "and where was that decided?",
    "Who owns config-service?",
    "Who should I ask about the payments service?",
    "What breaks if payments-gateway dies?",
]


def _frames(text: str) -> list[str]:
    return [ln[len("data: "):] for ln in text.splitlines() if ln.startswith("data: ")]


def _client(mock: bool, mp) -> TestClient:
    mp.setattr(main, "USE_MOCK", mock)
    return TestClient(main.app)


def _check_api(case, mp) -> None:
    if case == "health_mock":
        body = _client(True, mp).get("/health").json()
        assert body == {"status": "ok", "mock": True}
    elif case == "health_real":
        body = _client(False, mp).get("/health").json()
        assert body == {"status": "ok", "mock": False}
    elif case.startswith("fixture_stream_"):
        i = int(case.rsplit("_", 1)[1])
        resp = _client(True, mp).post("/ask", json={"question": _FIXTURE_QUESTIONS[i]})
        assert resp.status_code == 200
        frames = _frames(resp.text)
        assert frames[-1] == "[DONE]"
        assert len(frames) == 3
        first = json.loads(frames[0])
        second = json.loads(frames[1])
        assert set(first) == {"answer", "trail", "stale"}
        assert first["answer"] == ""
        assert set(second) == {"answer", "trail", "stale"}
        assert second["answer"]
    elif case == "ask_unknown_question":
        resp = _client(True, mp).post("/ask", json={"question": "not a known case"})
        assert resp.status_code == 200
        assert _frames(resp.text)[-1] == "[DONE]"
    elif case == "reject_empty_question":
        assert _client(True, mp).post("/ask", json={"question": ""}).status_code == 422
    elif case == "reject_missing_question":
        assert _client(True, mp).post("/ask", json={}).status_code == 422
    elif case == "reject_501_chars":
        r = _client(True, mp).post("/ask", json={"question": "x" * 501})
        assert r.status_code == 422
    elif case == "reject_non_dict_body":
        assert _client(True, mp).post("/ask", json=["a"]).status_code == 422
    elif case == "reject_invalid_json":
        r = _client(True, mp).post(
            "/ask", content=b"{not json", headers={"Content-Type": "application/json"}
        )
        assert r.status_code == 422
    elif case == "wrong_type_not_500":
        r = _client(True, mp).post("/ask", json={"question": 123})
        assert r.status_code in (200, 422)
    elif case == "cors_allows_localhost":
        r = _client(True, mp).options(
            "/ask",
            headers={"Origin": "http://localhost:5173",
                     "Access-Control-Request-Method": "POST"},
        )
        assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
    elif case == "cors_allows_127":
        r = _client(True, mp).options(
            "/ask",
            headers={"Origin": "http://127.0.0.1:5173",
                     "Access-Control-Request-Method": "POST"},
        )
        assert r.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    elif case == "cors_denies_evil":
        r = _client(True, mp).options(
            "/ask",
            headers={"Origin": "http://evil.example",
                     "Access-Control-Request-Method": "POST"},
        )
        assert "access-control-allow-origin" not in r.headers
    elif case == "content_type_event_stream":
        r = _client(True, mp).post("/ask", json={"question": _FIXTURE_QUESTIONS[0]})
        assert r.headers["content-type"].startswith("text/event-stream")
    elif case == "cache_control_no_cache":
        r = _client(True, mp).post("/ask", json={"question": _FIXTURE_QUESTIONS[0]})
        assert r.headers.get("cache-control") == "no-cache"
    elif case == "x_accel_buffering_off":
        r = _client(True, mp).post("/ask", json={"question": _FIXTURE_QUESTIONS[0]})
        assert r.headers.get("x-accel-buffering") == "no"
    elif case == "get_ask_is_405":
        assert _client(True, mp).get("/ask").status_code == 405
    elif case == "failure_frame_runtime_error":
        def boom(_q: str):
            raise RuntimeError("GROQ_API_KEY is not set")
        mp.setattr(main, "answer_question", boom)
        frames = _frames(_client(True, mp).post("/ask", json={"question": "q"}).text)
        assert frames[-1] == "[DONE]"
        payload = json.loads(frames[0])
        assert payload["answer"].startswith("I could not answer that")
        assert "GROQ_API_KEY" in payload["answer"]
        assert payload["trail"] == [] and payload["stale"] == []
    elif case == "failure_frame_generic":
        def boom(_q: str):
            raise ValueError("kaboom")
        mp.setattr(main, "answer_question", boom)
        frames = _frames(_client(True, mp).post("/ask", json={"question": "q"}).text)
        payload = json.loads(frames[0])
        assert "the lookup failed (ValueError)" in payload["answer"]
    else:  # pragma: no cover
        raise AssertionError(f"unknown api case {case!r}")


_API_CASES = [
    "health_mock",
    "health_real",
    "fixture_stream_0",
    "fixture_stream_1",
    "fixture_stream_2",
    "fixture_stream_3",
    "ask_unknown_question",
    "reject_empty_question",
    "reject_missing_question",
    "reject_501_chars",
    "reject_non_dict_body",
    "reject_invalid_json",
    "wrong_type_not_500",
    "cors_allows_localhost",
    "cors_allows_127",
    "cors_denies_evil",
    "content_type_event_stream",
    "cache_control_no_cache",
    "x_accel_buffering_off",
    "get_ask_is_405",
    "failure_frame_runtime_error",
    "failure_frame_generic",
]


# --------------------------------------------------------------------------- #
# Group: agent — the model-facing surface
# --------------------------------------------------------------------------- #

_AGENT_CHECKS = {
    # Was `len(agent.TOOLS) == 10`, which #22 (Microsoft Graph parity) made
    # false by adding five real tools — 10 -> 15. A hardcoded count fails on
    # every correct feature addition, and it fails in the one way that reads as
    # "the agent is broken" rather than "the test is stale". Assert the
    # invariant instead: the model-visible tool surface and the traversal
    # surface must stay the same size, so a tool can never be exposed to the
    # model without a function behind it, or vice versa.
    "tools_len_matches_graph": lambda: len(agent.TOOLS) == len(graph.TOOLS) > 0,
    "tool_keys": lambda: all(
        {"name", "description", "input_schema"} <= set(t) for t in agent.TOOLS
    ),
    "tool_names_match_graph": lambda: {t["name"] for t in agent.TOOLS} == set(graph.TOOLS),
    "schemas_are_objects": lambda: all(
        t["input_schema"].get("type") == "object" for t in agent.TOOLS
    ),
    "stale_types_is_seven": lambda: agent.STALE_TYPES == TYPES,
    "stale_types_subset": lambda: agent.STALE_TYPES <= TYPES,
    "model_is_set": lambda: isinstance(agent.MODEL, str) and bool(agent.MODEL),
    "max_tokens_positive": lambda: isinstance(agent.MAX_TOKENS, int) and agent.MAX_TOKENS >= 1,
    "max_tool_rounds_positive": lambda: (
        isinstance(agent.MAX_TOOL_ROUNDS, int) and agent.MAX_TOOL_ROUNDS >= 1
    ),
}


def _check_agent(key, _mp) -> None:
    assert _AGENT_CHECKS[key]()


# --------------------------------------------------------------------------- #
# Assemble the exactly-1000-case suite.
# --------------------------------------------------------------------------- #

CORE: list[tuple[str, object]] = []


def _add(group: str, payload: object) -> None:
    CORE.append((group, payload))


# per-service sweeps
for _s in SERVICES:
    _add("owner_of", _s)
    _add("blast_radius", _s)
    _add("expertise", _s)
    _add("sla_of", _s)

# provenance, current_team, on_call
for _p in PROJECTS:
    _add("provenance", _p)
for _person in PEOPLE:
    _add("current_team", _person)
for _t in TEAMS:
    _add("on_call", _t)

# decisions_about: every decision retrievable by a word from its own summary
for _did, _summary in DECISION_ROWS:
    _words = re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", _summary)
    _word = max(_words, key=len) if _words else ""
    _add("decisions_about", (_word, _did, None))

# decisions_about: fixed keywords, including the two planted answers
for _kw, _req, _cnt in [
    ("", None, len(DECISIONS)),
    ("pricing", None, 0),
    ("provider", "D-19", None),
    ("Reassign", None, None),
    ("payments", None, None),
    ("migration", None, None),
    ("superseded", None, None),
    ("zzzz-no-such-keyword", None, 0),
]:
    _add("decisions_about", (_kw, _req, _cnt))

# zero_dependents (fact 18) + staleness
for _z in sorted(ZERO_DEPENDENT_SERVICES):
    _add("zero_dependents", _z)
_add("staleness", None)

# invariants + vocab over all 10 tools
for _tool in _TOOL_CALLS:
    for _i in range(7):
        _add("invariants", (_tool, _i))
for _tool in _TOOL_CALLS:
    for _i in range(3):
        _add("vocab", (_tool, _i))

# hostile strings against every string-taking tool
for _tool in _STRING_TOOLS:
    for _junk in _GARBAGE:
        _add("garbage", (_tool, _junk))

# unknown services: honest empty, never an invented node
for _i in range(20):
    _fake = f"zzz-nonexistent-{_i:02d}"
    for _tool in ("blast_radius", "expertise", "owner_of", "sla_of"):
        _add("fakeservice", (_tool, _fake))

# the hand-written facts
for _key in _GROUND_TRUTH:
    _add("groundtruth", _key)

# api + agent surface
for _case in _API_CASES:
    _add("api", _case)
for _key in _AGENT_CHECKS:
    _add("agent", _key)

TARGET = 1000
_POOL = _alias_pool()
_NEED = TARGET - len(CORE)
assert _NEED >= 0, f"CORE already has {len(CORE)} > {TARGET} cases"
assert _NEED <= len(_POOL), f"alias pool too small: need {_NEED}, have {len(_POOL)}"

CASES: list[tuple[str, object]] = CORE + [("alias", p) for p in _POOL[:_NEED]]

_CHECKS = {
    "alias": _check_alias,
    "owner_of": _check_owner_of,
    "blast_radius": _check_blast_radius,
    "expertise": _check_expertise,
    "sla_of": _check_sla_of,
    "provenance": _check_provenance,
    "current_team": _check_current_team,
    "on_call": _check_on_call,
    "decisions_about": _check_decisions_about,
    "zero_dependents": _check_zero_dependents,
    "staleness": _check_staleness,
    "invariants": _check_invariant,
    "vocab": _check_vocab,
    "garbage": _check_garbage,
    "fakeservice": _check_fake_service,
    "groundtruth": _check_ground_truth,
    "api": _check_api,
    "agent": _check_agent,
}


def test_suite_is_exactly_1000_cases():
    assert len(CASES) == 1000
    assert {g for g, _ in CASES} == set(_CHECKS)


@pytest.mark.parametrize(
    "group,payload",
    CASES,
    ids=[f"{g}-{i}" for i, (g, _) in enumerate(CASES)],
)
def test_generated_case(group, payload, monkeypatch):
    _CHECKS[group](payload, monkeypatch)
