# Helio — a company brain

**Track 03: Company Brain · Graph Hacks**

Ask *"who knows about the payments service, what breaks if it goes down, and where
was that decided?"* — and get one answer with the path that produced it, including
the parts that are stale and the parts that do not exist.

Existing enterprise search answers *"where is the doc about X."* We answer **who
knows about X, what breaks if it goes down, where was that decided, and how current
is that answer** — in one traversal, with the path shown. Text search is used only at
the leaves.

The company is **Helio**: a synthetic 120-person fintech, 5 teams, 20 services,
mid-migration between payment providers. All data is synthetic.

**Live:** <https://helio-brain.onrender.com> · **Video:** see submission

---

## Why this is more than a chatbot

An LLM asked *"is this answer correct?"* is **circular**. A hallucinated ownership
chain looks exactly like a correct one, because both are plausible prose over
structurally valid edges.

So the 20 ground-truth facts in [`GROUND_TRUTH.md`](GROUND_TRUTH.md) were written by
hand, independently, **before any data was generated** — including 5 questions
designed to have no answer. The agent is scored against those, not against itself.

```
GROUND_TRUTH.md → generate.py → load.py → graph.py (Cypher) → verify.py
                                                              │
                                                ┌─────────────┘
                                                ▼
                                      agent.py + main.py → web/
```

---

## What it actually does

| Traversal | Question | The interesting part |
|---|---|---|
| **Blast radius** | What breaks if this service dies, and who gets paged? | Walks `HAS_DEPENDENT`, reports hop depth, owning team, on-call person |
| **Expertise** | Who knows this best? | Returns **volume and recency separately** — never a single rank |
| **Provenance** | Where was this decided, and is it still current? | Traverses `SUPERSEDES` so superseded decisions show *as* superseded |
| **Staleness** | What has not been re-verified in 90 days? | Freshness as edge properties, not a separate system |

### Three answers worth reading

**The trap.** Priya Sharma has the most commits on `payments-gateway` — 14. Her last
touch was 2026-04-15, the day she left the company. A single `ORDER BY count DESC`
returns her and is *technically correct on volume while being the wrong answer*.
Ours returns both signals:

> The Platform team owns payments. **Ravi Menon** has worked on it most recently
> (2026-09-28). **Priya Sharma** has the most commits (14), but her last touch was
> 2026-04-15 and is flagged as stale. Ask **Ravi Menon**.

**The contradiction.** A March document and a March Slack thread both say *"single
provider, Stripe."* Decision **D-19** (2026-05-06) says *"dual provider, Adyen
primary, Stripe fallback."* The document is stale, and the graph can prove it.

**The failure.** *"Who owns `config-service`?"* → **"The graph contains no
`OWNED_BY` edge. No team owns it."** Confident, not an apology — because that is the
truth, not a gap.

That last one is the point. Five of the twenty questions have **no answer in the
graph**, and an agent that invents one has failed even if the sentence reads
perfectly.

---

## Quick start

```bash
cp .env.example .env      # add ANTHROPIC_API_KEY
docker compose -f deploy/docker-compose.yml up --build
open http://localhost:8080
```

That is the whole setup. The `seed` service generates the CSVs and loads them into
FalkorDB, then the API waits for it to finish — so you never hit a live server
pointing at an empty graph.

- **FalkorDB Browser** (visual explorer): <http://localhost:3000>

> **Port 3000 collides.** FalkorDB's Browser wants it. If a standalone FalkorDB is
> already running, compose fails with `Bind for 0.0.0.0:3000 failed: port is already
> allocated` — that is a port clash, not a broken compose file. Stop the other
> container first.

### Without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker run -d --name falkordb -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
python scripts/generate.py     # writes data/*.csv, self-checks 25 facts
python scripts/load.py         # loads and asserts counts
uvicorn app.serve:app --port 8080
```

### Configuration

| Variable | Default | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | required for `/ask` |
| `ANTHROPIC_BASE_URL` | — | set to `https://openrouter.ai/api` to use OpenRouter |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5` | must match your provider's slug |
| `ANTHROPIC_MAX_TOKENS` | `1024` | lower it on a thin API budget — see below |
| `USE_MOCK` | `1` | **set to `0` for real data.** `1` answers from a JSON fixture and never touches the graph |
| `FALKORDB_HOST` / `_PORT` | `localhost` / `6379` | |
| `FALKORDB_SSL` | `false` | Cloud is plaintext on its instance port despite implying TLS |
| `FALKORDB_GRAPH` | `helio` | |

