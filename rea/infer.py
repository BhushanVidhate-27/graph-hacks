"""
rea/infer.py — folding observations into schemas, and paths into templates.

Two jobs, both of which decide what a frontend developer gets wrong most often:

1. SCHEMA FOLDING.  Given N samples of the same JSON value, produce one Schema
   with honest counts. The interesting cases, all of which a naive generator
   gets wrong:
     - a field present in some samples and absent in others  -> optional
     - a field that is null in one sample                   -> nullable + type
     - a string field with 4 distinct values over 40 samples -> enum
     - a string field with 40 distinct values               -> NOT an enum
       (this is why enum detection is capped by *stability*, not just count)
     - an array of objects                                    -> items folded
       across every element, not just the first
     - a number that is sometimes a float, sometimes an int -> "number | integer"
       which codegen turns into `number`, the correct answer

2. PATH TEMPLATING.  /users/8f2c.../posts/91 becomes /users/{userId}/posts/{id}
   so the generated client takes parameters instead of baked-in URLs. The hard
   part is not the regex, it is *not* templating a real segment: /api/v2/users
   must stay literal. REA therefore only templates a segment when it has
   evidence — either it varies across observations, or it matches a strong
   identifier shape, or the target's own spec told us it is a parameter.
"""

from __future__ import annotations

import re
from typing import Any, Iterable
from urllib.parse import parse_qsl

from rea.model import Endpoint, Field_, Observation, Param, Response, Schema

# --------------------------------------------------------------------------- #
# JSON type naming
# --------------------------------------------------------------------------- #

# Retained examples per field. Three is enough for a developer to eyeball a
# real payload and small enough that contract.json stays reviewable in a diff.
MAX_EXAMPLES = 3

# An enum is claimed only when the value set is BOTH small and stable. A field
# with 5 distinct values across 50 samples is a closed set. A field with 5
# distinct values across 5 samples might be a UUID we got lucky with.
ENUM_MAX_VALUES = 12
ENUM_MIN_SAMPLES = 3

# Recursion guard. A target that returns a self-referential structure would
# otherwise blow the stack, and a stack trace from a reverse-engineering tool is
# a useless output.
MAX_DEPTH = 12

_JSON_TYPE_OF = {
    type(None): "null",
    bool: "boolean",
    int: "integer",
    float: "number",
    str: "string",
    list: "array",
    dict: "object",
}


def json_type(value: Any) -> str:
    if isinstance(value, bool):  # before int: bool is a subclass of int
        return "boolean"
    return _JSON_TYPE_OF.get(type(value), "unknown")


# --------------------------------------------------------------------------- #
# Format sniffing — labels only, never creates a field.
# --------------------------------------------------------------------------- #

_ISO_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_URI = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://\S+$")
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$")
_OPAQUE = re.compile(r"^[A-Za-z0-9_-]{20,}$")


