# GROUND_TRUTH.md — Helio

**The 20 planted facts, written by hand.**

I wrote these. That is the only reason verification is real. Asking an AI "is this answer
correct?" is circular — a hallucinated ownership chain looks exactly like a correct one,
because both are plausible prose over structurally valid edges.

Nobody else on this team can check the truth. If a fact below is wrong, the agent is
correct and this file is wrong. Fix the file.

- **Company:** Helio — 120-person fintech, 5 teams, 20 services, migrating payment providers.
- **All data is synthetic.** Rule 6.
- **Verification:** ask all 20 questions through the running agent, compare to this file.
  Anything unconfirmable from these notes is a bug or a graph hole — fix it, don't paper over it.

---

## 0. The dependency DAG (source of truth for blast radius)

One row = *this service depends on the listed services*. `ledger-core` has no
dependencies; it is the root that everything financial hangs off.

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

**20 services · 22 `DEPENDS_ON` edges · verified acyclic.**

> **Why `auth-service` and `api-gateway` depend on nothing.** An earlier draft had both
> fanning out to "all public services". That was wrong twice over: it made the graph
> **cyclic** (`api-gateway → web-frontend → api-gateway`) and it dragged the entire
> frontend/edge tier into `payments-gateway`'s blast radius, inflating the answer to 14
> services of which most were noise. The public tier is *downstream of nothing* — it is
> the edge. Removing the fan-in is what makes fact 5 a sharp answer.

### Service ownership (team level)

| Team owns | Services |
|---|---|
| Platform | `payments-gateway`, `webhook-relay` |
| Payments | `checkout-api`, `mobile-bff`, `dispute-service` |
| Ledger | `ledger-core`, `settlement-batch`, `billing-invoicing`, `reporting-etl` |
| Risk | `fraud-scoring` |
| Growth | `notifications`, `recommendation` |
| — | `config-service` **has no owner at all** (fact 4) |

---

## 1–4 · Ownership

| # | Question | Correct answer |
|---|---|---|
| **1** | Who owns `payments-gateway` **today**? | **Ravi Menon** (Platform). Priya Sharma owned it until 2026-04-15, when decision **D-21** reassigned it. Evidence: `payments-ownership-handoff.md`. |
| **2** | Who owns `ledger-core`? | **Ledger** team, lead **Ana Duarte**. |
| **3** | Who owns `fraud-scoring`? | **Risk** team, **Diego Alvarez**. |
| **4** | Does every service have an owner? | **No.** `config-service` has **no `:OWNED_BY` edge**. Mei Lin contributes to it; nobody owns it. |

> Ownership is `(Service)-[:OWNED_BY]->(:Team)`, which cannot express a *person*. Fact 1
> is therefore carried by decision **D-21** + its evidence document, and read through the
> provenance path. This is deliberate — see §60 of `all_steps.md`.

---

## 5–7 · Blast radius

Blast radius walks the **inverse** edge `HAS_DEPENDENT`, never a reversed `DEPENDS_ON`.
Cypher cannot traverse an edge backwards; both edges are emitted from this one table.

| # | Question | Correct answer |
|---|---|---|
| **5** | What breaks if `payments-gateway` dies? | **8 services**, in 3 hops:<br>**depth 1** — `checkout-api`, `config-service`, `dispute-service`, `mobile-bff`, `notifications`, `webhook-relay`<br>**depth 2** — `fraud-scoring`<br>**depth 3** — `recommendation` |
| **6** | Which of those are owned by a different team? | Six, across three teams:<br>**Payments** — `checkout-api`, `mobile-bff`, `dispute-service`<br>**Growth** — `notifications`, `recommendation`<br>**Risk** — `fraud-scoring`<br>Plus `config-service`, which has **no team at all** — a bigger finding than cross-team ownership. |
| **7** | Which dependent has no contributor in 90 days? | **`notifications`** — owned by Growth, one hop from `payments-gateway`, and nobody has touched it since 2026-05-02. **Bus-factor risk.** |

