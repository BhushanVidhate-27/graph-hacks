"""
rea/har.py — turning recorded traffic into Observations.

HAR is the highest-value input REA has, and for a non-obvious reason: a HAR is
what a *real browser* did while using the app, which means it contains the
endpoints the product actually depends on — including the undocumented ones that
no OpenAPI lists — plus the auth headers, the sequence, and the error responses
that only appear when something is wrong.

Capturing one is a manual step, which is why REA does not stop there: rea.probe
reproduces the calls without a browser for targets nobody can click through.

Formats accepted:
  - HAR 1.2 (`log.entries`) — Chrome, Firefox, Safari, mitmproxy, Charles
  - HAR with `_resourceType`/`_initiator` extensions — preserved as-is
"""

from __future__ import annotations

import base64
import json
from typing import Any

from rea.infer import _parse_query
from rea.model import Observation


def _decode_text(har_str: dict[str, Any]) -> str:
    if not isinstance(har_str, dict):
        return ""
    text = har_str.get("text", "")
    if har_str.get("encoding") == "base64":
        try:
            return base64.b64decode(text).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001 - a corrupt entry must not kill the run
            return ""
    return text or ""


def _headers_to_dict(items: Any) -> dict[str, str]:
    if not isinstance(items, list):
        return {}
    return {
        i["name"]: i["value"]
        for i in items
        if isinstance(i, dict) and "name" in i and "value" in i
    }


def _maybe_json(raw: str, content_type: str) -> Any:
    if not raw:
        return None
    ct = (content_type or "").lower()
    # Sniff rather than trust the declared type: servers mislabel JSON as
    # text/html often enough that trusting it silently drops most of a SPA's
    # traffic, which is the traffic that matters.
    looks_json = "json" in ct or raw.lstrip()[:1] in ("{", "[")
    if not looks_json:
        return raw
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


def parse_sse(text: str) -> list[Any]:
    """
    Extract the `data:` payloads from an SSE body, decoded as JSON when
    possible.

    SSE matters more than it looks. An endpoint that answers
    `text/event-stream` is not "JSON, eventually": the frontend must implement a
    state machine, and the *frame boundaries* are part of the contract. Collapsing
    a stream into one merged object produces a client that renders nothing until
    the socket closes — which, for an infinite stream, is never.
    """
    frames: list[Any] = []
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue  # [DONE] is the terminator, not a payload
        try:
            frames.append(json.loads(payload))
        except ValueError:
            frames.append(payload)
    return frames


def load_har(raw: dict[str, Any], origin: str = "har") -> list[Observation]:
    """HAR document -> Observations, in recorded order."""
    entries = (raw.get("log") or {}).get("entries") or []
    out: list[Observation] = []
    for entry in entries:
        req = entry.get("request") or {}
        res = entry.get("response") or {}
        url = req.get("url", "")
        if not url:
            continue
        # Split the query off the URL: a HAR gives a raw query string and REA
        # wants name -> values so ?a=1&a=2 survives intact.
        base, _, query = url.partition("?")
        path = base.split("://", 1)[-1].split("/", 1)
        path = "/" + path[1] if len(path) > 1 else "/"

        req_ct = _headers_to_dict(req.get("headers")).get("content-type", "")
        req_text = _decode_text(req.get("postData") or {})
        res_ct = _headers_to_dict(res.get("headers")).get("content-type", "")
        res_text = _decode_text(res.get("content") or {})

        if "text/event-stream" in res_ct.lower():
            body: Any = parse_sse(res_text)
        else:
            body = _maybe_json(res_text, res_ct)

        status = int(res.get("status", 0) or 0)
        # HAR records a redirect as a 3xx with no body; a 0 status means the
        # request never completed. Both are dropped rather than folded in as
        # "observed a response of status 0", which would poison the contract.
        if status == 0:
            continue

        out.append(
            Observation(
                method=req.get("method", "GET").upper(),
                url=url,
                path=path,
                query=_parse_query(query),
                request_headers=_headers_to_dict(req.get("headers")),
                request_body=_maybe_json(req_text, req_ct),
                status=status,
                response_headers=_headers_to_dict(res.get("headers")),
                response_body=body,
                content_type=res_ct.split(";")[0].strip().lower(),
                origin=origin,
            )
        )
    return out


def load_har_file(path: str) -> list[Observation]:
    with open(path, "r", encoding="utf-8") as fh:
        return load_har(json.load(fh))