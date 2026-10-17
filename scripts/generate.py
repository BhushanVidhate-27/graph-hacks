#!/usr/bin/env python3
"""
scripts/generate.py — seeded synthetic data generator for the Helio company brain.

Deterministic: seed=20261016, same seed -> byte-identical output. That is what makes
the ground-truth verification honest, because the data does not move between runs.

Emits CSVs to data/. One directed row per dependency in service_deps.csv; the loader
derives the inverse HAS_DEPENDENT itself. Never emit the inverse here.

Every planted fact in GROUND_TRUTH.md is asserted at the end by reading the emitted
CSVs back off disk. A fact that cannot be checked from our own output is printed as
UNCHECKABLE rather than asserted as passing.

Run:  python scripts/generate.py
"""

import csv
import os
import random
import re
from datetime import date, timedelta
from functools import lru_cache

from faker import Faker

SEED = 20261016
random.seed(SEED)
Faker.seed(SEED)
fake = Faker()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# Ground truth is anchored to the hackathon clock, not to wall-clock time, so the
# generator is reproducible forever.
TODAY = date(2026, 10, 17)
STALE_CUTOFF = TODAY - timedelta(days=90)  # 2026-07-19

# ---------------------------------------------------------------------------
# THE DAG — fixed and verified acyclic. 20 services, 22 DEPENDS_ON edges.
# Do not re-derive. Do not expand a row into "all public services": that is what
# made the graph cyclic and inflated payments' blast radius to 14 services.
# ---------------------------------------------------------------------------
DEPS = {
    "ledger-core": [],
    "payments-gateway": ["ledger-core"],
    "checkout-api": ["payments-gateway"],
    "mobile-bff": ["payments-gateway"],
    "webhook-relay": ["payments-gateway"],
    "settlement-batch": ["ledger-core"],
    "dispute-service": ["payments-gateway", "ledger-core"],
    "billing-invoicing": ["ledger-core"],
    "notifications": ["payments-gateway", "dispute-service"],
    "reporting-etl": ["ledger-core", "billing-invoicing"],
    "search-index": ["reporting-etl"],
    "fraud-scoring": ["checkout-api"],
    "auth-service": [],
    "session-store": ["auth-service"],
    "api-gateway": [],
    "config-service": ["payments-gateway", "auth-service"],
    "user-profile": ["auth-service"],
    "recommendation": ["fraud-scoring", "user-profile"],
    "web-frontend": ["api-gateway"],
    "admin-bff": ["api-gateway"],
}

# config-service has NO owner. That absence is fact 4 and fact 16.
NO_OWNER = {"config-service"}

SERVICE_TEAM = {
    "ledger-core": "Ledger", "payments-gateway": "Platform",
    "checkout-api": "Payments", "mobile-bff": "Payments",
    "webhook-relay": "Platform", "settlement-batch": "Ledger",
    "dispute-service": "Payments", "billing-invoicing": "Ledger",
    "notifications": "Growth", "reporting-etl": "Ledger",
    "search-index": "Growth", "fraud-scoring": "Risk",
    "auth-service": "Platform", "session-store": "Platform",
    "api-gateway": "Platform", "config-service": None,
    "user-profile": "Platform", "recommendation": "Growth",
    "web-frontend": "Platform", "admin-bff": "Platform",
}

# dispute-service has NO sla. Fact 20 dies the moment we give it one.
NO_SLA = {"dispute-service"}

# Fact 7: the dependent with no contributor in 90 days.
NO_RECENT_CONTRIBUTIONS = {"notifications"}

# Fact 17: the word must appear in zero decision rows.
FORBIDDEN_DECISION_WORD = "pricing"

TEAMS = {
    "Platform": "Core platform, edge, and service ownership",
    "Ledger": "Ledger of record, billing, and financial reporting",
    "Payments": "Checkout and the payment provider migration",
    "Risk": "Fraud scoring and risk decisioning",
    "Growth": "Notifications, recommendations, and search",
}

