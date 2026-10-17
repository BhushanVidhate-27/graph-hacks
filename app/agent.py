"""
app/agent.py — the Anthropic tool-use loop.

Owner: Soham.  Rule 12 requires all three of us to explain every line, so this
is deliberately an explicit loop with no framework.  A framework would hide
exactly the part the judges ask about.

The four rules this file implements (soham.md §6):

  1. THE MODEL CHOOSES THE TOOL.  There is no hardcoded pipeline that runs
     every traversal and concatenates the output -- that is a search box with
     extra steps and it loses the track on multi-hop reasoning.  The tool
     *descriptions* are where routing quality lives (soham.md §7): if the model
     picks the wrong tool, fix the description, not the routing code.

  2. EVERY CLAIM CARRIES ITS TRAIL.  The rows a tool returned go back into the
     conversation, and the final answer is required to be traceable to them.
     The model must never assert a fact no tool returned.

  3. EMPTY RESULT != INVENTION.  When a tool returns nothing the answer says so.
     This is tested (ground-truth facts 16-20) and it is a demo beat, not an
     edge case: "The config service is owned by the Platform team" is a
     perfectly grammatical, entirely fabricated sentence.

  4. KEEP IT READABLE.  No framework, no magic.

ALL Cypher lives in app/graph.py and nowhere else (Bhushan owns it).  This
module never builds a query string -- it only calls graph functions with
parameters.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable

import anthropic
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

# How many tool-use round trips we allow before we force a final answer.
# The compound demo question ("who knows about payments AND what breaks if it
# goes down AND where was that decided") hits all three traversals, so we need
# room for several sequential calls rather than stopping at the first.
MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """You are Helio's company-brain assistant.

You answer questions about a fictional fintech called Helio -- who owns what,
who knows what, what breaks if a service goes down, and where a decision was
made -- by calling tools that traverse a knowledge graph. The graph also records
who is on call and on rotation, which team a person is in now (and whether they
have left), a service's contracted SLA, which services nothing depends on, and
decisions matched by keyword.

NON-NEGOTIABLE RULES:

1. Only state facts a tool returned. If the tools do not return a fact, say you
   do not know. Never infer an owner, a team, a date, an SLA or a decision that
   was not returned by a tool. A fluent, confident sentence that invents an
   owner is a FAILED answer even though it reads perfectly.

2. When a tool returns no rows, say so plainly and confidently: for example,
   "the graph contains no OWNED_BY edge for config-service." Do not apologise
   and do not speculate. An absent edge is a real, correct answer.

3. Surface tension rather than hiding it. If one person has the most
   contributions but has not touched the work recently, name both the volume and
   the recency and explain which one actually answers the question.

4. If a document or decision has been superseded or looks out of date, say so
   explicitly instead of silently preferring one source.

5. A question may have several parts. Chain the tool calls -- do not stop at the
   first one.

6. Ownership is not contribution volume. Ask the ownership tool for an owner;
   never infer one from who contributed most. A service can have no owner, and
   that absence is the answer.

7. A person may have left the company. Report a departure as a departure, and
   prefer the current team or current owner over a historical one.

