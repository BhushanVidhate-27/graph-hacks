"""
rea/export.py — turning a Contract into artifacts a frontend can consume.

Three outputs, three different audiences:

  contract.json  the machine-readable source of truth, with confidence and
                 evidence counts on everything. This is the artifact that gets
                 committed and diffed.
  openapi.json   OpenAPI 3.1, for codegen tools (orval, openapi-typescript,
                 Swagger UI) that already exist and work fine.
  types.ts       hand-usable TypeScript types + a fetch client, because most
                 teams end up hand-writing the client anyway and a generated
                 one that ignores optionality is worse than none.

Every export carries the evidence along:

  - optional fields become `field?: T`, never `field: T | null`
  - a field observed in 60% of samples is optional AND annotated, so the reason
    is visible in review
  - anything below the confidence floor is emitted as `unknown` with a comment
    saying how many samples backed it, rather than a confident wrong type
"""

from __future__ import annotations

import json
import re
from typing import Any

from rea.model import Contract, Endpoint, Field_, Response, Schema

# Below this, REA refuses to name a type. A confident wrong type costs more than
# an `unknown` the developer is forced to think about.
CONFIDENCE_FLOOR = 0.35


# --------------------------------------------------------------------------- #
# Type naming
# --------------------------------------------------------------------------- #

_RESERVED = {
    "default", "function", "class", "new", "delete", "in", "instanceof", "return",
    "void", "const", "let", "var", "type", "interface", "enum", "import", "export",
    "from", "as", "any", "number", "string", "boolean", "object",
}


def pascal(name: str) -> str:
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", name) if p]
    if not parts:
        return "Root"
    out = "".join(p[:1].upper() + p[1:] for p in parts)
    if out[0].isdigit():
        out = "N" + out
    return out


def safe_ident(name: str) -> str:
    if name in _RESERVED:
        return f"{name}_"
    if name and name[0].isdigit():
        return f"n{name}"
    return re.sub(r"[^A-Za-z0-9_$]", "_", name) or "field"


def singular(name: str) -> str:
    if name.endswith("ies") and len(name) > 4:
        return name[:-3] + "y"
    if name.endswith("s") and not name.endswith("ss") and len(name) > 1:
        return name[:-1]
    return name


# --------------------------------------------------------------------------- #
# OpenAPI 3.1
# --------------------------------------------------------------------------- #


def to_openapi(contract: Contract) -> dict[str, Any]:
    """
    OpenAPI 3.1.

    3.1 specifically, not 3.0: it is the version whose `type` accepts an array of
    types, which is exactly what a field observed as `string | null` needs. In
    3.0 that reality has to be faked with nullable:true plus a oneOf, and every
    downstream generator handles the fake worse than the truth.
    """
    doc: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": f"{contract.target or 'target'} — REA inferred contract",
            "version": "0.0.0-generated",
            "description": (
                "Reverse-engineered from observed traffic by REA "
                f"{contract.rea_version}. Not hand-written and not guaranteed "
                "complete; `x-rea-confidence` and `x-rea-samples` say how much "
                "traffic is behind each claim."
            ),
        },
        "paths": {},
    }

    for ep in contract.sorted_endpoints():
        # A path can legitimately support several methods; each gets its own op.
        doc["paths"].setdefault(ep.path, {})[ep.method.lower()] = _openapi_operation(ep)

    if contract.unverified:
        doc["x-rea-unverified"] = sorted(contract.unverified)
    if contract.traits:
        doc["x-rea-traits"] = contract.traits
    return doc


