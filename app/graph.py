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
import re
from typing import Any

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

GRAPH = os.getenv("FALKORDB_GRAPH", "helio")
HOST = os.getenv("FALKORDB_HOST", "localhost")
PORT = int(os.getenv("FALKORDB_PORT", "6379"))
USERNAME = os.getenv("FALKORDB_USERNAME", "")
PASSWORD = os.getenv("FALKORDB_PASSWORD", "")

# GROUND_TRUTH fact 8. Recency must reorder Priya below Ravi, so expertise()
# returns volume and recency separately and never a single fused ranking.
STALE_DAYS = 90


def _graph():
    """Connect to FalkorDB — local Docker or Cloud.

    Cloud needs three things local does not, and missing any one of them fails
    with a bare connection error rather than anything that names the cause:

      1. TLS (ssl=True). Plain TCP to a Cloud endpoint is refused.
      2. A non-default port (Cloud is not 6379).
      3. Credentials. Cloud requires a username/password pair even on Free.

    All three are read from env, so the same code runs locally and in production
    with no edit. Set FALKORDB_SSL=true for Cloud; it defaults off so the local
    Docker container keeps working untouched.
    """
    kwargs = {"host": HOST, "port": PORT}
    ssl_on = os.getenv("FALKORDB_SSL", "").strip().lower() in ("1", "true", "yes", "on")
    if ssl_on:
        kwargs["ssl"] = True
    if USERNAME:
        kwargs["username"] = USERNAME
    if PASSWORD:
        kwargs["password"] = PASSWORD
def db_health() -> bool:
    """Return True if FalkorDB is reachable and responding."""
    try:
        g = _graph()
        # Cheap query to verify connectivity
        g.query("RETURN 1").result_set
        return True
    except Exception:
        return False


def resolve_service(name: str) -> tuple[str, bool]:
    """Map a loose human phrase onto a real Service name.

    Returns (resolved_name, was_exact).

    This exists because of a real, observed failure, not a hypothetical one.
    Asked "who should I ask about the payments service?", the agent passed the
    literal string "payments-service" to owner_of(). That node does not exist, so
    the query returned nothing, and the agent reported — fluently and in total
    confidence — "The graph contains no OWNED_BY edge for payments-service, and
    no contribution history is recorded either."

    payments-gateway IS owned by Platform and has 28 commits of history. The
    Cypher was right, the database was right, and the answer was fabricated. This
    is the single worst failure mode in the whole product: it survives a casual
    read, because "no owner found" sounds exactly like a true negative.

    So every service-taking function resolves its argument FIRST. If nothing
    matches confidently we return the original string unchanged, so a genuinely
    unknown service still yields the honest empty answer — resolving must never
    invent a target that the caller did not name.
    """
    g = _graph()
    names = [r[0] for r in g.query(ALL_SERVICES).result_set]
    if name in names:
        return name, True

    low = (name or "").lower().strip()
    if not low:
        return name, False

    # "the payments service" / "payments-service" / "Payments Service" all mean
    # payments-gateway. Strip the generic tail before comparing.
    for suffix in (" service", "-service", "_service", " svc"):
        if low.endswith(suffix):
            low = low[: -len(suffix)]
    low = low.replace("the ", "").strip()

    for n in names:
        if n.lower() == low:
            return n, False

    hits = [n for n in names if low and low in n.lower()]
    if len(hits) == 1:
        return hits[0], False

    # Last resort: token overlap. Only accept a UNIQUE best match — an ambiguous
    # guess is worse than no guess, because it invents a node.
    toks = {t for t in re.split(r"[^a-z0-9]+", low) if len(t) > 2}
    if toks:
        scored = []
        for n in names:
            nt = {t for t in re.split(r"[^a-z0-9]+", n.lower()) if len(t) > 2}
            overlap = toks & nt
            if overlap:
                scored.append((len(overlap), len(n), n))
        if scored:
            scored.sort(reverse=True)
            best = scored[0]
            runner_up = scored[1] if len(scored) > 1 else None
            if runner_up is None or best[0] > runner_up[0]:
                return best[2], False

    return name, False


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
    service, _exact = resolve_service(service)
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
    service, _exact = resolve_service(service)
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
                      "date": owner[0][1], "via_edge": "EVIDENCED_BY"})

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
        # via_edge is restricted to Ujwal's FROZEN vocabulary of 9 values
        # (mock/trail.json -> via_edge_vocabulary). "ABOUT" is NOT in it. An
        # unrecognised edge renders a chip the frontend has no style for, and the
        # renderer is already merged and tested against the fixture.
        #   chained decision -> SUPERSEDES  (it was reached via the chain)
        #   unchained        -> EVIDENCED_BY (it was reached via its evidence)
        # If the team wants ABOUT rendered properly that is a one-word addition to
        # the vocabulary on Ujwal's side, not something to smuggle in from here.
        chained = bool(sup_id) or status == "superseded"
        trail.append({"type": "Decision", "name": did, "detail": detail,
                      "date": dt, "via_edge": "SUPERSEDES" if chained else "EVIDENCED_BY"})
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
        # Deliberately NOT added to trail. The stale thing here is a PROPERTY
        # (last_verified_at), not an edge, and the frozen via_edge vocabulary has
        # no entry for a property name. The row above still carries it.

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
    service, _exact = resolve_service(service)
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