Answer in short, plain sentences a busy engineer can act on."""


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #
#
# Descriptions are the routing signal.  Each names ONE intent in the words a
# person would actually use, rather than "queries the graph for ..." -- that
# prefix would be identical on every tool and carry no signal.

TOOLS: list[dict[str, Any]] = [
    {
        "name": "blast_radius",
        "description": (
            "What breaks if this service goes down, how deep the impact reaches, "
            "and who is on call for each affected service."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Exact service name, e.g. payments-gateway.",
                }
            },
            "required": ["service"],
        },
    },
    {
        "name": "expertise",
        "description": (
            "Who knows this service best, ranked by contribution volume with recency."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Exact service name, e.g. payments-gateway.",
                }
            },
            "required": ["service"],
        },
    },
    {
        "name": "provenance",
        "description": (
            "Where a decision about this project was made, who made it, and whether "
            "it has since been superseded."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Exact project name, e.g. payments-migration.",
                }
            },
            "required": ["project"],
        },
    },
    {
        "name": "staleness",
        "description": (
            "Which facts in the graph have not been verified in over 90 days and "
            "should therefore be treated as possibly out of date."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "owner_of",
        "description": (
            "Which team owns this service. Use this for any 'who owns / who is "
            "responsible for X' question. An unowned service returns no rows, and "
            "that absence is the answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Exact service name, e.g. config-service.",
                }
            },
            "required": ["service"],
        },
    },
    {
        "name": "decisions_about",
        "description": (
            "Decisions whose summary mentions a keyword, newest first. Use this "
            "when the question names a topic (e.g. 'pricing', 'SLA') rather than a "
            "project name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "A word expected in the decision summary, e.g. pricing.",
                }
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "zero_dependents",
        "description": (
            "Services that nothing else depends on. Use this for 'which services "
            "are safe to change / have no dependents'."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "sla_of",
        "description": (
            "The contracted SLA for a service. Returns no rows when none is "
            "recorded -- do not assume one exists."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Exact service name, e.g. dispute-service.",
                }
            },
            "required": ["service"],
        },
    },
    {
        "name": "current_team",
        "description": (
            "The team a person is in right now, and any team they have left. Use "
            "this for 'who works on X now' or to check whether someone is still "
            "with the company."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "person": {
                    "type": "string",
                    "description": "Full person name, e.g. Priya Sharma.",
                }
            },
            "required": ["person"],
        },
    },
    {
        "name": "on_call",
        "description": (
            "Who is on call for a team this week, and who is on the rotation but "
            "not on call. Use this for 'who gets paged'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "team": {
                    "type": "string",
                    "description": "Exact team name, e.g. Ledger.",
                }
            },
            "required": ["team"],
        },
    },
]


def _load_graph_module():
    """Import app.graph lazily.

    app/graph.py is Bhushan's and may not exist yet while we build against
    mocks.  Importing lazily keeps this module importable (and testable) before
    the graph lands, and gives a clear error if it is genuinely missing.
    """
    try:
        from app import graph  # noqa: WPS433 (intentional lazy import)
    except ImportError as exc:  # pragma: no cover - depends on a teammate's file
        raise RuntimeError(
            "app/graph.py is missing. It is Bhushan's file and it holds the only "
            "Cypher in the repo. Ping him rather than writing a query here."
        ) from exc
    return graph


# Dispatch goes through graph.TOOLS -- the dict app/graph.py publishes as
# name -> function.  Reading it directly (rather than a second hand-kept map)
# means the tool name the model chose and the function that runs cannot drift
# apart when either side adds a traversal.


def _normalise(raw: Any) -> dict[str, list[dict[str, Any]]]:
    """Normalise whatever graph.py returns into {"rows": [...], "trail": [...]}.

    The agreed contract (soham.md §12/§46) is that every graph function returns
    BOTH the raw rows and the nodes/edges that produced them, so the frontend can
    render a provenance trail whose chips are labelled with the edge that linked
    them.  We accept the tidy form and tolerate a plain row list while Bhushan's
    shape settles.
    """
    if raw is None:
        return {"rows": [], "trail": []}

    if isinstance(raw, dict):
        rows = list(raw.get("rows") or [])
        trail = list(raw.get("trail") or [])
        return {"rows": rows, "trail": trail}

    # A QueryResult from the falkordb driver: never iterate it, read result_set.
    result_set = getattr(raw, "result_set", None)
    if result_set is not None:
        header = list(getattr(raw, "header", None) or [])
        rows = [dict(zip(header, row)) for row in result_set] if header else list(result_set)
        return {"rows": rows, "trail": []}

    return {"rows": list(raw), "trail": []}


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Run one graph traversal and return its rows plus its trail."""
    graph = _load_graph_module()
    fn: Callable[..., Any] | None = getattr(graph, "TOOLS", {}).get(name)
    if fn is None:
        raise ValueError(
            f"Unknown tool {name!r}. app/graph.py publishes: "
            f"{sorted(getattr(graph, 'TOOLS', {}))}"
        )
    raw = fn(**arguments)
    return _normalise(raw)


# --------------------------------------------------------------------------- #
# The loop
# --------------------------------------------------------------------------- #