> **The `USE_MOCK` trap.** It defaults to `1`. Leave it and the app looks perfect,
> streams beautifully, answers every question, and never once reads the graph —
> because it is reading Ujwal's fixture. `GET /health` returns `{"mock": true|false}`
> and that one field tells you which you are looking at.

> **Token budget.** Some providers reject the entire request when `max_tokens`
> exceeds the remaining balance, rather than truncating the answer. Lower
> `ANTHROPIC_MAX_TOKENS` to fit.

---

## Verification

Two scripts, and the distinction between them matters.

```bash
python scripts/verify.py         # 21 checks — the Cypher is correct
python scripts/verify_agent.py   # 20 questions — the AGENT uses it correctly
```

`verify.py` asks the graph directly. `verify_agent.py` sends the same 20 questions
through the real `POST /ask` and checks the **answer text**, because a tool can
return perfect rows and the agent can still misreport them, invent a node, or
refuse. The agent is the thing being judged; the Cypher is only the mechanism.

The generator self-checks **25 facts** against the CSVs it just wrote, and exits
non-zero on any mismatch. It reads the files back **off disk** rather than trusting
in-memory objects — which is how it caught three real bugs on its first run.

---

## Data model

Seven node types — `Person`, `Team`, `Project`, `Service`, `Decision`, `Document`,
`Message` — and nothing else.

Full description: [`SCHEMA.md`](SCHEMA.md) · diagram: [`docs/schema.md`](docs/schema.md)

```
(Person)-[:MEMBER_OF      { since, role, valid_to }]->(Team)
(Person)-[:CONTRIBUTED_TO { role, commits, last_touch, last_verified_at }]->(Project)
(Service)-[:OWNED_BY]->(Team)
(Service)-[:DEPENDS_ON]->(Service)          (Service)-[:HAS_DEPENDENT]->(Service)
(Project)-[:USES]->(Service)
(Team)-[:HAS_ROTATION]->(:Person:Member)
(:Person:Member)-[:ON_CALL { week_start, week_end }]->(Team)
(Decision)-[:ABOUT]->(Project)              (Decision)-[:SUPERSEDES]->(Decision)
(Decision)-[:EVIDENCED_BY]->(Document|Message)  (Document|Message)-[:AUTHORED_BY]->(Person)
(Message)-[:MENTIONS]->(Person|Service|Project|Decision)
```

Two conventions carry weight:

**`DEPENDS_ON` and `HAS_DEPENDENT` are both emitted from one DAG row.** Cypher cannot
traverse an edge backwards. Skip the inverse and the blast-radius query returns `[]`
— not an error, just nothing.

**Freshness is edge properties, not a system.** `valid_to`, `last_touch`,
`last_verified_at`, `SUPERSEDES`. A separate staleness model would be a second
project.

### The dependency DAG

20 services, 22 edges, **verified acyclic**. `ledger-core` is the root that the
financial services hang off; `auth-service`, `api-gateway` and `ledger-core`
intentionally depend on nothing — the public tier is the edge, it is downstream of
nothing. Blast radius of `payments-gateway` is 8 services across 3 hops.

---

## The Cypher

All of it lives in [`app/graph.py`](app/graph.py) and nowhere else.

```cypher
// 1. Blast radius — what breaks, how deep, who is paged.
//    min(length(path)) is required: notifications depends on BOTH payments-gateway
//    and dispute-service, so it is reachable at depth 1 AND 2. Without min() it is
//    returned twice and the count reads 9 instead of 8.
MATCH path = (s:Service {name: $service})-[:HAS_DEPENDENT*1..4]->(dep:Service)
WITH dep, min(length(path)) AS depth
OPTIONAL MATCH (dep)-[:OWNED_BY]->(t:Team)
OPTIONAL MATCH (t)-[:HAS_ROTATION]->(m:Person:Member)-[oc:ON_CALL]->(t)
RETURN dep.name AS dep, depth, t.name AS owner_team, m.name AS on_call
ORDER BY depth, dep
```

```cypher
// 2. Expertise — volume AND recency, never fused into one rank.
//    A single ORDER BY count DESC returns the top contributor, which on this data
//    is someone who left the company two months before the demo.
MATCH (p:Person)-[c:CONTRIBUTED_TO]->(proj:Project)-[:USES]->(s:Service {name: $service})
RETURN p.name AS person, sum(c.commits) AS commits, max(c.last_touch) AS latest
ORDER BY commits DESC
```

