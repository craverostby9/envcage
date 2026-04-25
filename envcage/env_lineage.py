"""Track parent-child lineage relationships between snapshots."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_LINEAGE_FILE = ".envcage_lineage.json"


@dataclass
class LineageNode:
    snapshot: str
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "snapshot": self.snapshot,
            "parent": self.parent,
            "children": sorted(self.children),
            "note": self.note,
        }

    @staticmethod
    def from_dict(data: dict) -> "LineageNode":
        return LineageNode(
            snapshot=data["snapshot"],
            parent=data.get("parent"),
            children=data.get("children", []),
            note=data.get("note", ""),
        )


def _load_store(lineage_file: str) -> Dict[str, LineageNode]:
    p = Path(lineage_file)
    if not p.exists():
        return {}
    raw = json.loads(p.read_text())
    return {k: LineageNode.from_dict(v) for k, v in raw.items()}


def _save_store(store: Dict[str, LineageNode], lineage_file: str) -> None:
    Path(lineage_file).write_text(
        json.dumps({k: v.to_dict() for k, v in store.items()}, indent=2)
    )


def link_snapshot(
    snapshot: str,
    parent: str,
    note: str = "",
    lineage_file: str = _DEFAULT_LINEAGE_FILE,
) -> LineageNode:
    """Register *snapshot* as a child of *parent*."""
    store = _load_store(lineage_file)

    child_node = store.setdefault(snapshot, LineageNode(snapshot=snapshot))
    child_node.parent = parent
    child_node.note = note

    parent_node = store.setdefault(parent, LineageNode(snapshot=parent))
    if snapshot not in parent_node.children:
        parent_node.children.append(snapshot)

    _save_store(store, lineage_file)
    return child_node


def get_lineage(snapshot: str, lineage_file: str = _DEFAULT_LINEAGE_FILE) -> Optional[LineageNode]:
    """Return the lineage node for *snapshot*, or None if not tracked."""
    return _load_store(lineage_file).get(snapshot)


def ancestors(snapshot: str, lineage_file: str = _DEFAULT_LINEAGE_FILE) -> List[str]:
    """Return ordered list of ancestors, oldest first."""
    store = _load_store(lineage_file)
    result: List[str] = []
    current = snapshot
    seen: set = set()
    while True:
        node = store.get(current)
        if node is None or node.parent is None:
            break
        if node.parent in seen:
            break
        seen.add(node.parent)
        result.append(node.parent)
        current = node.parent
    result.reverse()
    return result


def descendants(snapshot: str, lineage_file: str = _DEFAULT_LINEAGE_FILE) -> List[str]:
    """Return all descendant snapshot names (breadth-first)."""
    store = _load_store(lineage_file)
    result: List[str] = []
    queue = list(store.get(snapshot, LineageNode(snapshot=snapshot)).children)
    seen: set = set()
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        result.append(current)
        node = store.get(current)
        if node:
            queue.extend(node.children)
    return result


def remove_lineage(snapshot: str, lineage_file: str = _DEFAULT_LINEAGE_FILE) -> bool:
    """Remove *snapshot* from the lineage store. Returns True if it existed."""
    store = _load_store(lineage_file)
    if snapshot not in store:
        return False
    node = store.pop(snapshot)
    if node.parent and node.parent in store:
        parent_node = store[node.parent]
        parent_node.children = [c for c in parent_node.children if c != snapshot]
    _save_store(store, lineage_file)
    return True
