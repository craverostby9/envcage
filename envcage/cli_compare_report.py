"""CLI commands for multi-snapshot comparison reports."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envcage.env_snapshot_compare_report import (
    build_multi_compare_report_from_files,
    save_report,
)


def cmd_compare_report(args: argparse.Namespace) -> None:
    """Build and display a comparison report across multiple snapshot files."""
    if len(args.snapshots) < 2:
        print("error: at least two snapshot files are required.", file=sys.stderr)
        sys.exit(1)

    try:
        report = build_multi_compare_report_from_files(args.snapshots)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return

    print(f"Snapshots : {', '.join(report.snapshot_names)}")
    print(f"Keys      : {len(report.entries)}")
    print()

    for entry in report.entries:
        status = "OK" if entry.consistent else "DIFF"
        print(f"  [{status}] {entry.key}")
        if not entry.consistent or args.verbose:
            for snap_name, value in entry.values.items():
                display = value if value is not None else "<missing>"
                print(f"         {snap_name}: {display}")

    print()
    print(report.summary())

    if args.output:
        save_report(report, args.output)
        print(f"Report saved to {args.output}")

    if report.any_inconsistencies:
        sys.exit(1)


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "compare-report",
        help="Compare multiple snapshots and produce a consistency report.",
    )
    parser.add_argument(
        "snapshots",
        nargs="+",
        metavar="SNAPSHOT",
        help="Two or more snapshot files to compare.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output report as JSON.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Show values for consistent keys too.",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        default=None,
        help="Save JSON report to FILE.",
    )
    parser.set_defaults(func=cmd_compare_report)
