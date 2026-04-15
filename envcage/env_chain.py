"""env_chain.py — ordered chain of snapshots with cascading key resolution.

A chain defines a priority-ordered list of snapshot files. When resolving
a key, the first snapshot in the chain that contains the key wins.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envcage.snapshot import load


@dataclass
class EnvChain:
    name: str
    description: str
    snapshots: List[str] = field(default_factory=list)  # ordered, highest priority first


# ---------- serialisation ----------

def _to_dict(chain: EnvChain) -> dict:
    return {
        "name": chain.name,
        "description": chain.description,
        "snapshots": chain.snapshots,
    }


def _from_dict(data: dict) -> EnvChain:
    return EnvChain(
        name=data["name"],
        description=data.get("description", ""),
        snapshots=data.get("snapshots", []),
    )


# ---------- persistence ----------

def save_chain(chain: EnvChain, path: str) -> None:
    Path(path).write_text(json.dumps(_to_dict(chain), indent=2))


def load_chain(path: str) -> EnvChain:
    return _from_dict(json.loads(Path(path).read_text()))


# ---------- factory ----------

def create_chain(
    name: str,
    snapshots: Optional[List[str]] = None,
    description: str = "",
) -> EnvChain:
    return EnvChain(
        name=name,
        description=description,
        snapshots=list(snapshots or []),
    )


# ---------- resolution ----------

def resolve(chain: EnvChain) -> Dict[str, str]:
    """Merge snapshots in priority order; first occurrence of a key wins."""
    merged: Dict[str, str] = {}
    for snap_path in reversed(chain.snapshots):  # lowest priority first
        snap = load(snap_path)
        merged.update(snap.get("env", {}))
    return merged


def resolve_key(chain: EnvChain, key: str) -> Optional[str]:
    """Return the value for *key* from the highest-priority snapshot that has it."""
    for snap_path in chain.snapshots:
        snap = load(snap_path)
        env = snap.get("env", {})
        if key in env:
            return env[key]
    return None


def source_of(chain: EnvChain, key: str) -> Optional[str]:
    """Return the snapshot file path that provides *key*, or None."""
    for snap_path in chain.snapshots:
        snap = load(snap_path)
        if key in snap.get("env", {}):
            return snap_path
    return None
