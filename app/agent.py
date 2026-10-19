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
import ssl
import urllib.error
import urllib.request
from typing import Any, Callable

from dotenv import load_dotenv

load_dotenv()

# urllib's default CA lookup resolves to the framework OpenSSL directory, which
# on this machine (python.org 3.14 framework build) does not exist — cafile and
# capath both come back None, so every HTTPS call fails with
# CERTIFICATE_VERIFY_FAILED. certifi ships a bundle and is already a transitive
# dependency. Built only when the default lookup is empty, so an environment
# with a working system store is left alone.
if not ssl.get_default_verify_paths().cafile and not ssl.get_default_verify_paths().capath:
    try:
        import certifi

        _SSL_CTX: ssl.SSLContext | None = ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover - certifi is a hard requirement
        _SSL_CTX = None
else:
    _SSL_CTX = None

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Provider: Groq, free tier, OpenAI-compatible.
#
# Anthropic was removed outright. Its SDK appends /v1/messages to whatever base
# URL it is given and only Groq's /openai/v1/chat/completions exists here
# (verified: /anthropic/v1/messages is a 404), so there was no configuration
# that made both work. The tool loop below is spoken directly over HTTP rather
# than through an SDK, which also drops a dependency.
#
# gpt-oss-120b is verified to return finish_reason="tool_calls" with a correct
# arguments object, which is the one thing this whole app depends on.
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# 1,000 requests/day free, confirmed from the live x-ratelimit headers rather
# than from the docs. That is 20x OpenRouter's free cap of 50/day, which is what
# made a live demo survivable.
_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")

# --------------------------------------------------------------------------
# Provider selection
#
# GROQ_API_KEY, plus GROQ_API_KEY_2 as an optional second account.
#
# Groq's free tier is counted per account, so the chain is kept: one exhausted
# key should cost a round trip, not the answer.
#
# OpenRouter keys are deliberately NOT read here. The two providers speak
# different protocols, so a stray OpenRouter key in .env became the second
# "Groq key" and every request that reached it 401'd with "Invalid API Key" —
# which then read as "the Groq key is bad" and sent debugging in the wrong
# direction. Keys must match the provider.
# --------------------------------------------------------------------------
_RETRY_STATUS = {401, 402, 408, 409, 425, 429, 500, 502, 503, 504, 529}


def _key_chain() -> list[str]:
    """Configured Groq keys, in order, blanks dropped, de-duplicated."""
    raw = [
        os.getenv("GROQ_API_KEY", ""),
        os.getenv("GROQ_API_KEY_2", ""),
    ]
    out: list[str] = []
    for k in raw:
        k = k.strip()
        if k and k not in out:
            out.append(k)
    return out

# Response budget per round. Was hardcoded at 1024, which is fine on a healthy
# balance and fatal on a thin one: OpenRouter rejects the whole request with
# HTTP 402 when max_tokens exceeds what the remaining balance can cover, so the
# answer is refused outright rather than truncated. Observed live:
#   "You requested up to 1024 tokens, but can only afford 842."
# Overridable so a thin balance can still produce answers without a code change.
MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "1024"))

# Transient failures that deserve a retry rather than a dead stream. 429 and 5xx
# are obvious; OpenRouter's in-flight budget also surfaces as 402 with
# Retry-After, which reads like a permanent billing failure but is not.
#
# 401 is included because OpenRouter returns it for FREE models that are merely
# rate-limited ("User not found"), not just for bad credentials. Verified: the
# same model answered three consecutive calls correctly and only started 401ing
# during a 20-question sweep. Retrying a genuinely wrong key costs one extra
# round trip and still raises the real error.
_RETRY_STATUS = {401, 402, 408, 409, 425, 429, 500, 502, 503, 504, 529}