def sniff_format(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if _ISO_DATETIME.match(value):
        return "date-time"
    if _UUID.match(value):
        return "uuid"
    if _ISO_DATE.match(value):
        return "date"
    if _EMAIL.match(value):
        return "email"
    if _URI.match(value):
        return "uri"
    return None


# --------------------------------------------------------------------------- #
# Schema folding
# --------------------------------------------------------------------------- #


class Folder:
    """
    Accumulates samples into a Schema.

    `total` counts samples offered to this position; `seen` counts those that
    actually had a value. That ratio is what `required` and `presence` come from
    — see Field_.presence.

    Nested positions get their OWN long-lived Folder (`self._sub`), bound to the
    same Schema object the parent holds. Earlier versions rebuilt a throwaway
    Folder per object, which silently reset enum accumulation — a field observed
    as "active" in 40 separate objects came out with no enum, because each
    object was folded into a fresh holder. Binding once fixes that and makes
    enum detection work across the whole sample set, which is the only way it
    can work at all.
    """

    def __init__(self, schema: Schema | None = None) -> None:
        self.schema = schema if schema is not None else Schema(kind="unknown")
        self._values: dict[str, list[Any]] = {}
        self._lens: dict[str, list[int]] = {}
        self._sub: dict[str, Folder] = {}
        self._items: "Folder | None" = None

    # -- public ----------------------------------------------------------- #

    def add(self, value: Any, depth: int = 0) -> None:
        if depth > MAX_DEPTH:
            return
        self.schema.total += 1
        kind = json_type(value)
        self.schema.types.add(kind)

        if value is None:
            if self.schema.kind == "unknown":
                self.schema.kind = "null"
            return

        if kind == "object":
            self._add_object(value, depth)
        elif kind == "array":
            self._add_array(value, depth)
        else:
            if self.schema.kind == "unknown":
                self.schema.kind = kind
            self.schema.seen += 1
            # A position holding scalars in one sample and objects in another is
            # real (union responses). Keep it addressable as an object schema.
            if "object" in self.schema.types:
                self.schema.kind = "object"

    def finish(self) -> Schema:
        """Fold accumulated distinct values into enums/formats. Recursive."""
        for name, f in self.schema.fields.items():
            if f.nullable:
                f.types.discard("null")
            values = self._values.get(name, [])
            if f.enum is None:
                f.enum = _maybe_enum(values)
            if f.fmt is None:
                fmts = {sniff_format(v) for v in values if isinstance(v, str)}
                fmts.discard(None)
                if len(fmts) == 1:
                    f.fmt = fmts.pop()
            lens = self._lens.get(name)
            if lens:
                f.min_len, f.max_len = min(lens), max(lens)
            if f.schema is not None and name in self._sub:
                # `name in self._sub` and not `.get()`: a merged-in field may have
                # no sub-Folder bound yet in THIS Folder instance, and finishing a
                # non-existent one raised KeyError mid-merge. Absent means "not
                # touched by this sample", which needs no finishing.
                self._sub[name].finish()
        if self._items is not None:
            self._items.finish()
        if self.schema.kind == "unknown" and self.schema.types:
            non_null = sorted(t for t in self.schema.types if t != "null")
            self.schema.kind = non_null[0] if non_null else "null"
        self._values.clear()
        self._lens.clear()
        return self.schema

    # -- internals -------------------------------------------------------- #

    def _field_folder(self, name: str) -> Field_:
        f = self.schema.fields.get(name)
        if f is None:
            f = Field_(name=name, schema=Schema(kind="unknown"))
            self.schema.fields[name] = f
            self._values.setdefault(name, [])
            self._lens.setdefault(name, [])
            self._sub[name] = Folder(f.schema)
        elif name not in self._sub:  # a Schema built by hand and attached later
            self._sub[name] = Folder(f.schema)
            self._values.setdefault(name, list(f.examples))
            self._lens.setdefault(name, [])
        return f

    def _items_folder(self) -> Folder:
        if self._items is None:
            if self.schema.items is None:
                self.schema.items = Schema(kind="unknown")
            self._items = Folder(self.schema.items)
        return self._items

    def _add_object(self, value: dict[str, Any], depth: int) -> None:
        if self.schema.kind == "unknown":
            self.schema.kind = "object"
        self.schema.seen += 1
        # Refresh EVERY known field's denominator to the objects seen so far,
        # including fields this sample does not contain. Doing it only for the
        # keys present in `value` means an absent field keeps its old (small)
        # total, `seen == total` stays true, and it gets exported as required.
        # That is the whole optionality bug, in one line.
        for known_field in self.schema.fields.values():
            known_field.total = self.schema.total
        for name, child in value.items():
            f = self._field_folder(name)
            sub = self._sub[name]
            # The denominator is the number of OBJECTS SEEN, not the number of
            # times this field appeared. Counting only occurrences makes every
            # field 100% present by construction, which is precisely the bug
            # that makes generated clients mark optional fields as required.
            f.total = self.schema.total
            kind = json_type(child)
            f.types.add(kind)
            if child is None:
                f.nullable = True
                # A null is still a PRESENT value. Counting it as absent makes
                # `field: T | null` render as optional, which tells the frontend
                # to branch on undefined for a field the server always sends.
                f.seen += 1
                continue
            f.seen += 1
            if kind in ("object", "array"):
                sub.add(child, depth + 1)
                continue
            if len(f.examples) < MAX_EXAMPLES:
                f.examples.append(child)
            # Cap retained values so a 10k-response crawl cannot blow up memory.
            if len(self._values[name]) < ENUM_MAX_VALUES * 4:
                self._values[name].append(child)
            if f.fmt is None:
                f.fmt = sniff_format(child)

    def _add_array(self, value: list[Any], depth: int) -> None:
        if self.schema.kind == "unknown":
            self.schema.kind = "array"
        self.schema.seen += 1
        # Fold EVERY element, not just the first: an array whose 2nd element has
        # a different shape is a top cause of "cannot read property of undefined"
        # in the frontend.
        items = self._items_folder()
        for el in value:
            items.add(el, depth + 1)


def _maybe_enum(values: list[Any]) -> list[Any] | None:
    """Closed value set, or None. See ENUM_MAX_VALUES note at the top."""
    scalars = [v for v in values if not isinstance(v, (dict, list))]
    if len(scalars) < ENUM_MIN_SAMPLES:
        return None
    distinct: list[Any] = []
    seen: set[str] = set()
    for v in scalars:
        key = f"{json_type(v)}:{v!r}"
        if key in seen:
            continue
        seen.add(key)
        distinct.append(v)
    if not distinct or len(distinct) > ENUM_MAX_VALUES:
        return None
    if len(distinct) == len(scalars):
        return None  # every value unique — not an enum, just data
    return sorted(distinct, key=lambda v: (json_type(v), str(v)))


def infer_schema(samples: Iterable[Any]) -> Schema:
    """Fold a list of same-shaped JSON samples into one Schema."""
    folder = Folder()
    for s in samples:
        folder.add(s)
    return folder.finish()


def _strip_len(schema: Schema) -> None:
    """No-op kept for symmetry: array length now lives on the parent Field_."""
    return


# --------------------------------------------------------------------------- #
# Path templating
# --------------------------------------------------------------------------- #

_VERSION_SEGMENT = re.compile(r"^v\d+(\.\d+)*$", re.I)
_STRONG_ID = re.compile(r"^\d+$|^[0-9a-fA-F]{8,}$|^\d{4}-\d{2}-\d{2}$")

# Segments that look like IDs but never are. Templating /api/v1 -> /api/{version}
# is the classic REA bug and it produces a contract nobody can use.
_NEVER_TEMPLATE = {
    "api", "v1", "v2", "v3", "graphql", "rest", "rpc", "health", "healthz",
    "status", "ping", "metrics", "login", "logout", "me", "index", "static",
    "assets", "admin", "auth", "oauth", "token", "search", "docs", "swagger",
    "openapi", "schema", "self", "sitemap", "feed", "rss", "ws", "websocket",
    "new", "edit", "list", "detail", "search", "null", "undefined", "true",
    "false", "data", "items", "results", "user", "users", "account", "settings",
}


def _is_version(seg: str) -> bool:
    return bool(_VERSION_SEGMENT.match(seg)) or seg.lower() in _NEVER_TEMPLATE


def _camel_to_words(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower()


def _param_name(seg: str, previous: str) -> str:
    """
    Name the placeholder from the segment *before* it, which is how REST APIs
    actually read: /users/{userId}. Falls back to the value's own shape.
    """
    prev = re.sub(r"[^A-Za-z0-9]+$", "", previous or "")
    singular = prev[:-1] if prev.endswith("s") and len(prev) > 1 else prev
    if singular:
        return singular + "Id"
    if seg.isdigit():
        return "id"
    if _UUID.match(seg):
        return "uuid"
    return "id"


def template_path(path: str, known_params: Iterable[int] = (), force: bool = False) -> tuple[str, list[Param]]:
    """
    Return (templated_path, params).

    `known_params` holds the indices of segments the target's own spec declares
    as parameters. Passing them makes templating exact rather than heuristic —
    that is the whole reason REA reads a shipped OpenAPI before probing.
    """
    known = set(known_params)
    segments = [s for s in path.split("/") if s != ""]
    out: list[str] = []
    params: list[Param] = []

    for i, seg in enumerate(segments):
        templatable = i in known or (force and seg != "") or _looks_like_id(seg)
        if templatable and not _is_version(seg):
            prev = segments[i - 1] if i > 0 else ""
            name = _param_name(seg, prev)
            # Disambiguate repeats: /users/{userId}/friends/{friendsId} is ugly
            # but unambiguous, and unambiguous beats pretty.
            while any(p.name == name for p in params):
                name = f"{name}{len(params) + 1}"
            params.append(
                Param(name=name, location="path", required=True, types={_id_type(seg)}, examples=[seg], observed=1)
            )
            out.append("{" + name + "}")
        else:
            out.append(seg)
    return "/" + "/".join(out), params


def _looks_like_id(seg: str) -> bool:
    if not seg or seg in _NEVER_TEMPLATE or _is_version(seg):
        return False
    if seg.isdigit():
        # Short integers are far more likely to be versions, years or enum codes
        # than record ids. Requiring >= 3 digits keeps /api/v2 and /p/1 intact.
        return len(seg) >= 3
    if _STRONG_ID.match(seg):
        return True
    if len(seg) >= 16 and _OPAQUE.match(seg):
        return True
    # A single lowercase word that is not a known noun is weak evidence; skip it.
    return False


def _id_type(seg: str) -> str:
    if seg.isdigit():
        return "integer"
    if _UUID.match(seg):
        return "uuid"
    return "string"


# --------------------------------------------------------------------------- #
# Endpoint assembly
# --------------------------------------------------------------------------- #


def _parse_query(query: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for k, v in parse_qsl(query, keep_blank_values=True):
        out.setdefault(k, []).append(v)
    return out


def content_type_of(headers: dict[str, str]) -> str:
    ct = headers.get("content-type") or headers.get("Content-Type") or ""
    return ct.split(";")[0].strip().lower()


def collect_params(obs: Observation, templated: str) -> dict[str, Param]:
    """
    Derive params from one observation: path placeholders (always required) plus
    query keys seen. `required` for a query param means "present in EVERY
    observation we have" — weak evidence, hence required=False unless it is in
    the target's own spec.
    """
    params: dict[str, Param] = {}
    for name in re.findall(r"\{(\w+)\}", templated):
        params[name] = Param(name=name, location="path", required=True, observed=1)
    for key, values in obs.query.items():
        p = params.get(key)
        if p is None:
            p = Param(name=key, location="query", required=False)
            params[key] = p
        if p.location == "query":
            p.observed += 1
            for v in values[:2]:
                p.examples.append(v)
                p.types.add(_id_type(v))
    return params


def _merge_param(dst: Param, src: Param) -> None:
    dst.types |= src.types
    dst.observed += src.observed
    for ex in src.examples:
        if len(dst.examples) < 3 and ex not in dst.examples:
            dst.examples.append(ex)
    # Query params stay optional unless something stronger says otherwise.
    if src.location == "path":
        dst.required = True


def add_observation(
    endpoints: dict[tuple[str, str], Endpoint],
    obs: Observation,
    known_params: dict[str, set[int]] | None = None,
    force_template: bool = False,
) -> Endpoint:
    """
    Fold one observation into the endpoint table, keyed by (method, template).

    This is the only writer of the endpoint table, so every invariant (samples
    deduped and sorted, examples capped, counts monotonic) lives here.
    """
    known = (known_params or {}).get(obs.path, set())
    path, _tparams = template_path(obs.path, known_params=known, force=force_template)
    key = (obs.method.upper(), path)
    ep = endpoints.get(key)
    if ep is None:
        ep = Endpoint(method=obs.method.upper(), path=path)
        endpoints[key] = ep

    ep.observations += 1
    if obs.path not in ep.samples:
        ep.samples.append(obs.path)
        ep.samples.sort()

    for name, p in collect_params(obs, path).items():
        if name in ep.params:
            _merge_param(ep.params[name], p)
        else:
            ep.params[name] = p

    # Request body.
    if obs.request_body is not None:
        if ep.request_schema is None:
            ep.request_schema = infer_schema([obs.request_body])
        else:
            _merge_schema(ep.request_schema, obs.request_body)
        if len(ep.request_examples) < 3:
            ep.request_examples.append(obs.request_body)

    # Response body, bucketed by (status, content-type) so that a 200 HTML error
    # page never contaminates the JSON schema.
    _record_response(ep, obs)

    # Auth hints: what the client had to send, and what happened when it didn't.
    _apply_auth_hints(ep, obs)
    return ep


def _is_stream(obs: Observation) -> bool:
    return (obs.content_type or "").startswith("text/event-stream")


def _record_response(ep: Endpoint, obs: Observation) -> None:
    ct = obs.content_type or content_type_of(obs.response_headers)

    if _is_stream(obs):
        resp = _response_for(ep, obs.status, ct)
        resp.count += 1
        # Frames are deduped by shape, not by content: a stream that sends the
        # same shape 400 times is ONE frame in the contract. What matters is how
        # many distinct shapes arrive and in what order they first appear, because
        # that is the state machine the frontend has to implement.
        for frame in obs.response_body if isinstance(obs.response_body, list) else []:
            fs = infer_schema([frame])
            _strip_len(fs)
            if not any(_schema_key(f) == _schema_key(fs) for f in resp.frames):
                resp.frames.append(fs)
        return

    if obs.response_body is None and not ct:
        return  # a request that produced neither a body nor a type teaches nothing

    resp = _response_for(ep, obs.status, ct)
    resp.count += 1
    if resp.schema is None:
        resp.schema = infer_schema([obs.response_body])
    else:
        _merge_schema(resp.schema, obs.response_body)
    _strip_len(resp.schema)
    if len(ep.response_examples) < 3:
        ep.response_examples.append(obs.response_body)


def _response_for(ep: Endpoint, status: int, ct: str) -> Response:
    rk = (status, ct)
    resp = ep.responses.get(rk)
    if resp is None:
        resp = Response(status=status, content_type=ct)
        ep.responses[rk] = resp
    return resp


def _apply_auth_hints(ep: Endpoint, obs: Observation) -> None:
    auth = ep.auth
    sent = {k.lower() for k in obs.request_headers}
    for header in ("authorization", "cookie", "x-api-key", "x-auth-token", "api-key"):
        if header in sent:
            auth.setdefault("mechanisms", {})
            auth["mechanisms"][header] = auth["mechanisms"].get(header, 0) + 1
    if obs.status in (401, 403):
        auth.setdefault("protected", True)
        if obs.status == 401:
            auth.setdefault("challenge", obs.response_headers.get("www-authenticate", ""))
    elif obs.status == 200 and auth.get("mechanisms"):
        auth.setdefault("protected", True)


def _schema_key(s: Schema) -> str:
    """Stable identity for a schema, used to dedupe SSE frames."""
    def walk(x: Schema) -> str:
        if x.fields:
            return "{" + ",".join(f"{k}:{walk(v.schema) if v.schema else '?'}" for k, v in sorted(x.fields.items())) + "}"
        if x.items is not None:
            return "[" + walk(x.items) + "]"
        return "|".join(sorted(x.types)) or x.kind

    return walk(s)


def _merge_schema(target: Schema, value: Any) -> None:
    """
    Fold one more sample into an existing Schema, keeping counts monotonic.

    Binding a Folder to `target` (rather than building a new Schema and
    overwriting) is what makes repeat merging correct: the Field_ objects, their
    `seen`/`total` counters and their sub-schemas all survive, so an endpoint
    probed 40 times reports 40 observations rather than the last one.
    """
    folder = Folder(target)
    folder.add(value)
    folder.finish()