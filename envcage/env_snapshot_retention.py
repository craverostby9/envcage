"""Retention policy management for environment snapshots.

Provides tools to define, apply, and evaluate retention policies that
determine which snapshots should be kept or pruned based on age, count,
or tag-based rules.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class RetentionPolicy:
    """Defines rules for retaining or pruning snapshots."""

    name: str
    max_count: Optional[int] = None          # keep at most N snapshots
    max_age_days: Optional[int] = None       # prune snapshots older than N days
    keep_tagged: bool = True                 # never prune tagged snapshots
    description: str = ""


@dataclass
class RetentionResult:
    """Outcome of evaluating a retention policy against a set of snapshots."""

    policy_name: str
    kept: List[str] = field(default_factory=list)
    pruned: List[str] = field(default_factory=list)
    protected: List[str] = field(default_factory=list)  # tagged / exempt

    @property
    def total_kept(self) -> int:
        return len(self.kept) + len(self.protected)

    @property
    def total_pruned(self) -> int:
        return len(self.pruned)

    def summary(self) -> str:
        lines = [
            f"Policy : {self.policy_name}",
            f"Kept   : {self.total_kept} (including {len(self.protected)} protected)",
            f"Pruned : {self.total_pruned}",
        ]
        if self.pruned:
            for p in self.pruned:
                lines.append(f"  - {p}")
        return "\n".join(lines)


def create_policy(
    name: str,
    max_count: Optional[int] = None,
    max_age_days: Optional[int] = None,
    keep_tagged: bool = True,
    description: str = "",
) -> RetentionPolicy:
    """Create a new RetentionPolicy."""
    return RetentionPolicy(
        name=name,
        max_count=max_count,
        max_age_days=max_age_days,
        keep_tagged=keep_tagged,
        description=description,
    )


def save_policy(policy: RetentionPolicy, path: str) -> None:
    """Persist a RetentionPolicy to a JSON file."""
    data = {
        "name": policy.name,
        "max_count": policy.max_count,
        "max_age_days": policy.max_age_days,
        "keep_tagged": policy.keep_tagged,
        "description": policy.description,
    }
    Path(path).write_text(json.dumps(data, indent=2))


def load_policy(path: str) -> RetentionPolicy:
    """Load a RetentionPolicy from a JSON file."""
    data = json.loads(Path(path).read_text())
    return RetentionPolicy(
        name=data["name"],
        max_count=data.get("max_count"),
        max_age_days=data.get("max_age_days"),
        keep_tagged=data.get("keep_tagged", True),
        description=data.get("description", ""),
    )


def apply_policy(
    policy: RetentionPolicy,
    snapshot_paths: List[str],
    tagged_snapshots: Optional[List[str]] = None,
) -> RetentionResult:
    """Evaluate which snapshots to keep or prune under *policy*.

    Args:
        policy: The retention policy to apply.
        snapshot_paths: Absolute or relative paths to snapshot files,
            ordered oldest-first (ascending mtime is used as tie-breaker).
        tagged_snapshots: Paths of snapshots that carry at least one tag
            and should be protected when ``policy.keep_tagged`` is True.

    Returns:
        A :class:`RetentionResult` describing kept, pruned, and protected paths.
    """
    tagged_set = set(tagged_snapshots or [])
    now = datetime.now(tz=timezone.utc)
    cutoff: Optional[datetime] = (
        now - timedelta(days=policy.max_age_days)
        if policy.max_age_days is not None
        else None
    )

    # Sort by modification time so we prune the oldest first.
    def _mtime(p: str) -> float:
        try:
            return os.path.getmtime(p)
        except OSError:
            return 0.0

    ordered = sorted(snapshot_paths, key=_mtime)

    protected: List[str] = []
    candidates: List[str] = []

    for p in ordered:
        if policy.keep_tagged and p in tagged_set:
            protected.append(p)
        else:
            candidates.append(p)

    # Apply age filter.
    if cutoff is not None:
        age_pruned = []
        age_kept = []
        for p in candidates:
            mtime = datetime.fromtimestamp(_mtime(p), tz=timezone.utc)
            if mtime < cutoff:
                age_pruned.append(p)
            else:
                age_kept.append(p)
        candidates = age_kept
    else:
        age_pruned = []

    # Apply count filter (keep the newest N among remaining candidates).
    count_pruned: List[str] = []
    if policy.max_count is not None and len(candidates) > policy.max_count:
        keep_n = policy.max_count
        count_pruned = candidates[:-keep_n] if keep_n else candidates[:]
        candidates = candidates[-keep_n:] if keep_n else []

    pruned = age_pruned + count_pruned
    kept = candidates

    return RetentionResult(
        policy_name=policy.name,
        kept=kept,
        pruned=pruned,
        protected=protected,
    )