> **Fact 5 does NOT include `ledger-core` or `settlement-batch`.** They are *upstream* of
> payments — payments breaks if **they** die, not the reverse. The original draft listed
> them; that was wrong and the generator would have been bent to match it.
>
> **Fact 7 was re-pointed from `settlement-batch` to `notifications`.** `settlement-batch`
> depends on `ledger-core`, so it is not in this blast radius at all and the question could
> not be answered as written. `settlement-batch` is still planted with zero recent
> contributors — it is simply no longer the answer to *this* question.

---

## 8–11 · Who knows what

| # | Question | Correct answer |
|---|---|---|
| **8** | Most commits on `payments-gateway`? | **Priya Sharma** — 14 commits, but last touch **2026-04-15**. She left the company that day. **Stale.** A naive `ORDER BY count DESC` returns her and is *technically correct on volume while being the wrong answer*. Recency must reorder her below Ravi. |
| **9** | Best person to ask about payments now? | **Ravi Menon.** Current owner since 2026-04-15. |
| **10** | Worked on **both** payments and ledger? | **Ana Duarte** — the only cross-team bridge. The only person contributing to a payments project *and* a ledger project. |
| **11** | Who's on call for Ledger this week? | **Diego Alvarez.** Priya Sharma is on **no** rotation — she left in April. |

> **Fact 8 is the single best 20 seconds of the demo.** A naive query gets it wrong. Ours
> catches it and explains the tension. Do not flatten this into one ranking — return volume
> *and* recency and let the agent narrate the conflict.

---

## 12–15 · Provenance

| # | Question | Correct answer |
|---|---|---|
| **12** | Where was the migration decided? | **D-14**, 2026-03-18, author **Elena Vasquez** (CTO). Evidence: `payments-provider-eval-v3.md`, plus a `#inc-payments` message the same day. |
| **13** | Was D-14 current? | **No — superseded by D-19** (2026-05-06): *"Dual provider: Adyen primary, Stripe fallback."* D-19 `SUPERSEDES` D-14. |
| **14** | Decision authority for payments/ledger? | **Elena Vasquez** — the **only** author of any `:Decision` node in the graph. All ~40 decisions are hers. |
| **15** | The planted contradiction? | `payments-provider-eval-v3.md` (2026-03-18) and the March Slack thread both say **"single provider, Stripe."** **D-19** (2026-05-06) says **"dual provider, Adyen primary."** **The document is stale** and the graph must be able to prove it. |

> The document carries `last_verified_at = 2026-03-18` so a >90-day staleness query catches
> it. D-19 is the current truth and is contradicted by nothing.

---

## 16–20 · Must FAIL correctly

These five are **genuinely absent** from the graph — not merely unanswered. An agent that
invents an answer here **has failed**, even when the sentence reads perfectly.

| # | Question | Required behaviour |
|---|---|---|
| **16** | Who owns `config-service`? | **"No `:OWNED_BY` edge exists."** Confident, not an apology, not an error string. No invented owner — *especially not* "the Platform team". |
| **17** | What did checkout decide about pricing? | **"No `:Decision` node about pricing."** No fabrication. Verified programmatically: the string `pricing` appears in **zero** decision rows. |
| **18** | Which service has zero dependents? | State the real list — it is **10** services: `admin-bff`, `config-service`, `mobile-bff`, `notifications`, `recommendation`, `search-index`, `session-store`, `settlement-batch`, `web-frontend`, `webhook-relay`. Do **not** guess "payments-gateway". |
| **19** | Aisha Khan's current team? | **Departed 2026-06-30.** Her `MEMBER_OF` edge carries `valid_to = 2026-06-30`. She appears in historical queries, never as *current*. Not her old team (Growth). |
| **20** | SLA for `dispute-service`? | **Not in the graph. Say so.** Every other service has an `sla` property; `dispute-service`'s is empty. If you give it an SLA, this test dies. |

