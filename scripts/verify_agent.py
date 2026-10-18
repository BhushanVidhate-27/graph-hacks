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
#
# `must` is an AND list — every entry has to be present. That is what makes it
# meaningful for the affirmative facts: "D-19" AND "supersed" both have to be
# there, because a model that says "D-14 is superseded" without naming D-19 has
# not answered "is D-14 STILL the current decision".
#
# The must-FAIL facts (16, 17, 19, 20) are a different assertion and cannot use
# it. Their real requirement is "the answer refuses", and refusal has many
# spellings — no answer can contain all of them at once. Those cases therefore
# carry ANY_OF instead, and both are matched as alternatives.
#
# Getting this wrong is not a rounding error, it is the gate lying in the
# direction that wastes a day. Measured on a live run, all four must-fail answers
# were correct and semantically complete refusals, and every one of them FAILED:
#
#   Q16 "The graph contains no OWNED_BY edge for config-service - meaning no
#        team (or person) is recorded as its owner."      -> matched 1 of 8
#   Q17 "The graph contains no decisions whose summary mentions pricing."
#                                                          -> matched 1 of 10
#   Q20 "The graph contains no SLA entry for dispute-service."
#                                                          -> matched 1 of 7
#
# Read as an AND list, those cases demand that every phrasing of "no" appear in
# one sentence. Widening the vocabulary cannot fix that — it makes it strictly
# harder, adding conjuncts. An earlier attempt at this gate did exactly that and
# the pass rate went DOWN. The fix is the matching rule, not the word list.
#
# The lists below are kept tight on purpose: each is the set of phrasings a
# correct refusal has actually been observed to use, not an open-ended thesaurus
# of words containing "no".
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
    (18, "Which services have zero dependents?",
     ["admin-bff", "settlement-batch"], []),
]

# fact -> (question, ANY_OF refusal markers, forbidden fabrication).
#
# `forbidden` is the part that does the real work. It is what would catch a
# confident invention ("Platform team owns config-service", "99.9%"), so the
# refusal marker only has to establish that the model did not invent — it is
# matched as OR because "no OWNED_BY edge", "no recorded owner" and "isn't owned
# by anyone" are three ways of saying one true thing.
ANY_OF: list[tuple[int, str, list[str], list[str]]] = [
    (16, "Who owns config-service?",
     ["no owned_by", "no owner", "no team owns", "does not exist",
      "no recorded owner", "not owned", "unowned", "no ownership"],
     ["Platform team owns config-service"]),
    (17, "What did checkout decide about pricing?",
     ["no decision", "not in the graph", "no :decision", "nothing",
      "not recorded", "no record", "does not contain", "no pricing decision"],
     ["they decided to change pricing"]),
    (19, "What team is Aisha Khan on now?",
     ["depart", "left", "no longer", "no current-team", "not recorded",
      "no current team", "no longer belongs", "no longer with"],
     ["Aisha Khan is on the Growth team"]),
    (20, "What is the SLA for dispute-service?",
     ["not in the graph", "no sla", "not recorded", "no sla is",
      "does not have an sla", "no recorded sla", "no contracted sla",
      "no sla entry", "no sla is recorded"],
     ["99.9", "99.95", "99.99"]),
]

FAILS: list[tuple] = []

# CASES is the ordered, numbered list the report prints. ANY_OF cases are folded
# back into it so there is exactly ONE ordered sequence of 20 questions and no
# risk of the two lists drifting apart on the fact numbers.
ORDERED: list[tuple[int, str, list[str], list[str], bool]] = sorted(
    [(f, q, m, x, True) for f, q, m, x in CASES]
    + [(f, q, m, x, False) for f, q, m, x in ANY_OF],
    key=lambda c: c[0],
)


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


# The model does not emit ASCII punctuation. A live run answered #18 with
# "admin<U+2011>bff, config<U+2011>service" — U+2011 NON-BREAKING HYPHEN, not
# U+002D. Substring-matching that against the ASCII needles in CASES() failed a
# fact the graph had already proven, which is the worst way for a gate to fail:
# it reads as a wrong answer and sends you hunting for a bug in the agent.
#
# NFKC does NOT fold U+2011 (it is not a compatibility equivalent of "-"), so
# normalise explicitly. This folds the dash/quote/space variants models actually
# emit, then lowercases. Substance is unchanged; only typography is.
_DASHES = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"), "-")
_QUOTES = {ord("\u2018"): "'", ord("\u2019"): "'", ord("\u201c"): '"', ord("\u201d"): '"'}
_SPACES = {ord("\u00a0"): " ", ord("\u2009"): " ", ord("\u202f"): " "}


def _norm(text: str) -> str:
    """Case- and typography-insensitive form for substring matching."""
    return text.translate(_DASHES).translate(_QUOTES).translate(_SPACES).lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    # 8080 is the port deploy/docker-compose.yml publishes and the one the
    # README tells people to open. It used to default to 8093, so running the
    # gate with no arguments failed all 20 questions with REQUEST FAILED and
    # looked like a total backend outage rather than a wrong default.
    ap.add_argument("--base-url", default="http://127.0.0.1:8080")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    print("=" * 96)
    print(f"B6 AT THE AGENT LAYER — {len(ORDERED)} questions via POST {base}/ask")
    print("=" * 96)

    for fact, question, must, forbidden, is_and in ORDERED:
        try:
            answer = ask(base, question)
        except Exception as exc:
            FAILS.append((fact, question, f"REQUEST FAILED: {exc}", ""))
            print(f"!! {fact:<3} {question[:44]:<46} REQUEST FAILED")
            continue

        low = _norm(answer)
        # `must` is matched as AND for the affirmative facts and OR for the
        # must-fail ones — see the note above ANY_OF. Getting the flag wrong
        # fails correct answers and, worse, makes a fabricated answer pass.
        matched = [m for m in must if _norm(m) in low]
        if is_and:
            missing = [m for m in must if _norm(m) not in low]
        else:
            missing = [] if matched else list(must)
        leaked = [f for f in forbidden if _norm(f) in low]
        ok = not missing and not leaked and bool(answer.strip())

        if ok:
            print(f"   {fact:<3} {question[:44]:<46} PASS")
        else:
            note = []
            if missing:
                note.append(
                    f"missing {missing}" if is_and
                    else f"no refusal marker; saw none of {must}"
                )
            if leaked:
                note.append(f"fabricated {leaked}")
            if not answer.strip():
                note.append("empty answer")
            FAILS.append((fact, question, answer.strip()[:220], "; ".join(note)))
            print(f"!! {fact:<3} {question[:44]:<46} FAIL")
            print(f"       answer: {answer.strip()[:200]}")
            print(f"       issue : {'; '.join(note)}")

    print("=" * 96)
    print(f"{len(ORDERED)} questions, {len(FAILS)} FAIL")
    print("=" * 96)
    if FAILS:
        print("\nGate 2 does NOT pass at the agent layer. Failures above.")
        return 1
    print("\nThe agent answers all 20 ground truths correctly over HTTP.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
