"""env_diff_report.py — Generate structured diff reports between multiple snapshot pairs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envcage.diff import diff_snapshots, DiffResult
from envcage.snapshot import load


@dataclass
class DiffReportEntry:
    label: str
    source: str
    target: str
    result: DiffResult

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "source": self.source,
            "target": self.target,
            "added": list(self.result.added),
            "removed": list(self.result.removed),
            "changed": [
                {"key": k, "before": b, "after": a}
                for k, (b, a) in self.result.changed.items()
            ],
            "has_changes": bool(
                self.result.added or self.result.removed or self.result.changed
            ),
        }


@dataclass
class DiffReport:
    entries: List[DiffReportEntry] = field(default_factory=list)

    def any_changes(self) -> bool:
        return any(
            e.result.added or e.result.removed or e.result.changed
            for e in self.entries
        )

    def summary(self) -> str:
        lines = []
        for e in self.entries:
            status = "CHANGED" if (e.result.added or e.result.removed or e.result.changed) else "IDENTICAL"
            lines.append(
                f"[{status}] {e.label}: +{len(e.result.added)} "
                f"-{len(e.result.removed)} ~{len(e.result.changed)}"
            )
        return "\n".join(lines) if lines else "No entries."

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}


def build_report(
    pairs: List[Dict[str, str]],
    snap_dir: Optional[str] = None,
) -> DiffReport:
    """Build a DiffReport from a list of {label, source, target} dicts."""
    report = DiffReport()
    base = Path(snap_dir) if snap_dir else Path(".")
    for pair in pairs:
        label = pair.get("label", f"{pair['source']} -> {pair['target']}")
        src = load(str(base / pair["source"]))
        tgt = load(str(base / pair["target"]))
        result = diff_snapshots(src["env"], tgt["env"])
        report.entries.append(
            DiffReportEntry(label=label, source=pair["source"], target=pair["target"], result=result)
        )
    return report


def save_report(report: DiffReport, path: str) -> None:
    Path(path).write_text(json.dumps(report.to_dict(), indent=2))


def load_report(path: str) -> dict:
    return json.loads(Path(path).read_text())
