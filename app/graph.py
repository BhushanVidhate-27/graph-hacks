"""
app/graph.py — THE ONLY CYPHER IN THE REPO.

Owned by Bhushan. Soham's app/agent.py imports exactly these four functions by
name; keep the signatures stable or he is blocked again.

VERIFIED FalkorDB constraints — do not rediscover these:
  - g.query(cypher, params).result_set   <- .result_set is REQUIRED. query() is not
    iterable; `for row in g.query(...)` raises TypeError.
  - FalkorDB is a SUBSET of OpenCypher. No Neo4j-only syntax.
  - NEVER undirected shortestPath((a)-[*]-(b)) — unsupported. Directed only.
  - NEVER db.idx.fulltext.* — not registered in the default image.
    Use WHERE x CONTAINS 'y'.
  - NEVER return type(node) in the same RETURN as an optional node — type
    mismatch. Return labels(node) instead.
  - Variable-length + OPTIONAL MATCH + collect(DISTINCT) is VERIFIED WORKING.
  - Cypher CANNOT traverse an edge backwards. Blast radius walks HAS_DEPENDENT,
    the inverse edge the loader derives from service_deps.csv. It is NOT a
    reversed DEPENDS_ON. Get this wrong and the query returns [] silently.

Every function returns {"rows": [...], "trail": [...]} so the frontend can render
a provenance trail with edge labels. Values are always passed as parameters,
never interpolated into the query string.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

GRAPH = os.getenv("FALKORDB_GRAPH", "helio")
HOST = os.getenv("FALKORDB_HOST", "localhost")
PORT = int(os.getenv("FALKORDB_PORT", "6379"))

# GROUND_TRUTH fact 8. Recency must reorder Priya below Ravi, so expertise()
# returns volume and recency separately and never a single fused ranking.
STALE_DAYS = 90


def _graph():
    return FalkorDB(host=HOST, port=PORT).select_graph(GRAPH)


def _trail(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise rows into the frozen trail[] contract.

    type, name, detail, date, via_edge — every field present on every row. A
    missing via_edge is a chip that renders wrong and nobody finds out until the
    real demo.
    """
    out = []
    for e in entries:
        out.append({
            "type": e.get("type", ""),
            "name": e.get("name", ""),
            "detail": e.get("detail", ""),
            "date": e.get("date", ""),
            "via_edge": e.get("via_edge", ""),
        })
    return out


# ---------------------------------------------------------------------------
# 1. BLAST RADIUS — what breaks if this service dies, and who gets paged
# ---------------------------------------------------------------------------
# min(length(path)) above is REQUIRED, not cosmetic: notifications depends on BOTH
# payments-gateway and dispute-service, so it is reachable at depth 1 AND depth 2.
# Without the min() it is returned twice and the count reads 9 instead of 8.

BLAST_RADIUS = """
MATCH path = (s:Service {name: $service})-[:HAS_DEPENDENT*1..4]->(dep:Service)
WITH dep, min(length(path)) AS depth
OPTIONAL MATCH (dep)-[:OWNED_BY]->(t:Team)
OPTIONAL MATCH (t)-[:HAS_ROTATION]->(m:Person:Member)-[oc:ON_CALL]->(t)
RETURN dep.name AS dep,
       depth,
       t.name AS owner_team,
       m.name AS on_call
ORDER BY depth, dep
"""

EXPLOSION = """
MATCH (s:Service {name: $service})-[:HAS_DEPENDENT*1..4]->(dep:Service)
OPTIONAL MATCH (dep)-[:OWNED_BY]->(t:Team)
WITH dep, collect(DISTINCT t.name) AS teams
RETURN dep.name AS dep,
       teams,
       size([x IN teams WHERE x IS NOT NULL AND x <> $owner_team]) AS cross_team
ORDER BY dep
"""


def blast_radius(service: str) -> dict[str, Any]:
    """What breaks if `service` dies, how deep the impact reaches, who is on call.

    Returns rows AND trail so Ujwal can render chips with real edge labels.
    """
    g = _graph()

    owner = g.query(
        "MATCH (s:Service {name: $service})-[:OWNED_BY]->(t:Team) RETURN t.name AS t",
        {"service": service}).result_set
    owner_team = owner[0][0] if owner else ""

    rows = g.query(BLAST_RADIUS, {"service": service}).result_set
    explosions = g.query(EXPLOSION, {"service": service,
                                     "owner_team": owner_team}).result_set

    by_dep = {r[0]: {"teams": r[1] or [], "cross_team": r[2]} for r in explosions}

    out_rows, trail = [], []
    for dep, depth, owner_t, on_call in rows:
        info = by_dep.get(dep, {"teams": [], "cross_team": 0})
        detail = f"{depth} hop(s) away"
        if info["teams"]:
            detail += f", owned by {'/'.join(t for t in info['teams'] if t)}"
        else:
            detail += ", NO OWNER"
        if info["cross_team"]:
            detail += " [different team]"
        if on_call:
            detail += f", on call: {on_call}"
        out_rows.append({
            "service": dep, "depth": depth, "owner_team": owner_t,
            "on_call": on_call, "cross_team": info["cross_team"], "detail": detail,
        })
        trail.append({"type": "Service", "name": dep, "detail": detail,
                      "date": "", "via_edge": "HAS_DEPENDENT"})

    return {"service": service, "rows": out_rows, "trail": _trail(trail),
            "count": len(out_rows)}


