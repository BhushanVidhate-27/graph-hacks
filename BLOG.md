# We taught a database to say "I don't know" — and then had to prove it wasn't lying

**Helio — a company knowledge graph agent · Graph Hacks**

Ask *"who knows about the payments service, what breaks if it goes down, and where was that decided?"*

Most enterprise search answers *"where is the doc about X."* Helio answers **who knows about X, what breaks if it goes down, where was that decided, and how current is that answer** — in one traversal, with the path shown.

This post is about the part nobody puts in the demo: how you know the thing is actually correct when the thing is an LLM.

---

## The problem is not retrieval. It's that retrieval can't be trusted.

A company's knowledge is a graph. Services depend on services. Teams own services. Decisions supersede other decisions. If you store that as documents, you can find the document. You cannot answer the questions that actually block someone at 2pm.

So we built the graph. FalkorDB, 7 node types, 14 edge types, a synthetic 120-person fintech mid-migration between payment providers. Then we pointed an LLM at it with a tool-use loop.

That part worked. Then we asked the obvious follow-up question:

> **How do you know it didn't just make something up?**

And we hit the wall that shaped this entire project.

### The circularity trap

The normal move is to ask the model "is this answer correct?" — to use the LLM as its own judge. This is worth stating plainly because it's so tempting:

**It is circular.** A hallucinated ownership chain and a correct ownership chain are *structurally identical*. Both are fluent prose over well-formed edges. Both mention services, teams, dates, and documents. A judge model asked "does this look right?" is being shown the same evidence in both cases. It cannot tell them apart, because **there is no evidence that distinguishes them.**

The failure is invisible by construction. There is no signal that would have warned us.

---

## The fix: write the answer key before you see the answer

We did something that felt backwards at the time. In `GROUND_TRUTH.md`, we hand-wrote **20 facts about the company before generating a single row of data.**

This inverted the usual order. Normally you build the system, then eyeball whether it works. We'd already committed to what "correct" means, so the generator now has to satisfy us rather than the other way around.

The uncomfortable part: **5 of those 20 questions have no answer in the graph.** We designed them that way, on purpose.

```
"Who owns config-service?"
  →  "The graph contains no OWNED_BY edge. No team owns it."
```

That response is the product. Not an apology, not a hedge, not a guess — because an absent edge is a *real, correct answer*, not a gap in our data.

An agent that invents an owner there has failed, **even if the sentence reads perfectly.** We made that an explicit scoring category rather than a footnote.

### Why that framing matters more than it sounds

Building a system that answers correctly is mostly an engineering problem. Building one that *fails honestly* is a design problem, and it changes what you optimise for. Once "refuse" is a scored behaviour with the same weight as "answer," the prompt stops being about being helpful and starts being about being *legible*. You stop asking "how do I make the model more useful?" and start asking "what would make this answer checkable?"

---

## What the graph caught that text search structurally cannot

### The volume/recency trap

Priya Sharma has the most commits on `payments-gateway` — 14. Her last touch was 2026-04-15, the day she left the company.

A `ORDER BY count DESC` returns Priya. That query is **technically correct on volume and the wrong answer to the question.** Any system that collapses "who knows this" into a single number produces this confidently, and nothing in the output looks suspicious.

We return both signals and refuse to blend them:

> The Platform team owns payments. **Ravi Menon** has worked on it most recently (2026-09-28). **Priya Sharma** has the most commits (14), but her last touch was 2026-04-15 and is flagged as stale. Ask **Ravi Menon**.

The fix wasn't a smarter model. It was **not having one number where two facts belong.** Volume and recency are separate properties of separate edges, and collapsing them is a modelling error, not an intelligence problem.

### The contradiction with a citation

A March document and a March Slack thread both say *"single provider, Stripe."* Decision **D-19** (2026-05-06) says *"dual provider, Adyen primary, Stripe fallback."*

Both sources are stale, and the graph can **prove** it — because `SUPERSEDES` is an edge, not an inference. This is the thing embeddings cannot do: they can tell you these documents are *similar*. They cannot tell you one of them has been *formally retired by a decision you can name*. Citations make staleness actionable; without the edge, "this doc is out of date" leaves the reader unable to tell which live decision it undercuts.

---

## The bug that taught us the most: our own gate was lying

Partway through, our verification gate reported that all four must-fail questions were **wrong**. They were, in fact, correct and complete refusals:

