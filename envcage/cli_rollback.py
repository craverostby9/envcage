"""CLI commands for rollback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envcage.rollback import rollback, rollback_log

_DEFAULT_LOG = ".envcage/rollback_log.json"


def cmd_rollback(args: argparse.Namespace) -> None:
    """Restore a snapshot to a destination path."""
    try:
        rec = rollback(
            source_path=args.source,
            destination_path=args.destination,
            label=args.label,
            log_file=args.log_file,
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Rolled back '{rec.source}' → '{rec.destination}' (label: {rec.label})")


def cmd_rollback_log(args: argparse.Namespace) -> None:
    """Print the rollback history."""
    records = rollback_log(args.log_file)
    if not records:
        print("No rollback history found.")
        return
    for i, r in enumerate(records, 1):
        print(f"{i:>3}. [{r.label}] {r.source} → {r.destination}")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # rollback restore
    p_rb = subparsers.add_parser("rollback", help="Restore a snapshot to a path")
    p_rb.add_argument("source", help="Snapshot file to restore from")
    p_rb.add_argument("destination", help="Destination snapshot file")
    p_rb.add_argument("--label", default="rollback", help="Label for this rollback")
    p_rb.add_argument("--log-file", default=_DEFAULT_LOG, dest="log_file",
                      help="Path to rollback log (default: .envcage/rollback_log.json)")
    p_rb.set_defaults(func=cmd_rollback)

    # rollback log
    p_log = subparsers.add_parser("rollback-log", help="Show rollback history")
    p_log.add_argument("--log-file", default=_DEFAULT_LOG, dest="log_file",
                       help="Path to rollback log")
    p_log.set_defaults(func=cmd_rollback_log)
