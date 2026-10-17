#!/usr/bin/env python3
"""
scripts/load.py — load data/*.csv into FalkorDB.

VERIFIED FalkorDB constraints (do not rediscover these):
  - g.query(cypher, params).result_set   <- .result_set is REQUIRED, query() is not
    iterable. `for row in g.query(...)` raises TypeError.
  - FalkorDB is a SUBSET of OpenCypher. No Neo4j-only syntax.
  - Cypher CANNOT traverse an edge backwards, so DEPENDS_ON is emitted from the CSV
    and HAS_DEPENDENT is derived here. Missing the inverse makes blast_radius
    silently return [] rather than raising.

Rules this loader follows:
  - Indexes created BEFORE bulk load.
  - Batched UNWIND, every batch passed as a parameter. Never interpolate values.
  - Node passes and relationship passes are SEPARATE: an edge cannot be created
    before both endpoints exist.
  - Every node type wrapped in its own try/except. A partial load that looks
    successful is worse than a loud failure.
  - Counts printed per label and asserted against the CSV row counts.

Run:  python scripts/load.py
"""

from __future__ import annotations

import csv
import os
import sys
import time
from collections import defaultdict

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

GRAPH = os.getenv("FALKORDB_GRAPH", "helio")
HOST = os.getenv("FALKORDB_HOST", "localhost")
PORT = int(os.getenv("FALKORDB_PORT", "6379"))

BATCH = 500

FAILURES: list[str] = []


def read_csv(name):
    with open(os.path.join(DATA, name)) as fh:
        return list(csv.DictReader(fh))


def rows(name):
    return read_csv(name)


