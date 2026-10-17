# Ujwal — Plan

**Track 03: Company Brain · Graph Hacks · Oct 15–18**
You own everything the judges actually **see**, and you're the lowest-risk member on the critical path — nothing you do waits on anyone. You also own **`mock/`**, the fake data everyone builds against on Day 1.

**`deploy/` and `video/` moved to Bhushan.** You no longer own them. See section 2.

Setup first: [`setup.md`](setup.md) — steps 1–8, then **10**, 11 and 21.

---

## Index

| # | Section |
|---|---|
| 1 | [Why this is yours](#) |
| 2 | [What you own](#) |
| 3 | [The contract](#) |
| 4 | [Independent tasks](#) |
| 5 | [Dependent task — one](#) |
| 6 | [The provenance renderer](#) |
| 7 | **`mock/` — you own the fake data** |
| 8 | [What not to build](#) |
| 9 | [Your three days](#) |
| 10 | [Gates](#) |
| 11 | [If you're behind](#) |
| 12 | [Handoffs](#) |
| 13 | [Submission](#) |
| 14 | [Prompt: web/ + mock/](#) |

---

<details>
<summary><b>1. Why this is yours and not shared</b></summary>

Two reasons.

**You are the only person whose work is fully independent.** Bhushan is on a sequential critical path; Soham is blocked on real graph data. You can finish 90% of your job against mocks on Day 1. That makes you the team's shock absorber — when Gate 2 slips, you're the one who doesn't care.

**But you also own the difference between a demo and a product.** The provenance trail is the concrete, visible proof of the thesis — *traverse structure, not similarity*. A list of names with citations is what everyone else ships. A traceable chain of edges is what makes this entry. Spend your hours there.

> **Owning `mock/` makes the first reason even stronger.** You now write the fake data *and* the interface that consumes it — so Day 1 isn't "waiting on Bhushan", it's "the contract is real and I wrote both ends of it". Nobody on this team can build anything on Day 1 without you.

> **Rule 3 is your real constraint:** *"A visualisation drawn on top of ordinary storage does not qualify."* A pretty UI can actively hurt us if it's decoration. Section 8.
</details>

<details>
<summary><b>2. What you own</b></summary>

**Own:**

| Path | Contents |
|---|---|
| `web/index.html` | The whole interface |
| `mock/` | **The fake data — one fixture file, the frozen contract in data form** |

**Don't touch:**

| Path | Owner |
|---|---|
| `GROUND_TRUTH.md` · `data/` · `scripts/` · `app/graph.py` | **Bhushan** |
| `app/agent.py` · `app/main.py` | **Soham** |
| `deploy/` · `video/` | **Bhushan** *(moved off you)* |

Soham freezes the contract by 15:00. **Build against your own `mock/`.** You no longer need to wait for anyone's endpoints — you are the source of the fake data.

> ⚠️ **Port 3000 conflict.** FalkorDB Browser runs on `3000`. If you start a JS dev server there you will collide and Bhushan's debugging loop breaks silently. Use `5173` or anything else.

> **`deploy/` and `video/` are Bhushan's now — say so in the group chat today.** He has a full critical path and just picked up two more deliverables. If he finds out at Sat 14:00 by asking where his deploy files are, that costs a day.

> **Still offer to help on the deploy.** You built the frontend, so you know what a blank page looks like. When Bhushan has a URL, be the person who opens it in incognito before he does — that check is Gate 4 and he's now alone on it.
</details>

<details>
<summary><b>3. The contract</b></summary>

Soham owns it. You consume it.

```
POST /ask   { question }   →   SSE   { answer, trail[], stale[] }

trail[] = [ { type, name, detail, date, via_edge }, ... ]
stale[] = [ { type, name, reason, last_verified_at }, ... ]
```

| Field | What you render |
|---|---|
| `trail[].type` | Chip label — `Person`, `Decision`, `Document`, `Message` |
| `trail[].name` | Main chip text |
| `trail[].detail` | Expands when the chip is clicked |
| `trail[].date` | Secondary text on the chip |
| `trail[].via_edge` | **The edge label between chips.** This is what makes the trail readable — never drop it |
| `stale[]` | ⚠ badge |

> ⚠️ **Native `EventSource` is GET-only.** Our contract is `POST /ask`, so it will not work. You need `fetch()` + `response.body.getReader()`. Soham knows — if you see a stuck spinner at Gate 2, this is why.
</details>

<details>
<summary><b>4. Independent tasks — start now, nothing blocks you</b></summary>

| # | Task | Done when |
|---|---|---|
| **U1** | `mock/` — **one fixture file** matching the frozen contract exactly | Soham's fake branch and your page both read it |
| **U2** | `web/index.html` — question box, streamed answer, trail | Renders fully against `mock/` |
| **U3** | **The provenance renderer** | Chips render `person → decision → doc → message` with edge labels |
| **U4** | Staleness badges from `stale[]` | ⚠ badge on outdated items |
| **U5** | Create the **FalkorDB Cloud** account, share creds | Bhushan + Soham have them **before 18:00** |
| **U6** | Test Bhushan's `deploy/` in incognito when he has a URL | Sat 16:00 — you're the cold-browser check |

**U1 first, then U5.** You wrote the mock, so you unblock the team twice before lunch: Soham can build his fake branch from it at 13:30, and Bhushan can create the Cloud instance at 15:00. Two people blocked on you is the highest-leverage ten minutes in the project.

**U6 is a small task with a large job title.** You're not deploying anything. You're the person who opens a URL in a logged-out browser and says whether it works — which is exactly the check Bhushan can't do honestly for himself, and exactly Gate 4.
</details>

<details>
<summary><b>5. Dependent task — one, and it's a one-liner</b></summary>

| # | Task | Done when |
|---|---|---|
| **U7** | Point at the real API at **Gate 2 (Fri 21:00)** | Change the fetch. **Renderer untouched.** |

That is the whole handoff. **You have the cleanest version of this in the project**, because you wrote `mock/` to the contract — so switching to real data should be a one-line change and nothing else.

If your renderer needs editing when real data arrives, the problem is in `mock/`, not the renderer: your fixture drifted from the contract. Fix `mock/`, not the trail.
</details>

<details>
<summary><b>6. The provenance renderer — spend your hours here</b></summary>

This is the single highest-leverage thing in the project. It's the strongest 20 seconds of the demo video and the concrete difference between *answers that show their path* and another chat UI.

Render the chain as **clickable chips**:

```
[ Priya Sharma · 14 commits · last 2026-04-15 ]
      ──CONTRIBUTED_TO──▶
[ D-14 · 2026-03-18 · superseded by D-19 ]
      ──EVIDENCED_BY──▶
[ payments-provider-eval-v3.md · ⚠ stale ]
      ──MENTIONS──▶
[ #inc-payments · 2026-03-28 ]
```

Each chip carries `type`, `name`, `date`, and the **edge label** linking it to the previous. Clicking expands the raw sub-result so a judge sees actual query output, not a summary you wrote.

**Why the edge labels matter:** without them it's a list of four things that happened to be near each other. With them it's a proof chain — `EVIDENCED_BY` and `SUPERSEDES` are doing semantic work that a plain search result can't do.

**Staleness is a first-class chip state**, not a footnote. `payments-provider-eval-v3.md` is stale, and the UI should say so at the moment it's displayed.

> If you finish everything else early, improve this. If you're running out of time, cut styling everywhere *except* here.
</details>

<details>
<summary><b>7. <code>mock/</code> — you own the fake data</b></summary>

Two people need fake data before real data exists. You now supply it to **both**, from **one** file.

```
mock/trail.json     the contract in data form
       │
       ├── Soham's fake branch in main.py      (builds against it Fri 13:30)
       └── your web/index.html                 (builds against it Fri 13:00)
```

**Why one file and not two.** If Soham writes his own fakes and you write yours, they drift. Then Gate 2 arrives, the real API lands, and your renderer breaks on real rows — because it was never tested on anything but yours. That failure costs Saturday morning, and Saturday morning is verification time. One file makes it impossible.

**What goes in it.** Realistic rows for the demo question, using the real names from Bhushan's ground truth so the fixtures survive the swap to real data:

```json
{
  "answer": "Ravi Menon knows payments best right now...",
  "trail": [
    { "type": "Person",     "name": "Priya Sharma",   "detail": "14 commits, last touch 2026-04-15", "date": "2026-04-15", "via_edge": "CONTRIBUTED_TO" },
    { "type": "Person",     "name": "Ravi Menon",     "detail": "Current owner since 2026-04-15",   "date": "2026-05-02", "via_edge": "OWNED_BY" },
    { "type": "Decision",   "name": "D-14",           "detail": "Superseded by D-19",              "date": "2026-03-18", "via_edge": "EVIDENCED_BY" },
    { "type": "Document",   "name": "payments-provider-eval-v3.md", "detail": "States Stripe-only", "date": "2026-03-18", "via_edge": "SUPERSEDES" },
    { "type": "Message",    "name": "#inc-payments",  "detail": "payments timeouts again after deploy", "date": "2026-03-28", "via_edge": "MENTIONS" }
  ],
  "stale": [
    { "type": "Person",   "name": "Priya Sharma", "reason": "left the company 2026-04-15", "last_verified_at": "2026-04-15" },
    { "type": "Document", "name": "payments-provider-eval-v3.md", "reason": "contradicted by D-19", "last_verified_at": "2026-03-18" }
  ]
}
```

**Four rules for the fixture:**

1. **Every field in the contract appears.** Including the boring ones. A missing `via_edge` is a chip that renders wrong and you won't find out until real data.
2. **Include a `stale[]` entry.** If your fixture has no stale items, U4 is untestable and you won't build the badge until Gate 2.
3. **Include at least one beat-5 case.** A `"I don't know"` answer with an empty `trail` — otherwise your empty state is untested, and that's the beat that proves the agent doesn't hallucinate.
4. **Real names, not lorem ipsum.** When Bhushan's data lands, the swap should be invisible.

> **Tell Soham the file exists, Fri 13:30.** He's supposed to be coding against mocks by then and he can't code against a file he doesn't know about. This is a two-minute message that saves him an hour.

> **You are the only person who can unblock both others on Day 1.** Mock data at 13:00, Cloud credentials at 15:00. Nobody else on this team can start until you've done those two things.
</details>

<details>
<summary><b>8. What not to build</b></summary>

**No graph visualisation. No network canvas. No force-directed anything.**

Rule 3: *"A visualisation drawn on top of ordinary storage does not qualify."* A pretty graph picture reads as decoration and actively works against the submission — it signals you had data and needed to draw it.

It also **takes hours you don't have** and tells a judge nothing they can't get from the Browser.

**Also skip:** auth, dark-mode polish, responsive layouts beyond one breakpoint, animation beyond a subtle chip fade. The trail is the product.

> One exception if you have spare time: a small static diagram of the *schema* (nodes + relationship types, no data) for the README. That's documentation, not decoration, and it's genuinely useful to a judge. Hand it to Bhushan — he writes the README.
</details>

<details>
<summary><b>9. Your three days</b></summary>

### Fri Oct 16

| Time | Do |
|---|---|
| 13:00 | **Register** · setup ([`setup.md`](setup.md)) · **U1** `mock/trail.json` |
| 13:30 | Tell Soham the mock file exists — unblock him |
| 14:00 | **U2** UI skeleton against `mock/` |
| 15:00 | **U5** FalkorDB Cloud account, share creds |
| 16:00 | **U3** provenance renderer — the real work |
| **18:00** | 🛑 **GATE 1** — mock demo end-to-end, all three |
| 18:00 | **U4** staleness badges |
| 20:00 | Polish against mock: empty state, streaming, badge hover |
| **21:00** | 🛑 **GATE 2** — **U7** switch to the real API |
| 23:30 | **Stop. Sleep by 01:00.** |

### Sat Oct 17

| Time | Do |
|---|---|
| 09:00–11:00 | Streaming polish, badge states, one narrow breakpoint |
| 11:00 | 🛑 **GATE 3** — real-data demo on all three machines |
| 12:00–14:00 | **Break. Non-negotiable.** |
| 14:00–16:00 | **FEATURE FREEZE** · **U6** cold-browser check on Bhushan's deploy |
| 17:00–20:00 | **Support Bhushan's video recording** — you'll be on camera |
| 20:00–22:00 | Schema diagram for the README · support Bhushan on README |
| **23:00** | 🛑 **GATE 5** — uninitiated teammate follows the README from scratch |

### Sun Oct 18

| Time | Do |
|---|---|
| 09:00–12:00 | Fix **only** what Gate 5 exposed |
| 12:00–14:00 | Frontend polish · last check of the live URL |
| **14:00** | 🛑 **HARD FREEZE** |
| 14:00–17:00 | Available to Bhushan — he's submitting alone |
| **17:00** | 🛑 **SUBMIT** — Bhushan presses it |
| 17:00–23:59 | Buffer — 7h, and uploads fail |

> **Your day is front-loaded and your Sunday is nearly empty.** That's the point of owning `mock/` instead of the deploy: you finish your real work by Sat 11:00 and then you're the team's spare capacity. Use it where it's actually needed — Gate 5 rewrites, and whatever Bhushan is stuck on at 15:00 Sunday.
</details>

<details>
<summary><b>10. Gates</b></summary>

| # | When | Must be true | If not |
|---|---|---|---|
| — | **Fri 13:30** | **`mock/trail.json` exists, Soham knows** | Nobody can build — do this first |
| — | **Fri 15:00** | **FalkorDB Cloud creds shared** | Blocks two people |
| 1 | Fri 18:00 | Mock demo runs end-to-end | Fix your fetch before polishing |
| 2 | Fri 21:00 | Switched to real API | Renderer shouldn't need changes |
| 3 | Sat 11:00 | Real-data demo on all three machines | Extend integration, cut polish |
| **4** | **Sat 16:00** | **You incognito-tested Bhushan's deploy** | **Tell the team now — he falls back to local setup** |
| 5 | Sat 23:00 | Teammate follows README from scratch | Fix your setup section |
| — | **Sun 14:00** | 🛑 **HARD FREEZE** | — |
| — | **Sun 17:00** | 🛑 **SUBMITTED** | 7h buffer left |

> **Gate 4 is Bhushan's now, and you're the person who can save it.** He owns the deploy but he can't test it honestly — he knows where every hack is and what works on his machine always looks like it works. You open it in incognito and say yes or no. That check catches what nothing else does.

> **Gate 2 is your real gate.** If your renderer needs editing when real data lands, the fault is in your `mock/` — you drifted from the contract. Fix the fixture, not the trail.
</details>

<details>
<summary><b>11. If you're behind</b></summary>

Cut in this order:

1. Narrow-width styling
2. Hover states, transitions
3. Chip expansion on click
4. Extra `mock/` fixture variety — one good fixture beats five stale ones

**Never cut:** U3 (provenance renderer) · U1 (`mock/`, because everyone builds on it) · the empty "I don't know" state

> A plain-looking page with a great trail beats a beautiful page with a list of names. Judges score the thesis, not the CSS.

> **You gave up the deploy and the video — don't also give up polish.** You have the shortest critical path in the team and the most free hours after Sat 11:00. Spend them on the trail, which is the thing being judged, rather than on the layout.
</details>

<details>
<summary><b>12. Handoffs</b></summary>

| To | What | When |
|---|---|---|
| **Soham** | **`mock/trail.json` exists — build against this, not your own fakes** | **Fri 13:30** — he's coding by then |
| **Bhushan + Soham** | **FalkorDB Cloud credentials** | Fri 15:00 |
| **Soham** | Contract questions while he's writing it | Fri 15:00 |
| **Soham** | Flag any `trail[]` shape change once real data lands | Sat 11:00 — don't leave him guessing |
| **Bhushan** | **Your incognito verdict on his deploy — yes or no, unvarnished** | **Sat 16:00** — Gate 4 |
| **Bhushan** | Schema diagram for the README | Sat 20:00 |
| **Bhushan** | Your Saturday: help with the video recording if he wants a second pair of eyes on the trail | Sat 17:00–20:00 |
| **All three** | "Deploy is broken" | Sat 16:00+, the moment you know |

> **Two messages unlock the whole team on Day 1.** *"The mock file is here"* at 13:30, *"here are the Cloud credentials"* at 15:00. Nothing anyone else does on Friday happens before those two messages.

> **You now have the shortest path and the most slack.** Bhushan has every critical deliverable including deploy and video; Soham has the agent. If something is late, it's usually theirs. Your highest-value hours after Sat 11:00 are spent on *their* deadlines — not on more of your own.
</details>

<details>
<summary><b>13. Submission</b></summary>

Bhushan authors the README and owns the submission. You own two things — and only one of them is code:

- [ ] **The trail renders real data correctly** — your item, and the one judges will look at longest
- [ ] **Your cold-browser verdict on the deploy** (Gate 4) — you don't build it, you verify it, and you say so plainly

Full Rule 10 checklist in [`bhushan.md`](bhushan.md) §12.

**What you should be able to say at the end,** for Rule 12:

> *"The answer streams token by token, and beneath it the trail renders each node as a chip labelled with the edge that got us there — `CONTRIBUTED_TO`, `EVIDENCED_BY`, `SUPERSEDES`. That's the point: you see the reasoning, not just the answer. Anything outdated gets a warning badge the moment you see it, because a correct answer from April isn't a correct answer today."*

That's 25 seconds. Practise it out loud before Sunday — all three of you must be able to explain the design, and **the trail is the design.**
</details>

<details>
<summary><b>14. Prompt — <code>mock/</code> + <code>web/index.html</code></summary>

```
I am building the frontend for a FalkorDB company-brain agent (Track 03).
I do NOT write Cypher or the LLM agent. I own web/ and mock/ only.

TASK 1: mock/trail.json -- FIRST, before anything else. Two of us build against
this file (my colleague builds his mock API branch from it, and my frontend reads
it), so it must match the frozen contract EXACTLY. One shared fixture, so our two
fake implementations cannot drift apart.

The backend contract is frozen:
  POST /ask {question} -> SSE stream of {answer, trail[], stale[]}
  trail[] = [{type, name, detail, date, via_edge}, ...]
  stale[] = [{type, name, reason, last_verified_at}, ...]

The fixture must contain:
- the full demo answer as a list of strings, so a streamer can be tested against it
- a realistic trail[] using these real names and values:
    Person    Priya Sharma                    14 commits, last 2026-04-15, via_edge CONTRIBUTED_TO
    Person    Ravi Menon                      current owner since 2026-04-15
    Decision  D-14 (2026-03-18)              superseded by D-19, via_edge EVIDENCED_BY
    Decision  D-19 (2026-05-06)              dual provider, Adyen primary
    Document  payments-provider-eval-v3.md   states Stripe-only, via_edge SUPERSEDES
    Message   #inc-payments (2026-03-28)     "payments timeouts again after deploy", via_edge MENTIONS
- a stale[] with at least two entries: Priya Sharma (left the company 2026-04-15)
  and the v3 document (contradicted by D-19)
- a SECOND fixture representing the failure case: "Who owns config-service?" ->
  an answer saying no OWNED_BY edge exists, trail[] EMPTY. I need to test the
  empty state, because that is one of the five demo beats.
- EVERY field present, including the boring ones. A missing via_edge is a chip that
  renders wrong and I will not find out until real data lands.

Output only mock/trail.json, then a 3-line note telling my colleague how to load it.

TASK 2: web/index.html -- single page, vanilla JS, NO build step, NO framework.

IMPORTANT: native EventSource is GET-only and our contract is POST, so use
fetch() + response.body.getReader() to consume the stream.

- Question box, streamed answer, and THE PROVENANCE TRAIL rendered as a horizontal
  chain of clickable chips:
      [ Priya Sharma | 14 commits | last 2026-04-15 ]
        --CONTRIBUTED_TO--> [ D-14 | 2026-03-18 | superseded by D-19 ]
        --EVIDENCED_BY-->  [ payments-provider-eval-v3.md | stale ]
        --MENTIONS-->      [ #inc-payments | 2026-03-28 ]
  Each chip shows type, name, date, and the EDGE LABEL that linked it to the
  previous one. Clicking a chip expands the raw sub-result.
- stale[] items render as a warning badge on the relevant chip.
- Handle the EMPTY trail case properly -- it is a demo beat, not an error state.
  It should read as a confident answer, not a broken page.
- Keep a SINGLE fetch() call site. Point it at the mock file to start; switching to
  the real endpoint must be a one-line change.
- NO graph visualisation, no network canvas, no force-directed anything. That is
  decoration and it hurts us.
- Spend the most effort on the provenance trail. It is the most important thing
  on the page.
```
</details>

---

**Next:** complete [`setup.md`](setup.md) steps 1–8, then **U1 — `mock/trail.json`** by 13:30 and tell Soham it exists. Then **U5 — the FalkorDB Cloud account** — before 15:00. Two people are blocked on both.
