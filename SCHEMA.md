# SCHEMA.md — Helio graph model

**The contract between the data layer, the Cypher, and the frontend.**

`scripts/generate.py`, `scripts/load.py` and `app/graph.py` must all agree with this
file. If they disagree, a traversal returns `[]` **silently** — not an error, just
nothing — and you lose an hour to a query that looks correct.

Node types: `Person`, `Team`, `Project`, `Service`, `Decision`, `Document`, `Message`.
Nothing else. Unused types are wasted generator time.

---

## 1. The `:Member` decision

> Anyone on a rotation carries a **second label**: `(:Person:Member)`.
> Ravi Menon is `(:Person:Member)`. Mei Lin is `(:Person)`.

**One node, two labels** — not a separate `Member` node type.

**Why it matters.** The original blast-radius Cypher assumed `(:Member)` was its own
node type. No schema defined it, so the generator, the loader and the query could each
have picked a different reading. They would all have "worked" and the query would have
returned nothing.

---

## 2. On-call: rotation membership is not the same as on call

**Resolved 2026-10-17.** The plan said *"Ravi Menon — on-call Ledger"* in the People
table while fact 11 said the answer was Diego Alvarez. Both cannot be the single
on-call person. The model is now two edges:

```
(:Team)-[:HAS_ROTATION {since}]->(:Person:Member)
(:Person:Member)-[:ON_CALL {week_start, week_end}]->(:Team)
```

- **`HAS_ROTATION`** = *is on this team's rotation.* A standing fact.
- **`ON_CALL`** = *is on call for this team during this week.* A dated fact.

So for Ledger: **Ravi Menon and Diego Alvarez are both on the rotation. Diego is on
call this week.** Fact 11 returns Diego. **Priya Sharma is on no rotation at all** —
that is why she cannot be the answer, and it is what makes the fact bite.

**This is the `ON_CALL` direction — note it points *back* at the Team.** The plan's
original sketch had `(:Member)-[:ON_CALL]->(:Person)`, which would require a self-loop
once `:Member` and `:Person` are the same node. Corrected here.

### The fact-11 query

```cypher
MATCH (t:Team {name: $team})<-[:ON_CALL]-(m:Person:Member)
WHERE m.on_call_week = date()          // loader stamps the current week
RETURN m.name AS on_call
```

`on_call_week` is stamped by the **loader**, never computed by the query — so the same
graph gives the same answer on every run, and re-running the generator cannot change
who is on call.

---

## 3. Nodes

| Label | Key properties | Notes |
|---|---|---|
| `Person` | `name`, `email`, `title`, `seniority`, `is_member` | `is_member` duplicates the `:Member` label **on purpose** — the label drives the query, the property survives CSV round-trips |
| `Team` | `name`, `description` | 5: Platform, Ledger, Payments, Risk, Growth |
| `Project` | `name`, `team`, `status`, `started_at` | ~40 |
| `Service` | `name`, `team`, `tier`, `sla`, `last_verified_at` | 20. **`config-service` has no `OWNED_BY` edge. `dispute-service` has an empty `sla`.** |
| `Decision` | `id`, `summary`, `date`, `author`, `status` | ~40. **Every one authored by Elena Vasquez.** |
| `Document` | `name`, `kind`, `date`, `author`, `last_verified_at` | ~200 |
| `Message` | `id`, `channel`, `ts`, `body` | ~2,000. Must mention real entities by name. |

Indexes, created **before** bulk load:

```cypher
CREATE INDEX ON :Service(name)
CREATE INDEX ON :Person(name)
CREATE INDEX ON :Project(name)
CREATE INDEX ON :Decision(id)
```

---

## 4. Relationships

`via_edge` values are restricted to exactly this set — the frontend renders chips off
it, and an unexpected value renders wrong with nobody noticing until Gate 2:

`CONTRIBUTED_TO` · `OWNED_BY` · `EVIDENCED_BY` · `SUPERSEDES` · `MENTIONS` ·
`HAS_DEPENDENT` · `DEPENDS_ON` · `MEMBER_OF` · `ON_CALL` · `USES` · `HAS_ROTATION` ·
`REPORTS_TO` · `ABOUT` · `AUTHORED_BY`

