#!/usr/bin/env python3
"""
scripts/verify.py — B6 ground-truth verification.

Asks all 20 GROUND_TRUTH questions through app/graph.py and compares each answer to
GROUND_TRUTH.md. Anything unconfirmable from those notes is a bug or a graph hole.

This is NOT the agent. It tests the Cypher directly. The agent layer is tested by
running the 20 questions through POST /ask, which is a separate pass.

Run:  python scripts/verify.py
Exit code 1 on any mismatch, so it can gate a commit.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import graph  # noqa: E402

RESULTS: list[tuple] = []


def check(fact: str, ok: bool, got: str, want: str) -> None:
    RESULTS.append((fact, "PASS" if ok else "FAIL", got, want))


def main() -> int:
    # ---- 1-4 ownership -------------------------------------------------
    d21 = graph.provenance("payments-migration")["rows"]
    reassign = [r for r in d21 if r["id"] == "D-21"]
    check("1  payments-gateway owner today",
          bool(reassign) and "Ravi Menon" in reassign[0]["summary"],
          reassign[0]["summary"] if reassign else "no D-21",
          "Ravi Menon (Platform); Priya until 2026-04-15")

    led = graph.owner_of("ledger-core")["rows"]
    check("2  ledger-core owner",
          bool(led) and led[0]["team"] == "Ledger",
          str(led), "Ledger team, lead Ana Duarte")

    fr = graph.owner_of("fraud-scoring")["rows"]
    check("3  fraud-scoring owner",
          bool(fr) and fr[0]["team"] == "Risk",
          str(fr), "Risk team, Diego Alvarez")

    cfg = graph.owner_of("config-service")
    check("4  every service owned?",
          cfg["count"] == 0 and not cfg["trail"],
          f"count={cfg['count']} trail={cfg['trail']}",
          "config-service has NO :OWNED_BY edge")

    # ---- 5-7 blast radius ---------------------------------------------
    br = graph.blast_radius("payments-gateway")
    names = sorted(r["service"] for r in br["rows"])
    want5 = sorted(["checkout-api", "config-service", "dispute-service",
                    "mobile-bff", "notifications", "webhook-relay",
                    "fraud-scoring", "recommendation"])
    check("5  blast radius", names == want5,
          f"{len(names)}: {names}", f"{len(want5)}: {want5}")
    check("5a upstream excluded",
          not ({"ledger-core", "settlement-batch"} & set(names)),
          "ledger-core/settlement-batch absent", "must NOT appear (upstream)")

    cross = [r["service"] for r in br["rows"] if r["cross_team"]]
    check("6  cross-team dependents",
          sorted(cross) == sorted(["checkout-api", "mobile-bff", "dispute-service",
                                   "notifications", "recommendation", "fraud-scoring"]),
          str(sorted(cross)), "6 across Payments/Growth/Risk + config-service unowned")

    # fact 7: which dependent has no contributor in 90 days
    svc_proj = graph._graph().query(
        "MATCH (p:Project)-[:USES]->(s:Service) RETURN s.name AS s, p.name AS p").result_set
    proj_of = {}
    for s, p in svc_proj:
        proj_of.setdefault(s, set()).add(p)
    fresh = graph._graph().query(
        "MATCH (p:Person)-[c:CONTRIBUTED_TO]->(proj) "
        "WHERE c.last_touch >= '2026-07-19' RETURN DISTINCT proj.name AS p").result_set
    fresh_p = {r[0] for r in fresh}
    stale = sorted(s for s in names if not (proj_of.get(s, set()) & fresh_p))
    check("7  dependent with no 90d contributor", stale == ["notifications"],
          str(stale), "exactly ['notifications']")

    # ---- 8-11 expertise -------------------------------------------------
    ex = graph.expertise("payments-gateway")["rows"]
    top = [r for r in ex if r.get("person") == "Priya Sharma"]
    check("8  most commits but stale",
          bool(top) and top[0]["commits"] == 14 and top[0]["stale"] is True,
          f"{top[0]['commits']} commits, last {top[0]['latest']}, stale={top[0]['stale']}"
          if top else "absent",
          "Priya Sharma, 14 commits, last touch 2026-04-15, STALE")

    ravi = [r for r in ex if r.get("person") == "Ravi Menon"]
    check("9  best person to ask now",
          bool(ravi) and ravi[0]["stale"] is False,
          f"{ravi[0]['commits']} commits, last {ravi[0]['latest']}" if ravi else "absent",
          "Ravi Menon (current, not stale)")

    both = graph._graph().query(
        "MATCH (a:Person)-[:CONTRIBUTED_TO]->(p1:Project)-[:USES]->(s1:Service {name:'payments-gateway'})"
        " MATCH (a)-[:CONTRIBUTED_TO]->(p2:Project)-[:USES]->(s2:Service {name:'ledger-core'})"
        " RETURN DISTINCT a.name AS a").result_set
    spans = sorted(r[0] for r in both)
    check("10 worked on both payments+ledger", spans == ["Ana Duarte"],
          str(spans), "Ana Duarte only")

    oc = graph.on_call("Ledger")
    on_now = sorted(r["person"] for r in oc["rows"] if r["on_call"])
    not_on = sorted(r["person"] for r in oc["rows"] if not r["on_call"])
    check("11 on call for Ledger this week", on_now == ["Diego Alvarez"],
          f"on_call={on_now}, rotation-not-on-call={not_on}",
          "Diego Alvarez on call; Ravi on rotation only; Priya on no rotation")

    # ---- 12-15 provenance ------------------------------------------------
    prov = graph.provenance("payments-migration")["rows"]
    d14 = [r for r in prov if r["id"] == "D-14"]
    d19 = [r for r in prov if r["id"] == "D-19"]
    check("12 where migration decided",
          bool(d14) and d14[0]["date"] == "2026-03-18"
          and "payments-provider-eval-v3.md" in d14[0]["evidence"],
          f"D-14 {d14[0]['date']} evidence={d14[0]['evidence']}" if d14 else "absent",
          "D-14 2026-03-18 Elena Vasquez, evidence payments-provider-eval-v3.md")

    check("13 D-14 superseded by D-19",
          bool(d19) and d19[0]["superseded_by"] == "D-14",
          f"D-19 supersedes {d19[0]['superseded_by']}" if d19 else "absent",
          "D-19 (2026-05-06) supersedes D-14, Adyen primary")

    authors = graph._graph().query(
        "MATCH (d:Decision) RETURN DISTINCT d.author AS a").result_set
    au = sorted(r[0] for r in authors)
    check("14 decision authority", au == ["Elena Vasquez"],
          str(au), "Elena Vasquez only")

    st = graph.staleness()["rows"]
    stale_doc = [r for r in st if r.get("name") == "payments-provider-eval-v3.md"]
    check("15 planted contradiction flagged",
          bool(stale_doc),
          stale_doc[0]["reason"] if stale_doc else "not flagged stale",
          "v3 doc cited by D-14 but D-19 supersedes it; doc is stale")

    # ---- 16-20 must fail correctly ---------------------------------------
    o = graph.owner_of("config-service")
    check("16 must-fail: config-service owner",
          o["count"] == 0 and o["trail"] == [],
          f"count={o['count']}", "no rows, no trail -> agent must say so")

    p = graph.decisions_about("pricing")
    check("17 must-fail: pricing decision", p["count"] == 0,
          f"count={p['count']}", "0 decisions containing 'pricing'")

    zd = graph.zero_dependents()
    check("18 zero dependents", zd["count"] == 10,
          f"count={zd['count']}", "10 services")

    ak = graph.current_team("Aisha Khan")
    check("19 Aisha Khan current team",
          ak["count"] == 0 and bool(ak["departed"]),
          f"current={ak['rows']} departed={ak['departed']}",
          "departed 2026-06-30, never current")

    sla = graph.sla_of("dispute-service")
    check("20 must-fail: dispute-service SLA", sla["count"] == 0,
          f"count={sla['count']} rows={sla['rows']}",
          "0 -> agent must say 'not in the graph'")

    # ---- report -----------------------------------------------------------
    print("=" * 96)
    print("B6 GROUND-TRUTH VERIFICATION — 20 facts against the LOADED graph")
    print("=" * 96)
    for fact, res, got, want in RESULTS:
        mark = "  " if res == "PASS" else "!!"
        print(f"{mark} {fact:<42} {res}")
        if res == "FAIL":
            print(f"       got:  {got}")
            print(f"       want: {want}")
    fails = sum(1 for r in RESULTS if r[1] == "FAIL")
    print("=" * 96)
    print(f"{len(RESULTS)} checks, {fails} FAIL")
    print("=" * 96)
    if fails:
        print("\nGate 2 cannot pass. Fix the graph, do not paper over it.")
        return 1
    print("\nAll 20 ground truths confirmed against the live graph.")
    print("Remaining: run the same 20 questions through POST /ask (agent layer).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
