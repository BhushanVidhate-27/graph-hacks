"""
rea/probe.py — reproducing a target's behaviour without a browser.

The active half of REA. Given a base URL it:

  1. looks for a spec the target already publishes (/openapi.json,
     /swagger.json, /api-docs, GraphQL introspection) and uses it as a HINT,
  2. crawls from the seeds, following links, forms and XHR-looking references,
  3. probes each discovered path with the methods a browser would plausibly use,
  4. records everything as Observations, exactly as if it had been captured.

Rule 1 is not "trust the docs". A shipped spec is the single best source of
*candidate paths* (it tells us which segments are parameters, which hand-written
heuristics get wrong) but it is never treated as fact: a path only enters the
contract if a request to it actually came back. Paths that exist in the spec and
survived no probe are recorded in Contract.unverified, which the report prints
loudly — "documented but never observed" is exactly the kind of gap that turns
into a 500 in production.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable
from urllib.parse import urljoin, urlsplit

import httpx

from rea.har import parse_sse
from rea.infer import content_type_of
from rea.model import Observation

# Probing a target you do not own is fine; hammering it is not. Defaults are
# deliberately timid and every knob is explicit.
DEFAULT_TIMEOUT = 10.0
DEFAULT_DELAY = 0.15  # seconds between requests
MAX_REQUESTS = 300
MAX_DEPTH = 3
USER_AGENT = "rea/0.1 (+contract-discovery; read-only probing)"

_SPEC_PATHS = (
    "/openapi.json",
    "/swagger.json",
    "/api/openapi.json",
    "/v1/openapi.json",
    "/api-docs",
    "/.well-known/openapi.json",
    "/openapi.yaml",
)

_HTML_LINK = re.compile(r"""(?:href|action|src)\s*=\s*["']([^"'#]+)["']""", re.I)
# Fragments emitted by SPAs and bundlers look like endpoints but are not routes.
_JS_NOISE = re.compile(r"\.(js|mjs|css|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|map)$", re.I)


@dataclass
class ProbeConfig:
    base_url: str
    timeout: float = DEFAULT_TIMEOUT
    delay: float = DEFAULT_DELAY
    max_requests: int = MAX_REQUESTS
    max_depth: int = MAX_DEPTH
    methods: tuple[str, ...] = ("GET", "OPTIONS")
    # Mutating verbs are OFF by default. Turning them on against a target that is
    # not yours creates invoices, deletes records and emails customers. REA will
    # not do that as a side effect of "discovering the API"; if you want it, ask
    # for it explicitly.
    allow_mutating: bool = False
    extra_headers: dict[str, str] = field(default_factory=dict)
    # A recorded HAR to replay. Replaying real traffic is the cheapest and most
    # accurate probe available — real parameters, real auth, real sequences.
    replay_har: str | None = None
    # Only descend into URLs under this origin. Prevents a crawler that follows
    # an outbound link from wandering into a third-party site.
    same_origin_only: bool = True
    on_request: Callable[[str, str, int], None] | None = None


@dataclass
class SpecHint:
    """What a self-published spec claims. Candidates, not facts."""

    paths: dict[str, set[int]] = field(default_factory=dict)  # path -> param indices
    methods: dict[str, set[str]] = field(default_factory=dict)  # path -> methods
    descriptions: dict[tuple[str, str], str] = field(default_factory=dict)
    security_schemes: dict[str, Any] = field(default_factory=dict)
    source: str = ""


def _indices_of_params(template: str) -> set[int]:
    segs = [s for s in template.split("/") if s != ""]
    return {i for i, s in enumerate(segs) if s.startswith("{") and s.endswith("}")}


def fetch_spec(client: httpx.Client, config: ProbeConfig, obs: list[Observation]) -> SpecHint:
    hint = SpecHint()
    for spec_path in _SPEC_PATHS:
        try:
            r = client.get(urljoin(config.base_url, spec_path))
        except httpx.HTTPError:
            continue
        if r.status_code != 200:
            continue
        try:
            doc = r.json()
        except ValueError:
            continue  # openapi.yaml, html docs page — not worth parsing here
        if not isinstance(doc, dict) or "paths" not in doc:
            continue
        hint.source = spec_path
        hint.security_schemes = doc.get("components", {}).get("securitySchemes", {}) or {}
        for path, ops in (doc.get("paths") or {}).items():
            if not isinstance(ops, dict):
                continue
            hint.paths[path] = _indices_of_params(path)
            hint.methods[path] = {m.upper() for m in ops if m.lower() in
                                  ("get", "post", "put", "patch", "delete", "head", "options")}
            for method, op in ops.items():
                if not isinstance(op, dict):
                    continue
                desc = op.get("summary") or op.get("description") or op.get("operationId")
                if desc:
                    hint.descriptions[(method.upper(), path)] = desc
        obs.append(
            _observation_from_response(client, config, "GET", spec_path, r, is_spec=True)
        )
        return hint
    return hint


def _observation_from_response(
    client: httpx.Client,
    config: ProbeConfig,
    method: str,
    url: str,
    response: httpx.Response,
    is_spec: bool = False,
) -> Observation:
    parts = urlsplit(str(response.request.url))
    ct = content_type_of(dict(response.headers))
    body: Any
    if "text/event-stream" in ct:
        body = parse_sse(response.text)
    else:
        try:
            body = response.json()
        except ValueError:
            body = response.text or None

    query: dict[str, list[str]] = {}
    # Guard the empty case: "".split("&") is [""], and unpacking that raises.
    # Reached on the very first request to any target that has no query string.
    for pair in (parts.query or "").split("&"):
        if not pair:
            continue
        k, _, v = pair.partition("=")
        if k:
            query.setdefault(k, []).append(_unquote(v))

    return Observation(
        method=method,
        url=str(response.request.url),
        path=parts.path,
        query=query,
        request_headers={k.lower(): v for k, v in dict(response.request.headers).items()},
        request_body=_safe_json(response.request.content),
        status=response.status_code,
        response_headers={k.lower(): v for k, v in response.headers.items()},
        response_body=body,
        content_type=ct,
        origin="spec" if is_spec else "probe",
    )


def _unquote(v: str) -> str:
    from urllib.parse import unquote_plus

    return unquote_plus(v)


def _safe_json(content: bytes | None) -> Any:
    if not content:
        return None
    try:
        return json.loads(content)
    except ValueError:
        try:
            return content.decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            return None


def _links_from_html(text: str, base: str) -> list[str]:
    out: list[str] = []
    for m in _HTML_LINK.finditer(text):
        href = m.group(1).strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "data:")):
            continue
        out.append(urljoin(base, href))
    return out


def _paths_in_js(text: str) -> list[str]:
    """
    Pull API-looking string literals out of a JS bundle.

    Heuristic and deliberately narrow: it only matches quoted strings that start
    with "/" and have no file extension. A SPA's routes live in its bundle even
    when they are never linked from the HTML, and a bundle is the only place
    they exist if the app is a single page.
    """
    return [
        m.group(1)
        for m in re.finditer(r"""["'](/[A-Za-z0-9_\-./{}:]{2,80})["']""", text)
        if not _JS_NOISE.match(m.group(1))
    ]