# week_start lives on the ON_CALL EDGE -- scripts/load.py stamps it there with
# SET o.week_start = ... . Reading m.on_call_week (a Person NODE property) returned
# None for every on-call person, so on_call() reported week_start=None and put a
# null `date` into the trail, which fails Answer.model_validate on the real path
# (the frozen contract says trail[].date is a str on every row). Bind the edge.
ON_CALL = """
MATCH (t:Team {name: $team})<-[oc:ON_CALL]-(m:Person:Member)
RETURN m.name AS on_call, oc.week_start AS week_start
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
    # Rotation members who are NOT on call stay in rows but not in trail:
    # HAS_ROTATION is not in the frozen via_edge vocabulary.
    return {"team": team, "rows": rows, "trail": trail, "count": len(rows),
            "on_call": on_names, "rotation_not_on_call": not_on}


def sla_of(service: str) -> dict[str, Any]:
    """SLA for a service. Empty for dispute-service on purpose (fact 20).

    count reflects rows actually returned. It previously counted the match before
    filtering empties, so dispute-service reported count=1 with zero rows — which
    reads to the agent as "an SLA exists" and is exactly the fabrication fact 20
    is testing for.
    """
    service, _exact = resolve_service(service)
    g = _graph()
    rows = [r[0] for r in g.query(
        "MATCH (s:Service {name: $service}) RETURN s.sla AS sla",
        {"service": service}).result_set if r[0]]
    return {"service": service, "rows": [{"sla": s} for s in rows],
            "trail": _trail([{"type": "Service", "name": service,
                              "detail": f"SLA {s}",
                              "via_edge": "OWNED_BY"} for s in rows]),
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


# ---------------------------------------------------------------------------
# 5. DIRECTORY, CHAT AND FILES — the Microsoft Graph parity surface
# ---------------------------------------------------------------------------
# Microsoft Graph is the "company graph" every judge already knows: /manager
# and /directReports for the reporting line, /groups/{id}/members for rosters,
# chat-message search, drive-item search. docs/microsoft-graph-parity.md maps
# its resource surface onto this schema and found four capabilities the data
# already carried but no tool exposed:
#
#   1. REPORTS_TO (99 edges, loaded since day one, NEVER queried by anything)
#   2. MEMBER_OF as a roster (only reachable per-person via current_team)
#   3. Message + MENTIONS (2,000 nodes the agent could not read at all)
#   4. Document (200 nodes surfaced only as staleness rows or decision evidence)
#
# The README promises "traversal first, text search only at the leaves" — and
# until this section the agent had NO leaf search over messages or documents,
# so the leaves existed in the graph and the agent could not read them.
#
# Everything here stays inside the frozen contract: via_edge values are taken
# from web/index.html's closed 14-entry VIA_EDGE_VOCABULARY (REPORTS_TO and
# MENTIONS and EVIDENCED_BY and MEMBER_OF are all in it), and any stale[]
# emissions use the 7-type vocabulary in app/agent.py.

# The chain ABOVE a person. min(length(path)) dedupes diamond shapes, the same
# reason BLAST_RADIUS needs it: with 99 REPORTS_TO edges a manager is sometimes
# reachable at two depths and would otherwise be returned twice.
REPORTS_UP = """
MATCH path = (p:Person {name: $person})-[:REPORTS_TO*1..6]->(m:Person)
WITH m, min(length(path)) AS depth
RETURN m.name AS manager, m.title AS title, m.seniority AS seniority, depth
ORDER BY depth
"""

# The chain BELOW a person. Same edge, opposite question: the SOURCE side is the
# report and the target side is the manager, so "who reports to X" walks
# (dr)-[:REPORTS_TO*]->(x) — never a reversed edge.
REPORTS_DOWN = """
MATCH path = (dr:Person)-[:REPORTS_TO*1..6]->(p:Person {name: $person})
WITH dr, min(length(path)) AS depth
RETURN dr.name AS report, dr.title AS title, dr.seniority AS seniority, depth
ORDER BY depth, report
"""

ALL_TEAMS = "MATCH (t:Team) RETURN t.name AS name"

TEAM_MEMBERS = """
MATCH (t:Team {name: $team})<-[m:MEMBER_OF]-(p:Person)
RETURN p.name AS person, p.title AS title, p.seniority AS seniority,
       m.role AS role, m.since AS since, m.valid_to AS valid_to
