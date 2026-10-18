# Soham - Daily Report (2026-10-17)

## Accomplishments

- **Bug Fix**: Fixed `on_call()` in `app/graph.py` to read `week_start` from the ON_CALL edge (`oc.week_start`) instead of the Person node (`m.on_call_week`). Root cause: the loader writes the date to the edge, but the read was pulling from a non-existent node property, causing trail dates to be `None` and breaking `Answer.model_validate`.
- **Test Suite**: Created `tests/test_generated_1000.py` — a data-driven suite of 1000+ cases covering alias resolution, all graph tools, invariants/vocabularies, hostile inputs, unknown services, all 20 ground-truth facts, `/ask` SSE/validation/CORS/failure frames, and agent surface. Runs against real FalkorDB.
- **Validation**: After the fix, `tests/test_generated_1000.py` passes **1001/1001 (100.00%)** in ~27s; existing tests (`tests/`) continue to pass (19/19).
- **Reliability**: Added `db_health()` in `graph.py` and made `/health` return **503** when DB is unavailable in real mode (`USE_MOCK=0`). Also added DB check to `/ask` to fail fast.
- **Docs**: Added "Validation & Test Coverage" section to `README.md` documenting the generated suite and its precision.
- **PR**: Opened [PR #21](https://github.com/BhushanVidhate-27/graph-hacks/pull/21) against upstream (`soham/on-call-week-start` → `main`) with fix + tests + README update.

## Technical Details

- **Files Changed** (on branch): `app/graph.py`, `app/main.py`, `tests/test_generated_1000.py` (new), `README.md`
- **Bug Details**: `on_call()` trail row previously had `date: None` (violates frozen `trail[].date: str` contract) → real `/ask` paths that included on-call chips would raise `ValidationError`. Fixed by binding edge: `MATCH (t)<-[oc:ON_CALL]-(m) RETURN ..., oc.week_start`.

## Next Steps
- Monitor PR #21 for review/merge.
- If requested, mark the on-call date checks `xfail` (strict) to keep mainline green while review continues; otherwise land the fix.
- Consider extending the generated suite if new behaviors are added.

## Metrics
- Generated tests: 1000 cases + 1 guard = 1001 total
- Pass rate (post-fix): 100.00%
- Precision against ground truth + frozen contract: 100.00%
