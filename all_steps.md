# All Steps — Graph Hacks · Track 03: Company Brain

Complete build order, Oct 15–18, 2026. **140 steps.**
Every step is small enough to finish in one sitting and check off when done.
**Click any step to unfold it.**

> **Read this first.** Steps 1–20 are shared setup. After step 20 the work splits
> three ways. Steps 21–60 are sequential and owned by Bhushan — nobody can skip
> ahead of them. Steps 61–80 run in parallel. Steps 81–140 are packaging and
> submission. ⚠️ marks a step that fails silently if you get it wrong.

---

## Index

| Phase | Steps | Who | Gate |
|---|---|---|---|
| 0 — Register & ground | 1–12 | all | — |
| 1 — Environment | 13–32 | all | — |
| 2 — Repo & ownership | 33–40 | Bhushan | — |
| 3 — Contract freeze | 41–48 | Soham | **S1** |
| 4 — Mock data | 49–56 | Ujwal | Fri 13:30 |
| 5 — Ground truth & schema | 57–64 | Bhushan | Fri 14:00 |
| 6 — Generator | 65–72 | Bhushan | — |
| 7 — Loader | 73–80 | Bhushan | Fri 18:00 |
| 8 — Cypher | 81–88 | Bhushan | — |
| 9 — Agent & API | 89–98 | Soham | **Gate 2** |
| 10 — Frontend | 99–106 | Ujwal | **Gate 2** |
| 11 — Verification | 107–116 | all | **Gate 2** |
| 12 — Deploy | 117–126 | Bhushan | **Gate 4** |
| 13 — Video | 127–132 | Bhushan | **Gate 5** |
| 14 — README | 133–137 | Bhushan | — |
| 15 — Submission | 138–140 | Bhushan | Sun 17:00 |

---

## Phase 0 — Register & ground · Steps 1–12

<details>
<summary><b>1. Register all three team members</b></summary>

Go to `wemakedevs.org/hackathons/falkordb` and register Bhushan, Soham and
Ujwal. Free, worldwide, any language, teams of up to 4. This is the **only hard
checkpoint the organiser sets** — everything else in this file is
self-imposed. Do it before anything else.

</details>

<details>
<summary><b>2. Decide the track in writing</b></summary>

Track **03 — Company Brain**. Post it in the team chat so all three agree and
there is a written record. Do **not** also enter Track 02 — the two overlap
heavily, and entering both with one project reads as unfocused.

</details>

<details>
<summary><b>3. Agree IP ownership (Rule 15)</b></summary>

Message each other in writing: all code goes into the shared public repo, all
three are authors, nobody claims individual ownership. Keep the message —
Rule 15 is checked, and "we discussed it" is not evidence.

</details>

<details>
<summary><b>4. Join the sponsor Discord</b></summary>

`discord.com/invite/Y2mMT9VdMy`. This is where FalkorDB staff answer questions
during the hackathon. Join before you need it — at 1am on Saturday the
response time is very different.

</details>

<details>
<summary><b>5. Read the rules once, all three of you</b></summary>

At minimum: Rule 2 (FalkorDB must be primary), Rule 3 (the graph must do real
work), Rule 6 (synthetic data only), Rule 8 (coding starts after Oct 15 00:01
IST), Rule 10 (submission items), Rule 11 (AI disclosure), Rules 12/13 (you
must be able to explain the code).

</details>

<details>
<summary><b>6. Mark the three rules that will disqualify us</b></summary>

- **Rule 3** — if the product still works with FalkorDB removed, the graph is
  decoration. Our retrieval path must *be* Cypher traversals.
- **Rule 6** — never ingest a real company's Slack. Synthetic only.
- **Rule 8** — no pre-built code. Planning notes and diagrams are explicitly
  permitted, so these `*.md` files are legal. A pre-written app is not.

</details>

<details>
<summary><b>7. Mark the deadline in IST</b></summary>

Submissions close **Oct 18, 23:59 IST** — not local time, not GMT. Run
`TZ=Asia/Kolkata date` and confirm what IST says right now. Then set two
alarms: **Oct 18 14:00 IST** (hard freeze) and **Oct 18 17:00 IST** (submit).
Both are buffer targets, not the real deadline.

</details>

<details>
<summary><b>8. Start the team chat and pin one message</b></summary>

Pin: the three names, the track, the file ownership table from step 35, and
**"`deploy/` and `video/` are Bhushan's"**. A silent ownership change reads as
"nobody's doing it" and costs a day.

</details>

<details>
<summary><b>9. Agree who creates the repo</b></summary>

Bhushan. Everyone else waits for the URL. Three people independently creating
three repos is twenty minutes of merge pain.

</details>

<details>
<summary><b>10. Agree the AI-use disclosure policy now</b></summary>

Rule 11 is mandatory and costs nothing to satisfy. Agree today that we disclose
prompt-assisted work in the README. Discovering this on Sunday night is a
crisis; deciding it on Friday afternoon is a paragraph.

</details>

<details>
<summary><b>11. Agree who does what, out loud, in chat</b></summary>

One message, not a document nobody reads. Any ownership change gets announced
in chat the same day it happens.

</details>

<details>
<summary><b>12. Start a shared running log</b></summary>

Create `NOTES.md` in the repo. Decisions, gotchas, dead ends. Costs five
minutes a day and saves the third person from rediscovering what the first two
learned at 2am.

</details>

---

## Phase 1 — Environment · Steps 13–32

<details>
<summary><b>13. Install Homebrew</b></summary>

Check with `brew --version`. If missing:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

On Apple Silicon also add `eval "$(/opt/homebrew/bin/brew shellenv)"` to
`~/.zprofile`.

</details>

<details>
<summary><b>14. Install Git and the GitHub CLI</b></summary>

```bash
brew install git gh
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
gh auth login
```

You need both: git for commits, `gh` for repo creation and collaborators.

</details>

<details>
<summary><b>15. Install Docker Desktop</b></summary>

```bash
brew install --cask docker
open -a Docker          # IMPORTANT: launch it once, wait ~30s for the whale to stop
```

Forgetting this launch is the single most common cause of "cannot connect to
the Docker daemon". Colima is a fine alternative:
`brew install colima colima-docker` then `colima start`.

</details>

<details>
<summary><b>16. Start FalkorDB</b></summary>

```bash
docker pull falkordb/falkordb:latest
docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest
```

This is the mandatory technology (Rule 2) and it runs in Docker.

</details>

<details>
<summary><b>17. Verify FalkorDB answers Cypher</b></summary>

```bash
docker exec falkordb redis-cli GRAPH.QUERY g "RETURN 1 AS ok"
```

Must print `1`. If it doesn't, run `docker logs falkordb` before going further —
do not carry a broken database into the next three phases.

</details>

<details>
<summary><b>18. Open the FalkorDB Browser</b></summary>

Go to `http://localhost:3000`. Nothing to install; it ships inside the
container. **This is your main debug tool** — every "why is this query returning
nothing" question gets answered here, faster than in Python.

Useful inside it: `:reset` to wipe, `MATCH (n) RETURN labels(n), count(*)`.

</details>

<details>
<summary><b>19. Note the port conflict — and say it in chat</b></summary>

FalkorDB uses **6379**, and its Browser uses **3000**. If anyone starts a JS dev
server on 3000 they collide, and the failure is silent — it looks like your
graph is broken. The frontend uses **5173**.

</details>

<details>
<summary><b>20. Install Python 3.11 or newer</b></summary>

