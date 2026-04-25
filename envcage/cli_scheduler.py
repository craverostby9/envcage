"""CLI commands for snapshot scheduler management."""
from __future__ import annotations

import argparse
from typing import Optional

from envcage.env_snapshot_scheduler import (
    add_schedule,
    due_schedules,
    list_schedules,
    mark_ran,
    remove_schedule,
)

_DEFAULT_FILE = ".envcage_schedule.json"


def cmd_schedule_add(args: argparse.Namespace) -> None:
    """Register a new snapshot schedule."""
    entry = add_schedule(
        name=args.name,
        output_path=args.output,
        interval_seconds=args.interval,
        schedule_file=getattr(args, "schedule_file", _DEFAULT_FILE),
    )
    print(f"Schedule '{entry.name}' added (every {entry.interval_seconds}s -> {entry.output_path})")


def cmd_schedule_remove(args: argparse.Namespace) -> None:
    """Remove a schedule by name."""
    sf = getattr(args, "schedule_file", _DEFAULT_FILE)
    removed = remove_schedule(args.name, schedule_file=sf)
    if removed:
        print(f"Schedule '{args.name}' removed.")
    else:
        print(f"No schedule named '{args.name}'.")


def cmd_schedule_list(args: argparse.Namespace) -> None:
    """List all registered schedules."""
    sf = getattr(args, "schedule_file", _DEFAULT_FILE)
    entries = list_schedules(schedule_file=sf)
    if not entries:
        print("No schedules registered.")
        return
    for e in entries:
        status = "enabled" if e.enabled else "disabled"
        last = f"{e.last_run:.0f}" if e.last_run else "never"
        print(f"  {e.name:20s}  every {e.interval_seconds:>8}s  last_run={last:>14}  [{status}]  -> {e.output_path}")


def cmd_schedule_due(args: argparse.Namespace) -> None:
    """Print schedules that are currently due to run."""
    sf = getattr(args, "schedule_file", _DEFAULT_FILE)
    due = due_schedules(schedule_file=sf)
    if not due:
        print("No schedules are currently due.")
        return
    for e in due:
        print(f"  DUE  {e.name}  -> {e.output_path}")


def cmd_schedule_mark(args: argparse.Namespace) -> None:
    """Mark a schedule as just-ran (updates last_run to now)."""
    sf = getattr(args, "schedule_file", _DEFAULT_FILE)
    entry = mark_ran(args.name, schedule_file=sf)
    if entry is None:
        print(f"No schedule named '{args.name}'.")
    else:
        print(f"Schedule '{entry.name}' marked as ran at {entry.last_run:.0f}.")


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("schedule", help="Manage snapshot schedules")
    sub = p.add_subparsers(dest="schedule_cmd", required=True)

    p_add = sub.add_parser("add", help="Add a schedule")
    p_add.add_argument("name", help="Unique schedule name")
    p_add.add_argument("output", help="Output snapshot file path")
    p_add.add_argument("--interval", type=int, default=3600, help="Interval in seconds (default 3600)")
    p_add.set_defaults(func=cmd_schedule_add)

    p_rm = sub.add_parser("remove", help="Remove a schedule")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_schedule_remove)

    p_ls = sub.add_parser("list", help="List all schedules")
    p_ls.set_defaults(func=cmd_schedule_list)

    p_due = sub.add_parser("due", help="Show schedules that are due")
    p_due.set_defaults(func=cmd_schedule_due)

    p_mark = sub.add_parser("mark", help="Mark a schedule as ran")
    p_mark.add_argument("name")
    p_mark.set_defaults(func=cmd_schedule_mark)
