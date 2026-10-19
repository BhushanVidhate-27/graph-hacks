"""
tests/test_rea.py — REA's contract with itself.

These tests exist because every one of them encodes a claim made in a docstring
or a comment somewhere in rea/. If a test here is deleted, something the tool
promises stops being true, so they are deliberately behaviour-level rather than
implementation-level.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from rea.contract import build_contract, match_spec_path, verify_contract
from rea.export import to_markdown, to_openapi, to_typescript
from rea.har import load_har, parse_sse
from rea.infer import infer_schema, json_type, sniff_format, template_path
from rea.model import Contract, Observation, iter_observations
from rea.probe import SpecHint


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


def obs(method="GET", path="/x", status=200, req=None, res=None, ct="application/json", **kw):
    return Observation(
        method=method,
        url=f"http://api.test{path}",
        path=path,
        query=kw.get("query", {}),
        request_headers=kw.get("request_headers", {}),
        request_body=req,
        status=status,
        response_headers=kw.get("response_headers", {}),
        response_body=res,
        content_type=ct,
    )


USER = {
    "id": 7,
    "name": "Ravi Menon",
    "role": "owner",
    "active": True,
    "deleted_at": None,
    "created_at": "2026-09-28T10:00:00Z",
}


# --------------------------------------------------------------------------- #
# Type + format sniffing
# --------------------------------------------------------------------------- #


def test_bool_is_not_int():
    """`True` is an `int` in Python. Trusting isinstance ordering here would type
    every boolean in a real payload as a number."""
    assert json_type(True) == "boolean"
    assert json_type(1) == "integer"


def test_format_sniffing_is_a_label_not_a_claim():
    assert sniff_format("2026-09-28T10:00:00Z") == "date-time"
    assert sniff_format("7c9e6679-7425-40de-944b-e07fc1f90ae7") == "uuid"
    assert sniff_format("ravi@helio.dev") == "email"
    assert sniff_format("Ravi Menon") is None
    assert sniff_format(7) is None


# --------------------------------------------------------------------------- #
# Schema folding
# --------------------------------------------------------------------------- #


def test_optional_field_is_optional_not_null():
    """A field absent from some responses is OPTIONAL. Emitting `field: T | null`
    is the single most common way a generated client breaks in production."""
    schema = infer_schema([{"a": 1}, {"a": 1, "b": 2}, {"a": 1, "b": 2}])
    assert schema.fields["a"].always_present is True
    assert schema.fields["b"].always_present is False
    assert schema.fields["b"].presence == pytest.approx(2 / 3)


def test_null_marks_nullable_but_not_absent():
    schema = infer_schema([{"a": None}, {"a": 1}])
    assert schema.fields["a"].nullable is True
    assert schema.fields["a"].always_present is True  # it WAS there, holding null


def test_enum_needs_evidence():
    """Three samples, one distinct value each, is not an enum — it is data."""
    few = infer_schema([{"s": "a"}, {"s": "b"}])
    assert few.fields["s"].enum is None

    stable = infer_schema([{"s": "active"}, {"s": "idle"}, {"s": "active"}, {"s": "idle"}])
    assert stable.fields["s"].enum == ["active", "idle"]


def test_many_distinct_values_is_never_an_enum():
    schema = infer_schema([{"id": f"v{i}"} for i in range(30)])
    assert schema.fields["id"].enum is None


def test_enum_accumulates_across_nested_objects():
    """Regression: an earlier version rebuilt a throwaway Folder per object, so
    every nested object was judged on its own and 'status' never became an enum
    no matter how many samples arrived."""
    samples = [{"item": {"status": s}} for s in ["a", "b", "c"] * 5]
    schema = infer_schema(samples)
    assert schema.fields["item"].schema.fields["status"].enum == ["a", "b", "c"]


def test_array_items_fold_across_every_element():
    """An array whose second element has a different shape is a top cause of
    'cannot read property of undefined'. Folding only element 0 hides it."""
    schema = infer_schema([{"items": [{"id": 1}, {"id": 2, "extra": True}]}])
    assert "id" in schema.fields["items"].schema.items.fields
    assert "extra" in schema.fields["items"].schema.items.fields
    assert schema.fields["items"].schema.items.fields["extra"].always_present is False


def test_integer_and_number_fold_to_number():
    """A field that is sometimes 1 and sometimes 1.5 must be `number`. A generator
    that says integer makes the frontend parse-fail on the float."""
    schema = infer_schema([{"v": 1}, {"v": 1.5}])
    assert schema.fields["v"].types == {"integer", "number"}
    assert schema.fields["v"].confidence() < 1.0


def test_deeply_nested_does_not_blow_the_stack():
    payload = cur = {}
    for _ in range(50):
        cur["n"] = {}
        cur = cur["n"]
    schema = infer_schema([payload])  # must return, not raise RecursionError
    assert schema.kind in ("object", "unknown")


# --------------------------------------------------------------------------- #
# Path templating
# --------------------------------------------------------------------------- #


def test_ids_become_params():
    path, params = template_path("/users/8123/posts")
    assert path == "/users/{userId}/posts"
    assert [p.name for p in params] == ["userId"]
    assert params[0].required is True


def test_uuids_become_params():
    path, _ = template_path("/orders/7c9e6679-7425-40de-944b-e07fc1f90ae7/refunds")
    assert path == "/orders/{orderId}/refunds"


def test_versions_and_nouns_are_never_templated():
    """Templating /api/v2/users into /api/{version}/users produces a contract
    nobody can use. This is the classic REA bug and it has an explicit test."""
    for path in ("/api/v1/users", "/v2/users", "/api/v2/orders/list", "/health"):
        templated, params = template_path(path)
        assert templated == path
        assert params == []


def test_short_numbers_stay_literal():
    """Requiring 3+ digits keeps /p/1 and /?page=2 style paths intact."""
    assert template_path("/p/1")[0] == "/p/1"
    assert template_path("/users/123")[0] == "/users/{userId}"


def test_known_params_from_spec_win():
    """The target's own spec knows /teams/{slug} even though `slug` is a plain
    word the heuristic would never template."""
    path, params = template_path("/teams/platform", known_params=[1])
    assert path == "/teams/{teamId}"
    assert params[0].required is True


# --------------------------------------------------------------------------- #
# Spec hints
# --------------------------------------------------------------------------- #


def test_spec_match_prefers_exact_literal_paths():
    hint = SpecHint(paths={"/users/me": set(), "/users/{id}": {1}},
                    methods={"/users/me": {"GET"}, "/users/{id}": {"GET"}})
    assert match_spec_path("/users/me", hint)[0] == "/users/me"
    assert match_spec_path("/users/55", hint) == ("/users/{id}", {1})
    assert match_spec_path("/nope", hint) is None


# --------------------------------------------------------------------------- #
# HAR
# --------------------------------------------------------------------------- #


def test_parse_sse_keeps_frames_separate():
    """Merging a stream into one object yields a client that renders nothing
    until the socket closes — which for a live stream is never."""
    frames = parse_sse('data: {"answer":"", "trail":[]}\n\ndata: {"answer":"hi"}\n\ndata: [DONE]\n\n')
    assert frames == [{"answer": "", "trail": []}, {"answer": "hi"}]


def test_har_round_trip():
    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "POST",
                        "url": "http://api.test/ask?verbose=1",
                        "headers": [{"name": "content-type", "value": "application/json"}],
                        "postData": {"text": json.dumps({"question": "who owns payments?"})},
                    },
                    "response": {
                        "status": 200,
                        "headers": [{"name": "content-type", "value": "application/json"}],
                        "content": {"text": json.dumps({"answer": "Platform team"})},
                    },
                }
            ]
        }
    }
    observations = load_har(har)
    assert len(observations) == 1
    o = observations[0]
    assert o.method == "POST"
    assert o.path == "/ask"
    assert o.query == {"verbose": ["1"]}
    assert o.request_body == {"question": "who owns payments?"}
    assert o.origin == "har"


def test_har_json_typed_as_html_is_still_parsed():
    """Servers mislabel SPA JSON as text/html constantly. Trusting the header
    silently drops most of a single-page app's traffic."""
    har = {"log": {"entries": [{
        "request": {"method": "GET", "url": "http://api.test/data", "headers": []},
        "response": {"status": 200,
                     "headers": [{"name": "content-type", "value": "text/html"}],
                     "content": {"text": '{"id": 1}'}},
    }]}}
    assert load_har(har)[0].response_body == {"id": 1}