```bash
brew install python@3.12
```

Verified working on 3.14.2, but new Pythons sometimes lack wheels. If
`pip install` fails to build, **drop to 3.12 — do not debug the build.** That
has a two-hour tail.

</details>

<details>
<summary><b>21. Create the virtual environment</b></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
which python          # must show .venv
```

Windows: `.venv\Scripts\activate`. Deactivate with `deactivate`.

</details>

<details>
<summary><b>22. Install every Python package in one command</b></summary>

```bash
pip install falkordb fastapi "uvicorn[standard]" anthropic pydantic faker python-dotenv httpx sse-starlette
```

Use `falkordb` — the official `falkordb-py` driver. **Never the old
`ioredisgraph`**, which is officially unsupported.

</details>

<details>
<summary><b>23. Freeze the requirements</b></summary>

```bash
pip freeze > requirements.txt
```

Rule 10 requires a setup that works on a clean machine, and this file is what
makes it possible. Freeze it now, refresh it once more before you finish.

</details>

<details>
<summary><b>24. Verify the FalkorDB client from Python</b></summary>

```python
from falkordb import FalkorDB
db = FalkorDB(host="localhost", port=6379)
g = db.select_graph("helio")
print(g.query("RETURN 1 AS ok").result_set)   # -> [[1]]
```

</details>

<details>
<summary><b>25. Learn the .result_set rule before it costs you an hour ⚠️</b></summary>

**`g.query()` returns a `QueryResult` that is NOT iterable.**
`for row in g.query(...)` raises `TypeError: 'QueryResult' object is not
iterable`. You must write `g.query(...).result_set`.

Say this out loud in the group chat — three people discovering it independently
is three wasted hours, and it is the single most expensive trap in the stack.

</details>

<details>
<summary><b>26. Get an Anthropic API key</b></summary>

Sign up at `console.anthropic.com` → API Keys → create a key. **Add billing
credit under Billing** — the free tier will not cover a hackathon, and
discovering that at midnight is fatal.

</details>

<details>
<summary><b>27. Verify the Anthropic key works</b></summary>

```bash
python -c "import anthropic; c=anthropic.Anthropic(); print(c.models.list().data[0].id)"
```

A `401` means the key is wrong or `.env` isn't loaded. If tool calls don't
fire, confirm you passed `tools=` in the request and are on a current model.

</details>

<details>
<summary><b>28. Create the .env file</b></summary>

```bash
cat > .env <<'EOF'
ANTHROPIC_API_KEY=sk-ant-...
FALKORDB_HOST=
FALKORDB_USERNAME=
FALKORDB_PASSWORD=
FALKORDB_GRAPH=helio
EOF
```

Load it in Python with `from dotenv import load_dotenv; load_dotenv()`.

</details>

<details>
<summary><b>29. Create .env.example and commit that instead</b></summary>

```bash
cp .env .env.example     # commit this one, secrets blanked
git check-ignore .env && echo "OK, ignored"
```

**Never commit `.env`** — keys in git history are in the public repo forever.

</details>

<details>
<summary><b>30. Write .gitignore before the first commit</b></summary>

```
.venv/
.env
__pycache__/
*.pyc
.DS_Store
node_modules/
```

Commit it before step 33 so nobody accidentally commits a venv.

</details>

<details>
<summary><b>31. Install VS Code and select the interpreter</b></summary>

```bash
brew install --cask visual-studio-code
code --install-extension ms-python.python
code --install-extension redhat.vscode-docker
```

Then `Cmd+Shift+P` → *Python: Select Interpreter* → `.venv`. Without this the
linter flags every import and you lose twenty minutes to noise.

</details>

<details>
<summary><b>32. Hold a 20-minute group call for steps 15–25 ⚠️</b></summary>

Everything above is what three people would otherwise rediscover separately, and
the `.result_set` trap fails **silently**. Do this call before splitting into
parallel work.

Discuss three things on the call: the `.result_set` gotcha, the port conflict,
and the `HAS_DEPENDENT` inverse-edge requirement — so all three start with the
same mental model.

</details>

---

## Phase 2 — Repo & ownership · Steps 33–40

<details>
<summary><b>33. Create the public repo</b></summary>

```bash
cd ~/Life && gh repo create graph-hacks --public --clone && cd graph-hacks
```

Rule 10 requires **public**. Not private-then-flipped later — public from the
start.

</details>

<details>
<summary><b>34. Add collaborators</b></summary>

```bash
gh repo add-collaborator soham -f push
gh repo add-collaborator ujwal -f push
```

Confirm all three can push before anyone writes a line of code.

</details>

<details>
<summary><b>35. Publish the file ownership table in the README</b></summary>

One file, one owner. With three people and two days, an unowned file is how you
lose a night to a bad merge.

| Path | Owner |
|---|---|
| `GROUND_TRUTH.md`, `data/`, `scripts/`, `app/graph.py`, `README.md`, `deploy/`, `video/` | Bhushan |
| `app/agent.py`, `app/main.py` | Soham |
| `web/`, `mock/` | Ujwal |

</details>

<details>
<summary><b>36. Create the directory skeleton</b></summary>

```bash
mkdir -p app data scripts web mock deploy video
```

Commit it immediately so everyone branches from the same shape.

</details>

<details>
<summary><b>37. Agree the branch model</b></summary>

Simplest that works: `main` plus one branch per person, merged at the gates.

**Never edit someone else's file to unblock yourself — ping them.** Being
blocked for 20 minutes is far cheaper than a merge conflict at 22:00.

</details>

<details>
<summary><b>38. Commit the planning docs</b></summary>

`bhushan.md`, `soham.md`, `ujwal.md`, `research.md`, `setup.md`, `all_steps.md`.

These are notes and diagrams, which **Rule 8 explicitly permits**. Committing
them also gives you a timestamped record that design work preceded the build.

</details>

<details>
<summary><b>39. Everyone clones the repo fresh</b></summary>

Delete your local copy, clone from GitHub, confirm the docs and `.gitignore`
came through. This proves your setup instructions before you need them at
Gate 5, when proving them is expensive.

</details>

<details>
<summary><b>40. Establish a daily standup</b></summary>

Five minutes, async, in the team chat: what you did, what you're blocked on,
what you're doing next. Three people on a critical path otherwise find out about
a blocker at the next gate, when it is already too late to react.

</details>

---

## Phase 3 — Contract freeze · Steps 41–48 · **Soham**

<details>
<summary><b>41. Freeze the API contract — Fri 15:00, hard ⚠️</b></summary>

```
POST /ask   { question }   →   SSE   { answer, trail[], stale[] }
trail[] = [ { type, name, detail, date, via_edge }, ... ]
stale[] = [ { type, name, reason, last_verified_at }, ... ]
GET /health
CORS for http://localhost:5173
```

Freeze it late and Ujwal loses hours building against a shape that changes.

</details>

<details>
<summary><b>42. Post the contract in the chat before writing any code</b></summary>

Ujwal builds a full day against this. Soham freezing it late is the one delay
that costs another person, so it is the only gate that is his rather than
Bhushan's.

</details>

<details>
<summary><b>43. Freeze trail[] with Bhushan's Cypher in mind — Fri 14:00 ⚠️</b></summary>

If Bhushan's rows are `[{node, via_edge}]` and the contract is
`[{type, name, ...}]`, someone is reshaping and that's fine — but agree it at
14:00 when the schema is sketched, **not** at 21:00 when the graph has landed.

Ujwal's renderer needs the shape the Cypher *actually* returns, not an assumed
one.

</details>

<details>
<summary><b>44. Tell Ujwal that native EventSource is GET-only ⚠️</b></summary>

Our contract is `POST /ask`, so `EventSource` will not work. He must use
`fetch()` + `response.body.getReader()`.

**Decide this once, now** — if he builds against `EventSource` it fails at
Gate 2 and reads as a frontend bug, costing an hour of debugging someone
else's code.

</details>

<details>
<summary><b>45. Name the SSE headers out loud ⚠️</b></summary>

```python
headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
```

Without the second one, proxies buffer the stream into a single lump. **It works
locally and dies in production**, and it will read as a bug in your code rather
than a proxy setting.

</details>

<details>
<summary><b>46. Define the tool signatures Bhushan must provide ⚠️</b></summary>

Send this to Bhushan at **Fri 14:00**, while he's sketching the schema. Soham is
otherwise blocked, and assuming a signature that doesn't exist wastes his Friday
evening.

```python
blast_radius(service) -> dependents, hop depth, owning team, on-call people
expertise(service)    -> people by contribution, volume AND recency
provenance(project)   -> decisions, author, superseded decision, evidence
staleness()           -> edges whose last_verified_at is older than 90 days
```

Every function must return the raw rows **and** the nodes/edges that produced
them, so the frontend can render a trail with edge labels.

</details>

<details>
<summary><b>47. Freeze the tool descriptions — routing quality lives here ⚠️</b></summary>

Each description names **one** intent, in the words a person would use. Avoid
`queries the graph for...` — the same prefix on all three carries no signal.
Routing quality comes from the descriptions, not from routing code.

```python
blast_radius(service: str)
    "What breaks if this service goes down, how deep the impact reaches,
     and who is on call for each affected service."

