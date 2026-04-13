"""CLI entry point for envcage."""

from __future__ import annotations

import argparse
import sys

from envcage.snapshot import capture, save, list_snapshots
from envcage.diff import diff_snapshot_files
from envcage.validate import validate_snapshot_file
from envcage.export import export_snapshot, export_snapshot_to_file


def cmd_snapshot(args: argparse.Namespace) -> int:
    required = args.require or []
    snapshot = capture(required_keys=required)
    save(snapshot, args.output)
    print(f"Snapshot saved to {args.output}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    result = diff_snapshot_files(args.base, args.head)
    if result.has_changes():
        print(result.summary())
        return 1
    print("No differences found.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    required = args.require or []
    result = validate_snapshot_file(
        args.snapshot,
        required_keys=required,
        allow_extra=not args.strict,
    )
    print(result.summary())
    return 0 if result.is_valid() else 1


def cmd_list(args: argparse.Namespace) -> int:
    snapshots = list_snapshots(args.directory)
    if not snapshots:
        print("No snapshots found.")
    for path in snapshots:
        print(path)
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    fmt = args.format
    if args.output:
        export_snapshot_to_file(args.snapshot, args.output, fmt=fmt)
        print(f"Exported to {args.output} ({fmt} format)")
    else:
        content = export_snapshot(args.snapshot, fmt=fmt)
        sys.stdout.write(content)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envcage",
        description="Validate, snapshot, and diff environment variable sets.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # snapshot
    p_snap = sub.add_parser("snapshot", help="Capture current environment")
    p_snap.add_argument("output", help="Path to save snapshot JSON")
    p_snap.add_argument("--require", nargs="*", metavar="KEY", help="Required keys")
    p_snap.set_defaults(func=cmd_snapshot)

    # diff
    p_diff = sub.add_parser("diff", help="Diff two snapshots")
    p_diff.add_argument("base", help="Base snapshot file")
    p_diff.add_argument("head", help="Head snapshot file")
    p_diff.set_defaults(func=cmd_diff)

    # validate
    p_val = sub.add_parser("validate", help="Validate a snapshot")
    p_val.add_argument("snapshot", help="Snapshot file to validate")
    p_val.add_argument("--require", nargs="*", metavar="KEY", help="Required keys")
    p_val.add_argument("--strict", action="store_true", help="Disallow extra keys")
    p_val.set_defaults(func=cmd_validate)

    # list
    p_list = sub.add_parser("list", help="List saved snapshots")
    p_list.add_argument("directory", nargs="?", default=".", help="Directory to scan")
    p_list.set_defaults(func=cmd_list)

    # export
    p_export = sub.add_parser("export", help="Export snapshot to dotenv, shell, or JSON")
    p_export.add_argument("snapshot", help="Snapshot file to export")
    p_export.add_argument(
        "--format", "-f",
        choices=["dotenv", "shell", "json"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    p_export.add_argument("--output", "-o", help="Write to file instead of stdout")
    p_export.set_defaults(func=cmd_export)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
