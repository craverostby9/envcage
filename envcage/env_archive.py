"""env_archive.py — Archive and restore snapshot files with metadata."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envcage.audit import _now_iso


@dataclass
class ArchiveEntry:
    snapshot: str
    archived_at: str
    reason: str
    archive_path: str

    def to_dict(self) -> dict:
        return {
            "snapshot": self.snapshot,
            "archived_at": self.archived_at,
            "reason": self.reason,
            "archive_path": self.archive_path,
        }

    @staticmethod
    def from_dict(d: dict) -> "ArchiveEntry":
        return ArchiveEntry(
            snapshot=d["snapshot"],
            archived_at=d["archived_at"],
            reason=d.get("reason", ""),
            archive_path=d["archive_path"],
        )


def _load_log(log_file: Path) -> List[ArchiveEntry]:
    if not log_file.exists():
        return []
    with log_file.open() as f:
        return [ArchiveEntry.from_dict(e) for e in json.load(f)]


def _save_log(log_file: Path, entries: List[ArchiveEntry]) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("w") as f:
        json.dump([e.to_dict() for e in entries], f, indent=2)


def archive_snapshot(
    snapshot_path: Path,
    archive_dir: Path,
    log_file: Path,
    reason: str = "",
) -> ArchiveEntry:
    """Move *snapshot_path* into *archive_dir* and record the action."""
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / snapshot_path.name
    shutil.move(str(snapshot_path), str(dest))
    entry = ArchiveEntry(
        snapshot=snapshot_path.name,
        archived_at=_now_iso(),
        reason=reason,
        archive_path=str(dest),
    )
    entries = _load_log(log_file)
    entries.append(entry)
    _save_log(log_file, entries)
    return entry


def restore_snapshot(snapshot_name: str, archive_dir: Path, restore_dir: Path, log_file: Path) -> Path:
    """Copy an archived snapshot back to *restore_dir*."""
    src = archive_dir / snapshot_name
    if not src.exists():
        raise FileNotFoundError(f"Archived snapshot not found: {src}")
    restore_dir.mkdir(parents=True, exist_ok=True)
    dest = restore_dir / snapshot_name
    shutil.copy2(str(src), str(dest))
    return dest


def list_archived(log_file: Path) -> List[ArchiveEntry]:
    return _load_log(log_file)
