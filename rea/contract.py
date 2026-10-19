"""
rea/contract.py — assembling observations into a Contract, and detecting drift.

Two things live here, both of which need the full picture:

  build_contract()  fold every Observation into endpoints, using the target's own
                    spec (when it has one) to make path templating exact, and
                    recording spec paths that never showed up in traffic.

  verify()          re-probe a target against a Contract that already exists and
                    report what changed. This is the feature that pays for the
                    tool: a contract you cannot detect drift against is a
                    snapshot, and snapshots of APIs go stale within a sprint.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from rea import __version__
from rea.infer import add_observation, content_type_of
from rea.model import Contract, Endpoint, Observation, Schema
from rea.probe import SpecHint


# --------------------------------------------------------------------------- #
# Spec template -> matcher
# --------------------------------------------------------------------------- #


def _template_regex(template: str) -> re.Pattern[str]:
    """
    Build a regex that matches concrete paths a spec template would cover.

    A templated segment becomes `[^/]+`. Note this cannot tell /users/me from
    /users/{id} — the spec does not record that either, so REA neither does.
    Anything the spec itself cannot distinguish, REA will not invent.
    """
    out: list[str] = []
    for seg in template.split("/"):
        if not seg:
            continue
        if seg.startswith("{") and seg.endswith("}"):
            out.append("[^/]+")
        else:
            out.append(re.escape(seg))
    return re.compile("^/" + "/".join(out) + "/?$")


def match_spec_path(path: str, hint: SpecHint) -> tuple[str, set[int]] | None:
    """Return (spec_template, param_indices) for a concrete path, or None."""
    for template in hint.paths:
        if _template_regex(template).match(path):
            return template, hint.paths[template]
    return None


def build_contract(
    observations: Iterable[Observation],
    hint: SpecHint | None = None,
    target: str = "",
    force_template: bool = False,
) -> Contract:
    """Fold observations into a Contract. Deterministic for a given input."""
    hint = hint or SpecHint()
    endpoints: dict[tuple[str, str], Endpoint] = {}
    observed_keys: set[str] = set()
    all_obs = list(observations)

    for obs in all_obs:
        # A spec document is evidence about the target, not about an endpoint.
        if obs.origin == "spec":
            continue
        # Status 0 means the request never completed (DNS, TLS, timeout). The path
        # was attempted but nothing about it was learned, so it must not be
        # counted as an observed endpoint — otherwise a contract claims endpoints
        # that have literally only ever failed.
        if obs.status == 0:
            continue
        known: dict[str, set[int]] = {}
        matched = match_spec_path(obs.path, hint)
        if matched:
            known[obs.path] = matched[1]
        ep = add_observation(endpoints, obs, known_params=known, force_template=force_template)
        observed_keys.add(ep.key)

    contract = Contract(
        target=target,
        endpoints=list(endpoints.values()),
        rea_version=__version__,
    )

    # Spec paths we could not observe. Reported, never emitted as facts.
    for template in sorted(hint.paths):
        methods = hint.methods.get(template) or {"GET"}
        for method in sorted(methods):
            key = f"{method} {template}"
            if key not in observed_keys:
                contract.unverified.append(key)

    # Descriptions from the spec are attached, but they stay documentation and
    # never change a confidence score — REA's confidence means "how sure are we
    # from traffic", and a doc comment is not traffic.
    for ep in contract.endpoints:
        desc = hint.descriptions.get((ep.method, ep.path))
        if desc:
            if ep.request_schema is not None:
                ep.request_schema.description = desc
            elif ep.success is not None and ep.success.schema is not None:
                ep.success.schema.description = desc
            else:
                ep.notes.append(desc)

    contract.traits = derive_traits(contract, hint, all_obs)
    return contract


def derive_traits(
    contract: Contract,
    hint: SpecHint,
    observations: Iterable[Observation] = (),
) -> dict[str, Any]:
    """
    Whole-target facts a frontend developer needs before writing a line:
    is it CORS-open, does it stream, how does it authenticate, is it versioned.
    """
    traits: dict[str, Any] = {}

    traits["methods"] = sorted({e.method for e in contract.endpoints})

    # An endpoint that streams is not "JSON, eventually" — the frontend needs a
    # state machine over frames, so it is called out at the target level rather
    # than left to be discovered in the per-endpoint table.
    streaming = sorted(
        e.key for e in contract.endpoints
        if any("event-stream" in ct for (_s, ct) in e.responses)
    )
    if streaming:
        traits["streaming"] = streaming

    prefixes: dict[str, int] = {}
    for e in contract.endpoints:
        segs = [s for s in e.path.split("/") if s]
        if segs and re.match(r"^v\d+$", segs[0], re.I):
            prefixes[segs[0]] = prefixes.get(segs[0], 0) + 1
    if prefixes:
        traits["versioned_prefix"] = sorted(prefixes)

    auth_methods: dict[str, int] = {}
    protected = 0
    for e in contract.endpoints:
        auth_methods.update(e.auth.get("mechanisms", {}))
        if e.auth.get("protected"):
            protected += 1
    if auth_methods:
        traits["auth_headers"] = sorted(auth_methods)
    if protected:
        traits["protected_endpoints"] = protected
    if hint.security_schemes:
        traits["advertised_security_schemes"] = sorted(hint.security_schemes)

    # CORS comes from response headers, which the folded Response deliberately
    # does not keep (it would bloat the contract with Set-Cookie and tracing
    # noise). So it is read here, while the raw observations are still in hand.
    cors: list[str] = []
    for obs in observations:
        if "access-control-allow-origin" in obs.response_headers:
            key = f"{obs.method} {obs.path}"
            if key not in cors:
                cors.append(key)
    if cors:
        traits["cors_headers_present_on"] = sorted(cors)

    error_shapes: dict[str, list[str]] = {}
    for e in contract.endpoints:
        for r in e.errors:
            if r.schema and r.schema.fields:
                error_shapes.setdefault(",".join(sorted(r.schema.fields)), []).append(
                    f"{e.key} -> {r.status}"
                )
    if error_shapes:
        # One canonical error envelope across endpoints is a strong signal the
        # frontend can have exactly one error path. Anything else means every
        # call site needs its own handling, and that is worth surfacing loudly.
        traits["error_envelopes"] = {k: sorted(v) for k, v in sorted(error_shapes.items())}

    return traits


# --------------------------------------------------------------------------- #
# Drift
# --------------------------------------------------------------------------- #


def verify_contract(baseline: Contract, fresh: Contract) -> dict[str, Any]:
    """
    Compare a committed Contract against a freshly observed one.

    The report is grouped by severity, because "the endpoint disappeared" and
    "an optional field became required" deserve very different reactions from a
    team, and a flat list of diffs gets triaged as if every entry were the same.
    """
    old = {e.key: e for e in baseline.endpoints}
    new = {e.key: e for e in fresh.endpoints}

    result: dict[str, Any] = {
        "breaking": [],
        "additive": [],
        "cosmetic": [],
        "unchanged": 0,
    }

    for key in sorted(old):
        if key not in new:
            result["breaking"].append({"kind": "endpoint_removed", "endpoint": key})
            continue
        for change in _diff_endpoint(old[key], new[key]):
            bucket = "breaking" if change.pop("_breaking", False) else "cosmetic"
            result[bucket].append(change)
        result["unchanged"] += 1

    for key in sorted(new):
        if key not in old:
            result["additive"].append({"kind": "endpoint_added", "endpoint": key})

    # Additive changes are safe for existing frontend code, so they belong in
    # their own bucket rather than buried with cosmetics. Bucket-by-severity is
    # the whole point of this function: a team triaging a flat list of diffs
    # treats a new optional field exactly like a deleted required one.
    result["additive"].extend(c for c in result["cosmetic"] if c["kind"] in ADDITIVE_KINDS)
    result["cosmetic"] = [c for c in result["cosmetic"] if c["kind"] not in ADDITIVE_KINDS]
    return result


ADDITIVE_KINDS = frozenset({"field_added", "endpoint_added", "error_response_new"})

# Minimum observations on each side before `verify` claims a schema change.
# Tuned by the same logic as ENUM_MIN_SAMPLES: three samples is the point where
# "this field is missing" stops being an accident of routing.
DRIFT_MIN_SAMPLES = 3


def _diff_endpoint(old: Endpoint, new: Endpoint) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []

    old_success, new_success = old.success, new.success
    if old_success and new_success and old_success.schema and new_success.schema:
        changes.extend(_diff_schema(old_success.schema, new_success.schema, prefix=""))

    if old_success and not new_success:
        changes.append({"kind": "success_response_lost", "endpoint": old.key, "_breaking": True})

    old_err = {(r.status): r for r in old.errors}
    new_err = {(r.status): r for r in new.errors}
    for status in sorted(set(old_err) - set(new_err)):
        changes.append(
            {"kind": "error_response_lost", "endpoint": old.key, "status": status, "_breaking": False}
        )
    for status in sorted(set(new_err) - set(old_err)):
        changes.append(
            {"kind": "error_response_new", "endpoint": old.key, "status": status, "_breaking": False}
        )

    return changes


def _diff_schema(old: Schema, new: Schema, prefix: str) -> list[dict[str, Any]]:
    """
    Compare two folds of the same endpoint's success body.

    Below DRIFT_MIN_SAMPLES on either side this returns NOTHING. One request is
    not evidence that a field was removed — it is evidence that we have not
    looked. Reporting it anyway teaches teams to ignore `rea verify`, and a
    drift detector people ignore is worse than none.
    """
    if old.total < DRIFT_MIN_SAMPLES or new.total < DRIFT_MIN_SAMPLES:
        return []

    changes: list[dict[str, Any]] = []
    for name in sorted(set(old.fields) - set(new.fields)):
        changes.append(
            {
                "kind": "field_removed",
                "path": f"{prefix}{name}",
                "_breaking": True,  # code reading it will throw
            }
        )
    for name in sorted(set(new.fields) - set(old.fields)):
        changes.append({"kind": "field_added", "path": f"{prefix}{name}", "_breaking": False})

    for name in sorted(set(old.fields) & set(new.fields)):
        of, nf = old.fields[name], new.fields[name]
        path = f"{prefix}{name}"
        # Field became always-present: optional -> required. Frontend types must
        # change from `field?: T` to `field: T`.
        if not of.always_present and nf.always_present and nf.seen >= 3:
            changes.append({"kind": "field_now_required", "path": path, "_breaking": True})
        if of.always_present and not nf.always_present and nf.total - nf.seen >= 3:
            changes.append({"kind": "field_now_optional", "path": path, "_breaking": True})
        if of.enum and nf.enum:
            removed = sorted(set(map(str, of.enum)) - set(map(str, nf.enum)), key=str)
            if removed:
                changes.append({"kind": "enum_values_removed", "path": path,
                                "values": removed, "_breaking": True})
        if of.schema and nf.schema:
            changes.extend(_diff_schema(of.schema, nf.schema, prefix=f"{path}."))
    return changes


def content_type_of_response(obs: Observation) -> str:
    return obs.content_type or content_type_of(obs.response_headers)