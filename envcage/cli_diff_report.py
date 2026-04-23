"""cli_diff_report.py — CLI commands for generating and displaying diff reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envcage.env_diff_report import build_report, save_report


def cmd_diff_report(args: argparse.Namespace) -> None:
    """Generate a diff report from a JSON pairs manifest or two snapshot files."""
    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            print(f"[error] Manifest not found: {args.manifest}", file=sys.stderr)
            sys.exit(1)
        pairs = json.loads(manifest_path.read_text())
        snap_dir = args.snap_dir or str(manifest_path.parent)
    elif args.source and args.target:
        pairs = [
            {
                "label": args.label or f"{args.source} -> {args.target}",
                "source": Path(args.source).name,
                "target": Path(args.target).name,
            }
        ]
        snap_dir = args.snap_dir or str(Path(args.source).parent)
    else:
        print("[error] Provide --manifest or both --source and --target.", file=sys.stderr)
        sys.exit(1)

    report = build_report(pairs, snap_dir=snap_dir)

    if args.output:
        save_report(report, args.output)
        print(f"Report saved to {args.output}")
    else:
        print(report.summary())

    if args.fail_on_changes and report.any_changes():
        sys.exit(1)


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "diff-report",
        help="Generate a structured diff report across snapshot pairs.",
    )
    p.add_argument("--manifest", help="JSON file listing {label, source, target} pairs.")
    p.add_argument("--source", help="Source snapshot file (single pair mode).")
    p.add_argument("--target", help="Target snapshot file (single pair mode).")
    p.add_argument("--label", help="Label for single-pair report entry.")
    p.add_argument("--snap-dir", dest="snap_dir", help="Base directory for snapshot files.")
    p.add_argument("--output", "-o", help="Save report as JSON to this path.")
    p.add_argument(
        "--fail-on-changes",
        dest="fail_on_changes",
        action="store_true",
        default=False,
        help="Exit with code 1 if any differences are found.",
    )
    p.set_defaults(func=cmd_diff_report)
