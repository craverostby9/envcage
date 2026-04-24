"""CLI commands for snapshot TTL management."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from envcage.env_ttl import (
    _DEFAULT_TTL_FILE,
    expired_snapshots,
    get_ttl,
    list_ttl,
    remove_ttl,
    set_ttl,
)


def cmd_ttl_set(args: argparse.Namespace) -> None:
    """Mark a snapshot with a TTL (seconds until expiry)."""
    entry = set_ttl(
        snapshot=args.snapshot,
        seconds=args.seconds,
        note=args.note or "",
        ttl_file=args.ttl_file,
    )
    print(f"TTL set: {entry.snapshot} expires at {entry.expires_at}")


def cmd_ttl_show(args: argparse.Namespace) -> None:
    """Show TTL info for a snapshot."""
    entry = get_ttl(args.snapshot, ttl_file=args.ttl_file)
    if entry is None:
        print(f"No TTL found for '{args.snapshot}'")
        return
    now = datetime.now(tz=timezone.utc)
    status = "EXPIRED" if entry.is_expired(now) else f"{entry.seconds_remaining(now):.0f}s remaining"
    print(f"Snapshot : {entry.snapshot}")
    print(f"Expires  : {entry.expires_at}")
    print(f"Status   : {status}")
    if entry.note:
        print(f"Note     : {entry.note}")


def cmd_ttl_remove(args: argparse.Namespace) -> None:
    """Remove TTL entry for a snapshot."""
    removed = remove_ttl(args.snapshot, ttl_file=args.ttl_file)
    if removed:
        print(f"TTL removed for '{args.snapshot}'")
    else:
        print(f"No TTL entry found for '{args.snapshot}'")


def cmd_ttl_list(args: argparse.Namespace) -> None:
    """List all TTL entries."""
    entries = list_ttl(ttl_file=args.ttl_file)
    if not entries:
        print("No TTL entries recorded.")
        return
    now = datetime.now(tz=timezone.utc)
    for e in sorted(entries, key=lambda x: x.expires_at):
        status = "EXPIRED" if e.is_expired(now) else f"{e.seconds_remaining(now):.0f}s"
        print(f"{e.snapshot:<40} {e.expires_at}  [{status}]")


def cmd_ttl_expired(args: argparse.Namespace) -> None:
    """Print all expired snapshots."""
    entries = expired_snapshots(ttl_file=args.ttl_file)
    if not entries:
        print("No expired snapshots.")
        return
    for e in entries:
        print(e.snapshot)


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--ttl-file", default=_DEFAULT_TTL_FILE, help="Path to TTL store")

    p_set = sub.add_parser("ttl-set", parents=[common], help="Set TTL for a snapshot")
    p_set.add_argument("snapshot")
    p_set.add_argument("seconds", type=float, help="Seconds until expiry")
    p_set.add_argument("--note", default="", help="Optional note")
    p_set.set_defaults(func=cmd_ttl_set)

    p_show = sub.add_parser("ttl-show", parents=[common], help="Show TTL for a snapshot")
    p_show.add_argument("snapshot")
    p_show.set_defaults(func=cmd_ttl_show)

    p_rm = sub.add_parser("ttl-remove", parents=[common], help="Remove TTL entry")
    p_rm.add_argument("snapshot")
    p_rm.set_defaults(func=cmd_ttl_remove)

    p_list = sub.add_parser("ttl-list", parents=[common], help="List all TTL entries")
    p_list.set_defaults(func=cmd_ttl_list)

    p_exp = sub.add_parser("ttl-expired", parents=[common], help="List expired snapshots")
    p_exp.set_defaults(func=cmd_ttl_expired)