expertise(service: str)
    "Who knows this service best, ranked by contribution volume with recency."

provenance(project: str)
    "Where a decision about this project was made, who made it, and whether
     it has since been superseded."
```

</details>

<details>
<summary><b>48. State the no-fabrication rule in the system prompt now ⚠️</b></summary>

> *"If the tools do not return a fact, say you don't know. Never infer an owner, a
> date, or a decision that was not returned."*

Do this early, not at Gate 2. A fluent fabrication is a **failed** answer even
when it reads perfectly — `"The config service is owned by the Platform team"` is
a perfectly grammatical, entirely invented sentence. The model has a strong
prior to produce one.

</details>

---

## Phase 4 — Mock data · Steps 49–56 · **Ujwal**

<details>
<summary><b>49. Write mock/trail.json FIRST — Fri 13:00 ⚠️</b></summary>

This is the contract in executable form, and **nobody on this team can build on
Day 1 without it.** It is the highest-leverage ten minutes in the project.

Two consumers: Soham's fake API branch and Ujwal's frontend.

</details>

<details>
<summary><b>50. Make it one shared file, not two ⚠️</b></summary>

Both consumers read **this** file. Two independently written mock sets drift —
then at Gate 2 the real API lands and the renderer breaks on a shape it has
never seen.

That failure costs Saturday morning, and Saturday morning is verification time.

</details>

<details>
<summary><b>51. Populate every field, including the boring ones</b></summary>

`type`, `name`, `detail`, `date`, `via_edge` — all present on **every** row.

A missing `via_edge` is a chip that renders wrong and nobody finds out until
real data lands at Gate 2, at the worst possible moment.

</details>

<details>
<summary><b>52. Include a stale[] entry ⚠️</b></summary>

At least two entries: Priya Sharma (left the company 2026-04-15) and
`payments-provider-eval-v3.md` (contradicted by D-19).

If the fixture has no stale items, the ⚠ badge is untestable and won't get built
until Gate 2 — when there is no time left to build it.

</details>

<details>
<summary><b>53. Include the failure case with an EMPTY trail ⚠️</b></summary>

`"Who owns config-service?"` → a confident *"No `:OWNED_BY` edge exists."* with
`"trail": []`.

This is one of five demo beats. If it's untested, your empty state breaks on the
day you record, in front of the judges.

</details>

<details>
<summary><b>54. Include the ranking-tension case ⚠️</b></summary>

Priya Sharma has the most commits (14) but left in April; Ravi Menon is
current. Both must appear in the trail.

A naive `ORDER BY count DESC` gets this wrong, and **the tension is the best 20
seconds of your demo**.

</details>

<details>
<summary><b>55. Use the real names, not lorem ipsum</b></summary>

Priya Sharma, Ravi Menon, D-14, D-19, `payments-provider-eval-v3.md`,
`#inc-payments`.

When Bhushan's data lands, the swap must be **invisible**.

</details>

<details>
<summary><b>56. Tell Soham the file exists — Fri 13:30, two minutes ⚠️</b></summary>

He is supposed to be coding against mocks by then and cannot code against a
file he doesn't know about.

This one message unblocks two people in a line, and it is the highest-leverage
thing Ujwal does all weekend.

</details>

---

## Phase 5 — Ground truth & schema · Steps 57–64 · **Bhushan**

<details>
<summary><b>57. Write GROUND_TRUTH.md — the 20 facts, by hand ⚠️</b></summary>

**You wrote these. That is the only reason verification is real.**

Asking an AI "is this answer correct?" is circular — a hallucinated ownership
chain looks exactly like a correct one, because both are plausible prose over
structurally valid edges. Nobody else on this team can check the truth.

15 facts are answerable, 5 are designed to fail.

</details>

<details>
<summary><b>58. Fix facts 5 and 6 before you generate anything ⚠️</b> — <b>DONE 2026-10-17</b></summary>

**Resolved.** The DAG and the blast-radius facts disagreed.

Walking `HAS_DEPENDENT` forward from `payments-gateway` gave `checkout-api`,
`mobile-bff`, `webhook-relay`, `dispute-service`, `notifications`,
`config-service`, `fraud-scoring`, `recommendation`. Facts 5 and 6 listed
`ledger-core` and `settlement-batch` — those are **upstream** of payments, not
downstream.

The generator could not satisfy both. Reconciled four ways, all verified by
script rather than by eye:

| # | Defect | Fix |
|---|---|---|
| 1 | DAG was **cyclic** — `api-gateway → web-frontend → api-gateway` and `api-gateway → admin-bff → api-gateway` | `auth-service` and `api-gateway` no longer fan out to all public services |
| 2 | That fan-in inflated payments' blast radius to **14** services, mostly frontend/edge noise | same fix — blast radius is now exactly **8** services across 3 hops |
| 3 | Facts 5 and 6 listed **upstream** services | rewritten to the real 8, depths included |
| 4 | `ledger-core` had **no row** in the DAG despite 7 services depending on it | added as a root — the count is **20 services, 22 `DEPENDS_ON` edges** |

Fact 7 was also re-pointed from `settlement-batch` to `notifications`:
`settlement-batch` depends on `ledger-core`, so it is not in the payments
blast radius and the question was unanswerable as written.

`GROUND_TRUTH.md` and `bhushan.md` §5 are updated. This step is closed.

</details>

<details>
<summary><b>59. Decide the :Member label convention and write it down ⚠️</b></summary>

The blast-radius Cypher already contains:

```cypher
OPTIONAL MATCH (dep)-[:OWNED_BY]->(t:Team)-[:HAS_ROTATION]->(:Member)-[:ON_CALL]->(p:Person)
```