def test_har_drops_incomplete_entries():
    har = {"log": {"entries": [
        {"request": {"method": "GET", "url": "http://api.test/x", "headers": []},
         "response": {"status": 0, "headers": [], "content": {}}},
    ]}}
    assert load_har(har) == []


# --------------------------------------------------------------------------- #
# Endpoint assembly
# --------------------------------------------------------------------------- #


def test_error_responses_do_not_contaminate_the_success_schema():
    """A 500 that returns `{"detail": "..."}` must not add `detail` to the 200."""
    c = build_contract([
        obs(path="/users", res={"id": 1, "name": "Ravi"}),
        obs(path="/users", status=500, res={"detail": "boom"}),
    ], target="http://api.test")
    ep = c.endpoints[0]
    assert set(ep.responses) == {(200, "application/json"), (500, "application/json")}
    assert "detail" not in ep.success.schema.fields


def test_status_zero_is_not_an_observed_endpoint():
    c = build_contract([obs(path="/down", status=0, res=None, ct="")], target="t")
    assert c.endpoints == []


def test_separate_methods_are_separate_endpoints():
    c = build_contract([obs(method="GET", path="/u", res={}), obs(method="DELETE", path="/u", res=None, ct="")],
                       target="t")
    assert {e.key for e in c.endpoints} == {"GET /u", "DELETE /u"}


