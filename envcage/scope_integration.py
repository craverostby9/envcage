"""Integration helpers: resolve and operate on snapshots via scope membership."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from envcage.scope import list_scopes, load_scope
from envcage.snapshot import load as load_snapshot

_DEFAULT_SCOPE_FILE = Path(".envcage") / "scopes.json"


def snapshots_in_scope(name: str, scope_file: Path = _DEFAULT_SCOPE_FILE) -> List[str]:
    """Return list of snapshot paths belonging to *name*."""
    scope = load_scope(name, scope_file)
    if scope is None:
        return []
    return list(scope.snapshots)


def snapshot_in_scope(snapshot_path: str, scope_name: str, scope_file: Path = _DEFAULT_SCOPE_FILE) -> bool:
    """Return True if *snapshot_path* is a member of *scope_name*."""
    return snapshot_path in snapshots_in_scope(scope_name, scope_file)


def scopes_for_snapshot(snapshot_path: str, scope_file: Path = _DEFAULT_SCOPE_FILE) -> List[str]:
    """Return all scope names that contain *snapshot_path*."""
    result = []
    for name in list_scopes(scope_file):
        scope = load_scope(name, scope_file)
        if scope and snapshot_path in scope.snapshots:
            result.append(name)
    return sorted(result)


def load_all_in_scope(name: str, scope_file: Path = _DEFAULT_SCOPE_FILE) -> Dict[str, dict]:
    """Load and return all snapshot dicts keyed by file path for *name*.

    Snapshots that cannot be read are silently skipped.
    """
    envs: Dict[str, dict] = {}
    for path_str in snapshots_in_scope(name, scope_file):
        p = Path(path_str)
        try:
            envs[path_str] = load_snapshot(p)
        except Exception:
            pass
    return envs


def scope_summary(scope_file: Path = _DEFAULT_SCOPE_FILE) -> str:
    """Return a human-readable summary of all scopes and their snapshot counts."""
    names = list_scopes(scope_file)
    if not names:
        return "No scopes defined."
    lines = []
    for name in names:
        scope = load_scope(name, scope_file)
        count = len(scope.snapshots) if scope else 0
        desc = f" — {scope.description}" if scope and scope.description else ""
        lines.append(f"{name}{desc}: {count} snapshot(s)")
    return "\n".join(lines)