**No schema sketch defines `:Member`.**

Recommended: rotation members are `(:Person:Member)` — one node, two labels.
Decide it and put it in the schema so the generator, the loader and the query
all agree.

If they don't, the query returns `[]` **silently** and you lose an hour to a
query that looks correct.

</details>

<details>
<summary><b>60. Specify how person-level ownership is encoded ⚠️</b></summary>

Service ownership is `(Service)-[:OWNED_BY]->(:Team)`, which cannot express
"Ravi Menon owns it today". Fact 1 needs a mechanism.

Plant a decision plus a handoff document — `D-21`, 2026-04-15, *"Reassign
payments-gateway ownership from Priya Sharma to Ravi Menon"*, evidence
`payments-ownership-handoff.md` — and let the provenance path carry it.

</details>

<details>
<summary><b>61. Sketch the schema — cut unused node types ⚠️</b></summary>

Required: `Person, Team, Project, Service, Decision, Document, Message`. Add
`Ticket` only if `dispute-service` genuinely needs one.

Unused node types are pure generator work you do not have time for.

</details>

<details>
<summary><b>62. Define freshness as edge properties, not a system ⚠️</b></summary>

`valid_to` on `MEMBER_OF`, `last_verified_at` on contributions, `SUPERSEDES` on
decisions.

A separate staleness model turns "keep knowledge current" into a second project
you cannot afford.

</details>

<details>
<summary><b>63. Send the schema and signatures to Soham — Fri 14:00</b></summary>

He's blocked on the function signatures and will otherwise assume shapes that
don't exist, then discover it at Gate 2.

</details>

<details>
<summary><b>64. Send "ground truth is planted" to both ⚠️</b></summary>

Two minutes now prevents two people building against wrong assumptions all
Friday.

Also tell Ujwal that `deploy/` and `video/` are yours — **say it out loud, don't
let it be a surprise** at Sat 14:00.

</details>

---

## Phase 6 — Generator · Steps 65–72 · **Bhushan**

<details>
<summary><b>65. Write a seeded generator — scripts/generate.py</b></summary>

Use `seed=20261016` with both `random.seed` and `faker.Faker.seed`.

**Same seed, identical output.** That determinism is what makes verification
honest — you can re-run it and prove nothing changed underneath you.

</details>

<details>
<summary><b>66. Emit all 20 planted facts, not plausible noise ⚠️</b></summary>

Plus the deliberate contradictions — ownership reassignment, superseded
decision, stale doc, unowned service, departed employee.

Those contradictions **are** the freshness demo and the proof the agent is not
just echoing text.

</details>

<details>
<summary><b>67. Build the 20-service dependency DAG as one table</b> — <b>DONE 2026-10-17</b></summary>

One row means "this service depends on these". The DAG is **fixed and verified
acyclic** — 20 services, 22 `DEPENDS_ON` edges:

```
ledger-core       -> (none)
payments-gateway  -> ledger-core
checkout-api      -> payments-gateway
mobile-bff        -> payments-gateway
webhook-relay     -> payments-gateway
settlement-batch  -> ledger-core
dispute-service   -> payments-gateway, ledger-core
billing-invoicing -> ledger-core
notifications     -> payments-gateway, dispute-service
reporting-etl     -> ledger-core, billing-invoicing
search-index      -> reporting-etl
fraud-scoring     -> checkout-api
auth-service      -> (none)
session-store     -> auth-service
api-gateway       -> (none)
config-service    -> payments-gateway, auth-service
user-profile      -> auth-service
recommendation    -> fraud-scoring, user-profile
web-frontend      -> api-gateway
admin-bff         -> api-gateway
```

**The two "all public services" rows are gone, deliberately.** Expanding them
is what created the cycles and the 14-service blast radius — see step 58. The
public tier is the edge; it is downstream of nothing.

Use this table verbatim. Do not re-derive it, and do not bend it to match an
expectation — print the actual computed closure and warn loudly if it disagrees.

</details>

<details>
<summary><b>68. Emit BOTH DEPENDS_ON and HAS_DEPENDENT from one DAG row ⚠️</b></summary>

**Cypher cannot traverse an edge backwards.**

Skip the inverse edge and the blast-radius query **silently returns `[]` — not
an error, just nothing.** This is a verified bug we already hit while planning.

One DAG row, two edges, two different names.

</details>

<details>
<summary><b>69. Make chat messages mention real entities by name ⚠️</b></summary>

`"payments timeouts again after deploy"` in `#inc-payments`,
`"ledger-core reconciliation is off by 2 cents"` — **never `"hey team"`**.

Without this the graph has no leaves, text search returns nothing, and the
provenance trail has nothing to point at.

**This is the one rule that decides whether the whole thing works.**

</details>

<details>
<summary><b>70. Make the five must-fail facts genuinely absent ⚠️</b></summary>

Not merely unanswered — **absent**:

- `config-service` has **no** `OWNED_BY` edge, ever
- The word `"pricing"` appears in **zero** decision rows or their evidence
- `dispute-service` has **no** SLA property, while every other service does
- `Aisha Khan`'s `MEMBER_OF` carries `valid_to=2026-06-30`
- At least 2 services have zero inbound `HAS_DEPENDENT` edges

Check all five programmatically before you exit.

</details>

<details>
<summary><b>71. Self-check against your own output and print the table ⚠️</b></summary>

Assert: Priya's commits == 14, last_touch == 2026-04-15, zero pricing
decisions, Aisha's `valid_to` == 2026-06-30, D-19 → D-14 resolves,
`settlement-batch` has zero recent touches, `config-service` has no owner.

Anything you **cannot** check from your own output, mark `UNCHECKABLE` rather
than asserting it passes.

A self-check is a smoke test, **not Gate 2** — do not mistake the two.

</details>

<details>
<summary><b>72. Confirm row counts in the Browser</b></summary>

18 services, ~100 people, ~2,000 messages visible at `http://localhost:3000`
before you load anything.

Confirm the generator's output is right before the loader makes it permanent.

</details>

---

## Phase 7 — Loader · Steps 73–80 · **Bhushan**

<details>
<summary><b>73. Create indexes BEFORE bulk loading</b></summary>

```cypher
CREATE INDEX ON :Service(name)
CREATE INDEX ON :Person(name)
CREATE INDEX ON :Project(name)
CREATE INDEX ON :Decision(id)
```

Creating them after the load means indexing a full table instead of building it
incrementally.

</details>

<details>
<summary><b>74. Delete the graph before every reload ⚠️</b></summary>

```bash
docker exec falkordb redis-cli GRAPH.LIST
docker exec falkordb redis-cli GRAPH.DELETE helio
```

Load twice into a dirty graph and **every count is wrong** — including the counts
your ground truth depends on.

This failure is silent.

</details>

<details>
<summary><b>75. Load with batched UNWIND, never one CREATE per row</b></summary>

```cypher
UNWIND $rows AS row CREATE (s:Service {name: row.name, team: row.team})
```

One `CREATE` per row means one round trip per row. This is the difference
between a two-minute load and a twenty-minute one.

</details>

<details>
<summary><b>76. Pass every batch as a parameter — never string-interpolate</b></summary>

```python
g.query(cypher, params).result_set
```

Interpolating values into the query string is an injection bug, a quoting bug
waiting to happen, and it breaks on any apostrophe in a name.

</details>

<details>
<summary><b>77. Separate node passes from relationship passes</b></summary>

**You cannot create a relationship before both endpoints exist.**