def _openapi_operation(ep: Endpoint) -> dict[str, Any]:
    op: dict[str, Any] = {
        "operationId": f"{ep.method.lower()}{pascal(ep.path)}",
        "responses": {},
        "x-rea-confidence": ep.confidence,
        "x-rea-observations": ep.observations,
    }
    if ep.samples:
        op["x-rea-sample-paths"] = ep.samples
    if ep.auth.get("protected"):
        op["security"] = [{"bearerAuth": []}, {"cookieAuth": []}]

    params = [p for p in ep.params.values() if p.location in ("path", "query")]
    if params:
        op["parameters"] = [
            {
                "name": p.name,
                "in": p.location,
                "required": p.required or p.location == "path",
                "schema": _openapi_scalar(p.types),
                **({"description": p.description} if p.description else {}),
            }
            for p in sorted(params, key=lambda p: (p.location, p.name))
        ]

    if ep.request_schema is not None:
        op["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": _openapi_schema(ep.request_schema),
                    **({"example": ep.request_examples[0]} if ep.request_examples else {}),
                }
            },
        }

    for (status, ct), r in sorted(ep.responses.items()):
        media = ct or "application/json"
        payload: dict[str, Any] = {"schema": _openapi_response_schema(r)}
        if ep.response_examples:
            payload["example"] = ep.response_examples[0]
        op["responses"][str(status)] = {
            "description": _status_text(status),
            "content": {media: payload},
        }
    if not op["responses"]:
        op["responses"]["default"] = {"description": "unobserved"}
    return op


def _status_text(status: int) -> str:
    return {
        200: "OK", 201: "Created", 204: "No Content",
        400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
        404: "Not Found", 405: "Method Not Allowed", 409: "Conflict",
        422: "Unprocessable Entity", 429: "Too Many Requests",
        500: "Internal Server Error", 502: "Bad Gateway", 503: "Service Unavailable",
    }.get(status, "Observed response")


def _openapi_scalar(types: set[str]) -> dict[str, Any]:
    if not types:
        return {}
    if types == {"integer"}:
        return {"type": "integer"}
    if types <= {"integer", "number"}:
        return {"type": "number"}
    if types == {"boolean"}:
        return {"type": "boolean"}
    if types <= {"string"}:
        return {"type": "string"}
    return {"type": sorted(types)[0]}  # single best guess; confidence records doubt


def _openapi_schema(s: Schema) -> dict[str, Any]:
    if s is None:
        return {}
    if s.kind == "object" and s.fields:
        props = {name: _openapi_field(f) for name, f in sorted(s.fields.items())}
        required = sorted(n for n, f in s.fields.items() if f.always_present)
        out: dict[str, Any] = {"type": "object", "properties": props}
        if required:
            out["required"] = required
        return out
    if s.kind == "array" and s.items is not None:
        return {"type": "array", "items": _openapi_schema(s.items)}
    out = _openapi_scalar(s.types)
    if s.description:
        out["description"] = s.description
    return out


def _openapi_response_schema(r: Response) -> dict[str, Any]:
    if r.frames:
        # A stream's schema is its frame sequence, oneOf'd. Collapsing it to a
        # single object is what makes generated clients hang forever.
        return {"oneOf": [_openapi_schema(f) for f in r.frames]}
    return _openapi_schema(r.schema) if r.schema else {}


def _openapi_field(f: Field_) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if f.enum:
        out["enum"] = f.enum
    if f.schema is not None and f.schema.fields:
        props = {n: _openapi_field(sub) for n, sub in sorted(f.schema.fields.items())}
        out["type"] = "object"
        out["properties"] = props
        req = sorted(n for n, sub in f.schema.fields.items() if sub.always_present)
        if req:
            out["required"] = req
    elif f.schema is not None and f.schema.items is not None:
        out["type"] = "array"
        out["items"] = _openapi_schema(f.schema.items)
    else:
        out.update(_openapi_scalar(f.types))

    if f.fmt and not out.get("format"):
        out["format"] = f.fmt
    if f.nullable:
        t = out.get("type")
        if isinstance(t, str):
            out["type"] = [t, "null"]
        elif isinstance(t, list) and "null" not in t:
            out["type"] = t + ["null"]
    if f.min_len is not None or f.max_len is not None:
        out["x-rea-length"] = {"min": f.min_len, "max": f.max_len}
    out["x-rea-presence"] = round(f.presence, 4)
    out["x-rea-confidence"] = f.confidence()
    if f.description:
        out["description"] = f.description
    return out


# --------------------------------------------------------------------------- #
# TypeScript
# --------------------------------------------------------------------------- #