# Model failover. ANTHROPIC_MODEL is tried first; if it keeps failing, each entry
# here is tried in turn. Motivation: free OpenRouter models are free but rate-
# limited hard, so a live demo can lose its answer to a busy provider rather
# than to anything wrong with the app. Naming two or three models gives the demo
# something to fail over to at no cost.
#
# These are the models this Groq key actually has. Verified by listing
# /openai/v1/models: llama-3.3-70b-versatile is NOT among them and returns
# model_not_found, so the commonly-recommended default is simply unavailable
# here. gpt-oss-120b is verified to emit finish_reason="tool_calls" with a
# correct arguments object; qwen3.8-27b is the backup. The prompt-guard, whisper
# and allam entries are excluded: guards classify text rather than answer, and
# the speech models have no chat interface.
FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv(
        "GROQ_FALLBACK_MODELS",
        "qwen/qwen3.8-27b,openai/gpt-oss-20b",
    ).split(",")
    if m.strip()
]


def _model_chain() -> list[str]:
    """Primary model first, then fallbacks, de-duplicated, order preserved."""
    seen, chain = set(), []
    for m in [MODEL, *FALLBACK_MODELS]:
        if m and m not in seen:
            seen.add(m)
            chain.append(m)
    return chain


def _create_with_retry(
    clients: list[Any], *, attempts: int = 4, **kwargs: Any
) -> Any:
    """Call client.messages.create, retrying transient failures with backoff.

    Walks _model_chain() on the OUTER level and the key chain on the inner one.
    That order is deliberate. The free-tier allowance is counted per account, so
    a rate-limited key fails EVERY model at once. Walking keys first (model inner)
    therefore burns the full retry budget on key 1's dead free models before
    key 2 is ever tried — measured at 2m31s for one question. Walking the
    primary model across all keys first means a healthy key 2 answers on the
    second attempt instead, and free models are only reached when every key has
    failed the paid one.

    Honours Retry-After when the provider sends one, otherwise backs off
    exponentially. Gives up on anything that is not transient, so a genuine
    missing key still fails fast with a useful message.
    """
    import time

    chain = _model_chain()
    last: Exception | None = None

    for model in chain:
        for client in clients:
            for attempt in range(attempts):
                try:
                    return client.messages.create(model=model, **kwargs)
                except Exception as exc:  # noqa: BLE001 - re-raised below if not transient
                    status = getattr(exc, "status_code", None)
                    if status not in _RETRY_STATUS or attempt == attempts - 1:
                        last = exc
                        break  # this model is done; try the next one
                    delay = 1.0 * (attempt + 1)
                    headers = getattr(getattr(exc, "response", None), "headers", None)
                    if headers:
                        try:
                            delay = max(delay, float(headers.get("Retry-After", delay)))
                        except (TypeError, ValueError):
                            pass
                    # Cap hard. A demo that stalls for minutes is worse than one
                    # that fails fast: the honest error frame is a usable answer,
                    # a spinner is not. 5s ceiling, so a 429 cannot eat the slot.
                    time.sleep(min(delay, 5.0))

    raise last if last else RuntimeError("no model available")

# How many tool-use round trips we allow before we force a final answer.
# The compound demo question ("who knows about payments AND what breaks if it
# goes down AND where was that decided") hits all three traversals, so we need
# room for several sequential calls rather than stopping at the first.
MAX_TOOL_ROUNDS = 6

# How many rows of one tool's result go back to the MODEL.
#
# The context is a shared, metered resource, and one tool can fill it on its own:
# staleness() returns 163 rows — measured at 25,985 characters, about 6,500 tokens
# — which is most of the 8,000 tokens-per-minute the smaller fallback model
# accepts for an ENTIRE request. Asked "which dependent has no contributor in 90
# days?" the model did a reasonable thing and called staleness(), and the very
# next request came back:
#
#     HTTP 413: Request too large for model `openai/gpt-oss-20b` ...
#     on tokens per minute (TPM): Limit 8000, Requested 10756
#
# The question was answered not by the graph or by the model but by arithmetic on
# the size of a tool result. Retrying cannot fix it — 413 is deterministic for a
# given payload, and _RETRY_STATUS correctly does not list it.
#
# The rows are still all returned to the API and to the trail; this bounds only
# what the model reads. Truncation is ALWAYS disclosed in the payload
# (`truncated` + `total_row_count`), never silent: an undisclosed cut reads to
# the model exactly like absence, and rule 3 exists to stop absence turning into
# a confident invention. A question that needs row 41 should get an honest
# "40 of 163" rather than an HTTP error.
#
# 40 is chosen against the graph, not guessed: the largest result any
# ground-truth question needs is team_members() at 21 rows, and staleness() now
# leads with the contradicted documents so the two rows that matter survive the
# cut (see the ordering note in staleness()).
MAX_ROWS_PER_TOOL_RESULT = 40