def batches(seq, size=BATCH):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def to_int(v, default=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def main():
    db = FalkorDB(host=HOST, port=PORT)
    g = db.select_graph(GRAPH)

    t0 = time.time()

    # ------------------------------------------------------------------
    # 0. Delete the graph first. Loading twice into a dirty graph makes
    #    every count wrong and every answer quietly incorrect.
    # ------------------------------------------------------------------
    print(f"Dropping graph '{GRAPH}' if it exists (dirty-graph trap)...")
    try:
        g.query(f"GRAPH.DELETE {GRAPH}")
    except Exception:
        pass  # absent graph is fine
    try:
        g.query("DELETE helio")
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 1. Indexes BEFORE bulk load
    # ------------------------------------------------------------------
    print("Creating indexes...")
    for stmt in [
        "CREATE INDEX ON :Service(name)",
        "CREATE INDEX ON :Person(name)",
        "CREATE INDEX ON :Project(name)",
        "CREATE INDEX ON :Decision(id)",
        "CREATE INDEX ON :Document(name)",
        "CREATE INDEX ON :Message(id)",
    ]:
        try:
            g.query(stmt)
        except Exception as exc:
            # "Attribute 'name' is already indexed" is benign on a re-load.
            msg = str(exc).lower()
            if "already indexed" not in msg and "exist" not in msg:
                FAILURES.append(f"index {stmt}: {exc}")
    print("  indexes ok")

    # ------------------------------------------------------------------
    # 2. NODE PASSES
    # ------------------------------------------------------------------
    def load_nodes(label, csv_name, cypher, rowmap):
        data = rows(csv_name)
        recs = [rowmap(r) for r in data]
        n = 0
        try:
            for chunk in batches(recs):
                g.query(cypher, {"rows": chunk})
                n += len(chunk)
            print(f"  {label:<10} {n:>6} rows")
            return n
        except Exception as exc:
            FAILURES.append(f"{label}: {exc}")
            print(f"  {label:<10} FAILED after {n} rows -> {exc}")
            return n

    print("Loading nodes...")

    n_teams = load_nodes(
        "Team", "teams.csv",
        "UNWIND $rows AS row MERGE (t:Team {name: row.name}) SET t.description = row.description",
        lambda r: {"name": r["name"], "description": r["description"]})

    n_people = load_nodes(
        "Person", "people.csv",
        "UNWIND $rows AS row MERGE (p:Person {name: row.name}) "
        "SET p.email = row.email, p.title = row.title, "
        "p.seniority = row.seniority, p.is_member = row.is_member",
        lambda r: {"name": r["name"], "email": r["email"], "title": r["title"],
                   "seniority": r["seniority"], "is_member": to_int(r["is_member"], 0)})

    # :Member is a SECOND LABEL on the Person node, not a separate node type.
    # blast_radius traverses (:Team)-[:HAS_ROTATION]->(:Member)-[:ON_CALL]->(:Person)
    # and returns [] silently if this label is missing.
    try:
        members = [r["member"] for r in rows("rotations.csv")]
        uniq = sorted(set(members))
        for chunk in batches(uniq):
            g.query("UNWIND $rows AS row MATCH (p:Person {name: row.name}) SET p:Member",
                    {"rows": [{"name": m} for m in chunk]})
        print(f"  {'Member':<10} {len(uniq):>6} labelled (:Person:Member)")
    except Exception as exc:
        FAILURES.append(f"Member label: {exc}")

    n_projects = load_nodes(
        "Project", "projects.csv",
        "UNWIND $rows AS row MERGE (p:Project {name: row.name}) "
        "SET p.team = row.team, p.status = row.status, p.started_at = row.started_at",
        lambda r: {"name": r["name"], "team": r["team"], "status": r["status"],
                   "started_at": r["started_at"]})

    n_services = load_nodes(
        "Service", "services.csv",
        "UNWIND $rows AS row MERGE (s:Service {name: row.name}) "
        "SET s.team = row.team, s.tier = row.tier, s.sla = row.sla, "
        "s.last_verified_at = row.last_verified_at",
        lambda r: {"name": r["name"], "team": r["team"], "tier": r["tier"],
                   "sla": r["sla"], "last_verified_at": r["last_verified_at"]})

    n_decisions = load_nodes(
        "Decision", "decisions.csv",
        "UNWIND $rows AS row MERGE (d:Decision {id: row.id}) "
        "SET d.summary = row.summary, d.date = row.date, d.author = row.author, "
        "d.project = row.project, d.status = row.status",
        lambda r: {"id": r["id"], "summary": r["summary"], "date": r["date"],
                   "author": r["author"], "project": r["project"],
                   "status": r["status"], "supersedes": r["supersedes"]})

    n_docs = load_nodes(
        "Document", "documents.csv",
        "UNWIND $rows AS row MERGE (d:Document {name: row.name}) "
        "SET d.kind = row.kind, d.date = row.date, d.author = row.author, "
        "d.project = row.project, d.last_verified_at = row.last_verified_at",
        lambda r: {"name": r["name"], "kind": r["kind"], "date": r["date"],
                   "author": r["author"], "project": r["project"],
                   "last_verified_at": r["last_verified_at"]})

    n_msgs = load_nodes(
        "Message", "messages.csv",
        "UNWIND $rows AS row MERGE (m:Message {id: row.id}) "
        "SET m.channel = row.channel, m.author = row.author, "
        "m.ts = row.ts, m.body = row.body",
        lambda r: {"id": r["id"], "channel": r["channel"], "author": r["author"],
                   "ts": r["ts"], "body": r["body"]})

    # ------------------------------------------------------------------
    # 3. RELATIONSHIP PASSES — separate, after every node exists
    # ------------------------------------------------------------------
    def load_rels(name, cypher, recs, quiet=False):
        n = 0
        try:
            for chunk in batches(recs):
                g.query(cypher, {"rows": chunk})
                n += len(chunk)
            if not quiet:
                print(f"  {name:<22} {n:>6} rows")
            return n
        except Exception as exc:
            FAILURES.append(f"{name}: {exc}")
            print(f"  {name:<22} FAILED after {n} rows -> {exc}")
            return n

    print("Loading relationships...")

    load_rels("MEMBER_OF",
              "UNWIND $rows AS row MATCH (p:Person {name: row.person}) "
              "MATCH (t:Team {name: row.team}) MERGE (p)-[r:MEMBER_OF]->(t) "
              "SET r.since = row.since, r.role = row.role, r.valid_to = row.valid_to",
              [{"person": r["person"], "team": r["team"], "since": r["since"],
                "role": r["role"], "valid_to": r["valid_to"]} for r in rows("person_team.csv")])

    load_rels("REPORTS_TO",
              "UNWIND $rows AS row MATCH (p:Person {name: row.person}) "
              "MATCH (m:Person {name: row.manager}) MERGE (p)-[:REPORTS_TO]->(m)",
              [{"person": r["person"], "manager": r["manager"]} for r in rows("reports_to.csv")])

    # config-service has team='' -> it gets NO OWNED_BY edge. That absence is fact 4
    # and fact 16; giving it an owner here silently kills two must-fail questions.
    own = [{"service": r["name"], "team": r["team"]}
           for r in rows("services.csv") if r["team"]]
    load_rels("OWNED_BY",
              "UNWIND $rows AS row MATCH (s:Service {name: row.service}) "
              "MATCH (t:Team {name: row.team}) MERGE (s)-[:OWNED_BY]->(t)",
              own)

    deps = [{"service": r["service"], "depends_on": r["depends_on"]}
            for r in rows("service_deps.csv")]
    load_rels("DEPENDS_ON",
              "UNWIND $rows AS row MATCH (a:Service {name: row.service}) "
              "MATCH (b:Service {name: row.depends_on}) MERGE (a)-[:DEPENDS_ON]->(b)",
              deps)

    # THE INVERSE EDGE. service_deps.csv holds ONE directed row; the inverse is
    # derived here and must never be written into the CSV. Omit this and the
    # blast-radius query returns [] with no error.
    load_rels("HAS_DEPENDENT",
              "UNWIND $rows AS row MATCH (a:Service {name: row.service}) "
              "MATCH (b:Service {name: row.depends_on}) MERGE (b)-[:HAS_DEPENDENT]->(a)",
              deps)

    load_rels("USES",
              "UNWIND $rows AS row MATCH (p:Project {name: row.project}) "
              "MATCH (s:Service {name: row.service}) MERGE (p)-[:USES]->(s)",
              [{"project": r["project"], "service": r["service"]}
               for r in rows("project_services.csv")])

    load_rels("CONTRIBUTED_TO",
              "UNWIND $rows AS row MATCH (p:Person {name: row.person}) "
              "MATCH (pr:Project {name: row.project}) MERGE (p)-[c:CONTRIBUTED_TO]->(pr) "
              "SET c.role = row.role, c.commits = row.commits, "
              "c.last_touch = row.last_touch, c.last_verified_at = row.last_verified_at",
              [{"person": r["person"], "project": r["project"], "role": r["role"],
                "commits": to_int(r["commits"], 0), "last_touch": r["last_touch"],
                "last_verified_at": r["last_verified_at"]} for r in rows("contributions.csv")])

    load_rels("HAS_ROTATION",
              "UNWIND $rows AS row MATCH (t:Team {name: row.team}) "
              "MATCH (m:Person:Member {name: row.member}) MERGE (t)-[h:HAS_ROTATION]->(m) "
              "SET h.since = row.since",
              [{"team": r["team"], "member": r["member"], "since": r["since"]}
               for r in rows("rotations.csv")])

    # ON_CALL is dated and points back at the Team. Rotation membership and being
    # on call are different facts (GROUND_TRUTH addendum 2026-10-17).
    # on_call_week is stamped HERE, by the loader, so the answer is deterministic
    # and re-running the generator cannot change who is on call.
    load_rels("ON_CALL",
              "UNWIND $rows AS row MATCH (m:Person:Member {name: row.member}) "
              "MATCH (t:Team {name: row.team}) MERGE (m)-[o:ON_CALL]->(t) "
              "SET o.week_start = row.week_start, o.week_end = row.week_end, "
              "o.on_call_week = row.week_start",
              [{"member": r["member"], "team": r["team"], "week_start": r["week_start"],
                "week_end": r["week_end"]} for r in rows("on_call.csv")])

    load_rels("ABOUT",
              "UNWIND $rows AS row MATCH (d:Decision {id: row.id}) "
              "MATCH (p:Project {name: row.project}) MERGE (d)-[:ABOUT]->(p)",
              [{"id": r["id"], "project": r["project"]} for r in rows("decisions.csv")
               if r["project"]])

    load_rels("SUPERSEDES",
              "UNWIND $rows AS row MATCH (d:Decision {id: row.id}) "
              "MATCH (p:Decision {id: row.supersedes}) MERGE (d)-[:SUPERSEDES]->(p)",
              [{"id": r["id"], "supersedes": r["supersedes"]} for r in rows("decisions.csv")
               if r["supersedes"]])

    # EVIDENCED_BY points at either a Document (by name) or a Message (by id).
    ev = rows("decision_evidence.csv")
    load_rels("EVIDENCED_BY doc",
              "UNWIND $rows AS row MATCH (d:Decision {id: row.decision}) "
              "MATCH (e:Document {name: row.evidence_ref}) MERGE (d)-[:EVIDENCED_BY]->(e)",
              [{"decision": r["decision"], "evidence_ref": r["evidence_ref"]}
               for r in ev if r["evidence_type"] == "document"])

    ev_msg = [r for r in ev if r["evidence_type"] == "message"]
    msg_index = {m["id"]: m for m in rows("messages.csv")}
    msg_by_date_channel = defaultdict(list)
    for m in rows("messages.csv"):
        msg_by_date_channel[(m["channel"], m["ts"])].append(m)

    ev_msg_recs = []
    for r in ev_msg:
        ref = r["evidence_ref"]              # "#inc-payments:2026-03-18"
        chan, _, day = ref.partition(":")
        for m in msg_by_date_channel.get((chan, day), [])[:1]:
            ev_msg_recs.append({"decision": r["decision"], "mid": m["id"]})
    load_rels("EVIDENCED_BY msg",
              "UNWIND $rows AS row MATCH (d:Decision {id: row.decision}) "
              "MATCH (e:Message {id: row.mid}) MERGE (d)-[:EVIDENCED_BY]->(e)",
              ev_msg_recs, quiet=not ev_msg_recs)
    if ev_msg_recs:
        print(f"  {'EVIDENCED_BY msg':<22} {len(ev_msg_recs):>6} rows")

    load_rels("AUTHORED_BY (doc)",
              "UNWIND $rows AS row MATCH (d:Document {name: row.name}) "
              "MATCH (p:Person {name: row.author}) MERGE (d)-[:AUTHORED_BY]->(p)",
              [{"name": r["name"], "author": r["author"]} for r in rows("documents.csv")
               if r["author"]])

    load_rels("AUTHORED_BY (msg)",
              "UNWIND $rows AS row MATCH (m:Message {id: row.id}) "
              "MATCH (p:Person {name: row.author}) MERGE (m)-[:AUTHORED_BY]->(p)",
              [{"id": r["id"], "author": r["author"]} for r in rows("messages.csv")
               if r["author"]])

    label_for = {"Service": "Service", "Person": "Person", "Project": "Project",
                 "Decision": "Decision"}
    for etype in ("Service", "Person", "Project", "Decision"):
        recs = [{"mid": r["message_id"], "name": r["entity_name"]}
                for r in rows("message_mentions.csv") if r["entity_type"] == etype]
        if recs:
            load_rels(f"MENTIONS {etype}",
                      f"UNWIND $rows AS row MATCH (m:Message {{id: row.mid}}) "
                      f"MATCH (e:{label_for[etype]} {{name: row.name}}) "
                      f"MERGE (m)-[:MENTIONS]->(e)",
                      recs)

    # ------------------------------------------------------------------
    # 4. VERIFY — counts per label, asserted against the CSVs
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("LOAD VERIFICATION")
    print("=" * 70)

    expected = {
        "Team": n_teams, "Person": n_people, "Project": n_projects,
        "Service": n_services, "Decision": n_decisions, "Document": n_docs,
        "Message": n_msgs,
    }
    bad = []
    for label, exp in expected.items():
        got = g.query(f"MATCH (n:{label}) RETURN count(n) AS c").result_set[0][0]
        flag = "OK " if got == exp else "MISMATCH"
        if got != exp:
            bad.append((label, exp, got))
        print(f"  {label:<10} csv={exp:<6} graph={got:<6} {flag}")

    print("-" * 70)
    edge_expect = {
        "DEPENDS_ON": len(deps),
        "HAS_DEPENDENT": len(deps),
        "OWNED_BY": len(own),
        "CONTRIBUTED_TO": len(rows("contributions.csv")),
        "MEMBER_OF": len(rows("person_team.csv")),
        "USES": len(rows("project_services.csv")),
    }
    for etype, exp in edge_expect.items():
        got = g.query(f"MATCH ()-[r:{etype}]->() RETURN count(r) AS c").result_set[0][0]
        flag = "OK " if got == exp else "MISMATCH"
        if got != exp:
            bad.append((etype, exp, got))
        print(f"  {etype:<18} csv={exp:<6} graph={got:<6} {flag}")

    print("=" * 70)
    print(f"Loaded in {time.time() - t0:.1f}s")

    # The must-fail facts, checked against the LIVE graph rather than the CSVs.
    # If these are wrong, every downstream answer is wrong and nothing else tells you.
    print("\nMust-fail invariants (live graph):")
    cfg = g.query("MATCH (s:Service {name:'config-service'})-[:OWNED_BY]->() RETURN count(s) AS c"
                  ).result_set[0][0]
    print(f"  config-service OWNED_BY edges : {cfg}  (must be 0)")
    sla = g.query("MATCH (s:Service {name:'dispute-service'}) RETURN s.sla AS sla"
                  ).result_set[0][0]
    print(f"  dispute-service sla           : {sla!r}  (must be empty)")
    price = g.query("MATCH (d:Decision) WHERE d.summary CONTAINS 'pricing' "
                    "RETURN count(d) AS c").result_set[0][0]
    print(f"  decisions containing 'pricing': {price}  (must be 0)")
    members = g.query("MATCH (p:Person:Member) RETURN count(p) AS c").result_set[0][0]
    print(f"  (:Person:Member) count        : {members}")

    problems = bad or FAILURES
    if problems:
        print("\n!! LOAD PROBLEMS")
        for p in problems:
            print("   -", p)
        sys.exit(1)

    print("\nOK. Graph loaded and verified.")


if __name__ == "__main__":
    main()