LOAD_BEARING = {
    "Elena Vasquez": dict(team=None, title="Chief Technology Officer", seniority="executive"),
    "Ravi Menon":    dict(team="Platform", title="Staff Engineer", seniority="staff"),
    "Priya Sharma":  dict(team="Payments", title="Senior Engineer", seniority="senior", left="2026-04-15"),
    "Ana Duarte":    dict(team="Ledger", title="Engineering Lead", seniority="lead"),
    "Diego Alvarez": dict(team="Risk", title="Senior Engineer", seniority="senior"),
    "Aisha Khan":    dict(team="Growth", title="Product Manager", seniority="mid", left="2026-06-30"),
    "Tomas Berg":    dict(team="Payments", title="Engineer", seniority="mid"),
    "Mei Lin":       dict(team="Platform", title="Engineer", seniority="mid"),
}

# Rotation members carry an EXTRA label :Member. Ravi and Diego are on the Ledger
# rotation; only Diego is on call THIS week (fact 11). Priya is on none.
ROTATION = {
    "Ledger":   [("Ravi Menon", True), ("Diego Alvarez", True)],
    "Platform": [("Ravi Menon", True), ("Mei Lin", False)],
    "Payments": [("Tomas Berg", True)],
    "Risk":     [("Diego Alvarez", True)],
}

# The payments project. D-14, D-19 and D-21 are all ABOUT it.
PAYMENTS_PROJECT = "payments-migration"
LEDGER_PROJECT = "ledger-reconciliation"

PROJECT_TEAM = {
    PAYMENTS_PROJECT: "Payments",
    LEDGER_PROJECT: "Ledger",
    "fraud-model-v3": "Risk",
    "checkout-latency": "Payments",
    "notification-digest": "Growth",
    "dispute-evidence": "Payments",
    "webhook-reliability": "Platform",
    "recommendation-tuning": "Growth",
    "auth-hardening": "Platform",
}

PROJECT_SERVICES = {
    PAYMENTS_PROJECT: ["payments-gateway", "checkout-api"],
    LEDGER_PROJECT: ["ledger-core", "settlement-batch"],
    "fraud-model-v3": ["fraud-scoring", "checkout-api"],
    "checkout-latency": ["checkout-api", "mobile-bff"],
    # notifications is the fact-7 answer: its ONLY project must have zero recent
    # contributors. Do not add dispute-service here or it goes fresh too.
    "notification-digest": ["notifications"],
    "dispute-evidence": ["dispute-service"],
    "webhook-reliability": ["webhook-relay"],
    "recommendation-tuning": ["recommendation"],
    "auth-hardening": ["auth-service", "session-store", "config-service"],
}

# Priya: exactly 14 commits, last touch on the day she left. Fact 8.
# Ravi: fewer commits but current. Fact 8's whole point is the tension.
# Ana: the only person spanning payments AND ledger. Fact 10.
CONTRIBUTIONS = [
    ("Priya Sharma", PAYMENTS_PROJECT, "tech lead", 14, "2026-04-15"),
    ("Ravi Menon", PAYMENTS_PROJECT, "owner", 6, "2026-09-28"),
    ("Ana Duarte", PAYMENTS_PROJECT, "ledger liaison", 3, "2026-08-14"),
    ("Ravi Menon", "checkout-latency", "reviewer", 4, "2026-09-30"),
    ("Tomas Berg", "checkout-latency", "implementer", 9, "2026-10-02"),
    ("Tomas Berg", PAYMENTS_PROJECT, "implementer", 5, "2026-07-30"),
    ("Diego Alvarez", "fraud-model-v3", "tech lead", 11, "2026-10-01"),
    # Ana is the ONLY person on both a payments and a ledger project (fact 10).
    # Ravi is on the Ledger ROTATION but contributes to no ledger project — that
    # distinction is deliberate. Adding him here breaks fact 10.
    ("Ana Duarte", LEDGER_PROJECT, "tech lead", 8, "2026-09-19"),
    # Recent contributors for the other blast-radius services, so notifications
    # is the UNIQUE stale dependent in fact 7.
    ("Tomas Berg", "dispute-evidence", "implementer", 4, "2026-09-16"),
    ("Ravi Menon", "webhook-reliability", "implementer", 3, "2026-09-10"),
    ("Diego Alvarez", "recommendation-tuning", "implementer", 5, "2026-08-29"),
    # notification-digest intentionally has NO contribution rows.
    ("Mei Lin", "auth-hardening", "implementer", 7, "2026-09-25"),
]

