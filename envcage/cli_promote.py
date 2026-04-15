"""CLI commands for snapshot promotion between environment stages."""

from __future__ import annotations

import argparse
from pathlib import Path

from envcage.promote import load_log, promote


def cmd_promote(args: argparse.Namespace) -> None:
    """Promote a snapshot from one stage to another."""
    record = promote(
        source_file=args.source,
        target_file=args.target,
        source_stage=args.source_stage,
        target_stage=args.target_stage,
        note=args.note or "",
        log_path=args.log,
    )
    print(
        f"Promoted: {record.source_stage} -> {record.target_stage}\n"
        f"  Source : {record.source_file}\n"
        f"  Target : {record.target_file}\n"
        f"  At     : {record.promoted_at}"
    )
    if record.note:
        print(f"  Note   : {record.note}")


def cmd_promote_log(args: argparse.Namespace) -> None:
    """List all recorded promotions."""
    records = load_log(args.log)
    if not records:
        print("No promotions recorded.")
        return
    for i, r in enumerate(records, 1):
        print(f"[{i}] {r.promoted_at}  {r.source_stage} -> {r.target_stage}")
        print(f"     src: {r.source_file}")
        print(f"     dst: {r.target_file}")
        if r.note:
            print(f"     note: {r.note}")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _DEFAULT_LOG = ".envcage_promotions.json"

    p_promote = subparsers.add_parser("promote", help="Promote a snapshot to another stage")
    p_promote.add_argument("source", help="Source snapshot file")
    p_promote.add_argument("target", help="Target snapshot file")
    p_promote.add_argument("--source-stage", default="staging", help="Label for the source stage")
    p_promote.add_argument("--target-stage", default="production", help="Label for the target stage")
    p_promote.add_argument("--note", default="", help="Optional note for this promotion")
    p_promote.add_argument("--log", default=_DEFAULT_LOG, help="Promotion log file")
    p_promote.set_defaults(func=cmd_promote)

    p_log = subparsers.add_parser("promote-log", help="List recorded promotions")
    p_log.add_argument("--log", default=_DEFAULT_LOG, help="Promotion log file")
    p_log.set_defaults(func=cmd_promote_log)