"""

# Message leaves. Two lookups feed one result — see search_messages().
# The WITH before RETURN mirrors PROVENANCE: aggregating straight into RETURN
# with ORDER BY on the same clause is the shape FalkorDB is verified on.
MESSAGES_BODY = """
MATCH (m:Message) WHERE m.body CONTAINS $kw
OPTIONAL MATCH (m)-[:MENTIONS]->(e)
WITH m, collect(DISTINCT e.name) AS mentions
RETURN m.id AS id, m.channel AS channel, m.author AS author, m.ts AS ts,
       m.body AS body, mentions
ORDER BY m.ts DESC
LIMIT 20
"""

# The structural answer plain search cannot give: messages that MENTION an
# entity even when the body never spells its name the way the asker did.
MESSAGES_ENTITY = """
MATCH (m:Message)-[:MENTIONS]->(e {name: $entity})
OPTIONAL MATCH (m)-[:MENTIONS]->(e2)
WITH m, collect(DISTINCT e2.name) AS mentions
RETURN m.id AS id, m.channel AS channel, m.author AS author, m.ts AS ts,
       m.body AS body, mentions
ORDER BY m.ts DESC
LIMIT 20
"""

DOCUMENTS_BY_KEYWORD = """
MATCH (d:Document)
WHERE d.name CONTAINS $kw OR d.kind CONTAINS $kw OR d.project = $kw
OPTIONAL MATCH (dec:Decision)-[:EVIDENCED_BY]->(d)
WITH d, collect(DISTINCT dec.id) AS cited_by
RETURN d.name AS name, d.kind AS kind, d.date AS date, d.project AS project,
       d.author AS author, d.last_verified_at AS last_verified_at, cited_by
