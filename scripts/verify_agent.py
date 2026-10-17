#!/usr/bin/env python3
"""
scripts/verify_agent.py — B6 at the AGENT layer.

scripts/verify.py proves app/graph.py is correct. It does NOT prove the agent
uses it correctly, and the agent is the thing being judged. Soham's own note
puts it plainly: "the Cypher can be right while the agent still answers wrong,
and the agent is the thing being judged."

So this asks all 20 GROUND_TRUTH questions through the running HTTP endpoint and
checks the ANSWER TEXT, not the underlying rows. A tool can return perfect rows
and the agent can still misreport them, invent a node, or flatly refuse.

Requires a server on --base-url with USE_MOCK=0 and a working model key.

Run:  python scripts/verify_agent.py [--base-url http://127.0.0.1:8093]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request

# (fact, question, [substrings that must ALL appear], [substrings that must appear NOWHERE])
CASES: list[tuple[int, str, list[str], list[str]]] = [
    (1, "Who owns payments-gateway today?",
     ["Ravi"], ["Priya is the owner"]),
    (2, "Who owns ledger-core?",
     ["Ledger"], []),
    (3, "Who owns fraud-scoring?",
     ["Risk"], []),
    (4, "Does every service have an owner?",
     ["config-service"], ["everyone has an owner", "all services have an owner"]),
    (5, "What breaks if payments-gateway dies?",
     ["checkout-api", "notifications"], []),
    (6, "Which of those are owned by a different team?",
     ["config-service"], []),
    (7, "Which dependent has no contributor in 90 days?",
     ["notifications"], []),
    (8, "Who has the most commits on payments-gateway?",
     ["Priya"], []),
    (9, "Who should I ask about the payments service?",
     ["Ravi"], []),
    (10, "Who has worked on both payments and ledger?",
     ["Ana"], []),
    (11, "Who is on call for Ledger this week?",
     ["Diego"], []),
    (12, "Where was the payments migration decided?",
     ["D-14"], []),
    (13, "Is D-14 still the current decision?",
     ["D-19", "supersed"], []),
    (14, "Who holds decision authority for payments and ledger?",
     ["Elena"], []),
    (15, "Is the provider evaluation document still accurate?",
     ["stale", "D-19"], []),
    (16, "Who owns config-service?",
     ["no owned_by", "no team owns", "does not exist", "no owner"],
     ["Platform team owns config-service"]),
    (17, "What did checkout decide about pricing?",
     ["no decision", "not in the graph", "no :decision", "nothing", "not recorded"],
     ["they decided to change pricing"]),
    (18, "Which services have zero dependents?",
     ["admin-bff", "settlement-batch"], []),
    (19, "What team is Aisha Khan on now?",
     ["depart", "left", "no longer"], ["Aisha Khan is on the Growth team"]),
    (20, "What is the SLA for dispute-service?",
     ["not in the graph", "no sla", "not recorded", "no sla is", "does not have an sla"],
     ["99.9", "99.95", "99.99"]),
]

FAILS: list[tuple] = []


def ask(base: str, question: str) -> str:
    req = urllib.request.Request(
        f"{base}/ask",
        data=json.dumps({"question": question}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    answer, buf = "", b""
    with urllib.request.urlopen(req, timeout=240) as resp:
        while chunk := resp.read(4096):
            buf += chunk
    for line in buf.decode(errors="replace").splitlines():
        if not line.startswith("data:"):
            continue
        try:
            payload = json.loads(line[5:].strip())
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("answer"):
            answer = payload["answer"]
    return answer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8093")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    print("=" * 96)
    print(f"B6 AT THE AGENT LAYER — 20 questions via POST {base}/ask")
    print("=" * 96)

    for fact, question, must, forbidden in CASES:
        try:
            answer = ask(base, question)
        except Exception as exc:
            FAILS.append((fact, question, f"REQUEST FAILED: {exc}", ""))
            print(f"!! {fact:<3} {question[:44]:<46} REQUEST FAILED")
            continue

        low = answer.lower()
        missing = [m for m in must if m.lower() not in low]
        leaked = [f for f in forbidden if f.lower() in low]
        ok = not missing and not leaked and bool(answer.strip())

        if ok:
            print(f"   {fact:<3} {question[:44]:<46} PASS")
        else:
            note = []
            if missing:
                note.append(f"missing {missing}")
            if leaked:
                note.append(f"fabricated {leaked}")
            if not answer.strip():
                note.append("empty answer")
            FAILS.append((fact, question, answer.strip()[:220], "; ".join(note)))
            print(f"!! {fact:<3} {question[:44]:<46} FAIL")
            print(f"       answer: {answer.strip()[:200]}")
            print(f"       issue : {'; '.join(note)}")

    print("=" * 96)
    print(f"{len(CASES)} questions, {len(FAILS)} FAIL")
    print("=" * 96)
    if FAILS:
        print("\nGate 2 does NOT pass at the agent layer. Failures above.")
        return 1
    print("\nThe agent answers all 20 ground truths correctly over HTTP.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
