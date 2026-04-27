"""CLI commands for snapshot summary reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envcage.env_snapshot_summary import build_report, summarise_snapshot_file


def cmd_summary(args: argparse.Namespace) -> None:
    """Print a summary report for one or more snapshot files."""
    paths: list[str] = args.snapshots
    if not paths:
        print("No snapshot files provided.", file=sys.stderr)
        sys.exit(1)

    report = build_report(paths)

    if getattr(args, "json", False):
        output = {
            "total_snapshots": report.total_snapshots,
            "total_keys": report.total_keys,
            "entries": [e.to_dict() for e in report.entries],
        }
        print(json.dumps(output, indent=2))
    else:
        print(report.summary())


def cmd_summary_single(args: argparse.Namespace) -> None:
    """Print a compact summary for a single snapshot file."""
    entry = summarise_snapshot_file(
        args.snapshot,
        tags=args.tags.split(",") if getattr(args, "tags", None) else [],
        note=getattr(args, "note", None),
    )
    lines = [
        f"Snapshot : {entry.name}",
        f"Path     : {entry.path}",
        f"Keys     : {entry.total_keys}",
        f"Sensitive: {entry.sensitive_keys}",
        f"Empty    : {entry.empty_values}",
        f"Dup vals : {entry.duplicate_values}",
    ]
    if entry.tags:
        lines.append(f"Tags     : {', '.join(entry.tags)}")
    if entry.note:
        lines.append(f"Note     : {entry.note}")
    print("\n".join(lines))


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_multi = sub.add_parser("summary", help="Summarise one or more snapshots")
    p_multi.add_argument("snapshots", nargs="+", help="Snapshot JSON files")
    p_multi.add_argument("--json", action="store_true", help="Output as JSON")
    p_multi.set_defaults(func=cmd_summary)

    p_single = sub.add_parser("summary-single", help="Detailed summary for one snapshot")
    p_single.add_argument("snapshot", help="Snapshot JSON file")
    p_single.add_argument("--tags", default="", help="Comma-separated tags")
    p_single.add_argument("--note", default=None, help="Optional note")
    p_single.set_defaults(func=cmd_summary_single)
