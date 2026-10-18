# Microsoft Graph parity

**Why this file exists.** Microsoft Graph (`https://graph.microsoft.com/v1.0`) is
the "company graph" every judge already knows, and its own reference
(<https://learn.microsoft.com/en-us/graph/api/overview?view=graph-rest-1.0>)
names four headline use cases: a user's **manager** and **direct reports**, a
group's **members**, **chat/file** search. This doc maps that resource surface
onto the Helio schema and names exactly where our agent was weaker — and what
was added to close it.

The exercise matters because the README positions Helio *against* enterprise
search and *alongside* Microsoft Graph: "M365 already holds people, files,
meetings and org data; Copilot sits on top" (see `research.md` §8). If our
agent cannot answer the questions Graph answers out of the box, the positioning
is just a claim.

## The mapping

| Microsoft Graph capability | Helio data (already present) | Agent tool | Status |
|---|---|---|---|
| `/users/{id}/manager` + transitive | `REPORTS_TO` (99 edges) | `reports_to` | **added** |
| `/users/{id}/directReports` + transitive | `REPORTS_TO` (same edge, source side) | `direct_reports` | **added** |
| `/groups/{id}/members` (roster + roles) | `MEMBER_OF {role, since, valid_to}` | `team_members` | **added** |
| chat / message search | 2,000 `Message` + 1,931 `MENTIONS` | `search_messages` | **added** |
| drive-item / SharePoint search | 200 `Document` | `find_documents` | **added** |
| `/users?$search`, `/people` (relevance) | `CONTRIBUTED_TO` | `expertise` | already had |
| directory roles / `memberOf` | `role` on `MEMBER_OF` | folded into `team_members` | covered |
| `/presence` (availability) | no node in the frozen 7-type schema | — | deliberate omission |
| `/events`, `findMeetingTimes` (calendar) | no node in the frozen 7-type schema | — | deliberate omission |
| delta / tracked changes | `SUPERSEDES`, `last_verified_at` | `staleness`, `provenance` | already had (stronger) |

## The gap that mattered

Four capabilities above were **already in the data and unreachable by the agent**:

- `REPORTS_TO` had been loaded since day one and **no query ever read it**. The
  graph knew Helio's entire reporting line; the agent could not answer "who does
  Ravi report to" with anything but a fabrication.
- The 2,000 `Message` and 200 `Document` nodes — the *leaves* the README
  promises "text search only at the leaves" — had **no leaf-search tool at all**.
  The leaves existed and the agent could not read them.
- `MEMBER_OF` was only reachable *per person* (`current_team`), never as a
  roster, so "who is on the Platform team" had no tool.

Closing these is not padding: it turns the README's leaf-search claim from a
sentence into a tool the model can call.

## Why presence and calendar are absent (on purpose)

`/presence` and `/events` have no counterpart in the frozen 7-node schema
(`Person, Team, Project, Service, Decision, Document, Message`). Adding a node
type for them would ripple through `SCHEMA.md`, `scripts/generate.py`,
`scripts/load.py` and the ground truth — a second project, not a parity fix.
Named here rather than faked, consistent with the product's core rule: **an
absent fact is reported as absent, never invented.**

## Staying inside the frozen contract

- `via_edge` on every new trail is drawn from `web/index.html`'s closed
  14-value `VIA_EDGE_VOCABULARY` (`REPORTS_TO`, `MENTIONS`, `MEMBER_OF`,
  `EVIDENCED_BY` are all in it). No chip renders unstyled.
- `find_documents` emits `stale[]` through the same extraction path as the other
  tools, so every `stale[].type` stays inside the frozen 7-type vocabulary
  (tested in `tests/test_agent.py`).

## Verified against the live graph

```
reports_to("Ravi Menon")            -> 6 hops up, direct manager first
direct_reports("Elena Vasquez")     -> 23 (direct + indirect, deduped by min depth)
team_members("platform team")       -> 21, current first, departed kept and flagged
search_messages("the payments service")
                                    -> resolves via MENTIONS to payments-gateway
find_documents("payments-migration")-> 15, freshness + citing decisions per row
reports_to("No Such Person")        -> 0 rows (honest negative)
team_members("NoTeam")              -> 0 rows (honest negative)
```

Plus `python scripts/verify.py` -> **21 checks, 0 FAIL** and all 20 ground
truths confirmed, so the additions regressed nothing.