```cypher
// 3. Provenance — where it was decided, and whether it still stands.
//    Evidence is aggregated, not fanned out, or one decision returns a row per
//    evidence node and the count is wrong.
MATCH (d:Decision)-[:ABOUT]->(p:Project {name: $project})
OPTIONAL MATCH (d)-[:SUPERSEDES]->(prev:Decision)
OPTIONAL MATCH (d)-[:EVIDENCED_BY]->(ev)
WITH d, prev, collect(DISTINCT ev.name) AS evidence
RETURN d.id, d.summary, d.date, d.status, evidence, prev.id, prev.summary
```

```cypher
// 4. Staleness — anything not re-verified in 90 days.
MATCH ()-[r]->()
WHERE r.last_verified_at IS NOT NULL
  AND r.last_verified_at < date() - duration({days: 90})
RETURN type(r) AS edge, r.last_verified_at
```

**FalkorDB is a subset of OpenCypher.** No Neo4j-only syntax. No undirected
`shortestPath`. No `db.idx.fulltext.*`. `g.query(...).result_set` — the result is not
iterable.

---

## Known limitations

**ACL / permission enforcement is out of scope.** This is the real one. Glean's moat
is that answers respect access control; production needs an authz layer over every
traversal. Named rather than faked.

**Free-tier hosting sleeps.** Render's free tier spins down after 15 minutes idle;
a cold start takes about 22 seconds. The first request after a gap is slow.

**Single-writer assumptions.** The generator is seeded and deterministic — three
consecutive runs are byte-identical — which is what makes the ground-truth
verification honest. It is not designed for concurrent writers.

**Entity resolution is lexical.** `resolve_service()` maps *"the payments service"* →
`payments-gateway` by stripping generic suffixes and matching tokens. It returns the
original string when nothing matches confidently, so unknown services still produce
honest negatives. It will not resolve *"the thing that handles money"* to
`payments-gateway`.

---

## Project layout

| Path | Owner | What |
|---|---|---|
| `GROUND_TRUTH.md` | Bhushan | the 20 hand-written facts |
| `SCHEMA.md` · `docs/schema.md` | Bhushan · Ujwal | graph model, diagram |
| `scripts/generate.py` | Bhushan | seeded generator, self-checks 25 facts |
| `scripts/load.py` | Bhushan | CSV → FalkorDB, asserts counts |
| `scripts/verify.py` · `verify_agent.py` | Bhushan | 21 Cypher checks · 20 agent checks |
| `app/graph.py` | Bhushan | **the only Cypher in the repo** |
| `app/agent.py` · `app/main.py` | Soham | tool-use loop, SSE |
| `app/serve.py` | Bhushan | single-origin production entrypoint |
| `web/` · `mock/` | Ujwal | frontend, shared fixture |
| `deploy/` | Bhushan | compose |

---

## AI use disclosure

**Rule 11.**

AI was used throughout development, and we are explicit about how:

- **The data is entirely synthetic**, generated by `scripts/generate.py` from a fixed
  seed. No real company, person, message or document is represented. Rule 6.
- **The ground truth was written by hand**, not generated or validated by an LLM.
  This was deliberate: asking a model "is this answer correct?" is circular, and it
  is the only reason the verification below means anything.
- **AI assistants wrote and reviewed code** across all three of us — scaffolding,
  refactors, test generation, and review. Every commit is attributed to the human who
  made it, and every change is visible in the git history.
- **The agent itself calls an LLM at runtime.** That is the product. It is called only
  through `app/agent.py`, with a fixed system prompt, and constrained to the
  traversal tools in `app/graph.py`. It has no direct database access and no ability
  to write.
- **No third-party model was used to generate, label or validate the ground truth.**

We can all explain the schema, the queries, the architecture and the trade-offs.

---

## Validation & Test Coverage

- **Data-Driven Test Suite**: `tests/test_generated_1000.py` contains 1000+ auto-generated cases covering alias resolution, every graph tool, invariants, vocabularies, hostile inputs, unknown services, all 20 hand-written facts, and the `/ask` SSE + validation + CORS + failure-frame contract. It runs against the real FalkorDB graph (no API key required for the structural/API cases).
- **Bug-catching discipline**: the suite caught a real bug (`on_call` reading the date from the wrong property) and, after a one-line fix, passes **1001/1001 (100.00%)** in ~27s. The existing suite (`tests/`) continues to pass.
- **Deterministic ground truth**: Scored against hand-written facts in [`GROUND_TRUTH.md`](GROUND_TRUTH.md), not against an LLM. Direct graph verification via [`scripts/verify.py`](scripts/verify.py); end-to-end agent verification via [`scripts/verify_agent.py`](scripts/verify_agent.py).

---

## Credits

Built by **Bhushan**, **Soham** and **Ujwal**.