def probe(base_url: str, config: ProbeConfig | None = None) -> tuple[list[Observation], SpecHint]:
    """
    Discover and record. Returns observations in the order they happened, plus
    whatever spec hints were found.
    """
    cfg = config or ProbeConfig(base_url=base_url)
    base = base_url if base_url.endswith("/") else base_url + "/"
    obs: list[Observation] = []
    spent = 0

    headers = {"user-agent": USER_AGENT, "accept": "application/json, text/html;q=0.9, */*;q=0.8"}
    headers.update(cfg.extra_headers)

    with httpx.Client(timeout=cfg.timeout, follow_redirects=True, headers=headers) as client:
        hint = fetch_spec(client, cfg, obs)
        spent += 1

        if cfg.replay_har:
            obs.extend(replay(client, cfg, cfg.replay_har))
            spent += len(obs)

        # Seed queue: the base URL plus every path the spec advertises.
        queue: list[tuple[str, int]] = [(base, 0)]
        queue.extend((urljoin(base, p), 0) for p in sorted(hint.paths))
        seen_urls: set[str] = set()

        while queue and spent < cfg.max_requests:
            url, depth = queue.pop(0)
            key = _normalise(url)
            if key in seen_urls:
                continue
            seen_urls.add(key)

            if cfg.same_origin_only and urlsplit(url).netloc != urlsplit(base).netloc:
                continue

            for method in cfg.methods:
                if spent >= cfg.max_requests:
                    break
                try:
                    response = client.request(method, url)
                except httpx.HTTPError as exc:
                    obs.append(_failed_observation(method, url, exc))
                    spent += 1
                    time.sleep(cfg.delay)
                    continue
                spent += 1
                o = _observation_from_response(client, cfg, method, url, response)
                obs.append(o)
                if cfg.on_request:
                    cfg.on_request(method, url, response.status_code)

                # Descend only into something that looks like an app.
                if method == "GET" and response.status_code == 200 and depth < cfg.max_depth:
                    ct = o.content_type
                    if "html" in ct:
                        queue.extend((u, depth + 1) for u in _links_from_html(response.text, url))
                    elif "javascript" in ct or "json" in ct:
                        found = _paths_in_js(response.text) if "javascript" in ct else []
                        queue.extend((urljoin(base, p), depth + 1) for p in found)
                time.sleep(cfg.delay)

    return obs, hint


