"""Rollback support: restore a previous snapshot as the active environment file."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envcage.snapshot import load, save
from envcage.history import record_snapshot


@dataclass
class RollbackRecord:
    label: str
    source: str          # path of the snapshot being restored
    destination: str     # path where it was written
    env: dict = field(default_factory=dict)


def to_dict(r: RollbackRecord) -> dict:
    return {
        "label": r.label,
        "source": r.source,
        "destination": r.destination,
        "env": r.env,
    }


def from_dict(d: dict) -> RollbackRecord:
    return RollbackRecord(
        label=d["label"],
        source=d["source"],
        destination=d["destination"],
        env=d.get("env", {}),
    )


def _load_log(log_file: Path) -> list[dict]:
    if not log_file.exists():
        return []
    return json.loads(log_file.read_text())


def _save_log(log_file: Path, entries: list[dict]) -> None:
    log_file.write_text(json.dumps(entries, indent=2))


def rollback(
    source_path: str,
    destination_path: str,
    label: str = "rollback",
    log_file: Optional[str] = None,
    history_file: Optional[str] = None,
) -> RollbackRecord:
    """Restore *source_path* snapshot to *destination_path*."""
    src = Path(source_path)
    dst = Path(destination_path)

    env = load(str(src))
    save(env, str(dst))

    record = RollbackRecord(
        label=label,
        source=str(src),
        destination=str(dst),
        env=env,
    )

    if log_file:
        lf = Path(log_file)
        entries = _load_log(lf)
        entries.append(to_dict(record))
        _save_log(lf, entries)

    if history_file:
        record_snapshot(str(dst), tags=[label], history_file=history_file)

    return record


def rollback_log(log_file: str) -> list[RollbackRecord]:
    """Return all rollback records from *log_file*."""
    return [from_dict(d) for d in _load_log(Path(log_file))]
