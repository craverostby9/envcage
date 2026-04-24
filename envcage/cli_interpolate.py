"""CLI commands for snapshot value interpolation."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envcage.env_interpolate import interpolate_snapshot_file, interpolate_snapshot
from envcage.snapshot import load


def cmd_interpolate(args: argparse.Namespace) -> None:
    """Resolve variable references in a snapshot and write the result."""
    src = Path(args.snapshot)
    if not src.exists():
        print(f"[error] snapshot not found: {src}", file=sys.stderr)
        sys.exit(1)

    dest = Path(args.output) if args.output else src.with_suffix(".interpolated.json")

    # Optional extra context from --set KEY=VALUE flags
    context: dict[str, str] = {}
    for item in args.set or []:
        if "=" not in item:
            print(f"[error] --set requires KEY=VALUE format, got: {item}", file=sys.stderr)
            sys.exit(1)
        k, v = item.split("=", 1)
        context[k] = v

    try:
        result = interpolate_snapshot_file(
            src,
            dest,
            context=context or None,
            strict=args.strict,
        )
    except KeyError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Interpolated snapshot saved to: {dest}")
    if result.resolved:
        print(f"  Resolved keys  ({len(result.resolved)}): {', '.join(sorted(result.resolved))}")
    if result.unresolved:
        print(f"  Unresolved keys ({len(result.unresolved)}): {', '.join(sorted(result.unresolved))}")
        if not args.strict:
            print("  [warn] Some references could not be resolved — use --strict to treat as errors.")


def cmd_interpolate_show(args: argparse.Namespace) -> None:
    """Print interpolated values to stdout without writing a file."""
    src = Path(args.snapshot)
    if not src.exists():
        print(f"[error] snapshot not found: {src}", file=sys.stderr)
        sys.exit(1)

    snap = load(str(src))
    result = interpolate_snapshot(snap["env"])

    for key, value in sorted(result.env.items()):
        marker = "*" if key in result.resolved else ("?" if key in result.unresolved else " ")
        print(f"  [{marker}] {key}={value}")

    print()
    print(f"Legend: [*] resolved  [?] unresolved  [ ] unchanged")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_interp = subparsers.add_parser(
        "interpolate", help="Resolve $VAR / ${VAR} references in snapshot values"
    )
    p_interp.add_argument("snapshot", help="Source snapshot file")
    p_interp.add_argument("-o", "--output", help="Destination snapshot file")
    p_interp.add_argument(
        "--set",
        metavar="KEY=VALUE",
        action="append",
        help="Extra context variables (repeatable)",
    )
    p_interp.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any reference cannot be resolved",
    )
    p_interp.set_defaults(func=cmd_interpolate)

    p_show = subparsers.add_parser(
        "interpolate-show", help="Preview interpolated values without saving"
    )
    p_show.add_argument("snapshot", help="Source snapshot file")
    p_show.set_defaults(func=cmd_interpolate_show)
