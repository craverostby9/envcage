"""CLI entry point for envcage."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envcage.diff import diff_snapshot_files
from envcage.snapshot import capture, list_snapshots, load, save
from envcage.validate import validate_snapshot_file


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Capture and save a snapshot of the current environment."""
    required = args.require or []
    snap = capture(required_keys=required)
    save(snap, args.output)
    print(f"Snapshot saved to {args.output}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    """Diff two snapshot files."""
    result = diff_snapshot_files(args.before, args.after)
    print(result.summary())
    return 1 if result.has_changes() else 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a snapshot file against required keys."""
    required = args.require or []
    result = validate_snapshot_file(
        args.snapshot,
        required_keys=required,
        allowed_extra=not args.strict,
    )
    print(result.summary())
    return 0 if result.is_valid else 1


def cmd_list(args: argparse.Namespace) -> int:
    """List saved snapshots in a directory."""
    snapshots = list_snapshots(args.dir)
    if not snapshots:
        print("No snapshots found.")
    for path in snapshots:
        print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envcage",
        description="Validate, snapshot, and diff environment variable sets.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # snapshot
    snap_parser = subparsers.add_parser("snapshot", help="Capture current environment")
    snap_parser.add_argument("output", help="Output file path for the snapshot")
    snap_parser.add_argument("-r", "--require", nargs="+", metavar="KEY", help="Required keys")

    # diff
    diff_parser = subparsers.add_parser("diff", help="Diff two snapshot files")
    diff_parser.add_argument("before", help="Path to the baseline snapshot")
    diff_parser.add_argument("after", help="Path to the new snapshot")

    # validate
    val_parser = subparsers.add_parser("validate", help="Validate a snapshot file")
    val_parser.add_argument("snapshot", help="Path to the snapshot file")
    val_parser.add_argument("-r", "--require", nargs="+", metavar="KEY", help="Required keys")
    val_parser.add_argument("--strict", action="store_true", help="Disallow extra keys")

    # list
    list_parser = subparsers.add_parser("list", help="List snapshots in a directory")
    list_parser.add_argument("dir", help="Directory to search for snapshots")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {"snapshot": cmd_snapshot, "diff": cmd_diff, "validate": cmd_validate, "list": cmd_list}
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
