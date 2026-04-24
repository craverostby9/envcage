"""CLI commands for snapshot checksum management.

Commands
--------
cmd_checksum_record  -- compute and store a snapshot's checksum
cmd_checksum_verify  -- verify a snapshot against its stored checksum
cmd_checksum_show    -- print the stored (or live) checksum for a snapshot
"""

from __future__ import annotations

import argparse
import sys

from envcage.env_checksum import (
    checksum_file,
    get_stored_checksum,
    record_checksum,
    verify_checksum,
)

_DEFAULT_STORE = ".envcage_checksums.json"


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_checksum_record(args: argparse.Namespace) -> None:
    """Compute and persist the checksum for a snapshot file."""
    digest = record_checksum(
        args.snapshot,
        args.store,
        algorithm=args.algorithm,
    )
    print(f"Recorded checksum for '{args.snapshot}': {digest}")


def cmd_checksum_verify(args: argparse.Namespace) -> None:
    """Verify a snapshot against its stored checksum; exit 1 on mismatch."""
    stored = get_stored_checksum(args.snapshot, args.store)
    if stored is None:
        print(
            f"No checksum recorded for '{args.snapshot}'. "
            "Run 'envcage checksum record' first.",
            file=sys.stderr,
        )
        sys.exit(2)

    ok = verify_checksum(args.snapshot, args.store, algorithm=args.algorithm)
    if ok:
        print(f"OK  '{args.snapshot}' matches stored checksum.")
    else:
        current = checksum_file(args.snapshot, algorithm=args.algorithm)
        print(
            f"MISMATCH '{args.snapshot}'\n"
            f"  stored : {stored}\n"
            f"  current: {current}",
            file=sys.stderr,
        )
        sys.exit(1)


def cmd_checksum_show(args: argparse.Namespace) -> None:
    """Print the stored checksum (or compute live if --live is set)."""
    if args.live:
        digest = checksum_file(args.snapshot, algorithm=args.algorithm)
        print(f"{digest}  {args.snapshot}  (live)")
    else:
        stored = get_stored_checksum(args.snapshot, args.store)
        if stored is None:
            print(f"No checksum recorded for '{args.snapshot}'.")
        else:
            print(f"{stored}  {args.snapshot}")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach checksum sub-commands to *subparsers*."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("snapshot", help="Path to the snapshot JSON file.")
    common.add_argument(
        "--store",
        default=_DEFAULT_STORE,
        help=f"Checksum store file (default: {_DEFAULT_STORE}).",
    )
    common.add_argument(
        "--algorithm",
        default="sha256",
        help="Hash algorithm (default: sha256).",
    )

    p = subparsers.add_parser("checksum", help="Snapshot checksum commands.")
    sub = p.add_subparsers(dest="checksum_cmd", required=True)

    sub.add_parser("record", parents=[common], help="Record a snapshot checksum.").set_defaults(
        func=cmd_checksum_record
    )

    sub.add_parser("verify", parents=[common], help="Verify a snapshot checksum.").set_defaults(
        func=cmd_checksum_verify
    )

    show_p = sub.add_parser("show", parents=[common], help="Show a stored checksum.")
    show_p.add_argument("--live", action="store_true", help="Compute checksum live instead.")
    show_p.set_defaults(func=cmd_checksum_show)