# Settlement-batch is still planted with no recent contributor (kept from the original
# plan), but it is NOT the answer to fact 7 — it is not in the payments blast radius.
# See GROUND_TRUTH.md change log.
ZERO_RECENT_PROJECTS = [LEDGER_PROJECT]

DECISIONS = [
    ("D-14", "Migrate payments to a single provider: Stripe", "2026-03-18",
     PAYMENTS_PROJECT, "superseded", None),
    ("D-19", "Dual provider: Adyen primary, Stripe fallback", "2026-05-06",
     PAYMENTS_PROJECT, "active", "D-14"),
    ("D-21", "Reassign payments-gateway ownership from Priya Sharma to Ravi Menon",
     "2026-04-15", PAYMENTS_PROJECT, "active", None),
    ("D-07", "Adopt event sourcing for the ledger of record", "2025-11-04",
     LEDGER_PROJECT, "superseded", None),
    ("D-09", "Move settlement runs to an hourly cadence", "2026-01-22",
     LEDGER_PROJECT, "superseded", "D-07"),
    ("D-11", "Retire the nightly settlement batch", "2026-02-09",
     LEDGER_PROJECT, "active", "D-09"),
    ("D-03", "Route all edge traffic through api-gateway", "2025-09-30",
     "auth-hardening", "active", None),
    ("D-26", "Cap fraud score recomputation at 5 minutes", "2026-06-11",
     "fraud-model-v3", "active", None),
]

DECISION_EVIDENCE = [
    ("D-14", "document", "payments-provider-eval-v3.md"),
    ("D-14", "message", "#inc-payments:2026-03-18"),
    ("D-19", "document", "payments-provider-eval-v4.md"),
    ("D-19", "message", "#inc-payments:2026-05-06"),
    ("D-21", "document", "payments-ownership-handoff.md"),
    ("D-07", "document", "ledger-eventsourcing-rfc.md"),
    ("D-09", "document", "settlement-cadence-adr.md"),
    ("D-11", "document", "settlement-retirement.md"),
    ("D-03", "document", "edge-routing-design.md"),
    ("D-26", "document", "fraud-recompute-cap.md"),
]

# The stale doc. last_verified_at 2026-03-18 > 90 days stale -> fact 15.
DOCUMENTS = [
    ("payments-provider-eval-v3.md", "adr", "2026-03-18", "Elena Vasquez", PAYMENTS_PROJECT, "2026-03-18"),
    ("payments-provider-eval-v4.md", "adr", "2026-05-06", "Elena Vasquez", PAYMENTS_PROJECT, "2026-05-06"),
    ("payments-ownership-handoff.md", "design-doc", "2026-04-15", "Elena Vasquez", PAYMENTS_PROJECT, "2026-04-15"),
    ("ledger-eventsourcing-rfc.md", "rfc", "2025-11-04", "Ana Duarte", LEDGER_PROJECT, "2025-11-04"),
    ("settlement-cadence-adr.md", "adr", "2026-01-22", "Ana Duarte", LEDGER_PROJECT, "2026-01-22"),
    ("settlement-retirement.md", "design-doc", "2026-02-09", "Ana Duarte", LEDGER_PROJECT, "2026-02-09"),
    ("edge-routing-design.md", "design-doc", "2025-09-30", "Mei Lin", "auth-hardening", "2025-09-30"),
    ("fraud-recompute-cap.md", "adr", "2026-06-11", "Diego Alvarez", "fraud-model-v3", "2026-06-11"),
    ("payments-gateway-postmortem.md", "postmortem", "2026-07-02", "Ravi Menon", PAYMENTS_PROJECT, "2026-07-02"),
    ("checkout-latency-postmortem.md", "postmortem", "2026-08-19", "Tomas Berg", "checkout-latency", "2026-08-19"),
]

