"""
rea/model.py — the shapes REA carries around.

Three layers, deliberately separate:

    Observation  one real HTTP exchange, exactly as it happened. Immutable-ish,
                 raw, lossy. Never merged, never guessed at.
    Schema       a folded view of many observations of the same thing. Holds
                 counts (`seen` / `total`) so "always" and "sometimes" stay
                 distinguishable.
    Contract     the deduplicated set of endpoints, ready for export.

The separation matters because merging is destructive: once two samples are
folded together you cannot tell "the server omitted this field" from "the first
sample never had it". REA keeps the raw layer so `--explain` can show exactly
which bytes behind a claim, and so a merge bug is debuggable instead of magic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable

SCHEMA_VERSION = 1

# --------------------------------------------------------------------------- #
# Layer 1: Observation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Observation:
    """One HTTP exchange. Bodies are kept decoded (dict/list/str/None)."""

    method: str
    url: str
    path: str
    query: dict[str, list[str]]  # name -> values, so ?a=1&a=2 survives
    request_headers: dict[str, str]
    request_body: Any
    status: int
    response_headers: dict[str, str]
    response_body: Any
    # Content type of the response, lowercased and parameter-stripped.
    # ("application/json", "text/event-stream", "text/html", ...)
    content_type: str = ""
    # Where this came from: "probe" or "har". Kept because a HAR sample is what
    # a *browser* did and a probe sample is what *we* did; they disagree about
    # auth headers often enough that hiding the distinction hides real bugs.
    origin: str = "probe"

    @property
    def is_error(self) -> bool:
        return self.status >= 400

    @property
    def is_stream(self) -> bool:
        return self.content_type.startswith("text/event-stream")


# --------------------------------------------------------------------------- #
# Layer 2: Schema
# --------------------------------------------------------------------------- #


@dataclass
class Field_:
    """
    One property of an object schema.

    `seen`/`total` are the whole point. A field present in 9 of 10 samples is
    emitted as non-required with `p_presence: 0.9`, because that is the truth
    and `required: true` would be a lie the frontend only discovers in
    production.
    """

    name: str
    types: set[str] = field(default_factory=set)
    seen: int = 0
    total: int = 0
    nullable: bool = False
    examples: list[Any] = field(default_factory=list)
    enum: list[Any] | None = None  # closed set, only when provably small+stable
    fmt: str | None = None  # date-time, uuid, email, uri ...
    # Nested object/array shape. None until a sample actually contained one.
    schema: "Schema | None" = None
    # Array element stats — cheap signal that a frontend developer wants.
    min_len: int | None = None
    max_len: int | None = None
    # Documentation lifted verbatim from the target's own spec, if it had one.
    description: str | None = None

    @property
    def presence(self) -> float:
        return self.seen / self.total if self.total else 0.0

    @property
    def always_present(self) -> bool:
        return self.total > 0 and self.seen == self.total

    def confidence(self) -> float:
        """
        How sure REA is of this field's TYPE, 0..1.

        Deliberately orthogonal to how often the field appears. Presence is
        already expressed by `always_present` (-> `?` in TypeScript, absence
        from `required` in OpenAPI), and folding it in here a second time meant a
        field seen once out of four samples scored 0.125 and got exported as
        `unknown` — even though its type was never in doubt. A rare field with a
        clear type is still a clear type.

        Weighted toward type *consistency*, not raw count: 3 samples agreeing on
        the type beat 30 disagreeing, because disagreement means the response is
        polymorphic and no single generated type will be right.
        """
        if not self.seen or not self.types:
            return 0.0
        # Type agreement: one type observed => 1.0, decays as the set grows.
        type_score = 1.0 / (1.0 + 0.75 * (len(self.types) - 1))
        # Sample weight with a floor of 0.5: one observation is weak evidence but
        # not zero evidence. Saturates at 4 samples.
        count_score = 0.5 + 0.5 * (min(self.seen, 4) / 4.0)
        return round(type_score * count_score, 3)


@dataclass
class Schema:
    """
    A folded shape. `kind` is one of "object", "array", "string", "integer",
    "number", "boolean", "null", "unknown".

    Arrays do NOT fold their items into a union — REA records the item schema
    across all observed elements, so `items` is one coherent type. This is a
    deliberate departure from JSON Schema, where heterogeneous arrays force a
    union that no frontend codegen handles well.
    """

    kind: str = "unknown"
    fields: dict[str, Field_] = field(default_factory=dict)
    items: "Schema | None" = None
    types: set[str] = field(default_factory=set)
    seen: int = 0
    total: int = 0
    description: str | None = None

    def confidence(self) -> float:
        if self.kind in ("string", "integer", "number", "boolean", "null"):
            if not self.types:
                return 0.0
            return round(1.0 / (1.0 + 0.75 * (len(self.types) - 1)) * (0.5 + 0.5 * min(self.seen, 4) / 4.0), 3)
        if not self.fields and not self.items:
            return 0.0
        own = 0.5 + 0.5 * (min(self.seen, 4) / 4.0) if self.seen else 0.0
        parts: list[float] = []
        if self.fields:
            parts.extend(f.confidence() for f in self.fields.values())
        if self.items is not None:
            parts.append(self.items.confidence())
        return round(own * (sum(parts) / len(parts)), 3) if parts else 0.0


# --------------------------------------------------------------------------- #
# Layer 3: Endpoint + Contract
# --------------------------------------------------------------------------- #


@dataclass
class Param:
    """A path/query/header parameter, with the evidence that makes it required."""

    name: str
    location: str  # "path" | "query" | "header"
    required: bool = False
    types: set[str] = field(default_factory=set)
    examples: list[Any] = field(default_factory=list)
    observed: int = 0
    description: str | None = None

    def confidence(self) -> float:
        if self.location == "path":
            return 1.0  # a path segment cannot be optional; that is why it is here
        if not self.observed:
            return 0.0
        return round(min(self.observed, 5) / 5.0 * (1.0 if self.required else 0.8), 3)


@dataclass
class Response:
    """One observed (status, content-type) pair and the body shape behind it."""

    status: int
    content_type: str
    schema: Schema | None = None
    count: int = 0
    # For text/event-stream: the distinct frame shapes, in arrival order of
    # first appearance. A frontend must implement a state machine over these, so
    # collapsing a stream into "a JSON object" would be actively harmful.
    frames: list[Schema] = field(default_factory=list)

    @property
    def is_error(self) -> bool:
        return self.status >= 400

    @property
    def is_stream(self) -> bool:
        return self.content_type.startswith("text/event-stream")

    @property
    def confidence(self) -> float:
        return self.schema.confidence() if self.schema else (0.6 if self.count else 0.0)


@dataclass
class Endpoint:
    method: str
    path: str  # templated, e.g. /users/{userId}/posts
    params: dict[str, Param] = field(default_factory=dict)
    request_schema: Schema | None = None
    responses: dict[tuple[int, str], Response] = field(default_factory=dict)
    observations: int = 0
    # Concrete paths this endpoint was seen at, sorted + deduped. Proves the
    # template is real and shows the developer real values to test with.
    samples: list[str] = field(default_factory=list)
    request_examples: list[Any] = field(default_factory=list)
    response_examples: list[Any] = field(default_factory=list)
    auth: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.method} {self.path}"

    @property
    def confidence(self) -> float:
        parts = [min(self.observations, 8) / 8.0]
        parts.extend(r.confidence for r in self.responses.values())
        if self.request_schema is not None:
            parts.append(self.request_schema.confidence())
        return round(sum(parts) / len(parts), 3) if parts else 0.0

    @property
    def success(self) -> Response | None:
        for (status, _ct), r in sorted(self.responses.items()):
            if not r.is_error:
                return r
        return None

    @property
    def errors(self) -> list[Response]:
        return [r for (_s, _c), r in sorted(self.responses.items()) if r.is_error]


@dataclass
class Contract:
    target: str = ""
    endpoints: list[Endpoint] = field(default_factory=list)
    # Endpoint keys the target advertises in its own spec but which we could
    # never observe. These are the "documented but unverified" holes.
    unverified: list[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION
    rea_version: str = ""
    # Machine-readable hints about the target as a whole: CORS, auth style,
    # API versioning, content negotiation.
    traits: dict[str, Any] = field(default_factory=dict)

    def sorted_endpoints(self) -> list[Endpoint]:
        # Deterministic ordering — see rule 3 in rea/__init__.py.
        return sorted(self.endpoints, key=lambda e: (e.path, e.method))

    def to_json(self) -> str:
        return json.dumps(to_dict(self), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, raw: str) -> "Contract":
        return from_dict(json.loads(raw))


# --------------------------------------------------------------------------- #
# Serialisation — hand-written, because dataclasses.asdict would drop the
# computed fields and json.dumps would order by insertion luck.
# --------------------------------------------------------------------------- #


def _schema_to_dict(s: Schema | None) -> dict[str, Any] | None:
    if s is None:
        return None
    out: dict[str, Any] = {"kind": s.kind, "seen": s.seen, "total": s.total}
    if s.types:
        out["types"] = sorted(s.types)
    if s.description:
        out["description"] = s.description
    if s.fields:
        out["fields"] = {name: _field_to_dict(f) for name, f in sorted(s.fields.items())}
    if s.items is not None:
        out["items"] = _schema_to_dict(s.items)
    out["confidence"] = s.confidence()
    return out


def _field_to_dict(f: Field_) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": f.name,
        "types": sorted(f.types),
        "seen": f.seen,
        "total": f.total,
        "presence": round(f.presence, 4),
        "required": f.always_present,
        "confidence": f.confidence(),
    }
    if f.nullable:
        out["nullable"] = True
    if f.enum:
        out["enum"] = f.enum
    if f.fmt:
        out["format"] = f.fmt
    if f.min_len is not None or f.max_len is not None:
        out["length"] = {"min": f.min_len, "max": f.max_len}
    if f.description:
        out["description"] = f.description
    if f.examples:
        out["examples"] = f.examples[:3]
    if f.schema is not None:
        out["schema"] = _schema_to_dict(f.schema)
    return out


def _response_to_dict(r: Response) -> dict[str, Any]:
    out: dict[str, Any] = {
        "status": r.status,
        "content_type": r.content_type,
        "count": r.count,
        "confidence": round(r.confidence, 3),
    }
    if r.schema is not None:
        out["schema"] = _schema_to_dict(r.schema)
    if r.frames:
        out["frames"] = [_schema_to_dict(f) for f in r.frames]
    return out


def _endpoint_to_dict(e: Endpoint) -> dict[str, Any]:
    return {
        "method": e.method,
        "path": e.path,
        "params": {
            p.name: {
                "location": p.location,
                "required": p.required,
                "types": sorted(p.types),
                "observed": p.observed,
                "examples": p.examples[:3],
                "confidence": p.confidence(),
            }
            for p in sorted(e.params.values(), key=lambda p: (p.location, p.name))
        },
        "request_schema": _schema_to_dict(e.request_schema),
        "responses": {
            f"{status} {ct}": _response_to_dict(r)
            for (status, ct), r in sorted(e.responses.items())
        },
        "observations": e.observations,
        "samples": e.samples,
        "auth": e.auth,
        "notes": sorted(e.notes),
        "confidence": e.confidence,
    }


def to_dict(c: Contract) -> dict[str, Any]:
    return {
        "rea_version": c.rea_version,
        "schema_version": c.schema_version,
        "target": c.target,
        "traits": c.traits,
        "unverified": sorted(c.unverified),
        "endpoints": [_endpoint_to_dict(e) for e in c.sorted_endpoints()],
    }


def _schema_from_dict(d: dict[str, Any] | None) -> Schema | None:
    if d is None:
        return None
    s = Schema(kind=d.get("kind", "unknown"), types=set(d.get("types", [])))
    s.seen = int(d.get("seen", 0))
    s.total = int(d.get("total", 0))
    s.description = d.get("description")
    for name, fd in (d.get("fields") or {}).items():
        f = Field_(
            name=name,
            types=set(fd.get("types", [])),
            seen=int(fd.get("seen", 0)),
            total=int(fd.get("total", 0)),
            nullable=bool(fd.get("nullable", False)),
            enum=fd.get("enum"),
            fmt=fd.get("format"),
            description=fd.get("description"),
        )
        length = fd.get("length") or {}
        f.min_len = length.get("min")
        f.max_len = length.get("max")
        f.examples = fd.get("examples", [])
        f.schema = _schema_from_dict(fd.get("schema"))
        s.fields[name] = f
    s.items = _schema_from_dict(d.get("items"))
    return s


def from_dict(d: dict[str, Any]) -> Contract:
    c = Contract(
        target=d.get("target", ""),
        schema_version=int(d.get("schema_version", SCHEMA_VERSION)),
        rea_version=d.get("rea_version", ""),
        traits=d.get("traits", {}),
        unverified=list(d.get("unverified", [])),
    )
    for ed in d.get("endpoints", []):
        e = Endpoint(method=ed["method"], path=ed["path"], observations=int(ed.get("observations", 0)))
        e.samples = list(ed.get("samples", []))
        e.auth = ed.get("auth", {})
        e.notes = list(ed.get("notes", []))
        for pname, pd in (ed.get("params") or {}).items():
            e.params[pname] = Param(
                name=pname,
                location=pd.get("location", "query"),
                required=bool(pd.get("required", False)),
                types=set(pd.get("types", [])),
                observed=int(pd.get("observed", 0)),
                examples=list(pd.get("examples", [])),
            )
        e.request_schema = _schema_from_dict(ed.get("request_schema"))
        for key, rd in (ed.get("responses") or {}).items():
            status_s, _, ct = key.partition(" ")
            r = Response(
                status=int(status_s),
                content_type=ct,
                count=int(rd.get("count", 0)),
                schema=_schema_from_dict(rd.get("schema")),
                frames=[f for f in (_schema_from_dict(x) for x in rd.get("frames", [])) if f],
            )
            e.responses[(r.status, r.content_type)] = r
        c.endpoints.append(e)
    return c


def iter_observations(rows: Iterable[dict[str, Any]]) -> list[Observation]:
    """Small helper for tests and one-liners."""
    return [
        Observation(
            method=r["method"],
            url=r.get("url", ""),
            path=r.get("path", ""),
            query=r.get("query", {}),
            request_headers=r.get("request_headers", {}),
            request_body=r.get("request_body"),
            status=int(r.get("status", 0)),
            response_headers=r.get("response_headers", {}),
            response_body=r.get("response_body"),
            content_type=r.get("content_type", ""),
            origin=r.get("origin", "probe"),
        )
        for r in rows
    ]