def test_streaming_endpoint_records_distinct_frames():
    c = build_contract([
        obs(method="POST", path="/ask", res=[{"answer": "", "trail": []}], ct="text/event-stream"),
        obs(method="POST", path="/ask", res=[{"answer": "", "trail": []}], ct="text/event-stream"),
        obs(method="POST", path="/ask", res=[{"answer": "done", "stale": []}], ct="text/event-stream"),
    ], target="t")
    r = c.endpoints[0].success
    assert r.is_stream
    assert len(r.frames) == 2  # deduped by shape, not by repetition
    assert "answer" in r.frames[0].fields
    assert "stale" in r.frames[1].fields


def test_unverified_spec_paths_are_reported_not_emitted():
    hint = SpecHint(paths={"/live": set(), "/dead": set()},
                    methods={"/live": {"GET"}, "/dead": {"POST"}})
    c = build_contract([obs(path="/live", res={})], hint, target="t")
    assert [e.path for e in c.endpoints] == ["/live"]
    assert c.unverified == ["POST /dead"]


def test_spec_descriptions_never_raise_confidence():
    c = build_contract([obs(path="/live", res={})],
                       SpecHint(paths={"/live": set()}, methods={"/live": {"GET"}},
                                descriptions={("GET", "/live"): "Fetch everything"}),
                       target="t")
    bare = build_contract([obs(path="/live", res={})], target="t")
    assert c.endpoints[0].confidence == bare.endpoints[0].confidence
    assert c.endpoints[0].success.schema.description == "Fetch everything"


def test_build_is_deterministic():
    """Two runs over the same observations must be byte-identical, or `git diff`
    is useless as a drift detector."""
    rows = [
        obs(path="/b", res={"z": 1, "a": 2}),
        obs(path="/a", res={"k": 3}),
        obs(path="/a", res={"k": 4, "extra": None}),
    ]
    first = build_contract(iter_observations([{"method": o.method, "path": o.path,
                                               "res": o.response_body, "status": o.status,
                                               "content_type": o.content_type}
                                              for o in rows]), target="t")
    second = build_contract(iter_observations([{"method": o.method, "path": o.path,
                                                "res": o.response_body, "status": o.status,
                                                "content_type": o.content_type}
                                               for o in rows]), target="t")
    assert first.to_json() == second.to_json()


def test_auth_mechanisms_are_recorded():
    c = build_contract([
        obs(path="/me", res={}, request_headers={"authorization": "Bearer x"}, status=401),
        obs(path="/me", res={}, request_headers={"authorization": "Bearer x"}),
    ], target="t")
    assert c.endpoints[0].auth["mechanisms"] == {"authorization": 2}
    assert c.endpoints[0].auth["protected"] is True


def test_trait_records_streaming_endpoints():
    c = build_contract([obs(method="POST", path="/ask", res=[{"a": 1}], ct="text/event-stream")],
                       target="t")
    assert c.traits["streaming"] == ["POST /ask"]


