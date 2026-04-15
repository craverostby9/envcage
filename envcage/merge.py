"""Merge two or more environment snapshots into a single snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envcage.snapshot import load, save


@dataclass
class MergeResult:
    """Result of merging two or more snapshots."""

    merged: Dict[str, str]
    conflicts: Dict[str, List[str]] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


def merge_snapshots(
    snapshots: List[Dict[str, str]],
    strategy: str = "last",
    sources: Optional[List[str]] = None,
) -> MergeResult:
    """Merge a list of environment snapshot dicts.

    Args:
        snapshots: List of snapshot dicts to merge.
        strategy: Conflict resolution strategy.
            - "last": last snapshot wins (default)
            - "first": first snapshot wins
        sources: Optional list of source labels for tracking.

    Returns:
        MergeResult with merged env and any conflicts detected.

    Raises:
        ValueError: If an unsupported strategy is provided.
    """
    if strategy not in ("last", "first"):
        raise ValueError(
            f"Unknown merge strategy {strategy!r}. Expected 'last' or 'first'."
        )

    if not snapshots:
        return MergeResult(merged={}, sources=sources or [])

    merged: Dict[str, str] = {}
    conflicts: Dict[str, List[str]] = {}

    for snapshot in snapshots:
        env = snapshot.get("env", snapshot)
        for key, value in env.items():
            if key in merged and merged[key] != value:
                if key not in conflicts:
                    conflicts[key] = [merged[key]]
                conflicts[key].append(value)
            if strategy == "first" and key in merged:
                continue
            merged[key] = value

    return MergeResult(
        merged=merged,
        conflicts=conflicts,
        sources=sources or [],
    )


def merge_snapshot_files(
    paths: List[str],
    strategy: str = "last",
    output_path: Optional[str] = None,
) -> MergeResult:
    """Load snapshots from files and merge them.

    Args:
        paths: List of snapshot file paths to merge.
        strategy: Conflict resolution strategy ("last" or "first").
        output_path: If provided, save the merged snapshot to this path.

    Returns:
        MergeResult with merged env and any conflicts detected.

    Raises:
        ValueError: If fewer than two paths are provided.
    """
    if len(paths) < 2:
        raise ValueError(
            f"At least two snapshot files are required to merge, got {len(paths)}."
        )

    snapshots = [load(p) for p in paths]
    result = merge_snapshots(snapshots, strategy=strategy, sources=paths)

    if output_path is not None:
        save({"env": result.merged}, output_path)

    return result