def _normalise(url: str) -> str:
    p = urlsplit(url)
    return f"{p.scheme}://{p.netloc}{p.path.rstrip('/')}"


def _failed_observation(method: str, url: str, exc: Exception) -> Observation:
    parts = urlsplit(url)
    return Observation(
        method=method,
        url=url,
        path=parts.path,
        query={},
        request_headers={},
        request_body=None,
        status=0,
        response_headers={},
        response_body=None,
        content_type="",
        origin="probe",
    )


def replay(client: httpx.Client, cfg: ProbeConfig, har_path: str) -> list[Observation]:
    """
    Re-send every distinct exchange from a HAR, in order.

    Replaying beats crawling for one specific reason: it produces the same
    responses the browser saw, so the inferred contract matches reality instead
    of matching whatever an anonymous GET happens to return.
    """
    from rea.har import load_har_file

    out: list[Observation] = []
    seen: set[tuple[str, str, str]] = set()
    for recorded in load_har_file(har_path):
        key = (recorded.method, urlsplit(recorded.url).path, recorded.url)
        if key in seen:
            continue
        seen.add(key)
        if not cfg.allow_mutating and recorded.method not in ("GET", "HEAD", "OPTIONS"):
            continue
        try:
            if recorded.method == "GET":
                r = client.get(recorded.url)
            else:
                r = client.request(recorded.method, recorded.url)
        except httpx.HTTPError:
            continue
        out.append(_observation_from_response(client, cfg, recorded.method, recorded.url, r))
        if cfg.on_request:
            cfg.on_request(recorded.method, recorded.url, r.status_code)
        time.sleep(cfg.delay)
    return out


def probe_many(base_urls: Iterable[str], config: ProbeConfig | None = None) -> tuple[list[Observation], SpecHint]:
    obs: list[Observation] = []
    hint = SpecHint()
    for base in base_urls:
        o, h = probe(base, config)
        obs.extend(o)
        for path, idx in h.paths.items():
            hint.paths.setdefault(path, idx)
        for path, methods in h.methods.items():
            hint.methods.setdefault(path, set()).update(methods)
        if not hint.source:
            hint.source = h.source
        for k, v in h.descriptions.items():
            hint.descriptions.setdefault(k, v)
        hint.security_schemes.update(h.security_schemes)
    return obs, hint