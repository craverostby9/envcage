"""Integration helpers: auto-record baseline after snapshot commands."""

from __future__ import annotations

from typing import Optional

from envcage.baseline import set_baseline, drift_from_baseline, list_baselines
from envcage.diff import has_changes

_BASELINE_FILE = ".envcage_baseline.json"


def auto_set_baseline(
    label: str,
    snapshot_path: str,
    baseline_file: str = _BASELINE_FILE,
) -> None:
    """Convenience wrapper used by hooks to set a baseline automatically."""
    set_baseline(label, snapshot_path, baseline_file)


def drift_summary(
    label: str,
    current_snapshot: dict,
    baseline_file: str = _BASELINE_FILE,
) -> Optional[str]:
    """Return a human-readable drift summary or None if no drift."""
    try:
        result = drift_from_baseline(label, current_snapshot, baseline_file)
    except KeyError:
        return None
    if not has_changes(result):
        return None
    lines = []
    for k in sorted(result.added):
        lines.append(f"  + {k}")
    for k in sorted(result.removed):
        lines.append(f"  - {k}")
    for k in sorted(result.changed):
        old, new = result.changed[k]
        lines.append(f"  ~ {k}: {old!r} -> {new!r}")
    return "\n".join(lines)


def baselines_for_snapshot(
    snapshot_path: str,
    baseline_file: str = _BASELINE_FILE,
) -> list:
    """Return all labels that point to *snapshot_path*."""
    store = list_baselines(baseline_file)
    return [label for label, path in store.items() if path == snapshot_path]