def _client() -> anthropic.Anthropic:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Put it in .env (never commit .env) "
            "and restart uvicorn -- a running server does not pick up .env edits."
        )
    return anthropic.Anthropic()


def run_agent(question: str) -> dict[str, Any]:
    """Answer a question by letting the model pick graph traversals.

    Returns {"answer": str, "trail": [...], "stale": [...]}.

    `trail` accumulates every node/edge any tool returned, in call order, so the
    frontend can render one continuous proof chain.  `stale` is filled from the
    staleness tool and from any row that carries a stale marker.
    """
    client = _client()

    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    trail: list[dict[str, Any]] = []
    # Keyed by (type, name) so the same stale fact returned by two tools badges
    # one chip instead of stacking a duplicate warning.
    stale: dict[tuple[str, str], dict[str, Any]] = {}

    for _round in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Keep the assistant turn in the transcript verbatim -- including any
        # tool_use blocks -- or the next request has dangling tool_result IDs.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            answer = "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
            return {"answer": answer, "trail": trail, "stale": list(stale.values())}

        # The model chose one or more tools. Run them and hand the results back.
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            try:
                result = call_tool(block.name, dict(block.input or {}))
                is_error = False
                payload: Any = {
                    "rows": result["rows"],
                    "row_count": len(result["rows"]),
                    # An empty result is returned explicitly and visibly -- we do
                    # not silently omit the call, because "the tool said nothing"
                    # is the evidence that lets the model say "I don't know".
                    "empty": len(result["rows"]) == 0,
                }
                trail.extend(result["trail"])
                for item in extract_stale(block.name, result["rows"]):
                    stale[(item["type"], item["name"])] = item
            except Exception as exc:  # noqa: BLE001 - surfaced to the model on purpose
                is_error = True
                payload = {"error": f"{type(exc).__name__}: {exc}"}

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(payload, default=str),
                    "is_error": is_error,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    # Ran out of rounds. Say so rather than inventing a conclusion.
    return {
        "answer": (
            "I could not reach a confident answer without more graph lookups than "
            "this run allows. Tell me which part to narrow down."
        ),
        "trail": trail,
        "stale": list(stale.values()),
    }


def extract_stale(tool_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lift stale facts out of a tool's ROWS into the frozen stale[] shape.

    This reads the tool's `rows`, NOT its `trail`.  app/graph.py projects rows
    into the trail with `_trail()`, which keeps only type/name/detail/date/
    via_edge and deliberately drops `stale` and `last_verified_at` -- so reading
    the trail would leave stale[] permanently empty.  The markers live on rows:

      staleness  -> every row is stale; the query filters on last_verified_at.
      expertise  -> a row is stale when the person's last touch is old.
      provenance -> a row is stale when it is a superseded decision.

    Contract (mock/trail.json): stale[] = [{type, name, reason, last_verified_at}].
    """
    if tool_name == "staleness":
        return [
            {
                "type": row.get("type", ""),
                "name": row.get("name", ""),
                "reason": row.get("reason", "not verified in over 90 days"),
                "last_verified_at": row.get("last_verified_at", ""),
            }
            for row in rows
        ]

    if tool_name == "expertise":
        return [
            {
                "type": "Person",
                "name": row.get("person", ""),
                "reason": row.get("detail", ""),
                "last_verified_at": row.get("latest", ""),
            }
            for row in rows
            if row.get("stale")
        ]

    if tool_name == "provenance":
        # Only a decision the graph marks superseded is stale.  Do NOT test the
        # row's `superseded_by` key: in app/graph.py that holds the decision this
        # one supersedes (the naming is inverted), so it is truthy on the CURRENT
        # decision -- D-19 -- and would badge the active answer as out of date.
        return [
            {
                "type": "Decision",
                "name": row.get("id", ""),
                "reason": row.get("detail", ""),
                "last_verified_at": row.get("date", ""),
            }
            for row in rows
            if row.get("status") == "superseded"
        ]

    return []


if __name__ == "__main__":  # quick manual check: python -m app.agent "question"
    import sys

    print(json.dumps(run_agent(sys.argv[1] if len(sys.argv) > 1 else "hi"), indent=2))
