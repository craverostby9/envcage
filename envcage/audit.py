"""Audit log for snapshot operations — tracks when snapshots were created, compared, or validated."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_AUDIT_FILE = ".envcage_audit.json"


@dataclass
class AuditEntry:
    timestamp: str
    action: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            timestamp=data["timestamp"],
            action=data["action"],
            details=data.get("details", {}),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record(action: str, details: Optional[dict] = None, audit_path: str = DEFAULT_AUDIT_FILE) -> AuditEntry:
    """Append an audit entry to the audit log file and return it."""
    entry = AuditEntry(timestamp=_now_iso(), action=action, details=details or {})
    entries = load(audit_path)
    entries.append(entry)
    path = Path(audit_path)
    path.write_text(json.dumps([e.to_dict() for e in entries], indent=2))
    return entry


def load(audit_path: str = DEFAULT_AUDIT_FILE) -> List[AuditEntry]:
    """Load all audit entries from the audit log file."""
    path = Path(audit_path)
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [AuditEntry.from_dict(d) for d in data]


def clear(audit_path: str = DEFAULT_AUDIT_FILE) -> None:
    """Remove all audit log entries."""
    path = Path(audit_path)
    if path.exists():
        path.unlink()


def summary(audit_path: str = DEFAULT_AUDIT_FILE) -> str:
    """Return a human-readable summary of audit entries."""
    entries = load(audit_path)
    if not entries:
        return "No audit entries found."
    lines = [f"Audit log ({len(entries)} entries):"]
    for e in entries:
        detail_str = ", ".join(f"{k}={v}" for k, v in e.details.items())
        lines.append(f"  [{e.timestamp}] {e.action}" + (f" — {detail_str}" if detail_str else ""))
    return "\n".join(lines)
