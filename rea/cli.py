"""
rea/cli.py — `python -m rea`.

Four subcommands, one per job:

    build    probe (or read a HAR) and write the contract artifacts
    har      the same, from recorded traffic — no network needed
    verify   re-probe and diff against a committed contract  <- the important one
    show     print a contract to stdout (no files touched)

Stdlib argparse on purpose. REA is a tool you run inside CI on a machine that
does not have the repo's venv, and a CLI that needs the project installed is a
CLI that only runs on your laptop.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from rea import __version__
from rea.contract import build_contract, verify_contract
from rea.export import to_markdown, to_openapi, to_typescript, write_all
from rea.har import load_har_file
from rea.model import Contract, Observation
from rea.probe import ProbeConfig, SpecHint, probe


def _observations_from_sources(args: argparse.Namespace) -> tuple[list[Observation], SpecHint]:
    obs: list[Observation] = []
    hint = SpecHint()

    for path in args.har or []:
        obs.extend(load_har_file(path))

    if args.url:
        cfg = ProbeConfig(
            base_url=args.url,
            timeout=args.timeout,
            delay=args.delay,
            max_requests=args.max_requests,
            max_depth=args.depth,
            allow_mutating=args.allow_mutating,
            extra_headers=_parse_headers(args.header),
            replay_har=args.replay,
            on_request=_progress if not args.quiet else None,
        )
        probed, probed_hint = probe(args.url, cfg)
        obs.extend(probed)
        for path, idx in probed_hint.paths.items():
            hint.paths.setdefault(path, idx)
        for path, methods in probed_hint.methods.items():
            hint.methods.setdefault(path, set()).update(methods)
        hint.descriptions.update(probed_hint.descriptions)
        hint.security_schemes.update(probed_hint.security_schemes)
        hint.source = hint.source or probed_hint.source

    return obs, hint


def _progress(method: str, url: str, status: int) -> None:
    print(f"  {method:7} {status:3}  {url}", file=sys.stderr)


def _parse_headers(items: list[str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        if ":" not in item:
            raise SystemExit(f"--header must be 'Name: value', got {item!r}")
        k, _, v = item.partition(":")
        out[k.strip()] = v.strip()
    return out


def _report(contract: Contract, outdir: str) -> None:
    """Print what was found, and — more importantly — what was not."""
    eps = contract.sorted_endpoints()
    print(f"\nREA {__version__}  target: {contract.target or '(from file)'}")
    print(f"{len(eps)} endpoint(s), {len(contract.unverified)} documented-but-unobserved\n")

    for ep in eps:
        statuses = ", ".join(str(s) for (s, _c) in sorted(ep.responses))
        stream = "  [SSE]" if any("event-stream" in c for (_s, c) in ep.responses) else ""
        print(f"  {ep.method:7} {ep.path:44} {statuses:12} {ep.observations:>3}x  conf {ep.confidence}{stream}")

    if contract.unverified:
        print(f"\n  ! advertised but never observed ({len(contract.unverified)}):")
        for key in sorted(contract.unverified)[:20]:
            print(f"      {key}")

    thin = [e for e in eps if e.confidence < 0.4]
    if thin:
        print(f"\n  ! low confidence ({len(thin)}): under-sampled, capture more traffic")
        for ep in thin:
            print(f"      {ep.key} ({ep.observations}x, conf {ep.confidence})")

    print(f"\n  wrote {outdir}/contract.json, openapi.json, types.ts, CONTRACT.md")


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def cmd_build(args: argparse.Namespace) -> int:
    obs, hint = _observations_from_sources(args)
    if not obs:
        print("nothing observed — no HAR given and no URL to probe", file=sys.stderr)
        return 2
    contract = build_contract(obs, hint, target=args.url or _target_of(obs),
                             force_template=args.force_template)
    written = write_all(contract, args.out)
    if args.format == "json":
        print(written["contract.json"], end="")
    elif args.format == "openapi":
        print(json.dumps(to_openapi(contract), indent=2, sort_keys=True))
    elif args.format == "ts":
        print(to_typescript(contract), end="")
    else:
        _report(contract, args.out)
    return 0


def cmd_har(args: argparse.Namespace) -> int:
    args.url = None
    return cmd_build(args)


def cmd_verify(args: argparse.Namespace) -> int:
    with open(args.contract, "r", encoding="utf-8") as fh:
        baseline = Contract.from_json(fh.read())
    obs, hint = _observations_from_sources(args)
    if not obs:
        print("nothing observed — cannot verify", file=sys.stderr)
        return 2
    fresh = build_contract(obs, hint, target=args.url or baseline.target)
    diff = verify_contract(baseline, fresh)

    print(f"\n{baseline.target or 'target'} — {diff['unchanged']} endpoint(s) unchanged")
    for bucket, icon in (("breaking", "BREAKING"), ("additive", "additive"), ("cosmetic", "note")):
        entries = diff[bucket]
        if not entries:
            continue
        print(f"\n  {icon} ({len(entries)}):")
        for change in entries:
            detail = change.get("path") or change.get("endpoint", "")
            extra = f" [{', '.join(map(str, change['values']))}]" if change.get("values") else ""
            print(f"    {change['kind']:26} {detail}{extra}")

    if diff["breaking"]:
        print("\n  Frontend must change before shipping.")
        return 1
    print("\n  No breaking changes.")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    with open(args.contract, "r", encoding="utf-8") as fh:
        contract = Contract.from_json(fh.read())
    if args.format == "md":
        print(to_markdown(contract), end="")
    elif args.format == "openapi":
        print(json.dumps(to_openapi(contract), indent=2, sort_keys=True))
    elif args.format == "ts":
        print(to_typescript(contract), end="")
    else:
        print(contract.to_json(), end="")
    return 0


def _target_of(obs: list[Observation]) -> str:
    for o in obs:
        if "://" in o.url:
            parts = o.url.split("://", 1)
            rest = parts[1].split("/", 1)[0]
            return f"{parts[0]}://{rest}"
    return ""


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rea", description="Reverse engineer anything into a frontend-ready contract.")
    p.add_argument("--version", action="version", version=f"REA {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp: argparse.ArgumentParser, network: bool = True) -> None:
        if network:
            sp.add_argument("--url", help="base URL to probe, e.g. http://localhost:8000")
        sp.add_argument("--har", action="append", help="HAR file to read (repeatable)")
        sp.add_argument("--out", default="contract", help="output directory (default: ./contract)")
        sp.add_argument("--format", choices=["summary", "json", "openapi", "ts"], default="summary")
        sp.add_argument("--quiet", action="store_true")
        sp.add_argument("--force-template", action="store_true",
                        help="template every non-literal path segment, not just obvious ids")
        if network:
            sp.add_argument("--replay", help="HAR to replay as live requests")
            sp.add_argument("--header", action="append", help="extra request header 'Name: value'")
            sp.add_argument("--timeout", type=float, default=10.0)
            sp.add_argument("--delay", type=float, default=0.15, help="seconds between requests")
            sp.add_argument("--max-requests", type=int, default=300)
            sp.add_argument("--depth", type=int, default=3)
            sp.add_argument("--allow-mutating", action="store_true",
                            help="permit POST/PUT/PATCH/DELETE replays. OFF by default.")

    b = sub.add_parser("build", help="probe and/or read HARs, then write the contract")
    common(b)
    b.set_defaults(func=cmd_build)

    h = sub.add_parser("har", help="build from HAR files only (no network)")
    common(h, network=False)
    h.set_defaults(func=cmd_har)

    v = sub.add_parser("verify", help="re-probe and diff against an existing contract")
    v.add_argument("contract", help="path to a committed contract.json")
    common(v)
    v.set_defaults(func=cmd_verify)

    s = sub.add_parser("show", help="render an existing contract")
    s.add_argument("contract")
    s.add_argument("--format", choices=["json", "md", "openapi", "ts"], default="md")
    s.set_defaults(func=cmd_show)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())