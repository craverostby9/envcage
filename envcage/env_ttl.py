"""TTL (time-to-live) tracking for snapshots.

Allows snapshots to be marked with an expiry timestamp and queried
for freshness or expiration.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_TTL_FILE = ".envcage_ttl.json"


@dataclass
class TTLEntry:
    snapshot: str
    expires_at: str  # ISO-8601
    note: str = ""

    def to_dict(self) -> dict:
        return {"snapshot": self.snapshot, "expires_at": self.expires_at, "note": self.note}

    @staticmethod
    def from_dict(d: dict) -> "TTLEntry":
        return TTLEntry(snapshot=d["snapshot"], expires_at=d["expires_at"], note=d.get("note", ""))

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(tz=timezone.utc)
        expiry = datetime.fromisoformat(self.expires_at)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return now >= expiry

    def seconds_remaining(self, now: Optional[datetime] = None) -> float:
        now = now or datetime.now(tz=timezone.utc)
        expiry = datetime.fromisoformat(self.expires_at)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return max(0.0, (expiry - now).total_seconds())


def _load_store(ttl_file: str) -> Dict[str, dict]:
    p = Path(ttl_file)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_store(store: Dict[str, dict], ttl_file: str) -> None:
    Path(ttl_file).write_text(json.dumps(store, indent=2))


def set_ttl(
    snapshot: str,
    seconds: float,
    note: str = "",
    ttl_file: str = _DEFAULT_TTL_FILE,
    now: Optional[datetime] = None,
) -> TTLEntry:
    now = now or datetime.now(tz=timezone.utc)
    expires_at = (now + timedelta(seconds=seconds)).isoformat()
    entry = TTLEntry(snapshot=snapshot, expires_at=expires_at, note=note)
    store = _load_store(ttl_file)
    store[snapshot] = entry.to_dict()
    _save_store(store, ttl_file)
    return entry


def get_ttl(snapshot: str, ttl_file: str = _DEFAULT_TTL_FILE) -> Optional[TTLEntry]:
    store = _load_store(ttl_file)
    raw = store.get(snapshot)
    return TTLEntry.from_dict(raw) if raw else None


def remove_ttl(snapshot: str, ttl_file: str = _DEFAULT_TTL_FILE) -> bool:
    store = _load_store(ttl_file)
    if snapshot not in store:
        return False
    del store[snapshot]
    _save_store(store, ttl_file)
    return True


def list_ttl(ttl_file: str = _DEFAULT_TTL_FILE) -> List[TTLEntry]:
    store = _load_store(ttl_file)
    return [TTLEntry.from_dict(v) for v in store.values()]


def expired_snapshots(
    ttl_file: str = _DEFAULT_TTL_FILE,
    now: Optional[datetime] = None,
) -> List[TTLEntry]:
    return [e for e in list_ttl(ttl_file) if e.is_expired(now)]
