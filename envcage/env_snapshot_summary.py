"""env_snapshot_summary.py — Generate a human-readable summary report for one or more snapshots."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envcage.redact import redact_snapshot
from envcage.env_stats import compute_stats
from envcage.snapshot import load


@dataclass
class SnapshotSummaryEntry:
    name: str
    path: str
    total_keys: int
    sensitive_keys: int
    empty_values: int
    duplicate_values: int
    tags: List[str] = field(default_factory=list)
    note: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "path": self.path,
            "total_keys": self.total_keys,
            "sensitive_keys": self.sensitive_keys,
            "empty_values": self.empty_values,
            "duplicate_values": self.duplicate_values,
            "tags": self.tags,
            "note": self.note,
        }


@dataclass
class SnapshotSummaryReport:
    entries: List[SnapshotSummaryEntry] = field(default_factory=list)

    @property
    def total_snapshots(self) -> int:
        return len(self.entries)

    @property
    def total_keys(self) -> int:
        return sum(e.total_keys for e in self.entries)

    def summary(self) -> str:
        lines = [f"Snapshot Summary ({self.total_snapshots} snapshots, {self.total_keys} total keys)"]
        for e in self.entries:
            lines.append(
                f"  {e.name}: {e.total_keys} keys, "
                f"{e.sensitive_keys} sensitive, "
                f"{e.empty_values} empty, "
                f"{e.duplicate_values} duplicate values"
            )
            if e.tags:
                lines.append(f"    tags: {', '.join(e.tags)}")
            if e.note:
                lines.append(f"    note: {e.note}")
        return "\n".join(lines)


def summarise_snapshot_file(
    path: str,
    tags: Optional[List[str]] = None,
    note: Optional[str] = None,
) -> SnapshotSummaryEntry:
    snap = load(path)
    env = snap.get("env", {})
    stats = compute_stats(env)
    return SnapshotSummaryEntry(
        name=Path(path).stem,
        path=path,
        total_keys=stats.total_keys,
        sensitive_keys=stats.sensitive_keys,
        empty_values=stats.empty_values,
        duplicate_values=stats.duplicate_values,
        tags=tags or [],
        note=note,
    )


def build_report(paths: List[str]) -> SnapshotSummaryReport:
    entries = [summarise_snapshot_file(p) for p in paths]
    return SnapshotSummaryReport(entries=entries)
