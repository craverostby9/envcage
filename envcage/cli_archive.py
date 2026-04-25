"""cli_archive.py — CLI commands for snapshot archiving and restoration."""
from __future__ import annotations

import argparse
from pathlib import Path

from envcage.env_archive import archive_snapshot, list_archived, restore_snapshot

_DEFAULT_ARCHIVE_DIR = Path(".envcage/archive")
_DEFAULT_LOG = Path(".envcage/archive_log.json")


def cmd_archive(
    args: argparse.Namespace,
    archive_dir: Path = _DEFAULT_ARCHIVE_DIR,
    log_file: Path = _DEFAULT_LOG,
) -> None:
    """Archive a snapshot file."""
    snap = Path(args.snapshot)
    if not snap.exists():
        print(f"[envcage] error: snapshot not found: {snap}")
        raise SystemExit(1)
    entry = archive_snapshot(snap, archive_dir, log_file, reason=getattr(args, "reason", ""))
    print(f"[envcage] archived: {entry.snapshot} -> {entry.archive_path}")


def cmd_archive_restore(
    args: argparse.Namespace,
    archive_dir: Path = _DEFAULT_ARCHIVE_DIR,
    log_file: Path = _DEFAULT_LOG,
) -> None:
    """Restore an archived snapshot."""
    restore_dir = Path(getattr(args, "restore_dir", "."))
    try:
        dest = restore_snapshot(args.snapshot, archive_dir, restore_dir, log_file)
        print(f"[envcage] restored: {args.snapshot} -> {dest}")
    except FileNotFoundError as exc:
        print(f"[envcage] error: {exc}")
        raise SystemExit(1)


def cmd_archive_list(
    args: argparse.Namespace,
    log_file: Path = _DEFAULT_LOG,
) -> None:
    """List all archived snapshots."""
    entries = list_archived(log_file)
    if not entries:
        print("[envcage] no archived snapshots.")
        return
    for e in entries:
        reason_str = f" ({e.reason})" if e.reason else ""
        print(f"  {e.snapshot}  archived={e.archived_at}{reason_str}")


def cmd_archive_purge(
    args: argparse.Namespace,
    archive_dir: Path = _DEFAULT_ARCHIVE_DIR,
    log_file: Path = _DEFAULT_LOG,
) -> None:
    """Remove all archived snapshots and clear the archive log."""
    entries = list_archived(log_file)
    if not entries:
        print("[envcage] no archived snapshots to purge.")
        return
    removed = 0
    for e in entries:
        path = archive_dir / e.archive_path
        if path.exists():
            path.unlink()
            removed += 1
    if log_file.exists():
        log_file.write_text("[]")
    print(f"[envcage] purged {removed} archived snapshot(s).")


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_archive = sub.add_parser("archive", help="Archive a snapshot")
    p_archive.add_argument("snapshot")
    p_archive.add_argument("--reason", default="")
    p_archive.set_defaults(func=cmd_archive)

    p_restore = sub.add_parser("archive-restore", help="Restore an archived snapshot")
    p_restore.add_argument("snapshot")
    p_restore.add_argument("--restore-dir", dest="restore_dir", default=".")
    p_restore.set_defaults(func=cmd_archive_restore)

    p_list = sub.add_parser("archive-list", help="List archived snapshots")
    p_list.set_defaults(func=cmd_archive_list)

    p_purge = sub.add_parser("archive-purge", help="Remove all archived snapshots")
    p_purge.set_defaults(func=cmd_archive_purge)