SYSTEM_PROMPT = """You are Helio's company-brain assistant.

You answer questions about a fictional fintech called Helio -- who owns what,
who knows what, what breaks if a service goes down, and where a decision was
made -- by calling tools that traverse a knowledge graph. The graph also records
who is on call and on rotation, which team a person is in now (and whether they
have left), the management reporting line (who reports to whom, and full team
rosters with roles and tenure), a service's contracted SLA, which services
nothing depends on, decisions matched by keyword, chat messages that mention a
word, service or person, and documents matched by keyword with their freshness
and the decisions that cite them.

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
   explicitly instead of silently preferring one source. When a stale document is
   cited by a decision, name that decision: the citation is what makes the
   staleness matter, and "the document is out of date" on its own leaves the
   reader unable to tell which live decision it undercuts.

5. A question may have several parts. Chain the tool calls -- do not stop at the
   first one.

6. Ownership is not contribution volume. Ask the ownership tool for an owner;
   never infer one from who contributed most. A service can have no owner, and
   that absence is the answer.

7. A person may have left the company. Report a departure as a departure, and
   prefer the current team or current owner over a historical one.

8. Owning a service and having the authority to decide about it are different
   things. A team OWNS a service; a person is named as the author on the
   Decision itself. "Who decides / who has authority / who signed off" is the
   decision's author -- look it up on decisions_about or provenance, never infer
   it from who owns the service.

9. A question may refer to something without naming it -- "those services",
   "them", "that document". If the graph makes one referent obvious, use it and
   answer; refusing to answer when the data was right there is the same failure
   as inventing it. But if nothing makes a referent obvious -- "which dependent"
   names no service at all, and there is no earlier message to inherit one from
   -- then say in one short line which service you need and stop. Do not pick a
   target out of the air, and do not answer "I do not know": both are worse than
   asking, because one invents and the other wastes the reader's time.

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
            "Where a decision about this project was made, who authored it, and "
            "whether it has since been superseded. Use this for 'who decided / "
            "who signed off / who had authority over' questions as well as for "
            "the decision itself."
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
            "Which team owns this service, plus the decision that last handed "
            "ownership to a named person. Use this for any 'who owns / who is "
            "responsible for X' question -- quote the person in the handover if "
            "there is one, not just the team. An unowned service returns no rows, "
            "and that absence is the answer."
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
        "name": "ownership_overview",
        "description": (
            "Every service in the graph with the team that owns it, marking the "
            "ones nothing owns. Use this for whole-set questions: 'does every "
            "service have an owner', 'which services are unowned'. Do not call "
            "owner_of repeatedly to answer these."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "decisions_about",
        "description": (
            "Decisions matching a keyword in the summary OR a decision id such as "
            "D-14, newest first, each with its status (active or superseded), who "
            "authored it, and any decision that replaced it. Use this when the "
            "question names a topic (e.g. 'pricing', 'provider'), a decision id, "
            "or asks who decided something or whether a decision still stands."
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
    {
        "name": "stale_dependents",
        "description": (
            "The services that depend on this one and have had nobody contribute "
            "to them in over 90 days. Use this for 'which of its dependents has "
            "gone quiet' rather than combining blast_radius with per-service "
            "expertise calls yourself."
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
    # ------------------------------------------------------------------------
    # The Microsoft Graph parity tools. Microsoft Graph answers /manager,
    # /directReports, /groups/{id}/members, chat search and drive-item search —
    # docs/microsoft-graph-parity.md maps each one. These five close the gaps
    # the data already supported but the agent could not reach: the reporting
    # line (REPORTS_TO was loaded and never queried), team rosters, and leaf
    # search over the 2,000 messages and 200 documents.
    {
        "name": "reports_to",
        "description": (
            "A person's management chain: their direct manager first, then who "
            "that manager reports to, up to the top. Use for 'who does X report "
            "to', 'who is X's manager', chain-of-command or skip-level questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "person": {
                    "type": "string",
                    "description": "Full person name, e.g. Ravi Menon.",
                }
            },
            "required": ["person"],
        },
    },
    {
        "name": "direct_reports",
        "description": (
            "Everyone who reports to a person, direct or through intermediate "
            "managers. Use for 'who reports to X' or 'who are X's direct reports'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "person": {
                    "type": "string",
                    "description": "Full person name, e.g. Elena Vasquez.",
                }
            },
            "required": ["person"],
        },
    },
    {
        "name": "team_members",
        "description": (
            "Everyone on a team, with titles, role and tenure, including members "
            "who have left. Use for 'who is on / works in the X team' or 'who is "
            "still on X'. For one named person's team, use current_team instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "team": {
                    "type": "string",
                    "description": "Team name, e.g. Platform (case-insensitive).",
                }
            },
            "required": ["team"],
        },
    },
    {
        "name": "search_messages",
        "description": (
            "Chat messages that mention a word, service, project or person, "
            "newest first, with channel, author and who else was mentioned. Use "
            "for 'what did people say about X in chat' or 'any incident chatter "
            "about X'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "A word, service or person to look for, e.g. api-gateway.",
                }
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "find_documents",
        "description": (
            "Documents (runbooks, ADRs, postmortems) matching a word, kind or "
            "project, each with how fresh it is and which decisions cite it. Use "
            "for 'is there a doc / runbook about X', 'find docs on X', and 'is "
            "that document still accurate' -- pass the descriptive phrase the "
            "person used if you have no exact filename."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "A word, phrase, kind or project name, e.g. runbook.",
                }
            },
            "required": ["keyword"],
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

    Any OTHER key the traversal returned is carried through untouched.  That is
    not tidiness, it is load-bearing: `departed` (current_team), `unowned`
    (ownership_overview) and `rotation_not_on_call` (on_call) sit beside `rows`
    precisely because `rows` is empty in the case that matters. Rebuilding the
    dict from just the two known keys silently deleted them, and the model then
    reported "no data" about a fact it had been handed. See run_agent() for the
    observed failure.
    """
    if raw is None:
        return {"rows": [], "trail": []}

    if isinstance(raw, dict):
        out = {k: v for k, v in raw.items() if k not in {"rows", "trail"}}
        out["rows"] = list(raw.get("rows") or [])
        out["trail"] = list(raw.get("trail") or [])
        return out

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

