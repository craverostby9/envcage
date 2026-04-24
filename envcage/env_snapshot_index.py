"""Snapshot index — maintains a searchable index of snapshot metadata."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class IndexEntry:
    name: str
    path: str
    key_count: int
    tags: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "key_count": self.key_count,
            "tags": self.tags,
            "description": self.description,
        }

    @staticmethod
    def from_dict(d: dict) -> "IndexEntry":
        return IndexEntry(
            name=d["name"],
            path=d["path"],
            key_count=d.get("key_count", 0),
            tags=d.get("tags", []),
            description=d.get("description", ""),
        )


def _load_index(index_file: str) -> Dict[str, IndexEntry]:
    if not os.path.exists(index_file):
        return {}
    with open(index_file, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return {k: IndexEntry.from_dict(v) for k, v in raw.items()}


def _save_index(index_file: str, index: Dict[str, IndexEntry]) -> None:
    with open(index_file, "w", encoding="utf-8") as fh:
        json.dump({k: v.to_dict() for k, v in index.items()}, fh, indent=2)


def index_snapshot(
    name: str,
    path: str,
    key_count: int,
    tags: Optional[List[str]] = None,
    description: str = "",
    index_file: str = ".envcage_index.json",
) -> IndexEntry:
    """Add or update a snapshot entry in the index."""
    store = _load_index(index_file)
    entry = IndexEntry(
        name=name,
        path=path,
        key_count=key_count,
        tags=sorted(set(tags or [])),
        description=description,
    )
    store[name] = entry
    _save_index(index_file, store)
    return entry


def remove_from_index(name: str, index_file: str = ".envcage_index.json") -> bool:
    """Remove a snapshot from the index. Returns True if it existed."""
    store = _load_index(index_file)
    if name not in store:
        return False
    del store[name]
    _save_index(index_file, store)
    return True


def get_index_entry(name: str, index_file: str = ".envcage_index.json") -> Optional[IndexEntry]:
    return _load_index(index_file).get(name)


def list_index(index_file: str = ".envcage_index.json") -> List[IndexEntry]:
    return sorted(_load_index(index_file).values(), key=lambda e: e.name)


def search_index(
    pattern: str,
    index_file: str = ".envcage_index.json",
    case_sensitive: bool = False,
) -> List[IndexEntry]:
    """Return entries whose name or description contains *pattern*."""
    entries = list_index(index_file)
    needle = pattern if case_sensitive else pattern.lower()
    results = []
    for e in entries:
        haystack = (e.name + " " + e.description) if case_sensitive else (e.name + " " + e.description).lower()
        if needle in haystack:
            results.append(e)
    return results