# ---------------------------------------------------------------------------
# 2. EXPERTISE — who knows this, recency-weighted
# ---------------------------------------------------------------------------
EXPERTISE = """
MATCH (p:Person)-[c:CONTRIBUTED_TO]->(proj:Project)-[:USES]->(s:Service {name: $service})
RETURN p.name AS person,
       sum(c.commits) AS commits,
       max(c.last_touch) AS latest,
       collect(DISTINCT proj.name) AS projects
ORDER BY commits DESC
"""


def expertise(service: str) -> dict[str, Any]:
    """People by contribution volume WITH recency.

    Deliberately returns volume and recency side by side rather than one fused
    rank. Fact 8: the top contributor by commits (Priya Sharma) is stale — she
    left 2026-04-15. Collapsing this to a single number is technically correct on
    volume and the wrong answer. The agent has to be able to narrate the tension.
    """
    g = _graph()
    rows = g.query(EXPERTISE, {"service": service}).result_set

    out_rows, trail = [], []
    for person, commits, latest, projects in rows:
        commits = int(commits)              # sum() returns a float; "14.0 commits" reads badly
        stale = latest < _cutoff()
        detail = f"{commits} commits, last touch {latest}"
        if stale:
            detail += " [STALE]"
        out_rows.append({
            "person": person, "commits": commits, "latest": latest,
            "stale": stale, "projects": projects, "detail": detail,
        })
        trail.append({"type": "Person", "name": person, "detail": detail,
                      "date": latest, "via_edge": "CONTRIBUTED_TO"})

    # Current ownership, so "who should I ask" has a second, fresher signal than
    # commit volume.
    owner = g.query(
        "MATCH (d:Decision)-[:ABOUT]->(proj:Project)-[:USES]->(s:Service {name: $service}) "
        "WHERE d.summary CONTAINS 'Reassign' RETURN d.summary AS s, d.date AS date "
        "ORDER BY d.date DESC LIMIT 1",
        {"service": service}).result_set
    if owner:
        out_rows.append({"person": "current owner (per decision)", "detail": owner[0][0],
                         "latest": owner[0][1], "commits": None, "stale": False})
        trail.append({"type": "Decision", "name": "ownership", "detail": owner[0][0],
                      "date": owner[0][1], "via_edge": "ABOUT"})

    return {"service": service, "rows": out_rows, "trail": _trail(trail),
            "count": len(out_rows)}


def _cutoff():
    from datetime import date, timedelta
    return (date(2026, 10, 17) - timedelta(days=STALE_DAYS)).isoformat()


# ---------------------------------------------------------------------------
# 3. PROVENANCE — where was this decided, and has it been superseded
# ---------------------------------------------------------------------------
# Evidence is aggregated with collect(DISTINCT ...) rather than left to fan out.
# A plain OPTIONAL MATCH returns one row per evidence node, so D-19 and D-14 each
# appeared twice and the decision count was wrong.
PROVENANCE = """
MATCH (d:Decision)-[:ABOUT]->(p:Project {name: $project})
OPTIONAL MATCH (d)-[:SUPERSEDES]->(prev:Decision)
OPTIONAL MATCH (d)-[:EVIDENCED_BY]->(ev)
WITH d, prev, collect(DISTINCT ev.name) AS evidence
RETURN d.id AS id,
       d.summary AS summary,
       d.date AS date,
       d.status AS status,
       evidence,
       prev.id AS superseded_id,
       prev.summary AS superseded_summary
ORDER BY d.date DESC
"""


def provenance(project: str) -> dict[str, Any]:
    """Decisions about `project`, who authored the evidence, what it superseded.

    Traverses SUPERSEDES so a superseded decision shows AS superseded (fact 13),
    which is what lets the agent flag the stale provider-evaluation document
    instead of quoting it as current truth (fact 15).
    """
    g = _graph()
    rows = g.query(PROVENANCE, {"project": project}).result_set

    out_rows, trail = [], []
    for did, summary, dt, status, evidence, sup_id, sup_summary in rows:
        detail = summary
        if sup_id:
            detail += f" [SUPERSEDES {sup_id}]"
        elif status == "superseded":
            detail += " [SUPERSEDED]"
        ev_names = [e for e in (evidence or []) if e]
        out_rows.append({
            "id": did, "summary": summary, "date": dt, "status": status,
            "evidence": ev_names, "superseded_by": sup_id,
            "supersedes_summary": sup_summary, "detail": detail,
        })
        trail.append({"type": "Decision", "name": did, "detail": detail,
                      "date": dt, "via_edge": "SUPERSEDES" if sup_id else "ABOUT"})
        for ev in ev_names:
            trail.append({"type": "Document", "name": ev,
                          "detail": "evidence for " + did, "date": dt,
                          "via_edge": "EVIDENCED_BY"})

    return {"project": project, "rows": out_rows, "trail": _trail(trail),
            "count": len(out_rows)}