Load all nodes for all types first, then all relationships. Getting this order
wrong produces partial loads that look successful.

</details>

<details>
<summary><b>78. Wrap each node type in its own try/except and report the count ⚠️</b></summary>

Print which type failed and how many rows went in.

**A partial load that looks successful is worse than a loud failure** — it lets
you proceed into verification with numbers that are quietly wrong.

</details>

<details>
<summary><b>79. Print counts per label and assert they match the CSVs ⚠️</b></summary>

If messages != 2000, stop and fix it.

Do not continue into verification with wrong numbers — every ground-truth count
downstream becomes unfalsifiable.

</details>

<details>
<summary><b>80. Measure before optimising</b></summary>

`g.query(...).run_time_ms` is free per-query timing.

Only reach for `falkordb-bulk-loader` if the load actually crawls. Measure
first, optimise second.

</details>

---

## Phase 8 — Cypher · Steps 81–88 · **Bhushan**

<details>
<summary><b>81. Write the blast-radius traversal — blast_radius() ⚠️</b></summary>

```cypher
// Blast radius — what breaks, who's paged
MATCH path = (s:Service {name:$service})-[:HAS_DEPENDENT*1..4]->(dep:Service)
OPTIONAL MATCH (dep)-[:OWNED_BY]->(t:Team)-[:HAS_ROTATION]->(:Member)-[:ON_CALL]->(p:Person)
RETURN dep.name AS dep, length(path) AS depth, t.name AS owner,
       collect(DISTINCT p.name) AS on_call
```

**Uses the inverse edge — not a reversed `DEPENDS_ON`.** A reversed arrow walks
the wrong way and returns `[]` with no error.

</details>

<details>
<summary><b>82. Write the expertise traversal — expertise() ⚠️</b></summary>

```cypher
MATCH (p:Person)-[c:CONTRIBUTED_TO]->(proj:Project)-[:USES]->(s:Service {name:$service})
RETURN p.name AS person, count(*) AS touches, max(c.last_touch) AS latest
ORDER BY touches DESC LIMIT 5
```

Return **volume AND recency — never a single ranking.**

Priya has the most commits and left in April; `ORDER BY count DESC` returns her
and is *technically correct on commits while being the wrong answer*. Return
both and let the agent explain the tension.

**This is the best 20 seconds of the demo.**

</details>

<details>
<summary><b>83. Write the provenance traversal — provenance() ⚠️</b></summary>

```cypher
MATCH (d:Decision)-[:ABOUT]->(p:Project {name:$project})
MATCH (d)-[:EVIDENCED_BY]->(ev)-[:AUTHORED_BY]->(who:Person)
OPTIONAL MATCH (d)-[:SUPERSEDES]->(prev:Decision)
RETURN d.id, d.summary, who.name AS author, ev.date, prev.summary AS superseded
```

Must follow the `SUPERSEDES` chain so a superseded decision **shows as**
superseded rather than silently vanishing.

</details>

<details>
<summary><b>84. Write the staleness query — staleness()</b></summary>

Edges whose `last_verified_at` is older than 90 days.

This is what produces the ⚠ badges and what catches the stale provider-eval
document.

</details>

<details>
<summary><b>85. Return rows AND the nodes/edges that produced them ⚠️</b></summary>

Every function must return the raw rows **and** the nodes and edges that produced
them, so the frontend can render a trail with edge labels.

Rows without the path cannot be rendered, and **the trail is the thing being
judged**.

</details>

<details>
<summary><b>86. Keep all Cypher in this one file — nowhere else ⚠️</b></summary>

One file, one owner, one place to look.

It is also a Rule 10 deliverable (item 4), so having it isolated makes
publishing it trivial.

</details>

<details>
<summary><b>87. Respect the verified FalkorDB limits ⚠️</b></summary>

- `.result_set` always — `query()` is not iterable
- **NEVER** undirected `shortestPath((a)-[*]-(b))` — it throws
- **NEVER** `db.idx.fulltext.*` — the procedure is not registered; use
  `WHERE x CONTAINS 'y'`
- **NEVER** return `type(node)` beside an optional node — type error; use
  `labels(node)`
- Variable-length + `OPTIONAL MATCH` + `collect(DISTINCT)` is verified working,
  use it freely

All of these were executed against `falkordb/falkordb:latest`. Don't
rediscover them.

</details>

<details>
<summary><b>88. Test each traversal against the loaded graph, not theory ⚠️</b></summary>

Each must return **real rows**.

If a query returns `[]`, check the edges exist before debugging the logic:

```cypher
MATCH (a)-[r]->(b) RETURN a.name, type(r), b.name LIMIT 20
```

An empty result is usually a reversed arrow, not a bug in your Cypher.

</details>

---

## Phase 9 — Agent & API · Steps 89–98 · **Soham**

<details>
<summary><b>89. Build app/main.py against mocks, not against the graph</b></summary>

The graph owner may be late and is on a sequential critical path.

Building against mocks first means his delay costs **nobody**.

</details>

<details>
<summary><b>90. Put every mock behind ONE function with a fake branch ⚠️</b></summary>

```python
def get_trail(question):
    # ---- FAKE BRANCH: delete this when the real graph lands ----
    if True:
        return MOCK_TRAIL
    # ---- REAL BRANCH ----
    return run_agent(question)
```

At Gate 2 you delete one branch and change nothing else. Scattered mock literals
mean grepping at 22:00 looking for the strings that leaked into real logic.

</details>

<details>
<summary><b>91. Stream with EventSourceResponse or StreamingResponse</b></summary>

```python
from sse_starlette.sse import EventSourceResponse

@app.post("/ask")
async def ask(req: Ask):
    return EventSourceResponse(stream_answer(req.question))
```

Or use `StreamingResponse` with `media_type="text/event-stream"`.

**The `X-Accel-Buffering` header is not optional** — see step 121.

</details>

<details>
<summary><b>92. Take real data through pydantic models</b></summary>

Shapes then cannot drift, because the type system enforces them. This is free
correctness.

</details>

<details>
<summary><b>93. Comment that the client must use fetch() + getReader()</b></summary>

Native `EventSource` is GET-only. Someone will try it anyway, and the comment
turns a ten-minute confusion into a thirty-second one.

</details>

<details>
<summary><b>94. Build app/agent.py as an explicit Anthropic tool-use loop ⚠️</b></summary>

**No framework — by design.**

Rule 12 requires explaining every line in judging, and a framework hides
exactly the part being judged.

</details>

<details>
<summary><b>95. Let the model choose the tool from the question ⚠️</b></summary>

Do **not** hardcode a pipeline that runs all three queries and concatenates the
output.

That is a search box with extra steps, and it loses the track on multi-hop
reasoning — which is the focus area for this hackathon.

</details>

<details>
<summary><b>96. Tie every claim to a trail row a tool returned ⚠️</b></summary>

Pass the returned rows back in and require claims to be traceable to them.

**Never let the model assert a fact no tool returned.** This is both an
accuracy property and your best Rule 12 talking point.

</details>

<details>
<summary><b>97. Make empty results explicit and visible ⚠️</b></summary>

Don't silently omit the tool call — return the empty result visibly so the model
and the user both see it.

When a tool returns nothing, the answer says so. **Correct failure is a feature,
not an edge case**, and it's one of five demo beats.

</details>

<details>
<summary><b>98. Allow sequential tool calls for the compound demo question ⚠️</b></summary>