def to_typescript(contract: Contract) -> str:
    """
    Emit types + a fetch client.

    Naming: one interface per response object, named from the endpoint and the
    field path (`AskResponse`, `AskResponseTrail`). Suffix-on-path rather than a
    shared `Response` keeps every type distinct, which is what codegen does too,
    and it means two endpoints that happen to return `{id, name}` still get
    separate types a developer can diverge later.
    """
    lines: list[str] = [
        "// Generated by REA " + (contract.rea_version or "") + " from observed traffic.",
        f"// Target: {contract.target}",
        "//",
        "// Optionality is evidence-based: `foo?: T` means the field was absent in",
        "// some observed responses, so handle it being undefined. `foo: T` means it",
        "// was present in every response seen.",
        "//",
        "// Do not edit by hand — re-run `rea build` and commit the diff instead.",
        "",
        "/* eslint-disable */",
        "",
    ]

    emitted: set[str] = set()

    def emit_object(s: Schema, name: str) -> None:
        """
        Emit one interface per object schema, then recurse into anything nested
        inside it (including array items, which is where `Trail` and `Stale`
        live for a streaming response and the part people forget).
        """
        if not s.fields or name in emitted:
            return
        emitted.add(name)
        body: list[str] = [f"export interface {name} {{"]
        for fname, f in sorted(s.fields.items()):
            body.append(f"  {render_field(f, name, emit_object)}")
        body.append("}")
        lines.extend(body)
        lines.append("")

        for fname, f in sorted(s.fields.items()):
            sub = f.schema
            if sub is None:
                continue
            if sub.fields:
                emit_object(sub, pascal(singular(fname)) or f"{name}Item")
            elif sub.items is not None and sub.items.fields:
                emit_object(sub.items, pascal(singular(fname)) or f"{name}Item")

    def emit_stream(ep: Endpoint, r: Response) -> None:
        """
        A stream's contract is its FRAME SEQUENCE, not a merged object.

        Emitted as a discriminated union plus an async-iterable alias, so a
        consumer writes `for await (const f of askStream())` and switches on the
        frames — instead of waiting for a socket that never closes.
        """
        base = pascal(ep.path)
        frame_names = [f"{base}Frame{i + 1}" for i in range(len(r.frames))]
        for name, frame in zip(frame_names, r.frames):
            emit_object(frame, name)
        union = f"{base}StreamFrame"
        if union in emitted:
            return
        emitted.add(union)
        lines.append("/**")
        lines.append(f" * Every frame shape observed from `{ep.key}`.")
        lines.append(f" * {r.count} frame(s) captured across {r.frames and 'the' or 'no'} distinct shape(s).")
        lines.append(" */")
        if len(frame_names) == 1:
            lines.append(f"export type {union} = {frame_names[0]};")
        else:
            lines.append(f"export type {union} =")
            for name in frame_names:
                lines.append(f"  | {name}")
            lines.append("  ;")
        lines.append("")
        lines.append(f"/** Async iterable over the `{ep.method} {ep.path}` stream. */")
        lines.append(f"export type {base}Stream = AsyncIterable<{union}>;")
        lines.append("")

    for ep in contract.sorted_endpoints():
        base = pascal(ep.path) or "Root"
        if ep.request_schema is not None and ep.request_schema.fields:
            emit_object(ep.request_schema, f"{base}{ep.method.capitalize()}Request")
        r = ep.success
        if r is not None:
            if r.frames:
                emit_stream(ep, r)
            elif r.schema is not None:
                emit_object(r.schema, f"{base}{ep.method.capitalize()}Response")

    lines.extend(_client(contract))
    return "\n".join(lines).rstrip() + "\n"


def render_field(f: Field_, owner: str, emit_object) -> str:
    ident = safe_ident(f.name)
    ts = ts_type(f, owner, emit_object)
    optional = "" if f.always_present else "?"
    comment: list[str] = []
    if not f.always_present:
        comment.append(f"present in {f.seen}/{f.total} observed responses")
    if f.nullable:
        comment.append("nullable")
    if f.confidence() < CONFIDENCE_FLOOR:
        comment.append(f"LOW CONFIDENCE ({f.confidence()}) — verify against the API")
    suffix = f"  // {'; '.join(comment)}" if comment else ""
    return f"{ident}{optional}: {ts};{suffix}"


