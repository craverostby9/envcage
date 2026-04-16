"""CLI commands for env-transform feature."""
from __future__ import annotations
import argparse
from envcage.env_transform import transform_snapshot_file


def cmd_transform(args: argparse.Namespace) -> None:
    replace_pair = None
    if args.replace_prefix:
        parts = args.replace_prefix.split(":")
        if len(parts) != 2:
            print("ERROR: --replace-prefix must be OLD:NEW")
            raise SystemExit(1)
        replace_pair = (parts[0], parts[1])

    result = transform_snapshot_file(
        args.src,
        args.dest,
        uppercase=args.uppercase,
        strip=args.strip,
        replace_prefix_pair=replace_pair,
    )

    if result.changes:
        print(f"Transformed {len(result.changes)} key(s):")
        for k in result.changes:
            print(f"  {k}")
    else:
        print("No changes applied.")
    print(f"Saved to {args.dest}")


def register(subparsers) -> None:
    p = subparsers.add_parser("transform", help="Transform snapshot keys/values")
    p.add_argument("src", help="Source snapshot file")
    p.add_argument("dest", help="Destination snapshot file")
    p.add_argument("--uppercase", action="store_true", help="Uppercase all keys")
    p.add_argument("--strip", action="store_true", help="Strip whitespace from values")
    p.add_argument("--replace-prefix", metavar="OLD:NEW",
                   help="Replace key prefix OLD with NEW")
    p.set_defaults(func=cmd_transform)