*"Who knows about the payments service, **and** what breaks if it goes down,
**and** where was that decided?"* hits **all three** tools.

The model must chain them rather than stopping at the first. Test this
specifically — it's the demo question, and a model that stops early looks broken
on camera.

</details>

---

## Phase 10 — Frontend · Steps 99–106 · **Ujwal**

<details>
<summary><b>99. Build web/index.html against mock/ — vanilla JS ⚠️</b></summary>

No framework, no bundler, nothing to install.

A build step is something that breaks on the demo machine at the worst moment.

</details>

<details>
<summary><b>100. Keep exactly ONE fetch() call site ⚠️</b></summary>

Point it at the mock file now; switching to the real endpoint must be a
one-line change.

If it isn't, mock logic has leaked into your UI — and if your renderer needs
editing when real data lands, **the fault is in `mock/`, not the renderer.**
Fix the fixture, not the trail.

</details>

<details>
<summary><b>101. Use fetch() + response.body.getReader() for SSE ⚠️</b></summary>

Not `EventSource` — GET-only, and our contract is `POST /ask`.

This is the most common cause of a stuck spinner at Gate 2.

</details>

<details>
<summary><b>102. Build the provenance renderer — spend your hours here ⚠️</b></summary>

This is the single highest-leverage thing in the project: the strongest 20
seconds of the demo, and the concrete difference between *answers that show
their path* and another chat UI.

```
[ Priya Sharma · 14 commits · last 2026-04-15 ]
      ──CONTRIBUTED_TO──▶
[ D-14 · 2026-03-18 · superseded by D-19 ]
      ──EVIDENCED_BY──▶
[ payments-provider-eval-v3.md · ⚠ stale ]
      ──MENTIONS──▶
[ #inc-payments · 2026-03-28 ]
```

</details>

<details>
<summary><b>103. Never drop via_edge ⚠️</b></summary>

Without the edge labels it's a list of four things that happened to be near each
other. With them it's a **proof chain** — `EVIDENCED_BY` and `SUPERSEDES` are
doing semantic work a plain search result cannot do.

**This is the visible difference between our entry and everyone else's.**

</details>

<details>
<summary><b>104. Make clicking a chip expand the raw sub-result</b></summary>

Judges must see **actual query output**, not a summary you wrote.

That is the difference between proving it and claiming it.

</details>

<details>
<summary><b>105. Make staleness a first-class chip state ⚠️</b></summary>

The ⚠ badge appears **at the moment** the item is displayed, not in a footnote
at the bottom.

`payments-provider-eval-v3.md` is stale and the UI should say so while you are
looking at it.

</details>

<details>
<summary><b>106. Build no graph visualisation ⚠️</b></summary>

No canvas, no force-directed anything.

Rule 3: *"A visualisation drawn on top of ordinary storage does not qualify."*
A pretty network graph reads as decoration and **actively works against the
submission** — it signals you had data and needed to draw it.

It also takes hours you don't have and tells a judge nothing they can't get from
the Browser.

*One exception if you have spare time: a small static **schema** diagram (nodes +
relationship types, no data) for the README. That's documentation, and hand it to
Bhushan.*

</details>

---

## Phase 11 — Verification · Steps 107–116 · **all three**

<details>
<summary><b>107. Gate 2 — swap mocks for the real graph — Fri 21:00 ⚠️</b></summary>

If this takes more than 20 minutes, mock logic leaked into real code.

That's a design bug in step 90, not a hard integration. Go fix the design rather
than patching forward.

</details>

<details>
<summary><b>108. Confirm the renderer needed NO changes ⚠️</b></summary>

If it did, your fixture drifted from the contract — the fault is in `mock/`, not
the renderer.

Fix the fixture. The whole point of one shared fixture was to make this a
non-event.

</details>

<details>
<summary><b>109. Ask all 20 ground-truth questions through the running agent ⚠️</b></summary>

**Through the agent, end to end** — not through Cypher directly.

The Cypher can be right while the agent still answers wrong, and the agent is
the thing being judged.

</details>

<details>
<summary><b>110. Compare every answer to GROUND_TRUTH.md, one at a time ⚠️</b></summary>

Anything you can't confirm from **your own notes** is a bug or a graph hole.
**Fix it, don't paper over it.**

Log every failure in `VERIFICATION.md`: date, question, wrong answer, fix. Re-run
after each fix.

</details>

<details>
<summary><b>111. Run the five break-it questions specifically ⚠️</b></summary>

`config-service` ownership · checkout pricing · zero-dependent service · Aisha's
current team · dispute-service SLA.

**An agent that invents an owner has failed, even though the sentence reads
fine.** Most entries never test this, which is why it's cheap for us to show.

</details>

<details>
<summary><b>112. Check fact 8 — the ranking trap — explicitly ⚠️</b></summary>

Does the agent surface Priya's commit volume **and** her departure, and then
pick Ravi for *"who should I ask about payments now"*?

A naive `ORDER BY count DESC` returns Priya and is technically correct on
commits while being the wrong answer.

**A naive query gets this wrong; yours must catch it and explain why.**

</details>

<details>
<summary><b>113. Check fact 15 — the contradiction — explicitly ⚠️</b></summary>

The doc and March Slack say *"single provider, Stripe"*. D-19 says *"dual
provider, Adyen primary"*.

The agent must flag **the document** as stale, not silently prefer one.

</details>

<details>
<summary><b>114. Check the two silent traps explicitly ⚠️</b></summary>

- **Wrong arrow direction** returns `[]`, not an error. Before debugging a query,
  check the edge exists:
  `MATCH (a)-[r]->(b) RETURN a.name, type(r), b.name LIMIT 20`
- **Double loading** into a dirty graph makes every count wrong.
  `GRAPH.DELETE helio` before every reload.

</details>

<details>
<summary><b>115. Hold Gate 3 — real-data demo on all three machines — Sat 11:00 ⚠️</b></summary>

If one machine fails, it's an **environment** bug, not a code bug — find it now,
not Saturday night.

This gate is what makes Gate 5 (a stranger following the README) likely to pass.

</details>

<details>
<summary><b>116. Take the break — Sat 12:00–14:00, non-negotiable ⚠️</b></summary>

Tired engineers ship unverified entries.

**An unverified demo is worse than a smaller verified one.** If you're out of
time, ship 2 traversals and 10 verified facts rather than 3 traversals and no
verification.

</details>

---

## Phase 12 — Deploy · Steps 117–126 · **Bhushan**

<details>
<summary><b>117. Write deploy/docker-compose.yml FIRST — Fri 21:30 ⚠️</b></summary>

**This is your fallback and it needs nothing but your own files.**

`docker compose up` is a legal submission under Rule 10 even with zero live
deploy. Make it Friday evening, not Saturday-afternoon panic.

The worst case of owning deploy is a smaller-looking entry, not a missing one.

</details>

<details>
<summary><b>118. Compose must give a complete working setup on a clean machine ⚠️</b></summary>

Only Docker and Python installed should be required.

```yaml
services:
  falkordb:
    image: falkordb/falkordb:latest
    ports: ["6379:6379"]
  api:
    build: ..
    ports: ["8000:8000"]
    env_file: ../.env
    depends_on: [falkordb]
```

Include `env_file` for `ANTHROPIC_API_KEY` and the FalkorDB credentials, plus
`depends_on` ordering so the API starts after the database.

</details>

<details>
<summary><b>119. Make the generator/load part of the setup — or document the commands</b></summary>

