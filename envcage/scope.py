"""Scope management: group snapshots under named scopes (e.g. 'production', 'staging')."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_SCOPE_FILE = Path(".envcage") / "scopes.json"


@dataclass
class Scope:
    name: str
    description: str = ""
    snapshots: List[str] = field(default_factory=list)


def _load_store(scope_file: Path) -> Dict[str, dict]:
    if not scope_file.exists():
        return {}
    return json.loads(scope_file.read_text())


def _save_store(store: Dict[str, dict], scope_file: Path) -> None:
    scope_file.parent.mkdir(parents=True, exist_ok=True)
    scope_file.write_text(json.dumps(store, indent=2))


def create_scope(name: str, description: str = "") -> Scope:
    return Scope(name=name, description=description)


def save_scope(scope: Scope, scope_file: Path = _DEFAULT_SCOPE_FILE) -> None:
    store = _load_store(scope_file)
    store[scope.name] = {"description": scope.description, "snapshots": scope.snapshots}
    _save_store(store, scope_file)


def load_scope(name: str, scope_file: Path = _DEFAULT_SCOPE_FILE) -> Optional[Scope]:
    store = _load_store(scope_file)
    if name not in store:
        return None
    entry = store[name]
    return Scope(name=name, description=entry.get("description", ""), snapshots=entry.get("snapshots", []))


def add_snapshot_to_scope(name: str, snapshot_path: str, scope_file: Path = _DEFAULT_SCOPE_FILE) -> Scope:
    scope = load_scope(name, scope_file) or Scope(name=name)
    if snapshot_path not in scope.snapshots:
        scope.snapshots.append(snapshot_path)
        scope.snapshots.sort()
    save_scope(scope, scope_file)
    return scope


def remove_snapshot_from_scope(name: str, snapshot_path: str, scope_file: Path = _DEFAULT_SCOPE_FILE) -> Scope:
    scope = load_scope(name, scope_file) or Scope(name=name)
    scope.snapshots = [s for s in scope.snapshots if s != snapshot_path]
    save_scope(scope, scope_file)
    return scope


def list_scopes(scope_file: Path = _DEFAULT_SCOPE_FILE) -> List[str]:
    return sorted(_load_store(scope_file).keys())


def delete_scope(name: str, scope_file: Path = _DEFAULT_SCOPE_FILE) -> bool:
    store = _load_store(scope_file)
    if name not in store:
        return False
    del store[name]
    _save_store(store, scope_file)
    return True
