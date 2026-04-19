"""CLI commands for merge-strategy operations."""
from __future__ import annotations
import argparse
import json
from envcage.snapshot import load
from envcage.env_merge_strategy import apply_strategy, STRATEGY_LAST_WINS


def cmd_merge_strategy(args: argparse.Namespace) -> None:
    """Merge multiple snapshot files using the chosen strategy."""
    if len(args.snapshots) < 2:
        print("error: at least two snapshot files required")
        raise SystemExit(1)

    snapshots = []
    for path in args.snapshots:
        snap = load(path)
        snapshots.append(snap["env"])

    result = apply_strategy(snapshots, strategy=args.strategy)

    if args.output:
        import envcage.snapshot as _snap_mod
        import time
        payload = {
            "env": result.env,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "required_keys": [],
        }
        with open(args.output, "w") as fh:
            json.dump(payload, fh, indent=2)
        print(f"Merged snapshot written to {args.output}")
    else:
        for k, v in sorted(result.env.items()):
            print(f"{k}={v}")

    print()
    print(result.summary())

    if result.has_conflicts and args.strict:
        raise SystemExit(2)


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "merge-strategy",
        help="Merge snapshots with a chosen conflict strategy",
    )
    p.add_argument("snapshots", nargs="+", metavar="SNAPSHOT", help="Snapshot files to merge")
    p.add_argument(
        "--strategy",
        choices=["last_wins", "first_wins", "strict"],
        default=STRATEGY_LAST_WINS,
        help="Conflict resolution strategy (default: last_wins)",
    )
    p.add_argument("--output", "-o", metavar="FILE", help="Write merged snapshot to file")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 2 if any conflicts are detected",
    )
    p.set_defaults(func=cmd_merge_strategy)