# ---------------------------------------------------------------------------
# 4. STALENESS — edges not re-verified in 90 days
# ---------------------------------------------------------------------------
STALENESS = """
MATCH ()-[r]->()
WHERE r.last_verified_at IS NOT NULL
  AND r.last_verified_at < $cutoff
RETURN type(r) AS edge,
       r.last_verified_at AS last_verified_at
ORDER BY r.last_verified_at
"""

STALE_DOCUMENTS = """
MATCH (d:Document)
WHERE d.last_verified_at IS NOT NULL AND d.last_verified_at < $cutoff
OPTIONAL MATCH (dec:Decision)-[:EVIDENCED_BY]->(d)
RETURN d.name AS doc, d.last_verified_at AS last_verified_at,
       collect(DISTINCT dec.id) AS cited_by
ORDER BY d.last_verified_at
"""


def staleness() -> dict[str, Any]:
    """Edges whose last_verified_at is older than 90 days.

    A document contradicted by a NEWER decision is the interesting case — it is
    the freshness demo (fact 15), so both are reported.
    """
    g = _graph()
    cutoff = _cutoff()
    edges = g.query(STALENESS, {"cutoff": cutoff}).result_set
    docs = g.query(STALE_DOCUMENTS, {"cutoff": cutoff}).result_set

    out_rows, trail = [], []
    for etype, last in edges:
        out_rows.append({"type": "edge", "name": etype, "last_verified_at": last,
                         "reason": f"not re-verified since {last}"})
        trail.append({"type": "edge", "name": etype,
                      "detail": f"not re-verified since {last}", "date": last,
                      "via_edge": "last_verified_at"})

    for name, last, cited in docs:
        contradicted = [c for c in cited if c]
        detail = f"last verified {last}"
        if contradicted:
            detail += f", evidence for {', '.join(sorted(contradicted))}"
        out_rows.append({"type": "Document", "name": name, "last_verified_at": last,
                         "reason": detail, "cited_by": contradicted})
        trail.append({"type": "Document", "name": name, "detail": detail,
                      "date": last, "via_edge": "EVIDENCED_BY"})

    return {"cutoff": cutoff, "rows": out_rows, "trail": _trail(trail),
            "count": len(out_rows)}


# ---------------------------------------------------------------------------
# Supporting lookups used to answer the must-fail questions. These exist so the
# agent has a real "nothing found" answer instead of an excuse to invent one.
# ---------------------------------------------------------------------------
def owner_of(service: str) -> dict[str, Any]:
    """Team owner of a service. An unowned service returns rows=[] on purpose."""
    g = _graph()
    rows = g.query(
        "MATCH (s:Service {name: $service})-[:OWNED_BY]->(t:Team) "
        "RETURN t.name AS team",
        {"service": service}).result_set
    trail = _trail([{"type": "Team", "name": r[0], "via_edge": "OWNED_BY",
                     "detail": f"owns {service}"} for r in rows])
    return {"service": service, "rows": [{"team": r[0]} for r in rows],
            "trail": trail, "count": len(rows)}


def decisions_about(keyword: str) -> dict[str, Any]:
    """Decisions matching a keyword. An absent keyword returns rows=[] on purpose."""
    g = _graph()
    rows = g.query(
        "MATCH (d:Decision) WHERE d.summary CONTAINS $keyword "
        "RETURN d.id AS id, d.summary AS summary, d.date AS date",
        {"keyword": keyword}).result_set
    return {"keyword": keyword, "rows": [{"id": r[0], "summary": r[1], "date": r[2]}
                                         for r in rows], "trail": [], "count": len(rows)}


