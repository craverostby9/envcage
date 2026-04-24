"""Generate structured comparison reports across multiple snapshots."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envcage.compare import CompareReport, compare_snapshots
from envcage.snapshot import load


@dataclass
class CompareReportEntry:
    key: str
    values: Dict[str, Optional[str]]  # snapshot_name -> value
    consistent: bool

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "values": self.values,
            "consistent": self.consistent,
        }


@dataclass
class MultiCompareReport:
    snapshot_names: List[str]
    entries: List[CompareReportEntry] = field(default_factory=list)

    @property
    def any_inconsistencies(self) -> bool:
        return any(not e.consistent for e in self.entries)

    @property
    def inconsistent_keys(self) -> List[str]:
        return [e.key for e in self.entries if not e.consistent]

    def summary(self) -> str:
        total = len(self.entries)
        bad = len(self.inconsistent_keys)
        if bad == 0:
            return f"All {total} key(s) consistent across {len(self.snapshot_names)} snapshot(s)."
        return (
            f"{bad}/{total} key(s) inconsistent across "
            f"{len(self.snapshot_names)} snapshot(s): {', '.join(self.inconsistent_keys)}"
        )

    def to_dict(self) -> dict:
        return {
            "snapshot_names": self.snapshot_names,
            "entries": [e.to_dict() for e in self.entries],
            "any_inconsistencies": self.any_inconsistencies,
            "summary": self.summary(),
        }


def build_multi_compare_report(
    snapshots: Dict[str, dict],
) -> MultiCompareReport:
    """Build a per-key comparison report from a name->env mapping."""
    names = list(snapshots.keys())
    all_keys: set = set()
    for env in snapshots.values():
        all_keys.update(env.get("env", {}).keys())

    entries: List[CompareReportEntry] = []
    for key in sorted(all_keys):
        values = {name: snapshots[name].get("env", {}).get(key) for name in names}
        unique_vals = set(v for v in values.values() if v is not None)
        consistent = len(unique_vals) <= 1 and all(
            key in snapshots[name].get("env", {}) for name in names
        )
        entries.append(CompareReportEntry(key=key, values=values, consistent=consistent))

    return MultiCompareReport(snapshot_names=names, entries=entries)


def build_multi_compare_report_from_files(
    snapshot_files: List[str],
) -> MultiCompareReport:
    """Load snapshot files and build a comparison report."""
    snapshots: Dict[str, dict] = {}
    for path in snapshot_files:
        snap = load(path)
        snapshots[Path(path).name] = snap
    return build_multi_compare_report(snapshots)


def save_report(report: MultiCompareReport, output_path: str) -> None:
    Path(output_path).write_text(json.dumps(report.to_dict(), indent=2))