ORDER BY d.date DESC
LIMIT 15
"""


def resolve_team(name: str) -> str:
    """Case-insensitive exact match onto a real Team name.

    "platform", "Platform", "Platform team" → "Platform". Same honest-negative
    contract as resolve_service: an unknown team returns the original string
    unchanged, so the query answers "nobody" instead of inventing a roster.
    """
    g = _graph()
    names = [r[0] for r in g.query(ALL_TEAMS).result_set]
    low = (name or "").lower().strip()
    for suffix in (" team", "-team", "_team"):
        if low.endswith(suffix):
            low = low[: -len(suffix)]
    for n in names:
        if n.lower() == low:
            return n
    return name


def reports_to(person: str) -> dict[str, Any]:
    """The management chain ABOVE `person` — direct manager first.

    Microsoft Graph's /users/{id}/manager and its transitive form. The
    REPORTS_TO edges were loaded since day one and nothing queried them: the
    graph knew the entire reporting line and the agent could not answer "who
    does Ravi report to" with anything but an invention.
    """
    g = _graph()
    rows = g.query(REPORTS_UP, {"person": person}).result_set

    out_rows, trail = [], []
    for manager, title, seniority, depth in rows:
        hops = int(depth)          # driver may hand back an int-like float
        detail = "direct manager" if hops == 1 else f"manager, {hops} levels up"
        if title:
            detail += f" — {title}"
        out_rows.append({
            "manager": manager, "title": title, "seniority": seniority,
            "hops": hops, "direct": hops == 1, "detail": detail,
        })
        trail.append({"type": "Person", "name": manager, "detail": detail,
                      "date": "", "via_edge": "REPORTS_TO"})

    return {"person": person, "rows": out_rows, "trail": _trail(trail),
            "count": len(out_rows)}


def direct_reports(person: str) -> dict[str, Any]:
    """Everyone who reports to `person`, direct and indirect.

    Microsoft Graph's /users/{id}/directReports and its transitive form. Same
    edge as reports_to, opposite question — the report is the SOURCE, so this
    walks (dr)-[:REPORTS_TO*]->(person) and never a reversed arrow.
    """
    g = _graph()
    rows = g.query(REPORTS_DOWN, {"person": person}).result_set

    out_rows, trail = [], []
    for report, title, seniority, depth in rows:
        hops = int(depth)
        detail = "direct report" if hops == 1 else f"indirect report, {hops} levels down"
        if title:
            detail += f" — {title}"
        out_rows.append({
            "report": report, "title": title, "seniority": seniority,
            "hops": hops, "direct": hops == 1, "detail": detail,
        })
        trail.append({"type": "Person", "name": report, "detail": detail,
                      "date": "", "via_edge": "REPORTS_TO"})

    return {"person": person, "rows": out_rows, "trail": _trail(trail),
            "count": len(out_rows)}


def team_members(team: str) -> dict[str, Any]:
    """The roster of `team` — current AND departed — with role and tenure.

    Microsoft Graph's /groups/{id}/members. current_team answers "which team is
    this person in"; this answers the other direction, "who is in this team".
    Departed members stay in the rows (flagged, sorted after the current ones)
    because on this dataset the trap answers live there: the top payments
    expert is someone who left in April, and a roster that silently drops her
    hides exactly the tension the product is built to surface.
    """
    team = resolve_team(team)
    g = _graph()
    rows = g.query(TEAM_MEMBERS, {"team": team}).result_set

    members = []
    for person, title, seniority, role, since, valid_to in rows:
        current = not valid_to
        detail = f"{role or 'member'} since {since}" if current else f"left {valid_to}"
        if title:
            detail = f"{title}, {detail}"
        members.append((current, person, title, seniority, role, since,
                        valid_to, detail))

    # Current members first, then alphabetical — the order the rows are read in.
    members.sort(key=lambda m: (not m[0], m[1]))

    out_rows, trail = [], []
    for current, person, title, seniority, role, since, valid_to, detail in members:
        out_rows.append({
            "person": person, "title": title, "seniority": seniority,
            "role": role, "since": since, "valid_to": valid_to,
            "current": current, "detail": detail,
        })
        trail.append({"type": "Person", "name": person, "detail": detail,
                      "date": valid_to or since, "via_edge": "MEMBER_OF"})

    departed = sum(1 for m in out_rows if not m["current"])
    return {"team": team, "rows": out_rows, "trail": _trail(trail),
            "count": len(out_rows), "current": len(out_rows) - departed,
            "departed": departed}


def _collected(values: list[Any]) -> list[str]:
    """collect(DISTINCT x) can carry nulls from unmatched OPTIONAL MATCHes."""
    return sorted({v for v in (values or []) if v})


def search_messages(keyword: str) -> dict[str, Any]:
    """Chat messages mentioning a word, service or person — the leaf search.

    Two lookups feed one result, deduped by message id:

      1. Lexical — body CONTAINS keyword. Tried lower-cased as well as given,
         because the generator writes bodies in lower case and CONTAINS is
         case-sensitive; without the variant "Incidents" finds nothing while
         "incidents" finds everything.
      2. Structural — messages that MENTION the entity. This is the graph
         answer plain search cannot give: the asker types "payments service"
         and the MENTIONS edges know that means payments-gateway, so messages
         about it are found even where the body spells it differently.
    """
    g = _graph()
    keyword = (keyword or "").strip()

    variants = []
    for v in (keyword, keyword.lower()):
        if v and v not in variants:
            variants.append(v)

    by_id: dict[str, dict[str, Any]] = {}
    for v in variants:
        for mid, channel, author, ts, body, mentions in g.query(
                MESSAGES_BODY, {"kw": v}).result_set:
            if mid not in by_id:
                by_id[mid] = {
                    "id": mid, "channel": channel, "author": author, "ts": ts,
                    "body": body, "mentions": _collected(mentions),
                    "matched_via": "body",
                }

    # Structural pass: the keyword itself, plus whatever resolve_service maps it
    # onto ("the payments service" -> payments-gateway). An unresolvable
    # keyword still tries its literal name — resolving must never invent a
    # target, and a literal match is an honest lookup.
    entities = {keyword}
    resolved, _exact = resolve_service(keyword)
    if resolved:
        entities.add(resolved)
    for entity in sorted(entities):
        if not entity:
            continue
        for mid, channel, author, ts, body, mentions in g.query(
                MESSAGES_ENTITY, {"entity": entity}).result_set:
            if mid in by_id:
                by_id[mid]["matched_via"] = "body + mentions"
            else:
                by_id[mid] = {
                    "id": mid, "channel": channel, "author": author, "ts": ts,
                    "body": body, "mentions": _collected(mentions),
                    "matched_via": "mentions",
                }

    out_rows, trail = [], []
    for row in sorted(by_id.values(), key=lambda r: r["ts"] or "", reverse=True)[:20]:
        body = row["body"] or ""
        snippet = body[:70] + ("…" if len(body) > 70 else "")
        detail = f"{row['channel']}: {snippet} ({row['matched_via']})"
        out_rows.append({**row, "detail": detail})
        trail.append({"type": "Message", "name": row["id"], "detail": detail,
                      "date": row["ts"], "via_edge": "MENTIONS"})

    return {"keyword": keyword, "rows": out_rows, "trail": _trail(trail),
            "count": len(out_rows)}


def find_documents(keyword: str) -> dict[str, Any]:
    """Documents matching a word, kind or project — with freshness and citations.

    Microsoft Graph's drive-item search. The 200 Document nodes were reachable
    only as staleness rows or as decision evidence; there was no way to answer
    "is there a runbook for this?" Freshness rides along per row so the agent
    can flag a stale doc in the same breath it finds it (the payments-provider
    contradiction is the demo beat this tool is named on).
    """
    g = _graph()
    keyword = (keyword or "").strip()
    cutoff = _cutoff()

    variants = []
    for v in (keyword, keyword.lower()):
        if v and v not in variants:
            variants.append(v)

    by_name: dict[str, dict[str, Any]] = {}
    for v in variants:
        for name, kind, date, project, author, last, cited in g.query(
                DOCUMENTS_BY_KEYWORD, {"kw": v}).result_set:
            if name not in by_name:
                by_name[name] = {
                    "name": name, "kind": kind, "date": date, "project": project,
                    "author": author, "last_verified_at": last,
                    "cited_by": _collected(cited),
                }

    out_rows, trail = [], []
    for row in sorted(by_name.values(),
                      key=lambda r: r["date"] or "", reverse=True)[:15]:
        last = row["last_verified_at"]
        stale = bool(last and last < cutoff)
        detail = f"{row['kind']}, verified {last}" if last else str(row["kind"])
        if stale:
            detail += " [STALE]"
        if row["cited_by"]:
            detail += f", cited by {', '.join(row['cited_by'])}"
        out_rows.append({**row, "stale": stale, "detail": detail})
        trail.append({"type": "Document", "name": row["name"], "detail": detail,
                      "date": last or row["date"], "via_edge": "EVIDENCED_BY"})

    return {"keyword": keyword, "rows": out_rows, "trail": _trail(trail),
            "count": len(out_rows)}


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
    # Microsoft Graph parity surface — see section 5 above.
    "reports_to": reports_to,
    "direct_reports": direct_reports,
    "team_members": team_members,
    "search_messages": search_messages,
    "find_documents": find_documents,
}
