"""CLI commands for env-mask: display snapshots with sensitive values masked."""
from __future__ import annotations

import argparse
import json
import sys

from envcage.env_mask import mask_snapshot_file


def cmd_mask(args: argparse.Namespace) -> None:
    """Print a snapshot with sensitive values partially masked."""
    try:
        result = mask_snapshot_file(
            args.snapshot,
            patterns=args.patterns or None,
            visible=args.visible,
        )
    except FileNotFoundError:
        print(f"error: snapshot not found: {args.snapshot}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(result.env, indent=2))
    else:
        for key, value in sorted(result.env.items()):
            print(f"{key}={value}")

    masked_count = len(result.masked_keys)
    if not args.quiet:
        print(
            f"\n# {masked_count} key(s) masked: {', '.join(result.masked_keys)}"
            if masked_count
            else "\n# No sensitive keys detected.",
            file=sys.stderr,
        )


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("mask", help="Display snapshot with sensitive values masked")
    p.add_argument("snapshot", help="Path to snapshot JSON file")
    p.add_argument(
        "--visible",
        type=int,
        default=4,
        metavar="N",
        help="Number of trailing characters to leave visible (default: 4)",
    )
    p.add_argument(
        "--patterns",
        nargs="+",
        metavar="PATTERN",
        help="Additional regex patterns to treat as sensitive",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the masked-keys summary line",
    )
    p.set_defaults(func=cmd_mask)