Either way the README states precisely what to run to populate the graph.

**A compose that starts an empty graph is a broken submission** — it passes
step 120 and fails every judge.

</details>

<details>
<summary><b>120. Test compose on a genuinely clean machine ⚠️</b></summary>

Not your laptop. The whole point is that it works for someone who has never seen
the repo.

Do it Saturday morning, not Saturday night.

</details>

<details>
<summary><b>121. Get the SSE headers from Soham — Sat 14:00, before the URL ⚠️</b></summary>

```python
headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
```

Without the second one the stream works locally and dies in production, and
**you will read that as a bug in his code.**

Thirty seconds of his time protects your video slot.

</details>

<details>
<summary><b>122. Attempt the live deploy — Fly.io preferred ⚠️</b></summary>

```bash
brew install flyctl && fly auth login
fly launch --no-deploy        # generates fly.toml — review it first
fly deploy
fly secrets set ANTHROPIC_API_KEY=sk-ant-...
fly secrets set FALKORDB_PASSWORD=...
fly open
```

**Do not let deploy eat the video.** If it's fighting you at Sat 16:00, stop and
ship compose.

</details>

<details>
<summary><b>123. Note the FalkorDB Cloud gotchas in config comments ⚠️</b></summary>

- TLS required, non-default port, client needs `ssl=True`
- Comment **every** place the stream could be buffered

**SSE works locally and dies in production about half the time** — don't let that
surprise you.

</details>

<details>
<summary><b>124. Keep fly logs open — it's your main debugging tool</b></summary>

"Works for me, blank for them" is a log problem, not a code problem.

Cold starts being slow is acceptable for a demo — pre-warm right before
recording.

</details>

<details>
<summary><b>125. Gate 4 — incognito test, Sat 16:00, and stop regardless ⚠️</b></summary>

Open the URL in a **logged-out browser** from a cold start.

A deploy that fails at Sat 16:00 is recoverable — you have compose and six
hours. **A deploy that fails at 02:00 Sunday is not.**

Stop at 16:00 and ship compose. This is the most dangerous gate in the project,
and its fallback is already written.

</details>

<details>
<summary><b>126. Let Ujwal give you the cold-browser verdict ⚠️</b></summary>

You know where every hack is, and what works on your machine always looks like
it works.

**He opens it in incognito and says yes or no, unvarnished.** That check catches
what nothing else does.

</details>

---

## Phase 13 — Video · Steps 127–132 · **Bhushan**

<details>
<summary><b>127. Write the 90-second script, five beats, before Sat 17:00 ⚠️</b></summary>

| Beat | Time | What |
|---|---|---|
| 1 | 0:00–0:10 | the multi-hop question, typed |
| 2 | 0:10–0:35 | answer streams, trail chips render left to right |
| 3 | 0:35–0:55 | **the trap** — top contributor by commits is stale; the agent explains why |
| 4 | 0:55–1:15 | **the contradiction** — doc says Stripe-only, D-19 says Adyen primary; doc flagged stale |
| 5 | 1:15–1:30 | **the failure** — "Who owns config-service?" → "No `:OWNED_BY` edge exists" |

</details>

<details>
<summary><b>128. Run the 5-minute pre-record checklist</b></summary>

- Graph loaded and populated
- App running, no errors in the terminal
- Cold start pre-warmed
- Browser zoom sane
- Notifications off
- Both URLs open and working
- Terminal scrollback cleared

</details>

<details>
<summary><b>129. Record the REAL app with all three present ⚠️</b></summary>

A screen recording of the actual running system.

**Not a mockup, not a prepared sequence. No background music** — judges read
your design off the interface and music competes with it.

</details>

<details>
<summary><b>130. Record a full raw take BEFORE editing anything ⚠️</b></summary>

**Re-recording because the trail didn't render is not.** Editing a good take is
fast; re-recording is not.

Get the raw 90 seconds on Saturday, then cut.

</details>

<details>
<summary><b>131. Upload Sunday 09:00 — first task — then open the link ⚠️</b></summary>

Then **open it in a logged-out browser and confirm it plays.**

A private, expired or wrong-format link means judges see nothing.

**Rule 10 requires the video; a broken link is an entry with no demo**, and "we
had one" scores zero.

This is the single most common way a finished entry scores nothing.

</details>

<details>
<summary><b>132. Fall back to an unedited take if editing fails</b></summary>

An unpolished video still submits.

**Cut polish before you cut the video's existence.** If you're behind, an
unedited screen recording beats no video.

</details>

---

## Phase 14 — README · Steps 133–137 · **Bhushan**

<details>
<summary><b>133. Write the positioning paragraph first ⚠️</b></summary>

> Existing enterprise search answers *"where is the doc about X."* We answer
> *"who knows about X, what breaks if it goes down, where was that decided, and
> how current is that answer"* — in one traversal, with the path shown. Text
> search is used only at the leaves.

**Don't position as "company search"** — that comparison loses instantly against
Glean. Position as **answers that show their path**, and name the difference
before the judge does.

</details>

<details>
<summary><b>134. Document the data model with a diagram ⚠️</b></summary>

Nodes, relationship types, and what each edge means.

Get Ujwal's static schema diagram — nodes and relationship types, no data.
Rule 10 item 3, and genuinely useful to a judge.

</details>

<details>
<summary><b>135. Publish the actual Cypher — Rule 10 item 4 ⚠️</b></summary>

**The queries themselves, not a description of them.**

"See `app/graph.py`" does not satisfy this. Paste the three traversals and the
staleness query into the README.

</details>

<details>
<summary><b>136. State the limitations rather than hide them ⚠️</b></summary>

- **ACL / permission enforcement is out of scope.** Glean's moat is that answers
  respect access control; production needs an authz layer over every traversal.
- **Synthetic data** — Helio is fictional, by design (Rule 6).
- **Entity resolution is trivial** — the generator knows ground truth; real
  deployment needs dedup across `@priya` / `Priya Sharma` / `@psharma`.

Naming these reads as maturity. **Inviting the question by staying silent reads
as not having thought about it.**

</details>

<details>
<summary><b>137. Write the AI-use disclosure — Rule 11, mandatory ⚠️</b></summary>

Plain, factual, near the top of the README.

**Cheap to comply with, catastrophic to omit** — getting disqualified for
non-disclosure costs everything.

</details>

---

## Phase 15 — Submission · Steps 138–140

<details>
<summary><b>138. Walk the Rule 10 checklist end to end — Fri, then Sat night ⚠️</b></summary>

- [ ] Public repo
- [ ] README with setup instructions
- [ ] README with the graph data model and diagram
- [ ] The Cypher queries the product depends on
- [ ] Demo video — **uploaded, and the link opened to confirm it plays**
- [ ] Live deploy **or** complete local setup *(yours)*
- [ ] Track declared — **Track 03: Company Brain**
- [ ] **AI-use disclosure** (Rule 11)
- [ ] All three can explain schema, queries, architecture, decisions (Rule 12)
- [ ] Data is synthetic / ours only (Rule 6)
- [ ] Main coding began after Oct 15, 00:01 IST (Rule 8)

**Five of these seven are documents, not code.** That's roughly half the
submission, and it's the half nobody plans for.

</details>

<details>
<summary><b>139. Gate 5 — an uninitiated teammate follows the README — Sat 23:00 ⚠️</b></summary>

A person who did not build it, no hand-holding.

Every stumble is a README bug. This is the last gate that can still improve the
submission, and it runs before the hard freeze.