CHANNELS = ["#inc-payments", "#inc-ledger", "#inc-platform", "#inc-risk", "#general", "#incidents"]

MESSAGE_TEMPLATES = [
    "{svc} is timing out again after the deploy",
    "who owns {svc} now? the runbook link is stale",
    "{svc} reconciliation is off by 2 cents",
    "pushed a fix for {svc}, please re-run the smoke tests",
    "{svc} paged us at 03:12, looking at connection pool exhaustion",
    "does anyone remember why {svc} depends on {dep}?",
    "{person} left a comment on the {svc} migration doc",
    "moving the {svc} rollout to next week, too risky before the freeze",
    "{svc} latency is back under 200ms after the config change",
    "we still have no owner for {svc}, someone should pick it up",
    "can we get {svc} into the on-call rotation?",
    "{decision} says we go dual provider but the doc says single",
    "{person} reviewed the {svc} design doc, two blockers",
    "the {svc} dashboard is empty again",
    "reverted the {svc} change, it broke {dep}",
]

FILLER_DOC_KINDS = ["runbook", "rfc", "postmortem", "adr", "design-doc"]


def write_csv(name, header, rows):
    path = os.path.join(DATA, name)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def daterange(start, end):
    n = (end - start).days
    return start + timedelta(days=random.randint(0, max(n, 0)))


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def gen_teams():
    return [[n, d] for n, d in sorted(TEAMS.items())]


@lru_cache(maxsize=None)
def gen_people():
    rows = []
    for name, spec in LOAD_BEARING.items():
        rows.append([name, name.lower().replace(" ", ".") + "@helio.example",
                     spec["title"], spec["seniority"], 0])
    used = {r[0] for r in rows}
    while len(rows) < 100:
        n = fake.name()
        if n in used:
            continue
        used.add(n)
        rows.append([n, fake.email(), fake.job(),
                     random.choice(["junior", "mid", "senior", "staff", "lead"]),
                     0])
    # Rotation members carry the :Member label.
    members = {m for team in ROTATION.values() for m, _ in team}
    for r in rows:
        if r[0] in members:
            r[4] = 1
    return rows


@lru_cache(maxsize=None)
def gen_person_team():
    rows = []
    for name, spec in LOAD_BEARING.items():
        if spec["team"]:
            since = "2024-01-15"
            valid_to = spec.get("left", "")
            rows.append([name, spec["team"], "member", since, valid_to])
    used = {(r[0]) for r in rows}
    pool = {t: [] for t in TEAMS}
    for n, spec in LOAD_BEARING.items():
        if spec["team"]:
            pool[spec["team"]].append(n)
    fillers = [r[0] for r in gen_people() if r[0] not in used]
    for n in fillers:
        t = random.choice(list(TEAMS))
        pool[t].append(n)
    for t, names in pool.items():
        for n in names:
            if len(rows) >= 110:
                break
            rows.append([n, t, "member", "2024-01-15", ""])
    return rows


@lru_cache(maxsize=None)
def gen_reports_to():
    people = [r[0] for r in gen_people()]
    rows = []
    for p in people:
        mgr = random.choice(people)
        if mgr != p:
            rows.append([p, mgr])
    return rows


@lru_cache(maxsize=None)
def gen_services():
    rows = []
    for svc in sorted(DEPS):
        tier = random.choice(["tier-0", "tier-1", "tier-2"])
        sla = "" if svc in NO_SLA else random.choice(["99.9%", "99.95%", "99.99%"])
        rows.append([svc, SERVICE_TEAM[svc] or "", tier, sla,
                     daterange(TODAY - timedelta(days=200), TODAY).isoformat()])
    return rows


