"""Bookmark management for named snapshot references."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_STORE = Path(".envcage") / "bookmarks.json"


@dataclass
class Bookmark:
    name: str
    snapshot_path: str
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Bookmark":
        return cls(
            name=data["name"],
            snapshot_path=data["snapshot_path"],
            description=data.get("description", ""),
        )


def _load_store(store_path: Path) -> Dict[str, dict]:
    if not store_path.exists():
        return {}
    return json.loads(store_path.read_text())


def _save_store(data: Dict[str, dict], store_path: Path) -> None:
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(data, indent=2))


def set_bookmark(
    name: str,
    snapshot_path: str,
    description: str = "",
    store_path: Path = _DEFAULT_STORE,
) -> Bookmark:
    """Create or overwrite a named bookmark."""
    store = _load_store(store_path)
    bm = Bookmark(name=name, snapshot_path=snapshot_path, description=description)
    store[name] = bm.to_dict()
    _save_store(store, store_path)
    return bm


def get_bookmark(name: str, store_path: Path = _DEFAULT_STORE) -> Optional[Bookmark]:
    """Return a bookmark by name, or None if not found."""
    store = _load_store(store_path)
    if name not in store:
        return None
    return Bookmark.from_dict(store[name])


def remove_bookmark(name: str, store_path: Path = _DEFAULT_STORE) -> bool:
    """Remove a bookmark. Returns True if it existed."""
    store = _load_store(store_path)
    if name not in store:
        return False
    del store[name]
    _save_store(store, store_path)
    return True


def list_bookmarks(store_path: Path = _DEFAULT_STORE) -> List[Bookmark]:
    """Return all bookmarks sorted by name."""
    store = _load_store(store_path)
    return [Bookmark.from_dict(v) for v in sorted(store.values(), key=lambda x: x["name"])]