```
Q16  "The graph contains no OWNED_BY edge for config-service…"
     → matched 1 of 8
Q17  "The graph contains no decisions whose summary mentions pricing."
     → matched 1 of 10
Q20  "The graph contains no SLA entry for dispute-service."
     → matched 1 of 7
```

Every one was a semantically perfect refusal. Every one failed.

The gate required all eight phrasings of "no" to appear in a single sentence. Read as an AND list, it was demanding that one sentence say "no no no no no no no no" — which no correct answer would ever do.

**We had shipped a gate that was backwards in the exact direction that wastes your time.** It was optimised to look thorough while penalising exactly the behaviour we said we wanted.

The instructive part is what we tried first: we widened the vocabulary. And the pass rate went **down**. Widening an AND list makes it strictly harder — every added term is another conjunct. An earlier attempt at this gate did precisely that.

> **The fix is the matching rule, not the word list.**

Refusal has many spellings, and no single answer contains all of them. So must-fail cases carry `ANY_OF` while affirmative cases keep AND — because "D-19" **and** "supersed" both have to be there to prove you understood *which* decision is current, but "no owner" only needs one honest phrasing.

That's the whole lesson, and it generalises past this project: **when a metric moves the wrong way, the metric is usually the bug.** We were about to "fix" the model. The model was fine.

---

## Other things that broke, and what they taught

**The server sends a full snapshot per SSE frame — not a delta.** Handlers must *replace*, not append. Append looks correct for exactly one frame, which is why it survives casual testing and then duplicates the whole answer trail in production. Protocol assumptions are code.

**Six graph facts the agent structurally could not reach.** Not "answered wrong" — *could not reach*. The Cypher was correct, the traversal was correct, and the agent still couldn't get to the answer because the shape of the returned rows didn't offer a path the model would take. A correct query behind an unreachable surface is still unreachable.

**Tool results blew past a 413.** A 6.5k-token tool result was large enough to be rejected outright. The fix was to return *trails* instead of raw rows — which turned out to be better product design anyway, because the trail is what a human wants to see.

**Agent results aren't stable run-to-run.** The model is sampled, so a single sweep tells you very little. Any conclusion drawn from one run — including "the fix worked" — is nearly worthless. This is why the ground-truth set is fixed and hand-written: it doesn't move when the model does.

---

## On the frontend, and deleting things

We started the site from a reverse-engineered capture of another product, which meant inheriting someone else's entire codebase — including 12 third-party scripts it loaded, including one that was **pulled from their domain**, and including a resource-saver script that deleted DOM nodes mid-parse and caused a hydration mismatch.

One of them was almost certainly why scroll only advanced two of four steps: their scroll controller driving our DOM. Remove all twelve: **0 console errors.**

Then the hard lesson. The captured HTML has **unclosed `<div>`s**, which means the obvious approach — count `<div>` and `</div>` until depth hits zero — silently runs past an element's real end. That deleted the footer and four entire sections in one cut. The cut *looked balanced*. Nothing complained. That's the worst kind of bug: the failure is invisible until you notice a section is gone.

The fix was to stop trusting the structure and start checking it: derive spans from a real HTML parser, and refuse to write unless the sentinel counts (`</main>`, `<footer>`, every `home-*-wrap`) survive. **A delete that can't fail silently is worth more than a delete that's usually right.**

There's a matching lesson in CSS. We tried "fixing" the cascade by layering the captured stylesheet so our utilities would win. It worked perfectly on buttons and **halved every section on the page**, because the markup used generic class names both stylesheets owned. Load order was the real mechanism all along.

---

## What I'd tell someone starting this

**Write the answer key first.** Everything downstream gets cheaper when correctness is defined before implementation exists.

**Treat "I don't know" as a feature with a score.** If refusal isn't measured, your model will be rewarded for guessing.

**Never let one number stand in for two facts.** The volume/recency trap wasn't an AI failure. It was a data-modelling choice we made years before the LLM existed.

**Don't fix the model when the metric is broken.** Our gate failed four correct answers for a day. Widening the vocabulary made it worse. The model was right the whole time.

**Make destructive operations fail loudly.** The unclosed-div bug and the layered-CSS bug had the same root cause: something looked correct while being wrong. Both were found by asking "what would I have to check to *know* this is safe?" — not by looking harder.

---

**Live:** https://helio-brain.onrender.com
**Repo:** `app/` (FastAPI + FalkorDB + LLM tool-use loop) · `scripts/` (generate → load → verify) · `front/` (static Next.js site)

All data is synthetic.