"""env_lock.py — Lock a snapshot to prevent accidental modification or overwrite."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_LOCK_FILE = ".envcage_locks.json"


@dataclass
class LockEntry:
    snapshot: str
    locked_at: str
    reason: str = ""


def _load_store(lock_file: str) -> Dict[str, dict]:
    p = Path(lock_file)
    if not p.exists():
        return {}
    with p.open() as f:
        return json.load(f)


def _save_store(store: Dict[str, dict], lock_file: str) -> None:
    with open(lock_file, "w") as f:
        json.dump(store, f, indent=2)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def lock_snapshot(
    snapshot: str,
    reason: str = "",
    lock_file: str = _DEFAULT_LOCK_FILE,
) -> LockEntry:
    """Mark *snapshot* as locked. Returns the new LockEntry."""
    store = _load_store(lock_file)
    entry = LockEntry(snapshot=snapshot, locked_at=_now_iso(), reason=reason)
    store[snapshot] = {"snapshot": snapshot, "locked_at": entry.locked_at, "reason": reason}
    _save_store(store, lock_file)
    return entry


def unlock_snapshot(snapshot: str, lock_file: str = _DEFAULT_LOCK_FILE) -> bool:
    """Remove the lock for *snapshot*. Returns True if it was locked."""
    store = _load_store(lock_file)
    if snapshot not in store:
        return False
    del store[snapshot]
    _save_store(store, lock_file)
    return True


def is_locked(snapshot: str, lock_file: str = _DEFAULT_LOCK_FILE) -> bool:
    """Return True if *snapshot* is currently locked."""
    return snapshot in _load_store(lock_file)


def get_lock(snapshot: str, lock_file: str = _DEFAULT_LOCK_FILE) -> Optional[LockEntry]:
    """Return the LockEntry for *snapshot*, or None."""
    store = _load_store(lock_file)
    raw = store.get(snapshot)
    if raw is None:
        return None
    return LockEntry(**raw)


def list_locks(lock_file: str = _DEFAULT_LOCK_FILE) -> List[LockEntry]:
    """Return all active locks."""
    store = _load_store(lock_file)
    return [LockEntry(**v) for v in store.values()]
