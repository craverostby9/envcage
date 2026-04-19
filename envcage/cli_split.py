"""CLI commands for splitting snapshots."""
from __future__ import annotations

import argparse
import json
import sys

from envcage.env_split import split_snapshot_file


def cmd_split(args: argparse.Namespace) -> None:
    prefixes = args.prefix or []
    groups: dict = {}
    if args.group:
        for g in args.group:
            name, _, keys_str = g.partition(":")
            if not name or not keys_str:
                print(f"Invalid group spec '{g}'. Expected name:KEY1,KEY2", file=sys.stderr)
                sys.exit(1)
            groups[name] = [k.strip() for k in keys_str.split(",")]

    if not prefixes and not groups:
        print("Provide --prefix or --group options.", file=sys.stderr)
        sys.exit(1)

    result = split_snapshot_file(
        source=args.source,
        prefixes=prefixes if prefixes else None,
        groups=groups if groups else None,
        output_dir=args.output_dir,
        strip_prefix=args.strip_prefix,
    )

    print(f"Split into {result.total_parts} part(s), {result.total_keys} total keys.")
    for name, env in result.parts.items():
        print(f"  {name}: {len(env)} key(s)")
    if result.unmatched:
        print(f"  (unmatched): {len(result.unmatched)} key(s)")


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("split", help="Split a snapshot by prefix or key groups")
    p.add_argument("source", help="Source snapshot file")
    p.add_argument("--prefix", action="append", metavar="PREFIX", help="Prefix to split on (repeatable)")
    p.add_argument("--group", action="append", metavar="NAME:KEY1,KEY2", help="Named group of keys (repeatable)")
    p.add_argument("--output-dir", default=".", help="Directory for output files")
    p.add_argument("--strip-prefix", action="store_true", help="Remove prefix from keys in output")
    p.set_defaults(func=cmd_split)
