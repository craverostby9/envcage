"""CLI commands for env variable type inference and checking."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envcage.snapshot import load
from envcage.env_variable_type import analyze_snapshot


def cmd_type_show(args: argparse.Namespace) -> None:
    """Show inferred types for all keys in a snapshot."""
    snap = load(args.snapshot)
    env = snap.get("env", {})
    report = analyze_snapshot(env)

    if args.json:
        data = [i.to_dict() for i in report.inferences]
        print(json.dumps(data, indent=2))
        return

    if not report.inferences:
        print("No keys found.")
        return

    col = max(len(i.key) for i in report.inferences)
    for inf in report.inferences:
        print(f"{inf.key:<{col}}  {inf.inferred_type}")


def cmd_type_check(args: argparse.Namespace) -> None:
    """Check snapshot types against an expected-types JSON file."""
    snap = load(args.snapshot)
    env = snap.get("env", {})

    expected_path = Path(args.expected)
    if not expected_path.exists():
        print(f"Expected-types file not found: {args.expected}", file=sys.stderr)
        sys.exit(2)

    with expected_path.open() as fh:
        expected: dict = json.load(fh)

    report = analyze_snapshot(env, expected=expected)

    if args.json:
        data = {
            "any_mismatches": report.any_mismatches,
            "mismatches": [m.to_dict() for m in report.mismatches],
        }
        print(json.dumps(data, indent=2))
    else:
        print(report.summary())

    sys.exit(1 if report.any_mismatches else 0)


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # --- type show ---
    p_show = sub.add_parser("type-show", help="Show inferred types for snapshot keys")
    p_show.add_argument("snapshot", help="Path to snapshot file")
    p_show.add_argument("--json", action="store_true", help="Output as JSON")
    p_show.set_defaults(func=cmd_type_show)

    # --- type check ---
    p_check = sub.add_parser(
        "type-check", help="Check snapshot types against expected types"
    )
    p_check.add_argument("snapshot", help="Path to snapshot file")
    p_check.add_argument("expected", help="Path to expected-types JSON file")
    p_check.add_argument("--json", action="store_true", help="Output as JSON")
    p_check.set_defaults(func=cmd_type_check)