# Fact 18.
#
# Two earlier versions of this were wrong, both silently:
#   1. NOT (s)<-[:HAS_DEPENDENT]-()  -> returned the 3 services with no DEPENDS_ON
#      (the DAG roots) instead of the 10 with no inbound HAS_DEPENDENT.
#   2. OPTIONAL MATCH (s)<-[:HAS_DEPENDENT]-(x) WHERE x IS NULL -> returned ALL 20
#      services. FalkorDB does not bind x in the WHERE, so x is null for every
#      row and the filter never rejects anything.
# So: read the real inbound set out of the graph and subtract in Python. The set
# comes from an actual query — this is not a hardcoded answer.
ALL_SERVICES = "MATCH (s:Service) RETURN s.name AS name"
# NOTE the source side, not the target. HAS_DEPENDENT runs dependency -> dependent,
# so a service that HAS dependents is a SOURCE. Returning b.name gives the
# dependents themselves and inverts the whole question (answer came back 3, not 10).
HAS_DEPENDENT_SOURCES = "MATCH (a:Service)-[:HAS_DEPENDENT]->(b:Service) RETURN DISTINCT a.name AS name"


def zero_dependents() -> dict[str, Any]:
    """Services with no inbound HAS_DEPENDENT edge (fact 18 — state the real list)."""
    g = _graph()
    all_s = [r[0] for r in g.query(ALL_SERVICES).result_set]
    depended = {r[0] for r in g.query(HAS_DEPENDENT_SOURCES).result_set}
    names = sorted(s for s in all_s if s not in depended)
    return {"rows": [{"name": n} for n in names],
            "trail": _trail([{"type": "Service", "name": n,
                              "detail": "nothing depends on it",
                              "via_edge": "HAS_DEPENDENT"} for n in names]),
            "count": len(names)}


ON_CALL = """
MATCH (t:Team {name: $team})<-[:ON_CALL]-(m:Person:Member)
RETURN m.name AS on_call, m.on_call_week AS week_start
"""

ROTATION = """
MATCH (t:Team {name: $team})-[:HAS_ROTATION]->(r:Person:Member)
RETURN r.name AS member
"""


def on_call(team: str) -> dict[str, Any]:
    """Who is on call for `team` this week, and who else is on the rotation.

    Fact 11. Ravi Menon is on the Ledger rotation but NOT on call this week, and
    Priya Sharma is on no rotation at all — so the graph has to reject two of its
    three plausible candidates rather than return the first match.
    """
    g = _graph()
    now = g.query(ON_CALL, {"team": team}).result_set
    rot = g.query(ROTATION, {"team": team}).result_set

    on_names = [r[0] for r in now]
    rot_names = [r[0] for r in rot]
    not_on = [n for n in rot_names if n not in on_names]

    rows = [{"person": n, "on_call": True, "week_start": w} for n, w in now]
    rows += [{"person": n, "on_call": False, "week_start": None} for n in not_on]

    trail = _trail([{"type": "Person", "name": n, "detail": "ON CALL this week",
                     "date": w, "via_edge": "ON_CALL"} for n, w in now])
    trail += _trail([{"type": "Person", "name": n,
                      "detail": "on the rotation, not on call this week",
                      "date": "", "via_edge": "HAS_ROTATION"} for n in not_on])
    return {"team": team, "rows": rows, "trail": trail, "count": len(rows)}


def sla_of(service: str) -> dict[str, Any]:
    """SLA for a service. Empty for dispute-service on purpose (fact 20).

    count reflects rows actually returned. It previously counted the match before
    filtering empties, so dispute-service reported count=1 with zero rows — which
    reads to the agent as "an SLA exists" and is exactly the fabrication fact 20
    is testing for.
    """
    g = _graph()
    rows = [r[0] for r in g.query(
        "MATCH (s:Service {name: $service}) RETURN s.sla AS sla",
        {"service": service}).result_set if r[0]]
    return {"service": service, "rows": [{"sla": s} for s in rows],
            "trail": _trail([{"type": "Service", "name": service,
                              "detail": f"SLA {s}", "via_edge": "SLA"} for s in rows]),
            "count": len(rows)}


def current_team(person: str) -> dict[str, Any]:
    """Current team. Empty when MEMBER_OF.valid_to is set — the person left (fact 19)."""
    g = _graph()
    rows = g.query(
        "MATCH (p:Person {name: $person})-[m:MEMBER_OF]->(t:Team) "
        "RETURN t.name AS team, m.valid_to AS valid_to",
        {"person": person}).result_set
    current = [r for r in rows if not r[1]]
    departed = [r for r in rows if r[1]]
    return {"person": person,
            "rows": [{"team": r[0], "valid_to": r[1]} for r in current],
            "departed": [{"team": r[0], "valid_to": r[1]} for r in departed],
            "trail": _trail([{"type": "Team", "name": r[0], "via_edge": "MEMBER_OF",
                              "detail": "current" if not r[1]
                                        else f"left {r[1]}"} for r in rows]),
            "count": len(current)}


TOOLS = {
    "blast_radius": blast_radius,
    "expertise": expertise,
    "provenance": provenance,
    "staleness": staleness,
    "owner_of": owner_of,
    "decisions_about": decisions_about,
    "zero_dependents": zero_dependents,
    "sla_of": sla_of,
    "current_team": current_team,
    "on_call": on_call,
}