def ts_type(f: Field_, owner: str, emit_object) -> str:
    if f.enum:
        vals = " | ".join(json.dumps(v) for v in f.enum)
        base = vals
    elif f.schema is not None and f.schema.fields:
        nested = pascal(singular(f.name)) or f"{owner}Item"
        base = nested
    elif f.schema is not None and f.schema.items is not None:
        nested = pascal(singular(f.name)) or f"{owner}Item"
        base = f"{nested}[]"
    else:
        base = ts_scalar(f)

    if f.nullable:
        base = f"{base} | null"
    if f.confidence() < CONFIDENCE_FLOOR:
        return f"unknown /* low confidence */"
    return base


def ts_scalar(f: Field_) -> str:
    types = {t for t in f.types if t != "null"}
    if not types:
        return "unknown"
    if types == {"integer"}:
        return "number"
    if types <= {"integer", "number"}:
        return "number"
    if types == {"boolean"}:
        return "boolean"
    if "string" in types:
        return "string"
    if types == {"array"}:
        return "unknown[]"
    if types == {"object"}:
        return "Record<string, unknown>"
    return " | ".join(sorted(types))


def _client_path(path: str) -> str:
    """
    Path -> name fragment for a client function.

    /users/{userId}/posts -> users/by userId/posts, i.e. `getUsersByUserIdPosts`.
    Keeping the parameter in the name means two endpoints that differ only by
    which id they take cannot collapse into one name, and the "By" reads like
    the call site a developer would write anyway.
    """
    out = []
    for seg in path.split("/"):
        if not seg:
            continue
        if seg.startswith("{") and seg.endswith("}"):
            out.append("by " + seg[1:-1])
        else:
            out.append(seg)
    return "/".join(out)