def _normalise_text(text: str) -> str:
    """Fold the typography models emit that we do not want to show a judge.

    A live answer came back as "Payments<U+2011>gateway is owned by the
    Platform team." — U+2011 NON-BREAKING HYPHEN, not U+002D. It renders
    identically but is a different string, so it breaks exact matching
    downstream: scripts/verify_agent.py asserted "admin-bff" against an
    answer containing "admin<U+2011>bff" and failed a fact the graph had
    already proven. The same trap also silently breaks copy-paste and any
    judge grepping the output for a service name.

    Typography only, no wording change. NFKC is not enough on its own —
    U+2011 is not a compatibility equivalent of "-", so it survives — hence
    the explicit table.
    """
    return (
        text.translate(_DASH_FOLD)
        .translate(_QUOTES_FOLD)
        .translate(_SPACES_FOLD)
    )


_DASH_FOLD = dict.fromkeys(
    map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"), "-"
)
_QUOTES_FOLD = {
    ord("’"): "'",
    ord("‘"): "'",
    ord("“"): '"',
    ord("”"): '"',
    ord("`"): "'",
}
_SPACES_FOLD = dict.fromkeys(
    map(
        ord,
        "\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u200b\u2028\u2029\u202f\u205f\u3000\ufeff",
    ),
    " ",
)


class _GroqError(Exception):
    """HTTP failure from Groq.

    Carries `status_code` so the retry loop can tell a transient 429 from a
    permanent 404, and a `response` shim because that is where the loop looks
    for Retry-After — Groq sets it on 429 and honouring it beats guessing.
    """

    def __init__(self, status: int, message: str, headers: Any = None) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status_code = status
        self.response = type("_R", (), {"headers": headers or {}})()