| Relationship | From → To | Properties | Carries |
|---|---|---|---|
| `MEMBER_OF` | `Person` → `Team` | `since`, `role`, **`valid_to`** | fact 19 — Aisha's `valid_to = 2026-06-30` |
| `REPORTS_TO` | `Person` → `Person` | — | |
| `OWNED_BY` | `Service` → `Team` | — | **fact 4 — `config-service` has none** |
| `DEPENDS_ON` | `Service` → `Service` | — | from the DAG |
| `HAS_DEPENDENT` | `Service` → `Service` | — | **inverse of `DEPENDS_ON`, emitted separately** |
| `USES` | `Project` → `Service` | — | |
| `CONTRIBUTED_TO` | `Person` → `Project` | `role`, `commits`, `last_touch`, `last_verified_at` | fact 8 — Priya 14 commits, `last_touch 2026-04-15` |
| `HAS_ROTATION` | `Team` → `Person:Member` | `since` | |
| `ON_CALL` | `Person:Member` → `Team` | `week_start`, `week_end` | fact 11 |
| `ABOUT` | `Decision` → `Project` | — | |
| `SUPERSEDES` | `Decision` → `Decision` | — | fact 13 — D-19 supersedes D-14 |
| `EVIDENCED_BY` | `Decision` → `Document` \| `Message` | — | fact 12 |
| `AUTHORED_BY` | `Document` \| `Message` → `Person` | — | |
| `MENTIONS` | `Message` → `Person` \| `Service` \| `Project` \| `Decision` | — | text-search leaves |

### ⚠️ `DEPENDS_ON` and `HAS_DEPENDENT` are both emitted

**Cypher cannot traverse an edge backwards.** One DAG row produces **two** edges under
two names. Skip the inverse and the blast-radius query returns `[]` — not an error,
just nothing.

`service_deps.csv` holds **one directed row per dependency**. The loader derives
`HAS_DEPENDENT` itself. Never write the inverse twice into the graph, or a dirty graph
gives every count a wrong answer.

---

## 5. Freshness is edge properties, not a system

> *"Keep knowledge current" is a second project. Do not build it.*

| Signal | Where it lives | Read by |
|---|---|---|
| Left the company | `MEMBER_OF.valid_to` | facts 11, 19 |
| Stale contribution | `CONTRIBUTED_TO.last_touch` | fact 8 |
| Never re-verified | `last_verified_at` on `CONTRIBUTED_TO`, `Service`, `Document` | staleness query |
| Superseded | `SUPERSEDES` | facts 13, 15 |

**Staleness query** — anything not re-verified in 90 days:

```cypher
MATCH ()-[r]->()
WHERE r.last_verified_at IS NOT NULL
  AND r.last_verified_at < date() - duration({days: 90})
RETURN type(r) AS edge, r.last_verified_at AS last_seen
```

The >90-day threshold is what catches `payments-provider-eval-v3.md`
(`last_verified_at = 2026-03-18`), contradicting D-19 — **fact 15**.

---

## 6. Handoffs

### → Soham (was blocked on this)

```python
blast_radius(service: str) -> dependents, hop_depth, owner_team, on_call
expertise(service: str)    -> people by contribution, volume AND recency
provenance(project: str)   -> decisions, author, superseded, evidence
staleness()                -> edges not re-verified in 90 days
```

Every function returns **raw rows AND the nodes/edges that produced them**, so the
frontend can render a trail with edge labels. All Cypher lives in `app/graph.py` and
nowhere else.

### → Ujwal

`trail[]` shape comes from the Cypher that **actually** runs, not the assumed one.
Agreed once real data loads (Gate 2), not before.

---

## 7. Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-10-17 | `:Member` is a **second label** on `Person` | one node, two labels — a separate node type would have broken the traversal silently |
| 2026-10-17 | `ON_CALL` split from `HAS_ROTATION`, points **back** at `Team` | plan contradicted itself on fact 11; rotation membership ≠ on call this week |
| 2026-10-17 | `on_call_week` stamped by the **loader** | keeps fact 11 deterministic across generator re-runs |
| 2026-10-17 | 20 services, `ledger-core` as root | `ledger-core` had no DAG row despite 7 dependents |
| 2026-10-17 | `auth-service` / `api-gateway` depend on nothing | removing the fan-in killed 2 cycles and cut blast radius 14 → 8 |
