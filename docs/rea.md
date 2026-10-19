# REA — Reverse Engineer Anything

REA turns a target you don't control into a **frozen contract**: endpoints,
types, auth, error shapes — precise enough that a frontend written against it is
correct on the first try.

It exists because hand-written API specs omit the three facts that break UIs:

1. which fields are *sometimes* absent (specs say `required: true` anyway),
2. which string fields are closed enums (so the frontend never validates),
3. that an endpoint **streams SSE** rather than returning JSON.

## Setup

No new dependencies — REA uses `httpx`, which is already in `requirements.txt`.

```bash
python -m rea --help
python -m pytest tests/test_rea.py -q     # 45 tests
```

## Use

```bash
# 1. Probe a running target
python -m rea build --url http://localhost:8000 --out contract

# 2. Or go from recorded browser traffic (no network, higher fidelity)
python -m rea har --har session.har --out contract

# 3. Later, in CI: re-probe and fail the build on breaking changes
python -m rea verify contract/contract.json --url http://localhost:8000

# 4. Render a committed contract in any format
python -m rea show contract/contract.json --format md
python -m rea show contract/contract.json --format ts
```

`build` writes four artifacts to `--out`:

| file | what it is |
|---|---|
| `contract.json` | source of truth — every claim with its sample count and confidence |
| `openapi.json` | OpenAPI **3.1** (nullable uses `type: [x, "null"]`, which 3.0 generators mangle) |
| `types.ts` | TypeScript types + fetch client, with `?` on evidence-based optionals |
| `CONTRACT.md` | the human contract, ending in a **Gaps** section |

## How it works

```
        ┌──────────────┐        ┌──────────────┐
HAR ───▶│   rea.har    │        │  rea.probe   │◀─── target (crawl + probe + replay)
        └──────┬───────┘        └──────┬───────┘
               │ Observation (raw)      │
               └───────────┬────────────┘
                           ▼
                    rea.infer ── schema folding + path templating
                           ▼
                    rea.contract ── endpoint table, traits, drift
                           ▼
              rea.export ── contract.json / openapi / types.ts / md
```

### Evidence, not guessing

- Nothing enters the contract without an observed exchange. Heuristics may
  *label* a field (looks like a date), never invent one.
- Optionality comes from `seen / total` counts, not from a guess. A field present
  in 9 of 10 samples is exported as `field?: T`, because `field: T` is a lie the
  frontend only discovers in production.
- Confidence is orthogonal to frequency: a rare field with an unambiguous type
  still gets a real type.
- Paths the target *advertises* but that were never observed are listed under
  "documented but never observed" — never emitted as fact.
- Output is deterministic. Two runs produce byte-identical files, so `git diff`
  works as a drift detector.

### Safety defaults

Mutating verbs are off (`--allow-mutating` to enable), requests are delayed
(`--delay`), capped (`--max-requests`), depth-limited (`--depth`), and crawling
stays on the target's origin.

## Known gaps

- Array items with no observed fields export as `unknown[]` rather than a named
  interface (an empty TypeScript interface is not useful).
- SSE frames are grouped by *full* nested shape, so frames of the same event with
  different payload sizes can appear as several frame types. Shallow grouping
  would be better; noted in `rea/infer.py`.
- GraphQL is only covered via `/openapi.json` discovery — no introspection.