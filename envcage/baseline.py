"""Baseline management: mark a snapshot as the baseline for drift detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envcage.diff import diff_snapshots, DiffResult
from envcage.snapshot import load

_DEFAULT_BASELINE_FILE = ".envcage_baseline.json"


def _load_store(baseline_file: str) -> dict:
    p = Path(baseline_file)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_store(store: dict, baseline_file: str) -> None:
    Path(baseline_file).write_text(json.dumps(store, indent=2))


def set_baseline(
    label: str,
    snapshot_path: str,
    baseline_file: str = _DEFAULT_BASELINE_FILE,
) -> None:
    """Associate *label* with *snapshot_path* as the baseline."""
    store = _load_store(baseline_file)
    store[label] = str(snapshot_path)
    _save_store(store, baseline_file)


def get_baseline(
    label: str,
    baseline_file: str = _DEFAULT_BASELINE_FILE,
) -> Optional[str]:
    """Return the snapshot path registered under *label*, or None."""
    return _load_store(baseline_file).get(label)


def remove_baseline(
    label: str,
    baseline_file: str = _DEFAULT_BASELINE_FILE,
) -> bool:
    """Remove the baseline entry for *label*. Returns True if it existed."""
    store = _load_store(baseline_file)
    if label not in store:
        return False
    del store[label]
    _save_store(store, baseline_file)
    return True


def list_baselines(baseline_file: str = _DEFAULT_BASELINE_FILE) -> dict:
    """Return all label -> snapshot_path mappings."""
    return dict(_load_store(baseline_file))


def drift_from_baseline(
    label: str,
    current_snapshot: dict,
    baseline_file: str = _DEFAULT_BASELINE_FILE,
) -> DiffResult:
    """Diff *current_snapshot* against the baseline registered under *label*."""
    path = get_baseline(label, baseline_file)
    if path is None:
        raise KeyError(f"No baseline registered for label '{label}'")
    base_snap = load(path)
    return diff_snapshots(base_snap, current_snapshot)
