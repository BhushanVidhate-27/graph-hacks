# Bhushan — Plan

**Track 03: Company Brain · Graph Hacks · Oct 15–18**
You are on the **critical path**. Your work is sequential, blocks both other members, and is the one task here that cannot be split three ways.

You also own **`deploy/`** and **`video/`** — both moved to you. See section 2 for how to sequence that on top of a full critical path.

Setup first: [`setup.md`](setup.md) — steps 1–8, then 11, **14**, **15** and 21.

---

## Index

| # | Section |
|---|---|
| 1 | [Why this is yours](#) |
| 2 | [What you own](#) |
| 3 | [Independent tasks](#) |
| 4 | [Dependent tasks](#) |
| 5 | [The 20 ground-truth facts](#) |
| 6 | [Verification procedure](#) |
| 7 | [Traps that break first](#) |
| 8 | [Your three days](#) |
| 9 | [Gates](#) |
| 10 | [If you're behind](#) |
| 11 | [Handoffs](#) |
| 12 | [Submission](#) |
| 13–15 | [Prompts: generate · load · graph](#) |
| 16–17 | [Prompts: deploy · video](#) |

---

<details>
<summary><b>1. Why this is yours and not shared</b></summary>

An AI will generate the data, generate the agent, and generate the answer. Asking an AI *"is this answer correct?"* is **circular** — a hallucinated ownership chain looks exactly like a correct one, because both are plausible prose over structurally valid edges.

**You wrote the planted facts by hand, independently.** That is the only reason verification is real. Soham and Ujwal can build fast; nobody else can check the truth. You are the bottleneck, and it is a bottleneck in judgement, not typing.

---

**The whole project:**

```
GROUND_TRUTH → schema → generate → load → graph.py (Cypher) → verify
                                                        │
                                            ┌───────────┘
                                            ▼
                                  Soham's agent + Ujwal's UI go live
```

Everything upstream of `graph.py` is sequential, must be written against the **loaded** graph rather than theory, and needs human-held ground truth. Soham and Ujwal work fully in parallel against mocks until Gate 2.
</details>

<details>
<summary><b>2. What you own</b></summary>

**Own:**

| Path | Contents |
|---|---|
| `GROUND_TRUTH.md` | The 20 planted facts |
| `data/` | Generated CSVs |
| `scripts/generate.py` · `scripts/load.py` | Synthetic company + loader |
| `app/graph.py` | **The only Cypher in the repo** |
| `README.md` | Authorship — data model, Cypher appendix, AI disclosure |
| `deploy/` | Dockerfile · `docker-compose.yml` · `fly.toml` · live URL |
| `video/` | Script, recording, edit, upload |
| Submission | You press submit |

**Don't touch** — no drive-by PRs:

| Path | Owner |
|---|---|
| `app/agent.py` · `app/main.py` | **Soham** |
| `web/` · `mock/` | **Ujwal** |

You need something in `agent.py` that isn't there? Ping Soham. You need a frontend tweak? Ping Ujwal. With three people and two days, an unowned file is how you lose a night to a bad merge.

---

### ⚠️ You now own the two things that fail latest

`deploy/` and `video/` came off Ujwal. That is a real load increase, and it lands on the **last** two days — the part of the project with the least slack. Two things keep it survivable:

**1. Neither blocks anyone else.** Soham and Ujwal both finish their code by Sat 11:00. Everything you own after that is a one-person job with no merge risk. Do the boring parts *early* — the `docker-compose.yml` is a Friday-evening task, not a Saturday-afternoon panic.

**2. Both have a hard fallback.** `docker compose up` is a legal submission under Rule 10 even with zero live deploy. An unpolished video still submits. So the *worst case* of this new scope is a smaller-looking entry, not a missing entry. Sequence so the fallback is always ready before you chase the better version.

| Owned | Fallback if it breaks | Decide by |
|---|---|---|
| `deploy/` | `docker compose up` + README instructions | Sat 17:00 · Gate 4 |
| `video/` | an unedited screen recording still submits | Sat 21:00 |

> **Do not let deploy eat the video, or the video eat verification.** In that order, verification wins.
</details>

<details>
<summary><b>3. Independent tasks — start now, nothing blocks you</b></summary>

| # | Task | Done when |
|---|---|---|
| **B1** | Write `GROUND_TRUTH.md` — the 20 facts in section 5 | Complete, internally consistent, no self-contradictions |
| **B2** | Sketch the schema, cut unused node types | Agreed in chat with Soham + Ujwal |
| **B3** | `scripts/generate.py` | Emits CSVs containing **all 20 planted facts** + the contradictions |

**B2 — required node types:** `Person, Team, Project, Service, Decision, Document, Message`. Add `Ticket` only if `dispute-service` needs one. Unused types are pure generator work you don't have time for.

**B3 — the one rule that matters:** chat messages must mention real entities — `"payments timeouts again after deploy"` in `#inc-payments`, not `"hey team"`. Without this the graph has no leaves, text search returns nothing, and the provenance trail has nothing to point at.
</details>

<details>
<summary><b>4. Dependent tasks — sequential, everyone waits</b></summary>

| # | Task | Done when |
|---|---|---|
| **B4** | `scripts/load.py` — indexes first, then batched `UNWIND` | 20 services, ~100 people, ~2,000 messages visible in Browser |
| **B5** | `app/graph.py` — the 3 traversals, **written against the loaded graph** | Each returns real rows |
| **B6** | Ground-truth verification — all 20 questions | Every answer matches the file |
| **B7** | Break-it pass — the 5 questions it should fail | Correct failures, zero fabrication |
| **B8** | `README.md` | A stranger can read it |
| **B9** | `deploy/` — compose **and** live URL | Both work from a cold browser |
| **B10** | `video/` — script, record, edit, upload | 90s, five beats, plays back |
| **B11** | Final submission | **Sun 18th, 17:00 IST** |

**B5 — three traversals.**

```cypher
// 1. Blast radius — what breaks, who's paged
MATCH path = (s:Service {name:$service})-[:HAS_DEPENDENT*1..4]->(dep:Service)
OPTIONAL MATCH (dep)-[:OWNED_BY]->(t:Team)-[:HAS_ROTATION]->(:Member)-[:ON_CALL]->(p:Person)
RETURN dep.name AS dep, length(path) AS depth, t.name AS owner,
       collect(DISTINCT p.name) AS on_call
```

```cypher
// 2. Expertise — who knows, recency-weighted
MATCH (p:Person)-[c:CONTRIBUTED_TO]->(proj:Project)-[:USES]->(s:Service {name:$service})
RETURN p.name AS person, count(*) AS touches, max(c.last_touch) AS latest
ORDER BY touches DESC LIMIT 5
```

```cypher
// 3. Provenance — where was this decided
MATCH (d:Decision)-[:ABOUT]->(p:Project {name:$project})
MATCH (d)-[:EVIDENCED_BY]->(ev)-[:AUTHORED_BY]->(who:Person)
OPTIONAL MATCH (d)-[:SUPERSEDES]->(prev:Decision)
RETURN d.id, d.summary, who.name AS author, ev.date, prev.summary AS superseded
```

> ⚠️ **Generate BOTH `DEPENDS_ON` and `HAS_DEPENDENT` from one DAG row.** Cypher cannot traverse an edge backwards. Skip the inverse edge and the blast-radius query silently returns `[]` — not an error, just nothing. This is a bug I hit while verifying this plan.

**Freshness is edge properties, not a system:** `valid_to` on `MEMBER_OF`, `last_verified_at` on contributions, `SUPERSEDES` on decisions. A separate staleness model turns "keep knowledge current" into a second project.

**B9 — order matters more than speed.** Build `docker-compose.yml` **first** — it's the Rule 10 fallback and it needs nothing but your own files. Then attempt the live URL. If the cloud deploy is fighting you at Sat 16:00, stop and ship compose. A working local setup scores; a broken live URL scores zero and costs you the video slot.

**B10 — record early, edit cheap.** Get a full 90s raw screen recording on Saturday, then cut. Editing a good take is fast; re-recording because the trail didn't render is not. Screen-record the **real app**, all three of you present, no music. Then **upload Sunday morning and open the link** — a private or expired video link is the single most common way a finished entry scores nothing.
</details>

<details>
<summary><b>5. The 20 ground-truth facts</b></summary>

Put these in `GROUND_TRUTH.md`. Company: **Helio** — 120-person fintech, 5 teams, 20 services, migrating payment providers.

> ⚠️ **Revised 2026-10-17.** Facts 5, 6, 7 and the DAG below were wrong and have been
> corrected. See the change log at the foot of this section. `GROUND_TRUTH.md` is the
> authoritative version — this section is a summary of it.

### Ownership

| # | Question | Correct answer |
|---|---|---|
| 1 | Who owns `payments-gateway` **today**? | **Ravi Menon** (Platform). Priya owned it until 2026-04-15 |
| 2 | Who owns `ledger-core`? | **Ledger** team, lead **Ana Duarte** |
| 3 | Who owns `fraud-scoring`? | **Risk** team, **Diego Alvarez** |
| 4 | Does every service have an owner? | **No.** `config-service` has **no `:OWNED_BY` edge** |

### Blast radius

| # | Question | Correct answer |
|---|---|---|
| 5 | What breaks if `payments-gateway` dies? | **8 services** — depth 1: `checkout-api`, `config-service`, `dispute-service`, `mobile-bff`, `notifications`, `webhook-relay` · depth 2: `fraud-scoring` · depth 3: `recommendation` |
| 6 | Which of those are owned by a different team? | Payments — `checkout-api`, `mobile-bff`, `dispute-service` · Growth — `notifications`, `recommendation` · Risk — `fraud-scoring`. Plus `config-service`, which has **no team at all** |
| 7 | Which dependent has no contributor in 90 days? | **`notifications`** — owned by Growth, one hop from payments, untouched since 2026-05-02. Bus-factor risk |

### Who knows what

| # | Question | Correct answer |
|---|---|---|
| 8 | Most commits on `payments-gateway`? | **Priya Sharma** — but last touch 2026-04-15, i.e. **stale**. Recency must reorder her below Ravi |
| 9 | Best person to ask about payments now? | **Ravi Menon** |
| 10 | Worked on **both** payments and ledger? | **Ana Duarte** — the only cross-team bridge |
| 11 | Who's on call for Ledger this week? | **Diego Alvarez**. Priya is on **no** rotation — she left in April |

### Provenance

| # | Question | Correct answer |
|---|---|---|
| 12 | Where was the migration decided? | **D-14**, 2026-03-18, author **Elena Vasquez** (CTO), evidence doc `payments-provider-eval-v3.md` |
| 13 | Was D-14 current? | **No — superseded by D-19** (2026-05-06): *Adyen primary, Stripe fallback, dual provider* |
| 14 | Decision authority for payments/ledger? | **Elena Vasquez** — the only `:Decision` author |
| 15 | The planted contradiction? | Doc + March Slack say **"single provider, Stripe"**; D-19 says **dual-provider, Adyen primary**. **Doc is stale** |

### Must FAIL correctly

| # | Question | Required behaviour |
|---|---|---|
| 16 | Who owns `config-service`? | **"No `:OWNED_BY` edge exists."** No invented owner |
| 17 | What did checkout decide about pricing? | **"No `:Decision` node about pricing."** No fabrication |
| 18 | Which service has zero dependents? | State which. Don't guess "payments" |
| 19 | Aisha Khan's current team? | **Departed 2026-06-30.** Not her old team |
| 20 | SLA for `dispute-service`? | Not in the graph. **Say so** |

### Service inventory — dependency DAG

20 services · 22 `DEPENDS_ON` edges · **verified acyclic**.

| Service | Depends on |
|---|---|
| `ledger-core` | — |
| `payments-gateway` | `ledger-core` |
| `checkout-api` | `payments-gateway` |
| `mobile-bff` | `payments-gateway` |
| `webhook-relay` | `payments-gateway` |
| `settlement-batch` | `ledger-core` |
| `dispute-service` | `payments-gateway`, `ledger-core` |
| `billing-invoicing` | `ledger-core` |
| `notifications` | `payments-gateway`, `dispute-service` |
| `reporting-etl` | `ledger-core`, `billing-invoicing` |
| `search-index` | `reporting-etl` |
| `fraud-scoring` | `checkout-api` |
| `auth-service` | — |
| `session-store` | `auth-service` |
| `api-gateway` | — |
| `config-service` | `payments-gateway`, `auth-service` |
| `user-profile` | `auth-service` |
| `recommendation` | `fraud-scoring`, `user-profile` |
| `web-frontend` | `api-gateway` |
| `admin-bff` | `api-gateway` |

> ⚠️ **`auth-service` and `api-gateway` depend on nothing, on purpose.** An earlier draft
> had both fanning out to "all public services". That made the graph **cyclic**
> (`api-gateway → web-frontend → api-gateway`, `api-gateway → admin-bff → api-gateway`)
> and dragged the whole frontend/edge tier into payments' blast radius, inflating fact 5
> to 14 services of which most were noise. The public tier is the *edge* — it is downstream
> of nothing. Removing the fan-in is what makes fact 5 a sharp answer.

### Change log — 2026-10-17, before any data was generated

| # | Was | Now | Why |
|---|---|---|---|
| 1 | `auth-service`, `api-gateway` → all public services | → nothing | 2 cycles + blast radius inflated to 14 |
| 2 | Fact 5 listed 7 services incl. `ledger-core`, `settlement-batch` | 8 services, upstream excluded | those two are **upstream** of payments — payments breaks if *they* die |
| 3 | Fact 7 → `settlement-batch` | → `notifications` | `settlement-batch` is not in the payments blast radius, so the question was unanswerable |
| 4 | "18 services" | **20 services** | `ledger-core` had no row despite 7 services depending on it |

### People

| Person | Team | Note |
|---|---|---|
| Elena Vasquez | — | CTO. Only `:Decision` author — **fact 14** |
| Ravi Menon | Platform | Current payments owner, on-call Ledger |
| Priya Sharma | ~~Payments~~ | **Left 2026-04-15.** Top by commits, stale — **fact 8** |
| Ana Duarte | Ledger | Only person on both payments + ledger — **fact 10** |
| Diego Alvarez | Risk | Owns fraud-scoring, on-call Ledger — **fact 11** |
| Aisha Khan | ~~Growth~~ | **Departed 2026-06-30** — **fact 19** |
| Tomas Berg | Payments | checkout-api, no decisions |
| Mei Lin | Platform | config-service contributor, no owner |
</details>

<details>
<summary><b>6. Verification procedure</b></summary>

- [ ] Ask all **20** questions through the running agent
- [ ] Compare each answer to `GROUND_TRUTH.md`
- [ ] Anything you can't confirm from **your own notes** is a bug or a graph hole — fix it, don't paper over it
- [ ] Log every failure in `VERIFICATION.md`: date, question, wrong answer, fix
- [ ] Re-run after each fix

**Gate 2 cannot pass until this is done.**

> An unverified demo is a worse entry than a smaller verified one. If you're out of time, ship 2 traversals and 10 verified facts rather than 3 traversals and no verification.
</details>

<details>
<summary><b>7. Traps that break first</b></summary>

**Fact 8 — the ranking trap.** Priya has the most commits but her last touch is April. `ORDER BY count DESC` returns Priya and is *technically correct on commits while being the wrong answer*. Return **both** volume and recency, and let the agent explain the tension.

> This is your best 20 seconds of demo. A naive query gets it wrong; yours catches it and explains why.

**Facts 16–20 — the fabrication trap.** *"Who owns config-service?"* → **"No `:OWNED_BY` edge exists."** An agent that invents an owner **has failed, even though the sentence sounds fine.** Most entries never test this.

**The silent-empty-result trap.** Wrong arrow direction returns `[]`, not an error. Before debugging a query, check the edge exists:
```cypher
MATCH (a)-[r]->(b) RETURN a.name, type(r), b.name LIMIT 20
```

**The dirty-graph trap.** `GRAPH.DELETE helio` before every reload, or you load twice into a dirty graph and every count is wrong.
</details>

<details>
<summary><b>8. Your three days</b></summary>

### Fri Oct 16

| Time | Do |
|---|---|
| 13:00 | **Register** · create repo, add teammates, make public · agree IP (Rule 15) |
| 13:30 | **B1** ground truth · **B2** schema |
| 14:00 | **B3** generator |
| **18:00** | 🛑 **GATE 1** — mock demo end-to-end, all three |
| 18:00 | **B4** load → graph populated |
| 20:30 | **B5** traversals in `graph.py` |
| **21:00** | 🛑 **GATE 2 (hard gate)** — all 20 ground truths correct |
| 21:30 | **B9a** `deploy/docker-compose.yml` — do it now, it's free, it's your fallback |
| 23:30 | **Stop. Sleep by 01:00.** |

### Sat Oct 17

| Time | Do |
|---|---|
| 09:00–11:00 | Integration with Soham · **B6** verification |
| 11:00 | 🛑 **GATE 3** — real-data demo on all three machines |
| 12:00–14:00 | **Break. Non-negotiable.** |
| 14:00–16:00 | **FEATURE FREEZE** · **B7** break-it pass · **B9b** live URL attempt |
| 16:00 | 🛑 **GATE 4** — deployed URL works from a cold browser (incognito) |
| 17:00–20:00 | **B10** video — script, record with all three, cut |
| 20:00–22:00 | **B8** README |
| **23:00** | 🛑 **GATE 5** — uninitiated teammate follows the README from scratch |

### Sun Oct 18

| Time | Do |
|---|---|
| 09:00–10:00 | **B10 upload + open the link.** Do this first. |
| 10:00–12:00 | Fix **only** what Gate 5 exposed |
| 12:00–14:00 | Video polish · **B8** final |
| **14:00** | 🛑 **HARD FREEZE** — nothing new after this line |
| 14:00–17:00 | Final deploy check · README · submission form filled |
| **17:00** | 🛑 **B11 SUBMIT.** Submit early. 7h buffer remains |

> Budget ~18h of solo work against 3 people × ~28h each — **now closer to 24h for you**, since `deploy/` and `video/` came across. **The constraint isn't hours — it is Gate 2.** If you feel the squeeze, cut polish from the video before you cut verification.
</details>

<details>
<summary><b>9. Gates</b></summary>

| # | When | Must be true | If not |
|---|---|---|---|
| 1 | Fri 18:00 | Mock demo runs end-to-end | Fix the contract before any real work |
| **2** | **Fri 21:00** | **All 20 ground truths correct** | **Cut to 2 traversals. No polish** |
| 3 | Sat 11:00 | Real-data demo on all three machines | Extend integration, cut features |
| 4 | Sat 16:00 | Deploy works from a cold browser | Fall back to local-setup README |
| 5 | Sat 20:00 | Video recorded and playable | Record an unedited take — it still submits |
| 6 | Sat 23:00 | Teammate follows README from scratch | Rewrite setup section |
| — | **Sun 14:00** | 🛑 **HARD FREEZE** | — |
| — | **Sun 17:00** | 🛑 **SUBMITTED** | 7h buffer left |

> Gates 4 and 5 are yours now. They are also the two most likely to fail, because both depend on the outside world — a hosting provider and an upload. **Both have fallbacks, so decide early rather than fighting at midnight.**

> Day 3 is empty on purpose. Deploys fail at 11pm, uploads fail, sites die mid-submission. Don't spend the buffer building.
</details>

<details>
<summary><b>10. If you're behind</b></summary>

Cut in this order:

1. Staleness query
2. 3rd traversal
3. Chat history
4. Dependency depth
5. **Video polish** — cuts before the video itself
6. **Live deploy** — `docker compose up` is a legal submission under Rule 10

**Never cut:** B6 verification · traversals · provenance data · deploy *fallback* · README · the video *existing*

> You now own twice the packaging, so the temptation to skip verification and "just get a demo up" is real. It's the wrong trade. A verified 2-traversal entry beats an unverified 3-traversal one every time. Cut scope, not rigour.

> State reasons when you cut. "Dropping the live deploy to protect verification time" lands. Going silent doesn't.
</details>

<details>
<summary><b>11. Handoffs</b></summary>

| To | What | When |
|---|---|---|
| **Soham** | Schema and expected function signatures from `graph.py` | Fri 14:00 — once B2 is done |
| **Ujwal** | The `trail[]` shape your Cypher *actually* returns | Sat 11:00 — his renderer needs the real shape, not the assumed one |
| **Both** | "Ground truth is planted, here's what's coming" | Fri 14:00 |
| **Ujwal** | Heads-up: `deploy/` and `video/` are yours now, plus `mock/` is his | Fri 13:00 — say it out loud, don't let it be a surprise |
| **Soham** | The deploy env vars he'll need on the live URL | Sat 14:00 |

> **`deploy/` and `video/` moved to you — tell the team today.** A silent ownership change reads as "nobody's doing it" and costs a day.

> **Gate 4 is yours and it's the most dangerous gate in the project.** A deploy that fails at Sat 16:00 is recoverable — you have the compose fallback and six hours. A deploy that fails at 02:00 Sun is not. So: compose first, live URL second, and stop at Sat 16:00 regardless.

> **Ujwal's mock data is your fastest integration path.** His `mock/` file matches the frozen contract exactly — you can test `graph.py`'s real output against it Friday night, before Soham's wiring is done.
</details>

<details>
<summary><b>12. Submission</b></summary>

Rule 10 — every item mandatory:

- [ ] Public repo
- [ ] README: setup instructions
- [ ] README: graph data model + diagram
- [ ] The Cypher queries the product depends on
- [ ] Demo video — **uploaded, then the link opened to confirm it plays**
- [ ] Live deploy **or** complete local setup *(yours)*
- [ ] Track declared — **Track 03: Company Brain**
- [ ] **AI-use disclosure** (Rule 11)
- [ ] All three can explain schema, queries, architecture, decisions (Rule 12)
- [ ] Data is synthetic/ours only (Rule 6)
- [ ] Main coding began after Oct 15, 00:01 IST (Rule 8)

**The two that quietly fail.** Both are yours, and both fail for reasons no amount of good code fixes:

| Item | The failure | The guard |
|---|---|---|
| Video link | private, expired, or wrong format → **judges see nothing** | Upload Sun 09:00. Open it in a logged-out browser. |
| Live deploy | works for you, blank for them | Incognito test, Sat 16:00, Gate 4 |

> Rule 10 requires the video. An entry with a broken video link is an entry with **no demo**, and "we had one" doesn't score.

**README positioning:**

> Existing enterprise search answers "where is the doc about X." We answer "who knows about X, what breaks if it goes down, where was that decided, and how current is that answer" — in one traversal, with the path shown. Text search is used only at the leaves.
>
> **Known limitation:** ACL/permission enforcement is out of scope. Glean's moat is that answers respect access control; production needs an authz layer over every traversal. Named rather than faked.

**Submit early.** The 7h buffer exists because something will break — and the two most likely things are the deploy and the video upload, both of which you now own. Your job at 17:00 Sun is to press the button, not to use the remaining time.

**Demo video beats (90 seconds, five):**

| Beat | Time | What |
|---|---|---|
| 1 | 0:00–0:10 | The multi-hop question, typed |
| 2 | 0:10–0:35 | Answer streams, trail chips render left to right |
| 3 | 0:35–0:55 | **The trap** — top contributor by commits is stale; the agent explains why |
| 4 | 0:55–1:15 | **The contradiction** — doc says Stripe-only, D-19 says Adyen primary; doc flagged stale |
| 5 | 1:15–1:30 | **The failure** — *"Who owns config-service?"* → *"No `:OWNED_BY` edge exists."* |

> Screen-record the **real app** with all three present. Not a mockup, not a prepared sequence. No background music — judges read your design off the interface, and music competes with it.
</details>

<details>
<summary><b>13. Prompt — <code>scripts/generate.py</code></summary>

```
I am building a FalkorDB-backed company-brain agent (Track 03). I own the data layer
and ALL Cypher. Generate ONLY the file I name, and respect these verified constraints:

- API: from falkordb import FalkorDB; db=FalkorDB(host,port); g=db.select_graph("helio")
  then g.query(cypher).result_set   <- result_set is REQUIRED, query() is not iterable
- FalkorDB is a SUBSET of OpenCypher. Never use Neo4j-only syntax.
- NEVER use undirected shortestPath((a)-[*]-(b)) -- unsupported. Directed form only.
- NEVER use db.idx.fulltext.* -- the procedure is not registered in the default image.
  Use WHERE x CONTAINS 'y' instead.
- NEVER return type(node) in the same RETURN as an optional node -- type mismatch.
  Return labels(node) instead.
- Variable-length + OPTIONAL MATCH + collect(DISTINCT) is VERIFIED WORKING. Use freely.
- Cypher CANNOT traverse an edge backwards. Any relationship needed in both directions
  must be generated TWICE under different names. My generator must emit BOTH
  DEPENDS_ON and HAS_DEPENDENT from one dependency DAG row.

The data must match GROUND_TRUTH.md EXACTLY -- 20 facts I wrote by hand, including
5-10 deliberate contradictions (reassignment, superseded decision, stale doc, unowned
service, departed employee). Those contradictions are the freshness demo and the proof
the agent is not just echoing text.

TASK: scripts/generate.py -- a seeded faker generator writing CSVs for a fictional
120-person fintech "Helio": 100 people, 5 teams, 20 services with a real acyclic DAG,
~200 documents, ~2000 chat messages that mention real services and people BY NAME,
~40 decisions with evidence links and at least one supersedes chain.

Output the file, then the exact command to run it, then what output proves it worked.
Do not add features I did not ask for.
```
</details>

<details>
<summary><b>14. Prompt — <code>scripts/load.py</code></summary>

```
FalkorDB, Python. Write scripts/load.py that reads my CSVs and loads them.

Constraints, all verified:
- g.query(cypher).result_set -- result_set is REQUIRED, query() is not iterable.
- FalkorDB is a SUBSET of OpenCypher. No Neo4j-only syntax.
- Create indexes BEFORE bulk loading:
    CREATE INDEX ON :Service(name)
    CREATE INDEX ON :Person(name)
    CREATE INDEX ON :Project(name)
    CREATE INDEX ON :Decision(id)
- Load with batched UNWIND, not one CREATE per row:
    UNWIND $rows AS row CREATE (s:Service {name: row.name, team: row.team})
  Pass every batch as a parameter. Never string-interpolate values into Cypher.
- Node creation and relationship creation must be SEPARATE passes. You cannot create
  a relationship before both endpoints exist.
- Wrap each node type in its own try/except and report which type failed and how many
  rows went in. A partial load that looks successful is worse than a loud failure.
- End by printing counts per label and assert they match the CSV row counts.

Tell me how many batches to use and roughly how long ~2,000 messages should take.
```
</details>

<details>
<summary><b>15. Prompt — <code>app/graph.py</code></summary>

```
FalkorDB, Python. Write app/graph.py -- this is the ONLY Cypher in the repo.

Constraints, all verified:
- g.query(cypher, params).result_set -- result_set is REQUIRED.
- FalkorDB is a SUBSET of OpenCypher. No Neo4j-only syntax.
- NEVER undirected shortestPath((a)-[*]-(b)) -- unsupported. Directed only.
- NEVER db.idx.fulltext.* -- not registered. Use WHERE x CONTAINS 'y'.
- NEVER return type(node) beside an optional node. Use labels(node).
- Variable-length + OPTIONAL MATCH + collect(DISTINCT) is VERIFIED WORKING.
- Cypher CANNOT traverse an edge backwards. Blast radius uses the inverse
  HAS_DEPENDENT edge I generate, NOT a reversed DEPENDS_ON.

Three functions, each taking params (never string-interpolated) and returning rows
that include the node path needed to render a provenance trail:

1. blast_radius(service) -> dependent services, hop depth, owning team, on-call people.
2. expertise(service) -> people ranked by contribution WITH RECENCY. Return volume AND
   recency, never a single ranking: the top contributor by commits is stale, and the
   agent must be able to explain that tension rather than hide it.
3. provenance(project) -> decisions, author, superseded decision, evidence node.
   Must traverse the SUPERSEDES chain so a superseded decision shows as superseded.

Plus a staleness query: edges whose last_verified_at is older than 90 days.

Every function must return the raw rows AND the nodes/edges that produced them, so the
frontend can render a trail with edge labels. Give me the exact Cypher for each.
```
</details>

<details>
<summary><b>16. Prompt — <code>deploy/</code></summary>

```
I am building a FalkorDB company-brain agent (Track 03). I own deploy/ and video/.
I do NOT write the frontend, the agent loop, or the Cypher.

TASK 1: deploy/ -- two deliverables, BOTH required.

(a) A Dockerfile + docker-compose.yml at the repo root so that `docker compose up`
    gives a COMPLETE working local setup on a clean machine with only Docker and
    Python installed. This is the mandatory fallback if deployment fails, and it is
    what I will ship if the live deploy does not work, so it MUST work.
    - services: falkordb (falkordb/falkordb:latest, port 6379) and the API (port 8000)
    - env_file for ANTHROPIC_API_KEY and FalkorDB credentials
    - depends_on ordering
    - the generator/load scripts must run as part of it, or the README must state
      the exact commands to populate the graph first

(b) A Fly.io config (fly.toml) that deploys the API connected to FalkorDB Cloud
    via environment variables. Include the secrets commands. Note in a comment that
    FalkorDB Cloud needs TLS on a non-default port, and that SSE needs
    `X-Accel-Buffering: no` or the proxy buffers the stream and it breaks in
    production only.

CRITICAL: SSE works locally and dies in production about half the time. Do not let
that surprise me. Comment every place the stream could be buffered.

Output: the compose file, the Dockerfile, and fly.toml, then the exact commands to
bring each up, then how to verify each one worked.
```
</details>

<details>
<summary><b>17. Prompt — demo video script</summary>

```
I am building a FalkorDB company-brain agent (Track 03). I own the demo video.

TASK: write my demo video script -- 90 seconds, 5 beats. This will be a screen
recording of the REAL running app, with all three of us present. No mockup, no
prepared sequence, no background music.

  0:00-0:10  the multi-hop question typed: "who knows about the payments service,
             what breaks if it goes down, and where was that decided?"
  0:10-0:35  the answer streams token by token and the provenance trail chips render
             left to right, each labelled with its edge (CONTRIBUTED_TO,
             EVIDENCED_BY, SUPERSEDES)
  0:35-0:55  the trap: the top contributor by commit volume is stale -- they left in
             April -- and the agent explains why the recent owner is the real answer
  0:55-1:15  the contradiction: a document says Stripe-only, a newer decision says
             dual-provider Adyen-primary, and the agent flags the document as stale
  1:15-1:30  the failure: "Who owns config-service?" -> "No OWNED_BY edge exists"

For EACH beat give me:
  - the exact keystrokes / clicks, so I can follow it while recording
  - the on-screen text that should appear
  - ONE narration line (max 20 words) -- I am not a narrator, so keep it minimal
  - what could go wrong in that beat and how to avoid it

Finish with a pre-record checklist I can run in 5 minutes before pressing record.
```
</details>

---

**Next:** write `GROUND_TRUTH.md` from section 5, then run prompt 13. Then `deploy/docker-compose.yml` Friday 21:30. Setup: [`setup.md`](setup.md).