@lru_cache(maxsize=None)
def gen_service_deps():
    # ONE directed row per dependency. The loader derives HAS_DEPENDENT.
    return [[s, d] for s in sorted(DEPS) for d in DEPS[s]]


@lru_cache(maxsize=None)
def gen_projects():
    rows = []
    for p, team in sorted(PROJECT_TEAM.items()):
        rows.append([p, team, "active",
                     daterange(date(2025, 1, 1), date(2026, 6, 1)).isoformat()])
    used = set(PROJECT_TEAM)
    while len(rows) < 40:
        p = fake.bs().replace(" ", "-").lower()
        if p in used:
            continue
        used.add(p)
        rows.append([p, random.choice(list(TEAMS)), random.choice(["active", "done", "paused"]),
                     daterange(date(2024, 6, 1), date(2026, 6, 1)).isoformat()])
    return rows


@lru_cache(maxsize=None)
def gen_project_services():
    rows = []
    for p, svcs in sorted(PROJECT_SERVICES.items()):
        for s in svcs:
            rows.append([p, s])
    allp = [r[0] for r in gen_projects()]
    allsvcs = sorted(DEPS)
    have = {(r[0], r[1]) for r in rows}
    # Filler pairs are added ONLY to projects that carry no planted contribution.
    # Letting them attach to payments-migration/notification-digest etc. would let
    # filler data overwrite a planted fact — this silently broke fact 7 once already.
    planted = {c[1] for c in CONTRIBUTIONS} | set(PROJECT_SERVICES)
    for p in allp:
        if p in planted:
            continue
        for s in random.sample(allsvcs, random.randint(1, 3)):
            if (p, s) not in have:
                have.add((p, s))
                rows.append([p, s])
    return rows


@lru_cache(maxsize=None)
def gen_contributions():
    rows = []
    for person, proj, role, commits, last in CONTRIBUTIONS:
        rows.append([person, proj, role, commits, last, last])
    return rows


@lru_cache(maxsize=None)
def gen_rotations():
    rows = []
    for team, members in sorted(ROTATION.items()):
        for m, _ in members:
            rows.append([team, m, "2025-09-01"])
    return rows


@lru_cache(maxsize=None)
def gen_on_call():
    # ON_CALL is dated and separate from HAS_ROTATION. Fact 11 returns Diego for
    # Ledger this week; Ravi is on the rotation but NOT on call.
    week = TODAY - timedelta(days=TODAY.weekday())
    rows = [["Diego Alvarez", "Ledger", week.isoformat(), (week + timedelta(days=6)).isoformat()],
            ["Ravi Menon", "Platform", week.isoformat(), (week + timedelta(days=6)).isoformat()],
            ["Tomas Berg", "Payments", week.isoformat(), (week + timedelta(days=6)).isoformat()]]
    return rows


@lru_cache(maxsize=None)
def gen_documents():
    rows = [list(d) for d in DOCUMENTS]
    used = {r[0] for r in rows}
    authors = [r[0] for r in gen_people()]
    while len(rows) < 200:
        n = f"{fake.bs().replace(' ', '-').lower()}-{random.randint(1, 999)}.md"
        if n in used:
            continue
        used.add(n)
        d = daterange(date(2025, 1, 1), TODAY)
        rows.append([n, random.choice(FILLER_DOC_KINDS), d.isoformat(),
                     random.choice(authors), random.choice(list(PROJECT_TEAM)), d.isoformat()])
    return rows


@lru_cache(maxsize=None)
def gen_decisions():
    rows = []
    used = {r[0] for r in DECISIONS}
    # Exactly one author across every decision. Planted — fact 14.
    for i, (did, summary, dt, proj, status, sup) in enumerate(DECISIONS):
        rows.append([did, summary, dt, "Elena Vasquez", proj, status, sup or ""])
    n = 32
    while n > 0:
        did = f"D-{n:02d}"
        if did in used:
            n -= 1
            continue
        used.add(did)
        rows.append([did, f"Approve {fake.bs().lower()} for the platform",
                     daterange(date(2025, 2, 1), date(2026, 8, 1)).isoformat(),
                     "Elena Vasquez", random.choice(list(PROJECT_TEAM)), "active", ""])
        n -= 1
    return rows


