"""Track and query snapshot history with metadata."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


_DEFAULT_HISTORY_PATH = ".envcage_history.json"


@dataclass
class HistoryEntry:
    snapshot_name: str
    path: str
    timestamp: str
    tags: List[str]
    note: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            snapshot_name=data["snapshot_name"],
            path=data["path"],
            timestamp=data["timestamp"],
            tags=data.get("tags", []),
            note=data.get("note", ""),
        )


def _load_history(history_path: str) -> List[HistoryEntry]:
    p = Path(history_path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return [HistoryEntry.from_dict(e) for e in raw]


def _save_history(entries: List[HistoryEntry], history_path: str) -> None:
    Path(history_path).write_text(
        json.dumps([e.to_dict() for e in entries], indent=2),
        encoding="utf-8",
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_snapshot(
    snapshot_name: str,
    path: str,
    tags: Optional[List[str]] = None,
    note: str = "",
    history_path: str = _DEFAULT_HISTORY_PATH,
) -> HistoryEntry:
    entries = _load_history(history_path)
    entry = HistoryEntry(
        snapshot_name=snapshot_name,
        path=path,
        timestamp=_now_iso(),
        tags=sorted(set(tags or [])),
        note=note,
    )
    entries.append(entry)
    _save_history(entries, history_path)
    return entry


def load_history(history_path: str = _DEFAULT_HISTORY_PATH) -> List[HistoryEntry]:
    return _load_history(history_path)


def find_by_tag(tag: str, history_path: str = _DEFAULT_HISTORY_PATH) -> List[HistoryEntry]:
    return [e for e in _load_history(history_path) if tag in e.tags]


def find_by_name(name: str, history_path: str = _DEFAULT_HISTORY_PATH) -> List[HistoryEntry]:
    return [e for e in _load_history(history_path) if e.snapshot_name == name]


def clear_history(history_path: str = _DEFAULT_HISTORY_PATH) -> None:
    _save_history([], history_path)
