"""Compare multiple snapshots side-by-side and produce a structured report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envcage.snapshot import load


@dataclass
class CompareReport:
    """Structured report of a multi-snapshot comparison."""

    labels: List[str]
    # key -> {label: value or None}
    matrix: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)

    @property
    def all_keys(self) -> List[str]:
        return sorted(self.matrix.keys())

    def is_consistent(self, key: str) -> bool:
        """Return True if all snapshots agree on the value for *key*."""
        values = list(self.matrix.get(key, {}).values())
        return len(set(v for v in values if v is not None)) <= 1

    def inconsistent_keys(self) -> List[str]:
        """Return keys whose values differ across at least two snapshots."""
        return [k for k in self.all_keys if not self.is_consistent(k)]

    def missing_in(self, label: str) -> List[str]:
        """Return keys absent from the snapshot identified by *label*."""
        return [
            k
            for k, row in self.matrix.items()
            if row.get(label) is None
        ]


def compare_snapshots(
    snapshots: List[Dict],
    labels: Optional[List[str]] = None,
) -> CompareReport:
    """Compare an ordered list of snapshot dicts.

    Parameters
    ----------
    snapshots:
        List of snapshot dicts (as returned by ``snapshot.load``).
    labels:
        Optional human-readable name for each snapshot.  Defaults to
        ``["snap_0", "snap_1", ...]``.
    """
    if labels is None:
        labels = [f"snap_{i}" for i in range(len(snapshots))]

    if len(labels) != len(snapshots):
        raise ValueError("labels length must match snapshots length")

    matrix: Dict[str, Dict[str, Optional[str]]] = {}

    for label, snap in zip(labels, snapshots):
        env: Dict[str, str] = snap.get("env", {})
        for key, value in env.items():
            matrix.setdefault(key, {label: None for label in labels})
            matrix[key][label] = value

    # Ensure every row has an entry for every label
    for key in matrix:
        for label in labels:
            matrix[key].setdefault(label, None)

    return CompareReport(labels=labels, matrix=matrix)


def compare_snapshot_files(
    paths: List[str],
    labels: Optional[List[str]] = None,
) -> CompareReport:
    """Load snapshot files and compare them."""
    snapshots = [load(p) for p in paths]
    if labels is None:
        labels = list(paths)
    return compare_snapshots(snapshots, labels=labels)