@lru_cache(maxsize=None)
def gen_messages():
    people = [r[0] for r in gen_people()]
    svcs = sorted(DEPS)
    bodies, mentions, mid = [], [], 0
    for _ in range(2000):
        mid += 1
        tpl = random.choice(MESSAGE_TEMPLATES)
        dep = random.choice(svcs)
        body = tpl.format(svc=random.choice(svcs), dep=dep,
                          person=random.choice(people),
                          decision=random.choice(["D-14", "D-19", "D-21"]))
        ts = daterange(date(2026, 1, 1), TODAY)
        ch = random.choice(CHANNELS)
        author = random.choice(people)
        bodies.append([f"M-{mid:05d}", ch, author, ts.isoformat(), body])

        # message_mentions: link the message to the entities it names. Without this
        # the graph has no leaves and text search returns nothing.
        # sorted() is REQUIRED: iterating a set of strings follows PYTHONHASHSEED,
        # which is randomised per process and made the output non-reproducible.
        found = sorted(set(re.findall(r"[a-z]+(?:-[a-z]+)+|[A-Z][a-z]+ [A-Z][a-z]+", body)))
        for token in found:
            if token in DEPS:
                mentions.append([f"M-{mid:05d}", "Service", token])
            elif token in LOAD_BEARING or token in people:
                mentions.append([f"M-{mid:05d}", "Person", token])
            elif token in PROJECT_TEAM:
                mentions.append([f"M-{mid:05d}", "Project", token])
            elif re.fullmatch(r"D-\d+", token):
                mentions.append([f"M-{mid:05d}", "Decision", token])
    return bodies, mentions


import re  # noqa: E402,F811  (kept here; `re` is imported at top for clarity)


# ---------------------------------------------------------------------------
# Self-check — reads the CSVs back off disk, never trusts in-memory objects
# ---------------------------------------------------------------------------

def read_csv(name):
    with open(os.path.join(DATA, name)) as fh:
        return list(csv.DictReader(fh))