class _GroqClient:
    """Minimal OpenAI-compatible client for Groq.

    Hand-rolled over urllib rather than pulling in the openai SDK: the whole
    surface used here is one POST to /chat/completions, and an SDK would add a
    dependency to save about forty lines. Tool schemas are already in OpenAI
    shape ({"name", "description", "input_schema"}), so the translation is a
    rename of one key rather than a rewrite.

    Deliberately not streaming: the app's SSE stream is built from whole
    answer frames by app/main.py, so per-token streaming would buy nothing.
    """

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.messages = self  # so client.messages.create(...) reads naturally

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        system: str,
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> _Response:
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system}]
            + _to_openai_messages(messages),
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        # Anthropic calls it input_schema; OpenAI calls it
                        # parameters. Same JSON Schema underneath.
                        "parameters": t["input_schema"],
                    },
                }
                for t in tools
            ],
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            f"{_BASE_URL}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                # urllib's default is "Python-urllib/3.14", and Groq sits
                # behind Cloudflare, which answers that with 403 error code
                # 1010 ("browser integrity check") — while the identical
                # request from curl returns 200. Identified by sending both and
                # comparing; a User-Agent is the only difference.
                "User-Agent": "helio-agent/1.0 (+https://github.com/BhushanVidhate-27/graph-hacks)",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120, context=_SSL_CTX) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try:
                message = json.loads(raw)["error"]["message"]
            except (ValueError, KeyError):
                message = raw[:200]
            raise _GroqError(exc.code, message, dict(exc.headers)) from exc
        except urllib.error.URLError as exc:
            raise _GroqError(503, str(exc.reason)) from exc

        msg = body["choices"][0]["message"]
        return _Response(
            text=msg.get("content") or "",
            tool_calls=[
                {
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    # OpenAI delivers arguments as a JSON *string*; malformed
                    # JSON is possible in principle, so it is parsed defensively
                    # rather than trusted.
                    "arguments": _parse_arguments(tc["function"].get("arguments")),
                }
                for tc in msg.get("tool_calls") or []
            ],
        )


def _to_openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Translate the loop's Anthropic-shaped transcript into OpenAI's format.

    Done in exactly one place, at the wire boundary, so the loop above keeps
    reading like the Anthropic API it was written against and only the transport
    knows the provider changed.

    Two differences that Groq rejects outright (HTTP 400, verified):

      * tool CALLS: Anthropic puts them in the assistant's `content` as blocks
        of type "tool_use". OpenAI has a separate top-level `tool_calls` array
        with `function.arguments` as a JSON *string*.
      * tool RESULTS: Anthropic puts them in a user message whose content blocks
        are type "tool_result" keyed by `tool_use_id`. OpenAI wants one
        `role: "tool"` message per call, keyed by `tool_call_id`.

    Leaving either in Anthropic shape produces:
      'messages.2.content' : one of the following must be satisfied[
        ('value must be a string') OR ('content.0.type' : value is not one of
        the allowed values ['text'])]
    """
    out: list[dict[str, Any]] = []

    for msg in messages:
        role = msg["role"]
        content = msg.get("content")

        if role == "user" and isinstance(content, list):
            # One role:"tool" message per tool_result, in order.
            for block in content:
                out.append(
                    {
                        "role": "tool",
                        "tool_call_id": block["tool_use_id"],
                        "content": block["content"],
                    }
                )
            continue

        if role == "assistant" and isinstance(content, list):
            text_parts: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            for block in content:
                if block.get("type") == "text":
                    text_parts.append(block["text"])
                elif block.get("type") == "tool_use":
                    tool_calls.append(
                        {
                            "id": block["id"],
                            "type": "function",
                            "function": {
                                "name": block["name"],
                                "arguments": json.dumps(block.get("input") or {}),
                            },
                        }
                    )
            assistant: dict[str, Any] = {
                "role": "assistant",
                # OpenAI rejects null content on a tool-call turn, so it is
                # omitted when the model called a tool without narrating.
                "content": "".join(text_parts) or "",
            }
            if tool_calls:
                assistant["tool_calls"] = tool_calls
            out.append(assistant)
            continue

        out.append({"role": role, "content": content})

    return out


def _parse_arguments(raw: Any) -> dict[str, Any]:
    """OpenAI sends tool arguments as a JSON string. Never raise on bad JSON."""
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


class _Block:
    """One content block: a text chunk or a tool call.

    Attribute access plus __getitem__, because the transcript is appended as
    plain JSON while the loop reads it as objects — without __getitem__ the
    transcript would serialise as {"type": ..., } rather than the wire shape.
    """

    def __init__(self, type: str, **fields: Any) -> None:
        self.type = type
        self.text: str | None = fields.get("text")
        self.id: str | None = fields.get("id")
        self.name: str | None = fields.get("name")
        self.input: dict[str, Any] | None = fields.get("input")

    def __getitem__(self, key: str) -> Any:
        return {"type": self.type, "text": self.text, "id": self.id,
                "name": self.name, "input": self.input}[key]

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"_Block({self.type!r}, name={self.name!r})"


class _Response:
    """What the loop consumes: text, plus tool calls in Anthropic's shape."""

    def __init__(self, text: str, tool_calls: list[dict[str, Any]]) -> None:
        self.text = text
        self.tool_calls = tool_calls
        self.stop_reason = "tool_use" if tool_calls else "end_turn"
        # The loop below reads block.type / block.text / block.input as
        # ATTRIBUTES and serialises the same objects into the transcript, so
        # these are objects, not dicts. Dicts were tried first and fail
        # immediately with "'dict' object has no attribute 'type'".
        self.content: list[Any] = []
        if text:
            self.content.append(_Block("text", text=text))
        for tc in tool_calls:
            self.content.append(
                _Block("tool_use", id=tc["id"], name=tc["name"], input=tc["arguments"])
            )


