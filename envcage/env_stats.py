"""env_stats.py — Compute statistics over a snapshot or set of snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envcage.redact import is_sensitive
from envcage.snapshot import load


@dataclass
class SnapshotStats:
    total_keys: int = 0
    sensitive_keys: int = 0
    empty_values: int = 0
    unique_values: int = 0
    duplicate_values: int = 0
    longest_key: str = ""
    longest_value_key: str = ""
    key_lengths: Dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "total_keys": self.total_keys,
            "sensitive_keys": self.sensitive_keys,
            "empty_values": self.empty_values,
            "unique_values": self.unique_values,
            "duplicate_values": self.duplicate_values,
            "longest_key": self.longest_key,
            "longest_value_key": self.longest_value_key,
        }


def compute_stats(env: Dict[str, str]) -> SnapshotStats:
    """Compute statistics for a given env dict."""
    stats = SnapshotStats()
    stats.total_keys = len(env)

    value_counts: Dict[str, int] = {}
    max_key_len = 0
    max_val_len = -1

    for key, value in env.items():
        if is_sensitive(key):
            stats.sensitive_keys += 1
        if value == "":
            stats.empty_values += 1

        value_counts[value] = value_counts.get(value, 0) + 1

        if len(key) > max_key_len:
            max_key_len = len(key)
            stats.longest_key = key

        if len(value) > max_val_len:
            max_val_len = len(value)
            stats.longest_value_key = key

        stats.key_lengths[key] = len(key)

    stats.unique_values = sum(1 for c in value_counts.values() if c == 1)
    stats.duplicate_values = sum(1 for c in value_counts.values() if c > 1)

    return stats


def stats_from_file(path: str) -> SnapshotStats:
    """Load a snapshot file and return its stats."""
    snap = load(path)
    return compute_stats(snap.get("env", {}))


def summary(stats: SnapshotStats) -> str:
    """Return a human-readable summary of stats."""
    lines: List[str] = [
        f"Total keys      : {stats.total_keys}",
        f"Sensitive keys  : {stats.sensitive_keys}",
        f"Empty values    : {stats.empty_values}",
        f"Unique values   : {stats.unique_values}",
        f"Duplicate values: {stats.duplicate_values}",
        f"Longest key     : {stats.longest_key!r}",
        f"Longest value in: {stats.longest_value_key!r}",
    ]
    return "\n".join(lines)