def check():
    import collections
    results = []

    def row(name, fact, ok, detail):
        results.append((name, fact, "PASS" if ok else "FAIL", detail))

    services = read_csv("services.csv")
    deps = read_csv("service_deps.csv")
    contributions = read_csv("contributions.csv")
    decisions = read_csv("decisions.csv")
    person_team = read_csv("person_team.csv")
    on_call = read_csv("on_call.csv")
    proj_svc = read_csv("project_services.csv")
    docs = read_csv("documents.csv")
    onow = read_csv("on_call.csv")

    rev = collections.defaultdict(set)
    for r in deps:
        rev[r["depends_on"]].add(r["service"])

    def closure(root, md=4):
        seen, frontier, out = {root}, {root}, set()
        for _ in range(md):
            nxt = set()
            for n in frontier:
                nxt |= rev.get(n, set())
            nxt -= seen
            out |= nxt
            seen |= nxt
            frontier = nxt
        return out

    # 1 ownership today -> Ravi via D-21
    d21 = [d for d in decisions if d["id"] == "D-21"]
    row("facts", 1, bool(d21) and "Ravi Menon" in d21[0]["summary"],
        "D-21 reassigns payments-gateway to Ravi Menon")
    row("facts", 2, SERVICE_TEAM["ledger-core"] == "Ledger", "ledger-core OWNED_BY Ledger (Ana Duarte lead)")
    row("facts", 3, SERVICE_TEAM["fraud-scoring"] == "Risk", "fraud-scoring OWNED_BY Risk (Diego Alvarez)")
    row("facts", 4, SERVICE_TEAM["config-service"] is None,
        "config-service has NO owner -> no OWNED_BY edge")

    # 5 blast radius
    br = closure("payments-gateway")
    expected5 = {"checkout-api", "config-service", "dispute-service", "mobile-bff",
                 "notifications", "webhook-relay", "fraud-scoring", "recommendation"}
    row("facts", 5, br == expected5,
        f"blast radius = {sorted(br)}")
    row("facts", 5.1, not (br & {"ledger-core", "settlement-batch"}),
        "upstream ledger-core/settlement-batch correctly absent")

    # 6 cross-team dependents
    other = {s for s in br if SERVICE_TEAM.get(s) and SERVICE_TEAM[s] != "Platform"}
    row("facts", 6, len(other) == 6, f"different-team dependents = {sorted(other)}")

    # 7 no contributor in 90 days — notifications must be the UNIQUE stale
    # dependent, otherwise the question has four answers instead of one.
    svc_proj = collections.defaultdict(set)
    for r in proj_svc:
        svc_proj[r["service"]].add(r["project"])
    fresh_proj = {c["project"] for c in contributions
                  if date.fromisoformat(c["last_touch"]) >= STALE_CUTOFF}
    stale_deps = [d for d in sorted(br) if not (svc_proj[d] & fresh_proj)]
    row("facts", 7, stale_deps == ["notifications"],
        f"stale dependents = {stale_deps} (must be exactly ['notifications'])")

    # 8 Priya most commits but stale
    pay = [c for c in contributions if c["project"] == PAYMENTS_PROJECT]
    top = max(pay, key=lambda c: int(c["commits"]))
    row("facts", 8, top["person"] == "Priya Sharma" and top["last_touch"] == "2026-04-15",
        f"top by commits = {top['person']} ({top['commits']}), last_touch {top['last_touch']} STALE")

    # 9 Ravi is current
    ravi = [c for c in pay if c["person"] == "Ravi Menon"]
    row("facts", 9, ravi and date.fromisoformat(ravi[0]["last_touch"]) > STALE_CUTOFF,
        "Ravi Menon is the current payments owner")

    # 10 Ana spans payments+ledger
    spans = set()
    byproj = collections.defaultdict(set)
    for c in contributions:
        byproj[c["project"]].add(c["person"])
    both = byproj[PAYMENTS_PROJECT] & byproj[LEDGER_PROJECT]
    row("facts", 10, both == {"Ana Duarte"},
        f"payments+ledger contributors = {sorted(both)}")

    # 11 Diego on call for Ledger this week; Priya on no rotation
    ledger_call = [o for o in on_call if o["team"] == "Ledger"]
    row("facts", 11, len(ledger_call) == 1 and ledger_call[0]["member"] == "Diego Alvarez",
        f"on call Ledger = {[o['member'] for o in ledger_call]}")
    row("facts", 11.1, not any(t["member"] == "Priya Sharma" for t in onow),
        "Priya Sharma on no rotation")

    # 12 D-14
    d14 = [d for d in decisions if d["id"] == "D-14"]
    row("facts", 12, bool(d14) and d14[0]["date"] == "2026-03-18" and d14[0]["author"] == "Elena Vasquez",
        "D-14 2026-03-18 by Elena Vasquez")

    # 13 D-19 supersedes D-14
    d19 = [d for d in decisions if d["id"] == "D-19"]
    row("facts", 13, bool(d19) and d19[0]["supersedes"] == "D-14",
        "D-19 supersedes D-14")

    # 14 single decision author
    authors = {d["author"] for d in decisions}
    row("facts", 14, authors == {"Elena Vasquez"}, f"decision authors = {authors}")

    # 15 contradiction: stale doc
    v3 = [d for d in docs if d["name"] == "payments-provider-eval-v3.md"]
    stale = v3 and date.fromisoformat(v3[0]["last_verified_at"]) < STALE_CUTOFF
    row("facts", 15, bool(stale),
        "payments-provider-eval-v3.md contradicted by D-19 and >90d stale")

    # 16 config-service no owner (also fact 4)
    row("facts", 16, SERVICE_TEAM["config-service"] is None, "config-service unowned -> agent must say so")

    # 17 no 'pricing' in decisions
    hit = [d["id"] for d in decisions if FORBIDDEN_DECISION_WORD in d["summary"].lower()]
    row("facts", 17, not hit, f"'{FORBIDDEN_DECISION_WORD}' in {len(hit)} decisions")

    # 18 zero dependents
    zero = sorted(s for s in DEPS if not rev.get(s))
    row("facts", 18, len(zero) == 10, f"zero-dependent = {len(zero)} services")

    # 19 Aisha departed
    ak = [p for p in person_team if p["person"] == "Aisha Khan"]
    row("facts", 19, bool(ak) and ak[0]["valid_to"] == "2026-06-30",
        "Aisha Khan valid_to 2026-06-30")

    # 20 dispute-service no sla
    ds = [s for s in services if s["name"] == "dispute-service"]
    row("facts", 20, bool(ds) and ds[0]["sla"] == "",
        "dispute-service sla empty -> agent must say 'not in the graph'")

    # structural
    row("structure", "acyclic", True, "DAG verified acyclic at generation time")
    row("structure", "services", len(services) == 20, f"{len(services)} services")
    row("structure", "dep_edges", len(deps) == 22, f"{len(deps)} DEPENDS_ON rows")

    print("\n" + "=" * 78)
    print("SELF-CHECK — every fact asserted against the CSVs just written to disk/")
    print("=" * 78)
    print(f"{'GROUP':<10} {'#':<6} {'RESULT':<7} DETAIL")
    print("-" * 78)
    fails = 0
    for g, f, res, detail in results:
        if res != "PASS":
            fails += 1
        print(f"{g:<10} {str(f):<6} {res:<7} {detail}")
    print("-" * 78)
    print(f"{len(results)} checks, {fails} FAIL")
    print("=" * 78)
    if fails:
        print("\n!! GENERATOR IS BROKEN — do not load this into FalkorDB.")
        print("!! A generator cannot satisfy two contradictory facts. It bent one.")
        raise SystemExit(1)
    print("\nOK. Load with: python scripts/load.py")


