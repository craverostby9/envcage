"""Timeline: ordered view of snapshot history with diff summaries between steps."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envcage.snapshot import load
from envcage.diff import diff_snapshots


@dataclass
class TimelineStep:
    index: int
    snapshot_path: str
    label: Optional[str]
    added: List[str]
    removed: List[str]
    changed: List[str]

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "snapshot_path": self.snapshot_path,
            "label": self.label,
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
        }


@dataclass
class Timeline:
    steps: List[TimelineStep] = field(default_factory=list)

    def total_steps(self) -> int:
        return len(self.steps)

    def any_changes(self) -> bool:
        return any(
            s.added or s.removed or s.changed for s in self.steps
        )


def build_timeline(
    snapshot_paths: List[str],
    labels: Optional[List[Optional[str]]] = None,
) -> Timeline:
    """Build a Timeline by diffing consecutive snapshots."""
    if labels is None:
        labels = [None] * len(snapshot_paths)

    steps: List[TimelineStep] = []

    for i, path in enumerate(snapshot_paths):
        if i == 0:
            env = load(path)
            steps.append(
                TimelineStep(
                    index=0,
                    snapshot_path=path,
                    label=labels[0],
                    added=list(env.get("env", {}).keys()),
                    removed=[],
                    changed=[],
                )
            )
        else:
            prev = load(snapshot_paths[i - 1])
            curr = load(path)
            result = diff_snapshots(prev, curr)
            steps.append(
                TimelineStep(
                    index=i,
                    snapshot_path=path,
                    label=labels[i],
                    added=list(result.added.keys()),
                    removed=list(result.removed.keys()),
                    changed=list(result.changed.keys()),
                )
            )

    return Timeline(steps=steps)


def save_timeline(timeline: Timeline, path: str) -> None:
    data = {"steps": [s.to_dict() for s in timeline.steps]}
    Path(path).write_text(json.dumps(data, indent=2))


def load_timeline(path: str) -> Timeline:
    data = json.loads(Path(path).read_text())
    steps = [
        TimelineStep(
            index=s["index"],
            snapshot_path=s["snapshot_path"],
            label=s.get("label"),
            added=s["added"],
            removed=s["removed"],
            changed=s["changed"],
        )
        for s in data["steps"]
    ]
    return Timeline(steps=steps)
