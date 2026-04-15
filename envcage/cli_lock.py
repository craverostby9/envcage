"""CLI commands for snapshot locking."""

from __future__ import annotations

import argparse
from typing import List

from envcage.env_lock import (
    get_lock,
    is_locked,
    list_locks,
    lock_snapshot,
    unlock_snapshot,
)

_DEFAULT_LOCK_FILE = ".envcage_locks.json"


def cmd_lock(args: argparse.Namespace) -> None:
    """Lock a snapshot file."""
    if is_locked(args.snapshot, lock_file=args.lock_file):
        print(f"[envcage] '{args.snapshot}' is already locked.")
        return
    entry = lock_snapshot(args.snapshot, reason=args.reason or "", lock_file=args.lock_file)
    reason_str = f" ({entry.reason})" if entry.reason else ""
    print(f"[envcage] Locked '{entry.snapshot}' at {entry.locked_at}{reason_str}")


def cmd_unlock(args: argparse.Namespace) -> None:
    """Unlock a previously locked snapshot file."""
    removed = unlock_snapshot(args.snapshot, lock_file=args.lock_file)
    if removed:
        print(f"[envcage] Unlocked '{args.snapshot}'.")
    else:
        print(f"[envcage] '{args.snapshot}' was not locked.")


def cmd_lock_list(args: argparse.Namespace) -> None:
    """List all locked snapshots."""
    locks = list_locks(lock_file=args.lock_file)
    if not locks:
        print("[envcage] No snapshots are currently locked.")
        return
    print(f"{'Snapshot':<40} {'Locked At':<30} Reason")
    print("-" * 80)
    for entry in sorted(locks, key=lambda e: e.snapshot):
        print(f"{entry.snapshot:<40} {entry.locked_at:<30} {entry.reason}")


def cmd_lock_check(args: argparse.Namespace) -> None:
    """Exit 0 if snapshot is locked, 1 if not."""
    if is_locked(args.snapshot, lock_file=args.lock_file):
        entry = get_lock(args.snapshot, lock_file=args.lock_file)
        print(f"[envcage] '{args.snapshot}' is LOCKED since {entry.locked_at}.")
        raise SystemExit(0)
    else:
        print(f"[envcage] '{args.snapshot}' is NOT locked.")
        raise SystemExit(1)


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    lf_kw = dict(default=_DEFAULT_LOCK_FILE, metavar="FILE", help="Lock store file")

    p_lock = subparsers.add_parser("lock", help="Lock a snapshot")
    p_lock.add_argument("snapshot")
    p_lock.add_argument("--reason", default="", help="Reason for locking")
    p_lock.add_argument("--lock-file", **lf_kw)
    p_lock.set_defaults(func=cmd_lock)

    p_unlock = subparsers.add_parser("unlock", help="Unlock a snapshot")
    p_unlock.add_argument("snapshot")
    p_unlock.add_argument("--lock-file", **lf_kw)
    p_unlock.set_defaults(func=cmd_unlock)

    p_list = subparsers.add_parser("lock-list", help="List locked snapshots")
    p_list.add_argument("--lock-file", **lf_kw)
    p_list.set_defaults(func=cmd_lock_list)

    p_check = subparsers.add_parser("lock-check", help="Check if a snapshot is locked")
    p_check.add_argument("snapshot")
    p_check.add_argument("--lock-file", **lf_kw)
    p_check.set_defaults(func=cmd_lock_check)
