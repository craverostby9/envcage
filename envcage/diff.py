"""Diff two environment snapshots and report added, removed, and changed keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envcage.snapshot import load


@dataclass
class DiffResult:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines: List[str] = []
        for key, value in sorted(self.added.items()):
            lines.append(f"+ {key}={value}")
        for key, value in sorted(self.removed.items()):
            lines.append(f"- {key}={value}")
        for key, (old, new) in sorted(self.changed.items()):
            lines.append(f"~ {key}: {old!r} -> {new!r}")
        return "\n".join(lines) if lines else "No differences found."


def diff_snapshots(
    old: Dict[str, str],
    new: Dict[str, str],
    keys: Optional[List[str]] = None,
) -> DiffResult:
    """Compare two env dicts and return a DiffResult.

    Args:
        old: The baseline environment snapshot.
        new: The environment snapshot to compare against.
        keys: Optional list of keys to restrict the diff to.

    Returns:
        A DiffResult describing the differences.
    """
    if keys is not None:
        old = {k: v for k, v in old.items() if k in keys}
        new = {k: v for k, v in new.items() if k in keys}

    old_keys = set(old)
    new_keys = set(new)

    result = DiffResult()
    result.added = {k: new[k] for k in new_keys - old_keys}
    result.removed = {k: old[k] for k in old_keys - new_keys}
    result.changed = {
        k: (old[k], new[k])
        for k in old_keys & new_keys
        if old[k] != new[k]
    }
    return result


def diff_snapshot_files(old_path: str, new_path: str, keys: Optional[List[str]] = None) -> DiffResult:
    """Load two snapshot files from disk and diff them."""
    old_snap = load(old_path)
    new_snap = load(new_path)
    return diff_snapshots(old_snap, new_snap, keys=keys)