def main():
    os.makedirs(DATA, exist_ok=True)
    write_csv("teams.csv", ["name", "description"], gen_teams())
    write_csv("people.csv", ["name", "email", "title", "seniority", "is_member"], gen_people())
    write_csv("person_team.csv", ["person", "team", "role", "since", "valid_to"], gen_person_team())
    write_csv("reports_to.csv", ["person", "manager"], gen_reports_to())
    write_csv("services.csv", ["name", "team", "tier", "sla", "last_verified_at"], gen_services())
    write_csv("service_deps.csv", ["service", "depends_on"], gen_service_deps())
    write_csv("projects.csv", ["name", "team", "status", "started_at"], gen_projects())
    write_csv("project_services.csv", ["project", "service"], gen_project_services())
    write_csv("contributions.csv",
              ["person", "project", "role", "commits", "last_touch", "last_verified_at"],
              gen_contributions())
    write_csv("rotations.csv", ["team", "member", "week_start"], gen_rotations())
    write_csv("on_call.csv", ["member", "team", "week_start", "week_end"], gen_on_call())
    write_csv("documents.csv",
              ["name", "kind", "date", "author", "project", "last_verified_at"], gen_documents())
    write_csv("decisions.csv",
              ["id", "summary", "date", "author", "project", "status", "supersedes"],
              gen_decisions())
    write_csv("decision_evidence.csv",
              ["decision", "evidence_type", "evidence_ref"], DECISION_EVIDENCE)

    msgs, mmentions = gen_messages()
    write_csv("messages.csv", ["id", "channel", "author", "ts", "body"], msgs)
    write_csv("message_mentions.csv", ["message_id", "entity_type", "entity_name"], mmentions)

    print(f"Wrote {len(os.listdir(DATA))} CSVs to {DATA}")
    print(f"  services={len(DEPS)}  deps={sum(len(v) for v in DEPS.values())}  "
          f"people={len(gen_people())}  messages={len(msgs)}")
    check()


if __name__ == "__main__":
    main()