def test_trait_detects_a_shared_error_envelope():
    c = build_contract([
        obs(path="/a", res={"ok": 1}),
        obs(path="/b", res={"ok": 1}),
        obs(path="/a", status=404, res={"error": "missing"}),
        obs(path="/b", status=404, res={"error": "missing"}),
    ], target="t")
    assert list(c.traits["error_envelopes"]) == ["error"]


# --------------------------------------------------------------------------- #
# Serialisation round-trip
# --------------------------------------------------------------------------- #


def test_contract_survives_json_round_trip():
    c = build_contract([
        obs(method="POST", path="/users/{userId}", req={"name": "Ravi"}, res=USER),
        obs(method="POST", path="/users/{userId}", req={"name": "Priya"}, res=USER),
    ], target="http://api.test")
    revived = Contract.from_json(c.to_json())
    assert revived.to_json() == c.to_json()
    assert revived.endpoints[0].method == "POST"
    assert revived.endpoints[0].request_schema.fields["name"].always_present is True


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #


def test_openapi_is_31_and_marks_only_always_present_fields_required():
    c = build_contract([
        obs(path="/u", res={"id": 1, "nick": "r"}),
        obs(path="/u", res={"id": 2}),
        obs(path="/u", res={"id": 3}),
    ], target="t")
    schema = to_openapi(c)["paths"]["/u"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["required"] == ["id"]
    props = schema["properties"]
    assert props["nick"]["x-rea-presence"] == pytest.approx(1 / 3, abs=1e-4)


def test_openapi_nullable_uses_a_type_array():
    """OpenAPI 3.1 allows `type: [x, "null"]`. The 3.0 workaround (nullable:true)
    is what every generator handles worst."""
    c = build_contract([obs(path="/u", res={"a": None}), obs(path="/u", res={"a": 1}),
                        obs(path="/u", res={"a": 2})], target="t")
    schema = to_openapi(c)["paths"]["/u"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["properties"]["a"]["type"] == ["integer", "null"]


def test_typescript_marks_optional_fields():
    ts = to_typescript(build_contract([
        obs(path="/u", res={"id": 1, "nick": "r"}), obs(path="/u", res={"id": 2}),
        obs(path="/u", res={"id": 3}), obs(path="/u", res={"id": 4}),
    ], target="t"))
    assert "nick?: string;" in ts
    assert "id: number;" in ts


def test_typescript_emits_a_stream_union_not_a_merged_object():
    ts = to_typescript(build_contract([
        obs(method="POST", path="/ask", res=[{"answer": "", "trail": []}], ct="text/event-stream"),
        obs(method="POST", path="/ask", res=[{"answer": "done", "stale": []}], ct="text/event-stream"),
    ], target="t"))
    assert "AskStreamFrame" in ts
    assert "AskFrame1" in ts and "AskFrame2" in ts
    assert "AsyncIterable<AskStreamFrame>" in ts
    # And the client must actually consume the stream incrementally.
    assert "async function* stream(" in ts


def test_typescript_client_builds_urls_with_params():
    ts = to_typescript(build_contract([obs(path="/users/8123", res={"id": 1})], target="http://api.test"))
    assert "export async function getUsersByUserId(" in ts


def test_markdown_has_a_gaps_section():
    """A contract that hides its own uncertainty reads as complete. The gaps
    section is what stops someone shipping on a single observation."""
    md = to_markdown(build_contract([obs(path="/u", res={"id": 1, "weird": "x"})], target="t"))
    assert "## Gaps" in md
    assert "seen 1x" in md


def test_markdown_lists_unverified_paths():
    md = to_markdown(build_contract([obs(path="/live", res={})],
                                    SpecHint(paths={"/live": set(), "/dead": set()},
                                             methods={"/live": {"GET"}, "/dead": {"GET"}}),
                                    target="t"))
    assert "Documented but never observed" in md
    assert "GET /dead" in md


# --------------------------------------------------------------------------- #
# Drift
# --------------------------------------------------------------------------- #


def _baseline():
    return build_contract([
        obs(path="/u", res={"id": 1, "nick": "r"}),
        obs(path="/u", res={"id": 2, "nick": "s"}),
        obs(path="/u", res={"id": 3, "nick": "t"}),
        obs(path="/gone", res={}),
    ], target="t")


def test_removed_field_is_breaking():
    fresh = build_contract([
        obs(path="/u", res={"id": 1}), obs(path="/u", res={"id": 2}),
        obs(path="/u", res={"id": 3}), obs(path="/gone", res={}),
    ], target="t")
    diff = verify_contract(_baseline(), fresh)
    kinds = {(c["kind"], c.get("path")) for c in diff["breaking"]}
    assert ("field_removed", "nick") in kinds


def test_new_field_is_additive_not_breaking():
    fresh = build_contract([
        obs(path="/u", res={"id": 1, "nick": "r", "team": "Platform"}),
        obs(path="/u", res={"id": 2, "nick": "s", "team": "Payments"}),
        obs(path="/u", res={"id": 3, "nick": "t", "team": "Ledger"}),
        obs(path="/gone", res={}),
    ], target="t")
    diff = verify_contract(_baseline(), fresh)
    assert not diff["breaking"]
    assert any(c["kind"] == "field_added" for c in diff["additive"])


def test_endpoint_removed_is_breaking():
    fresh = build_contract([
        obs(path="/u", res={"id": 1, "nick": "r"}),
        obs(path="/u", res={"id": 2, "nick": "s"}),
        obs(path="/u", res={"id": 3, "nick": "t"}),
    ], target="t")
    diff = verify_contract(_baseline(), fresh)
    assert any(c["kind"] == "endpoint_removed" and c["endpoint"] == "GET /gone"
               for c in diff["breaking"])


def test_enum_value_removed_is_breaking():
    b = build_contract([obs(path="/u", res={"s": "a"}), obs(path="/u", res={"s": "b"}),
                        obs(path="/u", res={"s": "a"})], target="t")
    f = build_contract([obs(path="/u", res={"s": "a"}), obs(path="/u", res={"s": "c"}),
                        obs(path="/u", res={"s": "a"})], target="t")
    diff = verify_contract(b, f)
    assert any(c["kind"] == "enum_values_removed" for c in diff["breaking"])


def test_single_sample_never_triggers_a_required_change():
    """A field seen once is not evidence of a schema change. REA must not cry
    wolf, or people will stop reading verify output."""
    b = build_contract([obs(path="/u", res={"id": 1, "nick": "r"})], target="t")
    f = build_contract([obs(path="/u", res={"id": 1})], target="t")
    assert not verify_contract(b, f)["breaking"]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def test_cli_har_subcommand_writes_all_four_artifacts(tmp_path):
    har = {"log": {"entries": [{
        "request": {"method": "GET", "url": "http://api.test/users/8123",
                    "headers": []},
        "response": {"status": 200,
                     "headers": [{"name": "content-type", "value": "application/json"}],
                     "content": {"text": json.dumps({"id": 8123, "name": "Ravi"})}},
    }]}}
    har_path = tmp_path / "session.har"
    har_path.write_text(json.dumps(har))
    out = tmp_path / "contract"

    result = subprocess.run(
        [sys.executable, "-m", "rea", "har", "--har", str(har_path), "--out", str(out), "--quiet"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    for name in ("contract.json", "openapi.json", "types.ts", "CONTRACT.md"):
        assert (out / name).exists(), name

    doc = json.loads((out / "openapi.json").read_text())
    assert doc["openapi"].startswith("3.1")
    assert "/users/{userId}" in doc["paths"]


def test_cli_show_renders_from_a_committed_contract(tmp_path):
    out = tmp_path / "contract"
    har = {"log": {"entries": [{
        "request": {"method": "GET", "url": "http://api.test/health", "headers": []},
        "response": {"status": 200,
                     "headers": [{"name": "content-type", "value": "application/json"}],
                     "content": {"text": '{"status":"ok"}'}},
    }]}}
    har_path = tmp_path / "s.har"
    har_path.write_text(json.dumps(har))
    subprocess.run([sys.executable, "-m", "rea", "har", "--har", str(har_path),
                    "--out", str(out), "--quiet"], check=True, capture_output=True)

    shown = subprocess.run(
        [sys.executable, "-m", "rea", "show", str(out / "contract.json")],
        capture_output=True, text=True,
    )
    assert shown.returncode == 0
    assert "GET /health" in shown.stdout