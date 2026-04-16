"""CLI commands for filtering snapshot keys."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envcage.env_filter import filter_snapshot
from envcage.snapshot import load


def cmd_filter(args: argparse.Namespace) -> None:
    try:
        snap = load(args.snapshot)
    except FileNotFoundError:
        print(f"error: snapshot not found: {args.snapshot}", file=sys.stderr)
        sys.exit(1)

    env = snap.get("env", {})

    prefixes: Optional[List[str]] = args.prefix if args.prefix else None

    result = filter_snapshot(
        env,
        pattern=args.pattern or None,
        prefixes=prefixes,
        sensitive_only=args.sensitive,
        non_sensitive_only=args.non_sensitive,
        empty_only=args.empty,
        case_sensitive=args.case_sensitive,
    )

    if args.keys_only:
        for k in sorted(result):
            print(k)
    else:
        print(json.dumps(result, indent=2))


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("filter", help="Filter keys in a snapshot")
    p.add_argument("snapshot", help="Path to snapshot file")
    p.add_argument("--pattern", default="", help="Regex pattern to match key names")
    p.add_argument(
        "--prefix", action="append", metavar="PREFIX", help="Filter by key prefix (repeatable)"
    )
    p.add_argument("--sensitive", action="store_true", help="Only sensitive keys")
    p.add_argument("--non-sensitive", dest="non_sensitive", action="store_true")
    p.add_argument("--empty", action="store_true", help="Only keys with empty values")
    p.add_argument("--case-sensitive", dest="case_sensitive", action="store_true")
    p.add_argument("--keys-only", dest="keys_only", action="store_true")
    p.set_defaults(func=cmd_filter)
