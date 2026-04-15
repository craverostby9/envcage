"""CLI commands for baseline management."""

from __future__ import annotations

import argparse

from envcage.baseline import (
    set_baseline,
    get_baseline,
    remove_baseline,
    list_baselines,
    drift_from_baseline,
)
from envcage.snapshot import capture, save
from envcage.diff import has_changes, summary as diff_summary

_BASELINE_FILE = ".envcage_baseline.json"


def cmd_baselineNamespace) -> None:
    set_baseline(args.label, args.snapshot, _BASELINE_FILE)
    print(f"Baseline '{args.label}' -> {args.snapshot}")


def cmd_baseline_remove(args: argparse.Namespace) -> None:
    removed = remove_baseline(args.label, _BASELINE_FILE)
    if removed:
        print(f"Removed baseline '{args.label}'.")
    else:
        print(f"No baseline found for '{args.label}'.")


def cmd_baseline_list(args: argparse.Namespace) -> None:
    entries = list_baselines(_BASELINE_FILE)
    if not entries:
        print("No baselines registered.")
        return
    for label, path in sorted(entries.items()):
        print(f"  {label:20s}  {path}")


def cmd_baseline_drift(args: argparse.Namespace) -> None:
    snap = capture(required=[])
    result = drift_from_baseline(args.label, snap, _BASELINE_FILE)
    if not has_changes(result):
        print(f"No drift detected from baseline '{args.label}'.")
    else:
        print(f"Drift from baseline '{args.label}':")
        print(diff_summary(result))


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("baseline", help="Manage environment baselines")
    sub = p.add_subparsers(dest="baseline_cmd", required=True)

    p_set = sub.add_parser("set", help="Register a snapshot as a baseline")
    p_set.add_argument("label", help="Baseline label")
    p_set.add_argument("snapshot", help="Path to snapshot file")
    p_set.set_defaults(func=cmd_baseline_set)

    p_rm = sub.add_parser("remove", help="Remove a baseline entry")
    p_rm.add_argument("label", help="Baseline label to remove")
    p_rm.set_defaults(func=cmd_baseline_remove)

    p_ls = sub.add_parser("list", help="List all baselines")
    p_ls.set_defaults(func=cmd_baseline_list)

    p_drift = sub.add_parser("drift", help="Show drift from a baseline")
    p_drift.add_argument("label", help="Baseline label to compare against")
    p_drift.set_defaults(func=cmd_baseline_drift)
