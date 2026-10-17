# Soham — Plan

**Track 03: Company Brain · Graph Hacks · Oct 15–18**
You own the agent loop and the backend contract. **Your first job is not code — it is unblocking two people.**

Setup first: [`setup.md`](setup.md) — steps 1–8, then **9**, 11, 12, 13 and 21.

---

## Index

| # | Section |
|---|---|
| 1 | [Why this is yours](#) |
| 2 | [What you own](#) |
| 3 | [The contract — freeze by 15:00](#) |
| 4 | [Independent tasks](#) |
| 5 | [Dependent task](#) |
| 6 | [The agent loop is the product](#) |
| 7 | [Tool descriptions](#) |
| 8 | [SSE — the one gotcha](#) |
| 9 | [Your three days](#) |
| 10 | [Gates](#) |
| 11 | [If you're behind](#) |
| 12 | [Handoffs](#) |
| 13 | [The 5 questions that break you](#) |
| 14 | [Submission](#) |
| 15–16 | [Prompts: main.py · agent.py](#) |

---

<details>
<summary><b>1. Why this is yours and not shared</b></summary>

Soham owns the **agent loop** — the thing judges are actually evaluating. It has to be explicit enough for three people to explain it under questioning (Rule 12), which rules out leaning on a framework abstraction. And it has to arrive **before** the graph does, because the graph is on someone else's critical path.

Your leverage is the contract. Freeze it by 15:00 and Ujwal builds all day against fakes; your delay costs nobody. Freeze it late and two people lose hours.

> **You own the failure behaviour too.** Facts 16–20 in Bhushan's ground truth require the agent to say *"I don't know"* correctly. That is an agent-loop property, not a Cypher property — it's yours.
</details>

<details>
<summary><b>2. What you own</b></summary>

**Own:**

| Path | Contents |
|---|---|
| `app/main.py` | FastAPI + SSE, the frozen contract |
| `app/agent.py` | Anthropic tool-use loop |
| — | Announcing and defending the API contract |

**Don't touch:**

| Path | Owner |
|---|---|
| `GROUND_TRUTH.md` · `data/` · `scripts/` · `app/graph.py` | **Bhushan** |
| `web/` · `mock/` | **Ujwal** |
| `deploy/` · `video/` | **Bhushan** *(moved off Ujwal)* |

You will see `graph.py` missing a function you need, or returning a different shape than you assumed. **Ping Bhushan. Do not edit it.** You can be 20 minutes blocked and still ahead of the alternative.

> **`deploy/` and `video/` moved to Bhushan today.** So it doesn't surprise you at Sat 14:00 when you need a live URL: he owns the environment, the secrets, and the deploy. Your job when the frontend is deployed is to tell him it streams — and to give him the SSE headers he needs to paste into the proxy config. He's already got them; you still wrote them first.
</details>

<details>
<summary><b>3. The contract — freeze by 15:00, Day 1</b></summary>

You define it. Ujwal builds against it. **Do not rename a field after 15:00** — it breaks his renderer, and he can't find out until Gate 3.

```
POST /ask   { question }   →   SSE   { answer, trail[], stale[] }

trail[] = [ { type, name, detail, date, via_edge }, ... ]
stale[] = [ { type, name, reason, last_verified_at }, ... ]

GET /health
CORS for http://localhost:3000
```

| Field | What Ujwal does with it |
|---|---|
| `trail[].via_edge` | Renders the **edge label** between chips. This is what makes the trail legible instead of decorative — never drop it |
| `trail[].date` | Shows on the chip |
| `trail[].detail` | Expands when a chip is clicked |
| `stale[]` | Renders the ⚠ badge |

> **Decide `trail[]` with Bhushan's Cypher in mind.** He returns nodes plus the edges that produced them. If his rows are `[{node, via_edge}]` and your contract is `[{type, name, ...}]`, you are reshaping — so agree the shape at 14:00 when he finishes the schema, not at 21:00 when he finishes loading.

**The contract has a second copy: `mock/trail.json`.** Ujwal owns it and writes it to match exactly what's above. That file is what both of you build against on Day 1 — so when you change a field name here, you are changing it there too, and he needs to hear about it **before 15:00, not after.**

> Think of it this way: the block above is the *spec*, and `mock/trail.json` is the *executable spec*. If they disagree, the executable one wins at runtime and the bug lands on Ujwal's Saturday.
</details>

<details>
<summary><b>4. Independent tasks — start now</b></summary>

| # | Task | Done when |
|---|---|---|
| **S1** | **Freeze the contract. Tell Ujwal. Ship mock endpoints.** | Ujwal confirms he's building against it — and against his `mock/` |
| **S2** | `app/main.py` — FastAPI + SSE, **mock data behind one function** | Ujwal can build a full day; Bhushan slipping costs nothing |
| **S3** | `app/agent.py` — tool-use loop, tools pointed at mocks | Model picks the tool itself from the question |
| **S4** | Staleness surfaced as `stale[]` | Badges have real data behind them |

**S2 — one function, one job.** Put every mock behind something like `def get_trail(question): ...` with a fake branch. At Gate 2 you delete the fake branch. If mocks are scattered inline you'll be grepping at 22:00.

**Whose mock data?** **Ujwal's.** He owns `mock/` — a single fixture file that matches the frozen contract exactly, so his frontend and your fake branch read the *same* rows and can never drift. Read it, don't edit it. If the contract needs to change, that's a 14:00 conversation with him, not a Friday-night edit to his file.

> This is worth doing deliberately. Two independently-written mock sets are how you get a renderer that works against your fakes and breaks against his — the classic Gate 2 failure, and it wastes the whole Saturday morning.
</details>

<details>
<summary><b>5. Dependent task — one, and it's small</b></summary>

| # | Task | Done when |
|---|---|---|
| **S5** | Swap mocks for `app/graph.py` at **Gate 2 (Fri 21:00)** | Only `agent.py` / `main.py` change. Nothing else |

Because S1–S4 are all built against mocks, S5 is a one-line change per call site. **If S5 takes more than 20 minutes, something leaked from the mock layer into your real logic.** That's a design bug in S2, not a hard integration — go find it.
</details>

<details>
<summary><b>6. The agent loop is the product</b></summary>

Four rules. These are what separate this from a search box.

**1. The model chooses the tool.** Do **not** hardcode a pipeline that runs all three queries and concatenates. That is a search box with extra steps, and it loses the track on "multi-hop reasoning."

**2. Every claim carries its trail.** Never let the model assert a fact no tool returned. Pass the returned rows back in and require claims to be traceable to them.

**3. Empty result ≠ invention.** When a tool returns nothing, the answer says so. This is a feature — see section 13.

**4. Keep it readable.** You must be able to explain every line in judging (Rule 12). If a line is hard to explain, rewrite it. A framework would hide the thing being judged, so there is no framework here by design.

**Rough shape:**
```
question
  → model + tools
    → tool call selected by the model
      → app/graph.py  (Bhushan)
    → rows + trail back to the model
  → answer, where every claim is tied to trail rows
```
</details>

<details>
<summary><b>7. Tool descriptions are where routing quality lives</b></summary>

If the model picks the wrong tool, the description is ambiguous. **Fix the description, not the routing code.** This is the highest-leverage tuning you'll do on Sat morning.

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

Each names **one** intent and uses the words a person would. Avoid "queries the graph for" — it's the same prefix on all three and carries no signal.

Test all three questions from the demo against routing:

| Question | Must pick |
|---|---|
| "What breaks if payments goes down?" | `blast_radius` |
| "Who should I ask about the payments service?" | `expertise` |
| "Where did we decide to switch payment providers?" | `provenance` |

> "Who knows about payments **and** what breaks if it goes down **and** where was that decided?" is the demo question and hits **all three**. Make sure the model can chain them rather than stopping at the first.
</details>

<details>
<summary><b>8. SSE — the one gotcha</b></summary>

> **Native `EventSource` is GET-only.** Our contract is `POST /ask`, so it will not work. Ujwal must use `fetch()` + `response.body.getReader()`.

Decide this once, early, and tell him — otherwise he builds against `EventSource` and it fails at Gate 2.

**Server**
```python
from sse_starlette.sse import EventSourceResponse
# optional but tidy:  pip install sse-starlette

@app.post("/ask")
async def ask(req: Ask):
    return EventSourceResponse(stream_answer(req.question))
```

**Required headers** — without the second one, proxies buffer the stream into one lump and it works locally but dies in production:
```python
return StreamingResponse(gen(), media_type="text/event-stream",
                         headers={"Cache-Control": "no-cache",
                                  "X-Accel-Buffering": "no"})
```

**Watch for:** uvicorn `--reload` restarting mid-stream during Ujwal's testing. It looks like a frontend bug.

> **One new job for you: hand the SSE headers to Bhushan.** He owns the deployment now and has never had to think about proxy buffering. Without `X-Accel-Buffering: no` the stream works locally and dies in production, and he'll read that as a bug in your code. Send him both headers at Sat 14:00, before he tries the live URL — it's thirty seconds of your time that protects his video slot.
</details>

<details>
<summary><b>9. Your three days</b></summary>

### Fri Oct 16

| Time | Do |
|---|---|
| 13:00 | **Register** · setup ([`setup.md`](setup.md)) |
| **13:30** | **S1 — contract frozen, Ujwal told, mock endpoints live** |
| 14:00 | **S2** FastAPI + SSE complete against mocks |
| 16:00 | **S3** tool-use loop against mocks |
| **18:00** | 🛑 **GATE 1** — mock demo end-to-end with both others |
| 18:00 | **S4** staleness against mocks |
| 20:30 | Sanity-check Bhushan's traversals with him **before** you wire them |
| **21:00** | 🛑 **GATE 2** — graph landed · **S5** swap mocks for real |
| 23:30 | **Stop. Sleep by 01:00.** |

### Sat Oct 17

| Time | Do |
|---|---|
| 09:00–11:00 | **Routing quality with Bhushan** — tune tool descriptions (section 7) |
| 11:00 | 🛑 **GATE 3** — real-data demo on all three machines |
| 12:00–14:00 | **Break. Non-negotiable.** |
| 14:00–17:00 | **FEATURE FREEZE** — error handling, streaming polish, nothing new · **send Bhushan the SSE headers at 14:00** |
| 17:00 | 🛑 **GATE 4** — Bhushan's deploy; support him if the stream dies in production |
| 18:00–21:00 | **Demo video — be present** |
| 21:00–23:00 | Fact-check the README against your actual code · **support Bhushan's video** |
| **23:00** | 🛑 **GATE 5** — uninitiated teammate follows the README from scratch |

### Sun Oct 18

| Time | Do |
|---|---|
| 09:00–12:00 | Fix **only** what Gate 5 exposed |
| 12:00–14:00 | Video polish |
| **14:00** | 🛑 **HARD FREEZE** |
| 14:00–17:00 | Final deploy checks · submission support |
| **17:00** | 🛑 **SUBMIT** — Bhushan presses it, you support |

> Routing quality is the last thing worth spending time on. Everything after FEATURE FREEZE is packaging.
</details>

<details>
<summary><b>10. Gates</b></summary>

| # | When | Must be true | If not |
|---|---|---|---|
| **S1** | **Fri 15:00** | **Contract frozen + mocks live** | Push real work aside and do this now |
| 1 | Fri 18:00 | Mock demo runs end-to-end | Fix the contract before any real work |
| 2 | Fri 21:00 | Graph landed, mocks swapped | Bhushan cuts scope — **not** you |
| 3 | Sat 11:00 | Real-data demo on all three machines | Extend integration, cut polish |
| 4 | Sat 17:00 | Deploy works from a cold browser | **Bhushan's now** — the graph and the stream are usually the blockers |
| 5 | Sat 23:00 | Teammate follows README from scratch | Fix your setup section |
| — | **Sun 14:00** | 🛑 **HARD FREEZE** | — |
| — | **Sun 17:00** | 🛑 **SUBMITTED** | 7h buffer left |

> **S1 is its own gate** because it's the only one that costs other people, not you.
</details>

<details>
<summary><b>11. If you're behind</b></summary>

Cut in this order:

1. Streaming polish → plain non-streamed response
2. Staleness badge → drop `stale[]`, send `[]`
3. `/health` endpoint niceties

**Never cut:** S1 (contract + mocks) · S2 (the endpoint works) · the model choosing tools · claims tied to trail rows

> If S5 takes over 20 minutes, you leaked mock logic into real code. That's an S2 design bug — go fix it rather than patching forward.
</details>

<details>
<summary><b>12. Handoffs</b></summary>

| To | What | When |
|---|---|---|
| **Ujwal** | The frozen contract, in writing | **Fri 15:00** — plus the `EventSource`-is-GET-only warning |
| **Ujwal** | What his `mock/` file must look like — he owns it, you spec it | Fri 15:00, with the contract |
| **Bhushan** | The function signatures you need from `graph.py` | Fri 14:00, while he's sketching the schema |
| **Ujwal** | Any change in `trail[]` shape once real data lands | Sat 11:00 — flag it, don't leave him guessing |
| **Bhushan** | The SSE headers + env vars his deploy needs | Sat 14:00 — he's deploying, you're the only one who knows the stream |
| **Bhushan** | README fact-check against your real code | Sat 21:00 |

> **The SSE headers are now a handoff, not a footnote.** Bhushan owns the deployment and can't know that `X-Accel-Buffering: no` is what stops the stream dying in production. Send him the two headers at Sat 14:00, before he tries the live URL — otherwise he'll debug a proxy problem as a code problem and lose his video slot.

> **You're the README's fact-checker for the backend.** If it claims an endpoint or field that doesn't exist, a judge will find it. Ten minutes at 21:00 saves that.
</details>

<details>
<summary><b>13. The 5 questions that break you</b></summary>

Ground truth facts 16–20 in Bhushan's `bhushan.md` §5. These are **your** responsibility — the Cypher is correct but a loose agent loop will still invent an answer.

| # | Question | Required behaviour |
|---|---|---|
| 16 | Who owns `config-service`? | **"No `:OWNED_BY` edge exists."** The edge genuinely doesn't exist |
| 17 | What did checkout decide about pricing? | **"No `:Decision` node about pricing."** |
| 18 | Which service has zero dependents? | State which. Don't guess "payments" |
| 19 | Aisha Khan's current team? | **Departed 2026-06-30.** Not her old team |
| 20 | SLA for `dispute-service`? | Not in the graph. **Say so** |

**The trap:** the model has a strong prior to produce a fluent answer. "The config service is owned by the Platform team" is a perfectly grammatical, entirely fabricated sentence.

**Enforcement, in order of how well it works:**
1. Instruct it: *"If the tools do not return a fact, say you don't know. Never infer an owner, date, or decision that was not returned."*
2. Return empty results explicitly and visibly — don't silently omit the tool call
3. Test all five every time you change the loop

> Correct failure is a **demo beat**, not a limitation. It's the moment that proves the agent isn't just a confident narrator. Put it in the video.
</details>

<details>
<summary><b>14. Submission</b></summary>

You don't author the README, but two things are yours:

- [ ] **README matches your actual code** — endpoints, fields, and the SSE shape
- [ ] **You can explain the agent loop unaided** (Rule 12)

Rule 12 covers all three of you and is the one people underestimate. Rehearse it out loud:

> *"The model gets three tools. It picks one based on the question. Each tool runs a Cypher traversal in `app/graph.py` and returns rows plus the edges that produced them. Those rows go back to the model, and the final answer is required to cite them. When a tool returns nothing, the answer says so."*

That's 25 seconds and it's the core of the project. If you can say that, you can answer anything they ask.

**Full Rule 10 checklist lives in [`bhushan.md`](bhushan.md) §12** — Bhushan owns submission, you support.
</details>

<details>
<summary><b>15. Prompt — <code>app/main.py</code></summary>

```
FalkorDB company-brain agent (Track 03). I own app/agent.py and app/main.py.
I do NOT write the generator or the Cypher.

FROZEN CONTRACT (my colleague Ujwal is building the frontend against this RIGHT NOW
and must not be blocked, and the graph owner may be late):
  POST /ask  {question}  ->  SSE stream of {answer, trail[], stale[]}
  trail[] = [{type, name, detail, date, via_edge}, ...]
  stale[] = [{type, name, reason, last_verified_at}, ...]
  GET /health
  CORS for http://localhost:3000

TASK: app/main.py -- FastAPI + SSE.

CRITICAL: START WITH MOCK DATA. Put every mock behind ONE function with a clearly
marked fake branch, so when the real graph lands I delete one branch and change
nothing else. Do not scatter mock literals through the handlers.

- Stream with sse-starlette's EventSourceResponse, or StreamingResponse with
  media_type="text/event-stream" and headers Cache-Control: no-cache and
  X-Accel-Buffering: no (without that header proxies buffer the stream and it
  works locally but dies in production).
- Note for the frontend: native EventSource is GET-only, so the client must use
  fetch() + response.body.getReader(). Add a comment saying so.
- Take real data through pydantic models so the shapes cannot drift.
- Return realistic mock trail rows that match the frozen contract exactly,
  including via_edge values like "CONTRIBUTED_TO", "EVIDENCED_BY", "SUPERSEDES".

Output only this file, then the command to run it, then a curl command that
proves the stream works.
```
</details>

<details>
<summary><b>16. Prompt — <code>app/agent.py</code></summary>

```
FalkorDB company-brain agent (Track 03). I own app/agent.py.

My colleague owns app/graph.py and exposes these 4 functions, each taking params
(never string-interpolated) and returning rows that include the nodes AND the edges
that produced them, so a frontend can render a provenance trail with edge labels:
  blast_radius(service) -> dependent services, hop depth, owning team, on-call people
  expertise(service)    -> people ranked by contribution volume WITH recency
  provenance(project)   -> decisions, author, superseded decision, evidence node
  staleness()           -> edges whose last_verified_at is older than 90 days

TASK: app/agent.py -- an Anthropic tool-use loop.

- Define each function as a tool with a pydantic arg schema and a precise,
  unambiguous description. Routing quality comes from the DESCRIPTIONS, not from
  routing code -- the model picks which tool to run from the question. Do NOT
  hardcode a pipeline that runs all three.
- Return the tool rows plus the edge labels back into the conversation.
- Every claim in the final answer MUST be tied to trail rows that a tool returned.
  Never let the model assert a fact no tool returned.
- If a tool returns nothing, the answer must say it does not know. This is
  required behaviour, not an edge case -- we are explicitly tested on questions
  the graph cannot answer, and a fluent fabrication is a FAILED answer even though
  it reads fine. Instruct the model that it must never infer an owner, a date, or a
  decision that was not returned.
- Handle the multi-part demo question ("who knows about payments AND what breaks
  if it goes down AND where was that decided") by allowing sequential tool calls.
- Keep the loop explicit and readable. No framework. I must be able to explain
  every line in judging.

Output only this file, then the command to run it.
```
</details>

---

**Next:** complete [`setup.md`](setup.md) steps 1–9, then **S1 by 15:00**. Coordinate the `trail[]` shape with Bhushan at 14:00.