</details>

<details>
<summary><b>140. Submit Sunday 17:00 IST. Press the button. ⚠️</b></summary>

Hard freeze at **14:00**. Nothing new after that line.

You have a **7-hour buffer and it exists because something will break** — and the
two most likely things are the deploy and the video upload, **both of which you
now own.**

Your job at 17:00 is to press the button, not to use the remaining time. Sunday
afternoon is empty on purpose.

</details>

---

## Appendix A — Verified FalkorDB limits

Every row here was executed against `falkordb/falkordb:latest`. **Don't
rediscover these.**

| Feature | Status |
|---|---|
| `g.query(cypher, params).result_set` | **Required** — `query()` is not iterable |
| Variable-length `[:TYPE*1..4]` | Works |
| Variable-length + `OPTIONAL MATCH` + `collect(DISTINCT)` | Works |
| `length(path)` for hop depth | Works |
| `count()` / `max()` + `ORDER BY` | Works |
| `MERGE … ON CREATE SET` | Works |
| `CREATE INDEX ON :Label(prop)` | Works |
| `WHERE x CONTAINS 'y'` text search | Works |
| Directed `shortestPath((a)-[*]->(b))` | Works |
| **Undirected** `shortestPath((a)-[*]-(b))` | **Throws** — directed only |
| `db.idx.fulltext.*` | **Not registered** — use `CONTAINS` |
| `type(node)` beside an optional node | **Type error** — use `labels(node)` |

---

## Appendix B — Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `TypeError: 'QueryResult' object is not iterable` | Missing `.result_set` | Add it — step 25 |
| Query returns `[]` but data exists | Reversed arrow | Step 88's edge-check query |
| `Cannot connect to the Docker daemon` | Desktop not running | `open -a Docker`, wait 30s |
| Port 3000 conflict | JS dev server vs FalkorDB Browser | Use 5173 — step 19 |
| Stream works locally, dead in production | Proxy buffering | `X-Accel-Buffering: no` — step 121 |
| Stuck spinner at Gate 2 | Client used `EventSource` | `fetch()` + `getReader()` — step 101 |
| Blank page in production, works locally | Buffering or TLS | `fly logs`, then SSE headers, then `ssl=True` |
| Graph counts doubled | Loaded twice into a dirty graph | `GRAPH.DELETE helio` — step 74 |
| `401` from Anthropic | Key wrong / `.env` not loaded | Restart uvicorn after editing `.env` |
| `externally-managed-environment` | venv not active | `source .venv/bin/activate` |
| `Address already in use` | Port taken | `lsof -i :8000` then kill, or `--port 8001` |
| Linter can't find imports | Wrong interpreter | VS Code → Select Interpreter |
| Agent invents an owner | No no-fabrication instruction | Steps 48 and 96 |
| `pip install` fails to build on 3.14 | Missing wheels | Drop to 3.12, don't debug |

---

## Appendix C — The two silent killers

Most time is lost to these two, so they're worth stating on their own.

**1. An empty result is not an error.** A reversed arrow, a missing inverse edge,
and an unloaded graph all produce `[]` and look identical. Before debugging query
logic, check the edge physically exists:

```cypher
MATCH (a)-[r]->(b) RETURN a.name, type(r), b.name LIMIT 20
```

**2. Loading twice is silent too.** `GRAPH.DELETE helio` before **every** reload,
or every count is wrong — including the counts your ground truth depends on.

---

## Appendix D — What you own

| Path | Owner | Contents |
|---|---|---|
| `GROUND_TRUTH.md` | Bhushan | The 20 hand-planted facts |
| `data/`, `scripts/` | Bhushan | Generator + loader |
| `app/graph.py` | Bhushan | **The only Cypher in the repo** |
| `README.md` | Bhushan | Data model, Cypher appendix, AI disclosure |
| `deploy/` | Bhushan | Dockerfile, compose, `fly.toml` |
| `video/` | Bhushan | Script, recording, upload |
| Submission | Bhushan | Presses submit |
| `app/agent.py`, `app/main.py` | Soham | Tool-use loop + frozen contract |
| `web/` | Ujwal | The interface |
| `mock/` | Ujwal | `mock/trail.json` — the shared fixture |

**`mock/` is load-bearing and shared.** Soham's fake API branch and Ujwal's
frontend both read it — one file, two consumers, deliberate. Two independently
written mock sets drift, and the drift only surfaces at Gate 2 when real data
lands and the renderer breaks on a shape it never saw.

**Never edit someone else's file to unblock yourself.** Ping them. Being blocked
20 minutes is much cheaper than a merge conflict at 22:00.

---

## Appendix E — Cut order, if you're behind

Cut in this order:

1. Staleness query
2. Third traversal
3. Chat history
4. Dependency depth
5. **Video polish** — cuts before the video itself
6. **Live deploy** — `docker compose up` is a legal submission under Rule 10

**Never cut:** ground-truth verification · the traversals · provenance data · the
deploy *fallback* · the README · the video *existing*.

> You own twice the packaging now, so the temptation to skip verification and
> "just get a demo up" is real. It's the wrong trade. **A verified two-traversal
> entry beats an unverified three-traversal one every time. Cut scope, not
> rigour.** And **state your reasons when you cut** — "dropping the live deploy to
> protect verification time" lands. Going silent doesn't.

---

## Appendix F — The five beats, and what each proves

| Beat | Proves |
|---|---|
| Multi-hop question | The graph does real work, not decoration (Rule 3) |
| Trail with edge labels | The answer shows its path — the thesis |
| Stale top contributor | Freshness is modelled, not bolted on |
| Doc vs superseded decision | Contradiction is detected and explained |
| "No `:OWNED_BY` edge exists" | **It doesn't hallucinate** |

The last beat is the one most entries never show. **It is the cheapest credibility
you will ever buy.**

---

## Appendix G — Rehearse this for Rule 12

All three of you must be able to explain the design. Two twenty-five-second
answers cover most of it.

**Soham** — *"The model gets three tools. It picks one based on the question.
Each tool runs a Cypher traversal in `app/graph.py` and returns rows plus the
edges that produced them. Those rows go back to the model, and the final answer is
required to cite them. When a tool returns nothing, the answer says so."*

**Ujwal** — *"The answer streams token by token, and beneath it the trail renders
each node as a chip labelled with the edge that got us there — `CONTRIBUTED_TO`,
`EVIDENCED_BY`, `SUPERSEDES`. That's the point: you see the reasoning, not just
the answer. Anything outdated gets a warning badge the moment you see it,
because a correct answer from April isn't a correct answer today."*

**Bhushan** — *"Everything upstream of `graph.py` is sequential: ground truth
written by hand, a seeded generator, a batched loader. The graph is the only
place Cypher lives. `DEPENDS_ON` and `HAS_DEPENDENT` are both generated from one
DAG row because Cypher can't traverse an edge backwards, so blast radius is a
forward walk. Freshness is edge properties — `valid_to`, `last_verified_at`,
`SUPERSEDES` — not a separate staleness system."*

**Practise these out loud before Sunday.** Rule 12 is the rule people
underestimate, and AI-written code you haven't internalised is a liability in the
judging room.

---

**Companion docs:** [`setup.md`](setup.md) · [`setup-windows.md`](setup-windows.md) ·
[`research.md`](research.md) · [`bhushan.md`](bhushan.md) · [`soham.md`](soham.md) ·
[`ujwal.md`](ujwal.md)