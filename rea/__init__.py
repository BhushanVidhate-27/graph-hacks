"""
rea — Reverse Engineer Anything.

Purpose (one sentence): turn a target you do not control into a *frozen contract*
— endpoints, types, auth, error shapes — precise enough that a frontend written
against it is correct on the first try.

Why this exists rather than "just read the OpenAPI doc":
  - Half the targets we integrate with have no docs, wrong docs, or docs that
    describe the happy path only. The frontend is then built against a guess.
  - Even when an OpenAPI exists, it lies by omission: it never says which fields
    are sometimes absent, which enums are closed, or that an endpoint streams
    SSE rather than returning JSON. Those three facts are what break UIs.
  - So REA is evidence-first. Every field in the output carries the number of
    observations behind it, and "unknown" is a first-class answer. A contract
    with 6 endpoints at confidence 0.9 is more useful than 40 at 0.2.

Design rules, non-negotiable:
  1. OBSERVE, DO NOT GUESS.  Nothing enters the contract without at least one
     observed exchange. Heuristics may *label* a field (looks like a date), never
     invent one.
  2. PROVENANCE OVER PRETTY.  Every schema field records `seen` / `total` so the
     generator can tell "always present" from "sometimes present" — that
     distinction is exactly what `required` gets wrong in hand-written specs.
  3. DETERMINISTIC OUTPUT.  No timestamps, no ordering by dict iteration luck.
     Two runs against the same target must produce byte-identical artifacts so
     `git diff` is a usable drift detector.
  4. THE TARGET MAY LIE TOO.  If the target ships its own OpenAPI, we read it —
     but as a *hint*, and every hint is verified by probing before it is trusted.

Subcommands live in rea.cli; run `python -m rea --help`.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]