def _client(contract: Contract) -> list[str]:
    base = (contract.target or "http://localhost").rstrip("/")
    lines = [
        "// ---- client ----------------------------------------------------------",
        "// Minimal fetch client. Handles the two things hand-rolled clients get",
        "// wrong: URL param substitution, and SSE streams that never close.",
        "",
        f"const BASE = {json.dumps(base)};",
        "",
        "export type Query = Record<string, string | number | boolean | undefined>;",
        "",
        "export class HttpError extends Error {",
        "  constructor(readonly status: number, readonly body: unknown) {",
        "    super(`HTTP ${status}`);",
        "  }",
        "}",
        "",
        "function buildUrl(path: string, pathParams: Record<string, string> = {}, query: Query = {}) {",
        "  let url = BASE + path.replace(/\\{(\\w+)\\}/g, (_, k) => encodeURIComponent(pathParams[k]));",
        "  const qs = new URLSearchParams();",
        "  for (const [k, v] of Object.entries(query)) if (v !== undefined) qs.set(k, String(v));",
        "  const s = qs.toString();",
        "  return s ? `${url}?${s}` : url;",
        "}",
        "",
        "async function request(path: string, init: RequestInit = {}) {",
        "  const res = await fetch(path, init);",
        "  if (!res.ok) throw new HttpError(res.status, await res.text().catch(() => null));",
        "  if (res.status === 204) return undefined;",
        "  const ct = res.headers.get('content-type') || '';",
        "  return ct.includes('json') ? res.json() : res.text();",
        "}",
        "",
    ]

    for ep in contract.sorted_endpoints():
        path_params = [p.name for p in ep.params.values() if p.location == "path"]
        query_params = [p.name for p in ep.params.values() if p.location == "query"]
        fn = safe_ident(ep.method.lower() + pascal(_client_path(ep.path)))
        args = ", ".join(
            [f"{safe_ident(p)}: string" for p in path_params]
            + [f"{safe_ident(p)}?: string | number | boolean" for p in query_params]
        )
        lines.append(f"/** {ep.key} — {ep.observations} observations, confidence {ep.confidence} */")
        lines.append(f"export async function {fn}({args}) {{")
        call = "buildUrl(" + json.dumps(ep.path)
        if path_params or query_params:
            call += ",\n    { " + ", ".join(safe_ident(p) for p in path_params) + " }"
            call += ",\n    { " + ", ".join(safe_ident(p) for p in query_params) + " }"
        call += ")"
        if ep.success and ep.success.is_stream:
            lines.append(f"  return stream({call});")
        elif ep.method in ("GET", "HEAD", "OPTIONS"):
            lines.append(f"  return request({call});")
        else:
            body = "body" if ep.request_schema is not None else "{}"
            lines.append(f"  return request({call}, {{ method: '{ep.method}',")
            lines.append("    headers: { 'content-type': 'application/json' },")
            lines.append(f"    body: JSON.stringify({body}) }});")
        lines.append("}")
        lines.append("")

    lines.extend([
        "/**",
        " * SSE reader. Yields each `data:` frame as it arrives instead of waiting",
        " * for the socket to close — the whole point of streaming. Callers must be",
        " * able to abort, so this takes an AbortSignal.",
        " */",
        "export async function* stream(",
        "  path: string,",
        "  pathParams: Record<string, string> = {},",
        "  init: RequestInit = {},",
        "): AsyncGenerator<unknown, void, unknown> {",
        "  const res = await fetch(buildUrl(path, pathParams), {",
        "    ...init,",
        "    headers: { accept: 'text/event-stream', ...(init.headers || {}) },",
        "  });",
        "  if (!res.ok || !res.body) throw new HttpError(res.status, await res.text().catch(() => null));",
        "  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();",
        "  let buf = '';",
        "  while (true) {",
        "    const { done, value } = await reader.read();",
        "    if (done) return;",
        "    buf += value;",
        "    let idx: number;",
        "    while ((idx = buf.indexOf('\\n\\n')) >= 0) {",
        "      const raw = buf.slice(0, idx);",
        "      buf = buf.slice(idx + 2);",
        "      const payload = raw.split('\\n')",
        "        .filter((l) => l.startsWith('data:'))",
        "        .map((l) => l.slice(5).trim())",
        "        .join('');",
        "      if (!payload || payload === '[DONE]') continue;",
        "      try { yield JSON.parse(payload); } catch { yield payload; }",
        "    }",
        "  }",
        "}",
        "",
    ])
    return lines


# --------------------------------------------------------------------------- #
# Markdown — the document a human actually reads
# --------------------------------------------------------------------------- #


def to_markdown(contract: Contract) -> str:
    lines: list[str] = [
        f"# {contract.target or 'Target'} — reverse-engineered contract",
        "",
        f"Generated by **REA {contract.rea_version}** from observed traffic. "
        "Every claim below has a sample count behind it; re-run `rea build` to "
        "regenerate, `rea verify` to detect drift.",
        "",
    ]

    if contract.unverified:
        lines += [
            "## Documented but never observed",
            "",
            "The target advertises these, but no request reproduced them. Treat as "
            "**unverified** — they may be dead, or may need auth REA did not have.",
            "",
        ]
        lines += [f"- `{k}`" for k in sorted(contract.unverified)]
        lines.append("")

    traits = contract.traits
    if traits:
        lines += ["## Target traits", ""]
        for key in sorted(traits):
            value = traits[key]
            if isinstance(value, (dict, list)) and len(str(value)) > 160:
                lines.append(f"- **{key}**: _{len(value)} entries, see contract.json_")
            else:
                lines.append(f"- **{key}**: `{value}`")
        lines.append("")

    lines += ["## Endpoints", ""]
    if not contract.endpoints:
        lines += ["_Nothing observed. Check the base URL and whether the app needs a session._", ""]
        return "\n".join(lines)

    for ep in contract.sorted_endpoints():
        lines.append(f"### `{ep.method} {ep.path}`")
        lines.append("")
        lines.append(
            f"{ep.observations} observation(s) · confidence **{ep.confidence}**"
            + (f" · seen at {', '.join('`' + s + '`' for s in ep.samples[:3])}" if ep.samples else "")
        )
        lines.append("")

        if ep.params:
            lines.append("**Parameters**")
            lines.append("")
            for p in sorted(ep.params.values(), key=lambda p: (p.location, p.name)):
                ex = f" e.g. `{p.examples[0]}`" if p.examples else ""
                req = "required" if p.required else f"optional (seen {p.observed}x)"
                lines.append(f"- `{p.name}` ({p.location}, {req}){ex}")
            lines.append("")

        if ep.request_schema is not None and ep.request_schema.fields:
            lines.append("**Request body**")
            lines.append("")
            lines += _md_schema(ep.request_schema)
            lines.append("")

        for (status, ct), r in sorted(ep.responses.items()):
            tag = "error" if r.is_error else "success"
            lines.append(f"**{status} {ct or 'unknown'}** _({tag}, {r.count}x, confidence {round(r.confidence, 3)})_")
            lines.append("")
            if r.frames:
                lines.append(f"Streams {len(r.frames)} distinct frame shape(s) over SSE:")
                lines.append("")
                for i, fr in enumerate(r.frames):
                    lines.append(f"Frame {i + 1}:")
                    lines.append("")
                    lines += _md_schema(fr, indent="  ")
                lines.append("")
            elif r.schema is not None and r.schema.fields:
                lines += _md_schema(r.schema)
                lines.append("")
            else:
                lines += [f"_No body observed._", ""]

    lines += _md_gaps(contract)
    return "\n".join(lines).rstrip() + "\n"