def _clients() -> list[_GroqClient]:
    """One client per configured key, in chain order."""
    keys = _key_chain()
    if not keys:
        raise RuntimeError(
            "No model API key. Set GROQ_API_KEY in .env — never commit .env — "
            "then restart uvicorn, because a running server does not pick up "
            ".env edits."
        )
    return [_GroqClient(k) for k in keys]


def run_agent(question: str) -> dict[str, Any]:
    """Answer a question by letting the model pick graph traversals.

    Returns {"answer": str, "trail": [...], "stale": [...]}.

    `trail` accumulates every node/edge any tool returned, in call order, so the
    frontend can render one continuous proof chain.  `stale` is filled from the
    staleness tool and from any row that carries a stale marker.
    """
    clients = _clients()

    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    trail: list[dict[str, Any]] = []
    # Keyed by (type, name) so the same stale fact returned by two tools badges
    # one chip instead of stacking a duplicate warning.
    stale: dict[tuple[str, str], dict[str, Any]] = {}

    for _round in range(MAX_TOOL_ROUNDS):
        response = _create_with_retry(
            clients,
            # model comes from _model_chain() inside the wrapper, so it can fail
            # over. Passing it here too would be a duplicate kwarg.
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Keep the assistant turn in the transcript verbatim -- including any
        # tool_use blocks -- or the next request has dangling tool_result IDs.
        messages.append(
            {
                "role": "assistant",
                # _Block is an object so the loop can read block.type; the
                # transcript has to be plain JSON because it is re-serialised
                # into the next request body. Convert here, at the boundary,
                # rather than making _Block a dict and breaking attribute
                # access in the loop.
                "content": [
                    {
                        k: v
                        for k, v in (
                            (k, getattr(b, k, None))
                            for k in ("type", "text", "id", "name", "input")
                        )
                        if v is not None
                    }
                    for b in response.content
                ],
            }
        )

        if response.stop_reason != "tool_use":
            answer = _normalise_text(
                "".join(
                    block.text for block in response.content if block.type == "text"
                ).strip()
            )
            return {"answer": answer, "trail": trail, "stale": list(stale.values())}

        # The model chose one or more tools. Run them and hand the results back.
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            try:
                result = call_tool(block.name, dict(block.input or {}))
                is_error = False
                # Forward the WHOLE result, not just `rows`.
                #
                # app/graph.py returns sibling keys next to `rows` that carry the
                # answer to exactly the questions where `rows` is empty:
                # current_team -> `departed`, ownership_overview -> `unowned`,
                # on_call -> `rotation_not_on_call`. Sending only `rows` threw
                # them away, so for "What team is Aisha Khan on now?" the model
                # received {"rows": [], "row_count": 0, "empty": true} and the
                # fact that she LEFT on 2026-06-30 — sitting in `departed`, in the
                # very payload the tool returned — never reached it. It then
                # answered "The graph contains no current_team edge for Aisha
                # Khan", which is what the truncated payload actually said.
                #
                # That is the worst class of bug here: the answer was computed
                # correctly and then thrown away on the way to the only component
                # that could have read it. `trail` is the one key left out — it is
                # the chip data, already accumulated into `trail` above, and
                # re-sending it would just triple the tokens.
                payload: Any = {k: v for k, v in result.items() if k != "trail"}
                total = len(result["rows"])
                payload["rows"] = result["rows"][:MAX_ROWS_PER_TOOL_RESULT]
                payload["row_count"] = len(payload["rows"])
                payload["total_row_count"] = total
                # An empty result is returned explicitly and visibly -- we do
                # not silently omit the call, because "the tool said nothing"
                # is the evidence that lets the model say "I don't know".
                payload["empty"] = total == 0
                if total > MAX_ROWS_PER_TOOL_RESULT:
                    # Say so out loud. A silently shortened list is
                    # indistinguishable from a short graph, which is the one
                    # inference rule 3 forbids.
                    payload["truncated"] = (
                        f"showing {MAX_ROWS_PER_TOOL_RESULT} of {total} rows; the "
                        "graph holds more than are shown here. Do not conclude a "
                        "row is absent because it is not in this list."
                    )
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


# The frozen stale[].type vocabulary.  mock/trail.json says stale[].type uses the
# "same vocabulary as trail[].type", and lists exactly these seven.  A stale badge
# is STYLED by this value, so a type outside the list is not a new kind of badge --
# it is an undefined one, and the renderer has no rule for it.  The wire contract
# is frozen after Day 1 15:00, so this code conforms to the list rather than
# extending it.
STALE_TYPES = frozenset(
    {"Person", "Decision", "Document", "Message", "Service", "Project", "Team"}
)


def extract_stale(tool_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lift stale facts out of a tool's ROWS into the frozen stale[] shape.

    This reads the tool's `rows`, NOT its `trail`.  app/graph.py projects rows
    into the trail with `_trail()`, which keeps only type/name/detail/date/
    via_edge and deliberately drops `stale` and `last_verified_at` -- so reading
    the trail would leave stale[] permanently empty.  The markers live on rows:

      staleness  -> every row is stale; the query filters on last_verified_at.
      expertise  -> a row is stale when the person's last touch is old.
      provenance -> a row is stale when it is a superseded decision.
      decisions_about -> a row is stale when it is a superseded decision.
      find_documents -> a row is stale when last_verified_at predates the same
                   90-day cutoff staleness() uses (the payments-provider
                   contradiction, findable from the document side too).

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
            # app/graph.py's staleness() also returns edge-level rows.  Measured on
            # the live graph: 163 rows = 162 Document + 1 edge, where the edge row
            # is {"type": "edge", "name": "CONTRIBUTED_TO"}.  "edge" is NOT in the
            # frozen vocabulary above, and graph.py's own _trail() already keeps
            # edge rows OUT of the trail -- so this row can never badge a chip, and
            # must not reach the wire as an undefined badge type.  The row is still
            # handed to the model inside `rows`, so nothing is hidden from the
            # answer; only the unstyled badge is suppressed.
            if row.get("type") in STALE_TYPES
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

    if tool_name == "decisions_about":
        # decisions_about() now returns status like provenance() does, so a
        # decision found by keyword or id badges the same way. Without this a
        # keyword lookup for a superseded decision would return it with a stale
        # flag in `rows` and no badge -- the one signal the frontend styles.
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

    if tool_name == "find_documents":
        return [
            {
                "type": "Document",
                "name": row.get("name", ""),
                "reason": row.get("detail", ""),
                "last_verified_at": row.get("last_verified_at", ""),
            }
            for row in rows
            if row.get("stale")
        ]

    return []


if __name__ == "__main__":  # quick manual check: python -m app.agent "question"
    import sys

    print(json.dumps(run_agent(sys.argv[1] if len(sys.argv) > 1 else "hi"), indent=2))