---

## Load-bearing people

| Person | Team | Note |
|---|---|---|
| **Elena Vasquez** | — | CTO, no team. **Only** author of any `:Decision` — fact 14. |
| **Ravi Menon** | Platform | Current `payments-gateway` owner. On the Ledger rotation — fact 11. `(:Person:Member)`. |
| **Priya Sharma** | ~~Payments~~ | **Left 2026-04-15.** Exactly **14** commits on the payments project, `last_touch 2026-04-15`. On **no** rotation — facts 8, 11. |
| **Ana Duarte** | Ledger | Only person spanning payments **and** ledger — fact 10. |
| **Diego Alvarez** | Risk | Owns `fraud-scoring`. On the Ledger rotation — fact 11. |
| **Aisha Khan** | ~~Growth~~ | **Departed 2026-06-30**, `valid_to` set — fact 19. |
| **Tomas Berg** | Payments | `checkout-api`. Zero decisions. |
| **Mei Lin** | Platform | Contributes to `config-service`. Owns nothing — fact 4. |

Plus ~92 faker-generated fillers across Platform, Ledger, Payments, Risk, Growth.

**`(:Person:Member)`** — anyone on a rotation carries a second label. So Ravi Menon is
`(:Person:Member)`. This is load-bearing: the blast-radius Cypher already contains
`(:Team)-[:HAS_ROTATION]->(:Member)-[:ON_CALL]->(:Person)`. If the generator, loader and
query disagree on this, the query returns `[]` **silently**.

---

## Freshness is edge properties, not a system

```
(:Person)-[:MEMBER_OF      { since, role, valid_to }]->(:Team)
(:Person)-[:CONTRIBUTED_TO { role, commits, last_touch, last_verified_at }]->(:Project)
(:Decision)-[:SUPERSEDES]->(:Decision)
(:Document)-[:last_verified_at]
```

A separate staleness model is **out of scope**. Do not build one.

---

## Change log — decisions taken 2026-10-17

These four were resolved before any data was generated. Each one would otherwise have
failed at Gate 2, when there was no time left to fix it.

| # | Was | Now | Why |
|---|---|---|---|
| 1 | `auth-service`, `api-gateway` → all public services | → nothing | Caused 2 cycles + inflated blast radius to 14 |
| 2 | Fact 5 listed 7 services incl. `ledger-core` | 8 services, upstream excluded | `ledger-core`/`settlement-batch` are upstream of payments |
| 3 | Fact 7 → `settlement-batch` | → `notifications` | `settlement-batch` is not in the payments blast radius |
| 4 | "18 services" | **20 services** | `ledger-core` had no row in the table despite 7 dependents |

---

## Addendum 2026-10-17 — on-call resolved

`bhushan.md` §5 contradicted itself: the People table said *"Ravi Menon — on-call
Ledger"*, fact 11 said the answer was **Diego Alvarez**. Both cannot be the single
on-call person.

**Resolved:** rotation membership and on-call are separate facts.

| Person | On the Ledger rotation? | On call this week? |
|---|---|---|
| Ravi Menon | yes | **no** |
| Diego Alvarez | yes | **yes** |
| Priya Sharma | **no** — left 2026-04-15 | no |

**Fact 11 answer is unchanged: Diego Alvarez.** What changed is the model —
`HAS_ROTATION` (standing) is now distinct from `ON_CALL` (dated). See
[`SCHEMA.md`](SCHEMA.md) §2.

Ravi being on the rotation but *not* on call this week is what makes fact 11 a real
answer rather than a lookup: the graph has to reject two of its three candidates.

**Fact 10 note:** this also strengthens fact 10. Ana Duarte is on neither payments nor
ledger's rotation — she is the only person who worked both, with no on-call
justification. That is exactly the kind of hidden bus-factor the product exists to
surface.