def _md_schema(s: Schema, indent: str = "") -> list[str]:
    out: list[str] = []
    for name, f in sorted(s.fields.items()):
        types = "/".join(sorted(f.types)) or "unknown"
        bits = [types]
        if f.fmt:
            bits.append(f.fmt)
        if f.enum:
            bits.append("enum " + ", ".join(json.dumps(v) for v in f.enum[:8]))
        flag = "" if f.always_present else f" _optional ({f.seen}/{f.total})_"
        out.append(f"{indent}- `{name}`: {', '.join(bits)}{flag}")
        if f.schema is not None and f.schema.fields:
            out += _md_schema(f.schema, indent + "  ")
        elif f.schema is not None and f.schema.items is not None and f.schema.items.fields:
            out.append(f"{indent}  - items:")
            out += _md_schema(f.schema.items, indent + "    ")
    return out


def _md_gaps(contract: Contract) -> list[str]:
    """
    The "what we do not know" section.

    This is the section that makes REA worth more than a one-time scrape. A
    contract without it reads as complete, and someone will build a feature on an
    endpoint REA only saw once and quietly guess wrong.
    """
    gaps: list[str] = []
    for ep in contract.sorted_endpoints():
        thin: list[str] = []
        if ep.observations < 3:
            thin.append(f"`{ep.method} {ep.path}` seen {ep.observations}x — optionality is a guess")
        if ep.success is not None and ep.success.schema is not None:
            for name, f in sorted(ep.success.schema.fields.items()):
                if f.confidence() < CONFIDENCE_FLOOR:
                    thin.append(
                        f"`{ep.method} {ep.path}` → `{name}` "
                        f"(confidence {f.confidence()}, {f.seen}/{f.total} samples)"
                    )
        gaps.extend(thin)
    if not gaps:
        return ["## Gaps", "", "_No confidence gaps found. That is unusual — double-check the sample counts._", ""]
    return ["## Gaps — capture more before trusting these", ""] + [f"- {g}" for g in sorted(gaps)] + [""]


def write_all(contract: Contract, outdir: str) -> dict[str, str]:
    """Write every artifact. Returns {relative_path: contents} for tests."""
    import os

    os.makedirs(outdir, exist_ok=True)
    written: dict[str, str] = {}

    written["contract.json"] = contract.to_json()
    written["openapi.json"] = json.dumps(to_openapi(contract), indent=2, sort_keys=True) + "\n"
    written["types.ts"] = to_typescript(contract)
    written["CONTRACT.md"] = to_markdown(contract)

    for name, contents in written.items():
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as fh:
            fh.write(contents)
    return written