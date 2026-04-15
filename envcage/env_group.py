"""env_group.py — group snapshots under named logical groups (e.g. 'production', 'staging')."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class EnvGroup:
    name: str
    description: str = ""
    snapshots: List[str] = field(default_factory=list)


# ---------- persistence ----------

def _load_store(store_path: Path) -> Dict[str, dict]:
    if store_path.exists():
        return json.loads(store_path.read_text())
    return {}


def _save_store(store_path: Path, data: Dict[str, dict]) -> None:
    store_path.write_text(json.dumps(data, indent=2))


# ---------- public API ----------

def create_group(name: str, description: str = "", snapshots: Optional[List[str]] = None) -> EnvGroup:
    """Return a new EnvGroup (not persisted)."""
    return EnvGroup(
        name=name,
        description=description,
        snapshots=sorted(set(snapshots or [])),
    )


def save_group(group: EnvGroup, store_path: Path) -> None:
    """Persist *group* to the JSON store at *store_path*."""
    data = _load_store(store_path)
    data[group.name] = {
        "description": group.description,
        "snapshots": group.snapshots,
    }
    _save_store(store_path, data)


def load_group(name: str, store_path: Path) -> Optional[EnvGroup]:
    """Return the named group or *None* if it does not exist."""
    data = _load_store(store_path)
    entry = data.get(name)
    if entry is None:
        return None
    return EnvGroup(name=name, description=entry.get("description", ""), snapshots=entry.get("snapshots", []))


def list_groups(store_path: Path) -> List[str]:
    """Return sorted list of group names in *store_path*."""
    return sorted(_load_store(store_path).keys())


def add_snapshot_to_group(name: str, snapshot_path: str, store_path: Path) -> EnvGroup:
    """Add *snapshot_path* to group *name*, creating the group if absent."""
    group = load_group(name, store_path) or EnvGroup(name=name)
    if snapshot_path not in group.snapshots:
        group.snapshots = sorted(group.snapshots + [snapshot_path])
    save_group(group, store_path)
    return group


def remove_snapshot_from_group(name: str, snapshot_path: str, store_path: Path) -> Optional[EnvGroup]:
    """Remove *snapshot_path* from group *name*. Returns *None* if group missing."""
    group = load_group(name, store_path)
    if group is None:
        return None
    group.snapshots = [s for s in group.snapshots if s != snapshot_path]
    save_group(group, store_path)
    return group


def delete_group(name: str, store_path: Path) -> bool:
    """Delete group *name*. Returns *True* if it existed."""
    data = _load_store(store_path)
    if name not in data:
        return False
    del data[name]
    _save_store(store_path, data)
    return True
