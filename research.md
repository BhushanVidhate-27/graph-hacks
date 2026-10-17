# Research — Graph Hacks / FalkorDB / Company Brain

Everything collected so far, with sources. Compiled Fri 16 Oct 2026.

**Source tags used throughout:**

| Tag | Meaning |
|---|---|
| `[site]` | Read directly from the hackathon or docs page |
| `[verified]` | **Executed on this machine** — output confirmed |
| `[analysis]` | Our reasoning or judgement, not a fact from a source |
| `[unverified]` | Believed true, not tested |

---

## Index

| # | Section |
|---|---|
| 1 | [The hackathon](#) |
| 2 | [Rules that constrain us](#) |
| 3 | [Submission requirements](#) |
| 4 | [The three tracks](#) |
| 5 | [Track selection](#) |
| 6 | [Sponsor: FalkorDB](#) |
| 7 | [FalkorDB technical findings](#) |
| 8 | [Market landscape](#) |
| 9 | [Sponsor motive](#) |
| 10 | [Our architecture](#) |
| 11 | [Design decisions and why](#) |
| 12 | [Risks and open questions](#) |
| 13 | [Sources](#) |

---

<details>
<summary><b>1. The hackathon</b></summary>

`[site]` **Graph Hacks: Context for AI Agents** — WeMakeDevs × FalkorDB

| | |
|---|---|
| Dates | **Oct 15 – Oct 18, 2026** |
| Format | Online, from anywhere |
| Teams | Solo or up to 4 members; one team per participant |
| Prize pool | **$20,000 total** |
| Language | Open-ended — **no graph database experience assumed** |
| Sponsor Discord | `discord.com/invite/Y2mMT9VdMy` |

**Timeline `[site]`**

| When | What |
|---|---|
| Now | Registration open — *the only actionable checkpoint today* |
| **Oct 15, 00:01 IST** | Hacking begins. Code must start after this |
| **Oct 18, 23:59 IST** | Submissions close |

> ⚠️ **There are no intermediate milestones on the schedule page.** Nothing between "hacking begins" and "submissions close" — no checkpoints, no demo day, no judging rounds. Self-imposed gates are therefore mandatory, not a convenience.

**Eligibility `[site]`** — worldwide, free to enter, any programming language, existing projects may continue (Rule 8 covers this), coding assistants permitted with disclosure (Rule 11).

---

**Other pages `[site]`**

| Page | URL |
|---|---|
| Overview | `wemakedevs.org/hackathons/falkordb` |
| Schedule | `/hackathons/falkordb/schedule` |
| Rules | `/hackathons/falkordb/rules` |
| Resources | `/hackathons/falkordb/resources` |
| Docs | `docs.falkordb.com` |
| FalkorDB Cloud | `app.falkordb.cloud` |
</details>

<details>
<summary><b>2. Rules that constrain us</b></summary>

`[site]` All 18 rules. The six that actually shape our decisions:

**Rule 2 — FalkorDB must be the primary graph database** and must support a central part of what the product does. Not a sidecar, not one of several.

**Rule 3 — the graph must do real work.** This is the dangerous one:
> *"A visualisation drawn on top of ordinary storage does not qualify: if the product still works once FalkorDB is taken out, the graph is decoration rather than the thing the product runs on."*

→ **Our retrieval path must *be* Cypher traversals.** A RAG chatbot with a graph-rendered org chart is disqualified by construction. This also rules out a network-graph canvas in the UI.

**Rule 6 — data must be public, synthetic, or our own.** No private, login-protected, paywalled, personal, or restricted data.
→ **Rules out ingesting a real company's Slack.** Forces synthetic data or public corpora.

**Rule 8 — main coding and design must begin after Oct 15, 00:01 IST.** Ideas, notes, graph models and diagrams beforehand are explicitly permitted.
→ Planning documents are legal. Pre-built code would not be.

**Rule 11 — AI assistants allowed, use must be disclosed.** `[analysis]` Disclosing costs nothing and is mandatory; getting disqualified for non-disclosure costs everything.

**Rules 12–13 — we must understand the code and explain the graph model, queries, architecture and technical decisions.** Projects entirely AI-generated without meaningful contribution or understanding may be rejected.
→ This is the rule with a hidden price tag: AI-written code you haven't internalised is a liability at judging. See §12.

**Other rules `[site]`** — 1 (team size), 4 (deployment freedom), 5 (name your tracks on submission), 9 (OSS/public APIs/templates permitted), 14 (prizes), 15 (IP ownership — agree internally), 16–17 (conduct, no plagiarism or judging manipulation), 18 (failure to comply → disqualification).
</details>

<details>
<summary><b>3. Submission requirements</b></summary>

`[site]` **Rule 10 — every submission must include:**

| # | Item | Notes |
|---|---|---|
| 1 | **Public source-code repository** | must be public |
| 2 | **README with setup instructions** | |
| 3 | **README with your graph data model** | |
| 4 | **The Cypher queries or graph algorithms the product depends on** | the queries themselves, not a description of them |
| 5 | **A demo video showing the working project** | |
| 6 | **A live deployment, or complete local setup instructions** | local setup is an accepted fallback |
| 7 | **The track you are entering** | must be named |

Plus, from other rules: AI-use disclosure (11), data legality (6).

> `[analysis]` Five of these seven are *documents*, not code. That's roughly half the submission, and it's the half nobody plans for. The README and video are as load-bearing as the graph.
</details>

<details>
<summary><b>4. The three tracks</b></summary>

`[site]`

| Track | Build | Prize |
|---|---|---|
| **01 — Agents That Act on Connected Data** | Agent that uses the graph to decide and act — fraud, security triage, codebase analysis | **iPhone 18 Pro** |
| **02 — Agent Memory and Coordination** | Agents that remember across sessions and share state | **PS5 with GTA VI** |
| **03 — Company Brain** | Agent that understands how a company works — people, teams, projects, docs, decisions in one graph | **M6 Mac Mini** |

`[site]` **Key focus per track:**

**01** — multi-hop reasoning · graph queries and algorithms as agent tools · tool selection through MCP · actions based on what the graph shows · explainable results

**02** — episodic, semantic and procedural memory · persistent conversation history · shared state and handoffs between agents · high-concurrency reads and writes · separate memory per user or tenant

**03** — knowledge from docs, tickets and chats in one graph · who owns what, and who knows what · tracing decisions back to source · keeping knowledge current as things change · answers with clear sources

**Side prizes `[site]`**

| Prize | Award | Who |
|---|---|---|
| Best blog post | **AirPods 5** | 1 winner |
| Top 50 submissions | **T-shirt** | every member of each of the top 50 teams |

**Rules `[site]`** — you may enter one, two, or all three tracks; you must name every track you're entering at submission.

> `[analysis]` Prizes are consumer goods, not cash. Total $20k across a global 3-day event is poor money for the effort. The realistic payoff is a strong portfolio project plus a top-50 t-shirt — worth calibrating expectations on.
</details>

<details>
<summary><b>5. Track selection</b></summary>

`[analysis]` We chose **Track 03 — Company Brain**.

**Difficulty ranking: 02 easiest → 03 middle → 01 hardest.**

**02 is easiest** because the data is self-generated — no external corpus to ingest. The schema (sessions, messages, facts, handoffs) is well-trodden via mem0/Graphiti/Letta. The demo is easy to stage. Its risk is *generic*: judges see many "chatbot with memory" demos, so the bar isn't having memory, it's memory that's **good** — updates on change, handles contradictions, doesn't grow unbounded, scoped per tenant.

**03 is middle** — highest demo ceiling of the three, but the risk is spending all your time on ingestion and entity resolution and having nothing working. Mitigated by synthetic data, which removes ingestion entirely and gives known ground truth.

**01 is hardest** because it needs a genuinely connected dataset (transactions, security findings) *and* a pipeline to build it. Get that wrong and it's a chatbot with a graph bolted on — exactly what Rule 3 disqualifies.

**Why 03 anyway `[analysis]`:** it's the only track where the *data model itself* is the intellectual work. In 02 the model is plumbing; in 01 the data is the bottleneck. In 03 the model — people, ownership, decisions, freshness — is the whole contribution, and it maps directly onto the company's stated key-focus list. It also scores best on the demo video, which is a mandatory deliverable.

**Overlap warning `[analysis]`** — 02 and 03 substantially overlap: both are "connect things and remember". Enter both with the same project looks unfocused. Pick one.

**The framing `[analysis]`:**

> Traverse the relationships first. Search text only at the leaves.

Vector retrieval captures similarity between *text*; these answers live in *structure*. "Who knows about payments, what breaks if it goes down, and where was that decided?" spans a dependency DAG, an on-call rota, a decision doc and a Slack thread from eight months ago. No single document contains it. That's why retrieval has to be traversal.
</details>

<details>
<summary><b>6. Sponsor: FalkorDB</b></summary>

`[site]` Positioning and claims from the hackathon page:

- Open-source graph database **built for AI agents**
- "Traversals are fast enough to run on **every step of an agent loop**"
- One instance holds **thousands of isolated graphs** via multigraph topology → one graph per user, agent or tenant, without separate deployments
- Query language: **Cypher**
- Graph algorithms as agent tools: **shortest path, PageRank, centrality, connected components, community detection**
- Official clients: **Python, Node.js, Java, Rust, Go, PHP, C#**
- Listed integrations: **GraphRAG-SDK, QueryWeaver, MCP, Graphiti, Cognee, LangChain, LlamaIndex**
- **FalkorDB Browser** for running queries and inspecting the data model
- One-line start: `docker pull falkordb/falkordb:latest`

**The sponsor's own example query `[site]`** — and note it's structurally the same shape as ours:

```cypher
MATCH (p:Person)-[:WORKED_ON]->(:Project)-[:USES]->(s:System {name: $system})
RETURN p.name AS person, count(*) AS projects
ORDER BY projects DESC
LIMIT 5
```
*(the "who knows about this system" example — multi-hop through a project to a system, with a count aggregate)*

> `[analysis]` The sponsor is signalling what they want: multi-hop traversal returning counts, not keyword search. Our three traversals sit exactly in that space.

---

**Docs reference `[site]`**

| Page | URL |
|---|---|
| Getting started | `docs.falkordb.com/getting-started/` |
| Cypher | `docs.falkordb.com/cypher/` |
| Cypher support / limitations | `docs.falkordb.com/cypher/cypher-support`, `/known-limitations` |
| Clients | `docs.falkordb.com/getting-started/clients` |
| Algorithms | `docs.falkordb.com/algorithms/` |
| Browser | `docs.falkordb.com/browser/` |
| Docker | `docs.falkordb.com/operations/docker` |
| Configuration | `docs.falkordb.com/getting-started/configuration` (`BOLT_PORT`, `GRAPH.CONFIG SET`) |
| Integrations | `docs.falkordb.com/integration/` |
| GitHub | `github.com/FalkorDB/FalkorDB` |
</details>

<details>
<summary><b>7. FalkorDB technical findings</b></summary>

`[verified]` Everything in this section was **executed** against FalkorDB `latest` on this machine — image digest `b0bdcac2cbaff989e77cb0610439b7a9289e86de033ccbbd4368b66fb680ae7e`.

**Client API `[verified]`**

```python
from falkordb import FalkorDB
db = FalkorDB(host="localhost", port=6379)
g  = db.select_graph("helio")
g.query(cypher)          # -> QueryResult
g.query(cypher).result_set   # -> [[1]]   <-- REQUIRED
```

> ⚠️ **`QueryResult` is not iterable.** `for row in g.query(...)` raises `TypeError: 'QueryResult' object is not iterable`. This is the single most expensive gotcha in the stack — it costs the first hour and fails confusingly.

**`QueryResult` attributes `[verified]`**
`cached_execution` · `header` · `indices_created` · `indices_deleted` · `labels_added` · `labels_removed` · `nodes_created` · `nodes_deleted` · `properties_removed` · `properties_set` · `relationships_created` · `relationships_deleted` · **`result_set`** · `run_time_ms`

`run_time_ms` is free per-query timing — use it to decide whether the bulk loader is needed.

---

**Works `[verified]`**

| Feature | Result |
|---|---|
| Variable-length `[:TYPE*1..4]` | ✅ |
| Variable-length + `OPTIONAL MATCH` + `collect(DISTINCT)` | ✅ returned `[['ledger', 'Platform', ['Ravi']]]` |
| `length(path)` for hop depth | ✅ |
| `count()` / `max()` aggregate with `ORDER BY` | ✅ |
| `MERGE … ON CREATE SET` | ✅ |
| `CREATE INDEX ON :Label(prop)` | ✅ |
| `db.indexes()` | ✅ |
| `WHERE x CONTAINS 'y'` text search | ✅ |
| Directed `shortestPath((a)-[*]->(b))` | ✅ |

**Does not work `[verified]` — three findings that each broke a planned query**

| Attempted | Result | Use instead |
|---|---|---|
| `shortestPath((a)-[*]-(b))` **undirected** | `FalkorDB does not currently support undirected shortestPath traversals` | directed `[*]->` only |
| `db.idx.fulltext.createNodeIndex(...)` then `db.idx.fulltext.query(...)` | creation appeared to succeed; **query failed** — `Procedure db.idx.fulltext.query is not registered` | `WHERE body CONTAINS 'x'` |
| `RETURN type(ev)` alongside an optional node | `Type mismatch: expected Edge or Null but was Node` | return `labels(node)` instead |

---

**Bugs this verification caught in our own plan `[verified]`**

1. **Reversed arrow in the blast-radius query.** `(payments)<-[:DEPENDS_ON*1..4]-(dep)` returned `[]`. The stored edge is `(payments)-[:DEPENDS_ON]->(ledger)` meaning *payments depends on ledger*. Reversing the arrow to find dependents walks the wrong way — and **fails silently with an empty result, not an error.**
2. **Blast radius and upstream impact both need forward traversal.** Cypher cannot walk an edge backwards at all. → **Generate both `DEPENDS_ON` and `HAS_DEPENDENT` from one DAG row.**
3. **A `RETURN` mixing `type()` with an optional node is a type error** — caught before it reached a demo.

---

**General behaviour `[site]`**

- **Subset of OpenCypher** with proprietary extensions — do not assume Neo4j-only syntax. Check `/cypher/known-limitations`.
- Speaks the **Redis protocol** — `GRAPH.QUERY` / `GRAPH.RO_QUERY`, not Bolt, by default.
- **Bolt is experimental**, enabled via the `BOLT_PORT` configuration parameter. Official clients support both RESP and Bolt.
- **Successor to RedisGraph**, built by the same team. RedisGraph reached **end-of-life 31 Jan 2025** — a separate product; never present old RedisGraph clients or behaviour as current.
- **Official clients `[site]`:** `falkordb-py` (pypi: `falkordb`), `falkordb-ts` (npm), `jfalkordb` (maven), `falkordb-rs` (crates), `falkordb-go`, `falkordb-php`, `NFalkorDB` (nuget). Community/OGM: `falkordb-py-orm`, `falkordb-go-orm`, `spring-data-falkordb`.
- Old RedisGraph clients may work via protocol compatibility but are **officially unsupported** — use official clients only.

**Integrations `[site]`** — REST API · Kafka Connect sink · Apache Jena (RDF/SPARQL) · Spring Data FalkorDB · Snowflake Native App · **n8n GraphRAG community nodes** · PyTorch Geometric · **Graphify** (KG generation from code/docs/PDFs → FalkorDB) · **bulk loader** (CSV → binary batches).

**Environment `[verified]`**

| Item | Result |
|---|---|
| Python 3.14.2 | ✅ `pip install falkordb faker` clean — this was the main risk, wheels often missing on new Pythons |
| Docker 29.9.1 | ✅ pull + run + Cypher all working |
| Node 22 | present, unused |

> `[analysis]` If a dependency fails to build on 3.14, drop to 3.12 rather than debugging the build — no time budget for it.
</details>

<details>
<summary><b>8. Market landscape</b></summary>

`[analysis]` based on `[site]` sponsor context. Competitors are real products; the gap assessment is our judgement.

**Crowded — enterprise search `[unverified]`**

| Product | Notes |
|---|---|
| **Glean** | Category leader. Notably built on a "Work Graph" of people, content and org structure internally. **Permissions-aware answers are its actual moat** |
| **Microsoft Graph** | M365 already holds people, files, meetings and org data; Copilot sits on top. The most under-appreciated competitor to any "company brain" idea |
| **Notion AI** | Wiki Q&A for company docs |
| **Atlassian Rovo / Confluence** | Search + agents across tickets and docs |
| **Google Workspace** | Suite-level Q&A |
| **Sana** | Markets itself around "company brain" |

**Crowded — agent memory (Track 02's real competition) `[unverified]`**

- **Zep / Graphiti** — temporal knowledge graphs for agents; closest existing thing to Track 02
- **Mem0**, **Cognee**, **Neo4j agent memory**, **LangChain graph memory**

**Crowded — GraphRAG `[unverified]`**

- Microsoft GraphRAG · Neo4j GraphRAG for Python · **FalkorDB GraphRAG SDK** (sponsor's own)

**Thin — the composite traced answer `[analysis]`**

Almost none of them answer the *composite* multi-hop question with a traced path:

> *Who knows about the payments service, what breaks if it goes down, where was that decided, and how current is that answer?*

Search products stop at "here are the docs". Provenance usually means a doc citation, not the decision chain that produced the claim. Change-awareness is usually a separate alerting system, not part of the answer.

**Positioning consequence `[analysis]`:** don't position as "company search" — that comparison loses instantly against Glean. Position as **answers that show their path**, and name the difference before the judge does.

**Gap to name in the README `[analysis]`:** permission/ACL enforcement. Glean's entire value is that answers respect ACLs; that can't be faked in a hackathon. Naming it as known future work reads as maturity. Inviting the question by staying silent reads as not having thought about it.
</details>

<details>
<summary><b>9. Sponsor motive</b></summary>

`[analysis]` — inference, not stated by the organiser.

**FalkorDB**

1. **Category repositioning.** Graph databases lost the 2010s to Postgres/Snowflake. "Graph DB for AI agents" is the wedge that works *now* — an agent loop issues many small traversals per step, which is where low-latency traversal beats a round trip to a vector store.
2. **The multigraph story needs evidence.** "Thousands of isolated graphs per instance" is the multi-tenant agent-memory pitch. It only lands if people actually build the demos. A hackathon is customer acquisition for the *use case*, not the database.
3. **Reference architectures.** Winning repos become the templates people copy — the cheapest ecosystem and docs strategy available.
4. **Beat the "it's just RAG" narrative** in public, with examples that don't come from a vendor.

**The prize choice is deliberate `[analysis]`** — iPhone, PS5 + GTA VI, Mac Mini, AirPods. Not cash. Cheaper for the sponsor, better PR than "$50k to a startup," and legible enough to pull in people who'd never register for a database conference. It's a funnel.

**WeMakeDevs `[analysis]`** — community growth. Many hackathons; the metric is registration volume and content, not rigorous judging. Don't read the judging as adversarial.

---

**The alignment `[analysis]`:** the sponsor wants demos proving a graph is load-bearing in an agent loop. Our interest lines up exactly — provided we build the *traced multi-hop* thing rather than another chat-with-memory.

---

**Open items `[analysis]**

| Item | Status |
|---|---|
| Are all three registered? | **Unconfirmed — do this first** |
| Public repo created + collaborators added | Unconfirmed |
| IP ownership agreed in writing (Rule 15) | Unconfirmed |
| FalkorDB Cloud account | Ujwal, before Fri 18:00 |
| Anthropic key + billing credit | Soham/Bhushan |
| `trail[]` shape agreed across all three | **Before Fri 14:00** |
</details>

<details>
<summary><b>10. Our architecture</b></summary>

`[analysis]`

```
┌──────────────────────────────────────────────────┐
│  Browser — vanilla JS, no build step              │
│  question box · streamed answer · provenance trail│
└──────────────────────┬───────────────────────────┘
                       │ POST /ask  →  SSE
┌──────────────────────▼───────────────────────────┐
│  FastAPI  (Soham)                                 │
│    GET /health · CORS for :3000                   │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│  Anthropic tool-use loop  (Soham)                │
│    model SELECTS the traversal from the question │
│    every claim tied to trail rows                │
│    empty result → "don't know"                   │
└──────┬──────────────────────┬────────────────────┘
       │                      │
┌──────▼──────────┐  ┌────────▼────────────────────┐
│ graph.py        │  │ staleness → stale[] badges   │
│ (Bhushan)       │  │ (Bhushan)                    │
│ ONLY Cypher      │  └─────────────────────────────┘
└──────┬──────────┘
       │
┌──────▼──────────────────────���────────────────────┐
│  FalkorDB  (Docker local · Cloud prod)           │
│  isolated graph "helio"                          │
└──────────────────────────────────────────────────┘

Offline / data layer (Bhushan, no dependency on the above):
  GROUND_TRUTH.md → generate.py → CSVs → load.py → FalkorDB
```

**Stack**

| Layer | Choice | Why |
|---|---|---|
| Graph DB | **FalkorDB** | mandatory; Docker local, Cloud prod |
| Language | **Python 3.11+** (3.14.2 verified) | one language end to end |
| Client | `falkordb` (official `falkordb-py`) | not old `ioredisgraph` |
| API | FastAPI + `uvicorn[standard]` | SSE streaming |
| LLM | Anthropic SDK | **tool use is the product** |
| Validation | pydantic | tool arg schemas free |
| Data gen | faker + stdlib random/datetime | synthetic company |
| Debug | FalkorDB Browser | main dev loop |
| Frontend | single page, vanilla JS | no build step |

**Deliberately excluded `[analysis]`**

| Excluded | Why |
|---|---|
| LangChain / LlamaIndex | adds indirection over the exact tool loop being judged |
| Vector DB / embeddings | invites "it's just RAG"; `CONTAINS` at the leaves is enough |
| Neo4j driver | Bolt is experimental; official client is the supported path |
| Graphify / Cognee | they write the schema — Rule 12 means we defend every edge type |
| Graph visualisation | Rule 3 bans graphs-as-decoration; a network canvas actively hurts |
| Framework in the agent loop | Rule 12 — must explain every line under questioning |
</details>

<details>
<summary><b>11. Design decisions and why</b></summary>

`[analysis]` unless tagged otherwise.

**Synthetic data over public corpora.** Rule 6 forbids restricted data, so "ingest a company Slack" is out. Synthetic gives known ground truth, so we can prove the agent isn't hallucinating, and removes ingestion from the critical path entirely. The weakness — it reads as fake — is fixed by making the fictional company specific and coherent.

**Both `DEPENDS_ON` and `HAS_DEPENDENT`.** `[verified]` Cypher cannot traverse an edge backwards. Two different questions (what does X need / what breaks if X dies) both need a *forward* walk, so both relationships must physically exist. Generated from one DAG row.

**Freshness as edge properties.** `valid_to` on `MEMBER_OF`, `last_verified_at` on contributions, `SUPERSEDES` on decisions. A separate staleness model turns "keep knowledge current" into a second project we can't afford.

**`CONTAINS` over full-text search.** `[verified]` `db.idx.fulltext.query` isn't registered in the default image. `CONTAINS` works and is simpler — no index setup, no extra failure mode.

**Plain Cypher over built-in algorithms.** The three traversals are easy in Cypher, and whatever we use we must explain (Rule 12). Documented algorithms exist; using them is optional, not required by the rules.

**No framework in the agent loop.** Rule 12 requires explaining the architecture. A framework hides exactly the part being judged.

**Model picks the tool.** A pipeline that runs all three queries and concatenates is a search box. The demonstration of agentic behaviour is that the *model* selects the traversal from the question — including the compound demo question hitting all three in sequence.

**Claims tied to trail rows.** The model must never assert a fact no tool returned. This is both an accuracy property and a Rule 12 talking point.

**Contract-first, mocks-first.** Soham freezes `trail[]` by 15:00 and ships fake endpoints. Ujwal builds all day against fakes; Bhushan's delay costs nobody. Gate 2 swaps one branch.

**File ownership, no drive-by PRs.** Bhushan owns `graph.py`, Soham owns `agent.py`/`main.py`, Ujwal owns `web/`+`deploy/`. With three people and two days, an unowned file is how you lose a night to a merge.

**Verification against hand-written ground truth.** An AI generated the data, the agent *and* the answer — asking AI "is this right?" is circular, because a hallucinated ownership chain is indistinguishable from a correct one at the text level. Only someone who wrote the planted truth independently can check it.

**Correct failure is a feature.** Five questions are designed to be unanswerable. An agent that invents an owner *has failed, even though the sentence reads fine* — and the failure case is a demo beat, not a limitation.

**Deploy both ways.** Live URL is stronger for judges; `docker compose up` on a clean machine is the Rule 10 fallback and the insurance if the cloud deploy dies at 11pm.

---

**Graph model**

```
(:Person)-[:MEMBER_OF {since, role, valid_to}]->(:Team)
(:Person)-[:CONTRIBUTED_TO {role, commits, last_touch}]->(:Project)
(:Person)-[:REPORTS_TO]->(:Person)

(:Project)-[:OWNED_BY]->(:Team)
(:Project)-[:USES]->(:Service)

(:Service)-[:DEPENDS_ON]->(:Service)          -- what it needs
(:Service)-[:HAS_DEPENDENT]->(:Service)       -- what breaks if it dies
(:Service)-[:OWNED_BY]->(:Team)

(:Team)-[:HAS_ROTATION]->(:Member)-[:ON_CALL]->(:Person)

(:Decision)-[:ABOUT]->(:Project)
(:Decision)-[:EVIDENCED_BY]->(:Document|Message)
(:Decision)-[:SUPERSEDES]->(:Decision)

(:Message)-[:IN_CHANNEL]->(:Channel)
(:Message)-[:MENTIONS]->(:Person)
(:Document)-[:AUTHORED_BY]->(:Person)
(:Ticket)-[:ASSIGNED_TO]->(:Person)
(:Ticket)-[:BLOCKS]->(:Ticket)
```

**Synthetic company — "Helio"** `[analysis]` — 120-person fintech, 5 teams, 18 services, mid-migration to a new payments provider. ~100 people · ~200 documents · ~2,000 chat messages · ~40 decisions. Chat messages **must** mention real entities by name, or the graph has no leaves for text search and the provenance trail has nothing to point at.

**The 20 ground-truth facts** are enumerated in [`bhushan.md`](bhushan.md) §5 — 15 answerable, 5 designed to fail.
</details>

<details>
<summary><b>12. Risks and open questions</b></summary>

`[analysis]`

**Risks, highest first**

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Sunday deploy failure** | High | Submission dead | `docker compose up` fallback written **before** Sat 17:00; test on a clean machine |
| **Demo video upload/link failure** | Medium | Mandatory deliverable missing | Record locally as well as uploading; **open it after upload**; verify it's not a private link |
| **Ground truth not verified** | Medium | Entry is unprovable | Gate 2 blocks everything; 20 facts tested before any polish |
| **Rule 3 violation** | Medium | Disqualification | Retrieval path *is* Cypher; remove FalkorDB and it must collapse, not degrade |
| **Registration not done** | Unknown | Cannot submit | Do it now — it's the only actionable checkpoint |
| **"just RAG" read** | Medium | Loses the track | State positioning in the README; show that text search is only used at the leaves |
| **Python 3.14 build failure** | Low | Blocks install | Fall back to 3.12 immediately, don't debug |
| **MCP time sink** | Medium | Wastes the critical path | Hard 30-minute cap; skip if tools already work |

**Hidden costs**

- **Rule 12/13 is the expensive one.** AI-written code you haven't internalised is a liability at judging. Budget real time to read what you submit — this is the hidden price of heavy AI use, and it's why Rule 13 exists.
- **Rule 8.** Build must have started after Oct 15. Our planning documents are notes and diagrams, which are explicitly permitted.

**Known limitations to declare rather than hide**

- **ACL / permission enforcement** — out of scope. Production needs an authz layer over every traversal. This is Glean's moat.
- **Synthetic data** — Helio is fictional, by design (Rule 6).
- **Entity resolution is trivial** — the generator knows ground truth. Real deployment needs dedup across `@priya` / `Priya Sharma` / `@psharma`.

**Open questions**

| Question | Owner | Needed by |
|---|---|---|
| What's the exact `trail[]` shape Bhushan's Cypher actually returns? | Bhushan + Soham | **Fri 14:00** |
| FalkorDB Cloud: TLS required, non-default port? | Ujwal | Fri 18:00 |
| Does the submission form have video duration/resolution limits? | Ujwal | Sat |
| Which deploy target — Fly.io or Vercel? | Ujwal | Fri 18:00 |
| Is MCP worth the time given working tools? | all three | Sat morning |
</details>

<details>
<summary><b>13. Sources</b></summary>

**Hackathon**

- `wemakedevs.org/hackathons/falkordb` — overview, tracks, prizes, FAQ
- `wemakedevs.org/hackathons/falkordb/rules` — all 18 rules
- `wemakedevs.org/hackathons/falkordb/schedule` — timeline, checkpoints
- `wemakedevs.org/hackathons/falkordb/resources` — docs links, videos
- Code of Conduct: `wemakedevs.org/coc`

**FalkorDB docs**

- `docs.falkordb.com` — index at `docs.falkordb.com/llms.txt`
- `docs.falkordb.com/getting-started/clients` — official client table
- `docs.falkordb.com/integration/` — REST, Kafka Connect, n8n, PyG, Graphify, bulk loader
- `docs.falkordb.com/cypher/`, `/cypher/cypher-support`, `/cypher/known-limitations`
- `github.com/FalkorDB/FalkorDB` · `github.com/FalkorDB/GraphRAG-SDK`

**Product**

- `app.falkordb.cloud` — Cloud signup
- `docs.falkordb.com/browser/` — Browser

**Locally verified**

- `falkordb/falkordb:latest`, digest `b0bdcac2cbaff989e77cb0610439b7a9289e86de033ccbbd4368b66fb680ae7e`
- Python 3.14.2 · Docker 29.9.1 · Node v22.23.3
- All Cypher findings in §7 executed against a live instance

**Companion docs**

| File | Contents |
|---|---|
| [`setup.md`](setup.md) | macOS/Linux setup, 21 steps |
| [`setup-windows.md`](setup-windows.md) | Windows equivalent, same numbering |
| [`bhushan.md`](bhushan.md) | Critical path — data, Cypher, verification, submission |
| [`soham.md`](soham.md) | Contract, agent loop, backend |
| [`ujwal.md`](ujwal.md) | Provenance renderer, deploy, demo video |

---

**Not covered yet `[analysis]`** — we haven't read FalkorDB's algorithms or Cypher-support pages in depth, and haven't looked at what `npx @modelcontextprotocol/inspector` or the GraphRAG SDK would actually give us. Both are optional; revisit only if the core plan slips.
</details>