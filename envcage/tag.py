"""Tag snapshots with labels for easier organization and retrieval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_TAG_FILE = ".envcage_tags.json"


def _load_tag_store(tag_file: str = DEFAULT_TAG_FILE) -> Dict[str, List[str]]:
    """Load the tag store from disk, returning empty dict if not found."""
    path = Path(tag_file)
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def _save_tag_store(store: Dict[str, List[str]], tag_file: str = DEFAULT_TAG_FILE) -> None:
    """Persist the tag store to disk."""
    with open(tag_file, "w") as f:
        json.dump(store, f, indent=2)


def add_tag(snapshot_name: str, tag: str, tag_file: str = DEFAULT_TAG_FILE) -> None:
    """Add a tag to a snapshot. Duplicate tags are silently ignored."""
    store = _load_tag_store(tag_file)
    tags = store.setdefault(snapshot_name, [])
    if tag not in tags:
        tags.append(tag)
        tags.sort()
    _save_tag_store(store, tag_file)


def remove_tag(snapshot_name: str, tag: str, tag_file: str = DEFAULT_TAG_FILE) -> None:
    """Remove a tag from a snapshot. No-op if tag does not exist."""
    store = _load_tag_store(tag_file)
    if snapshot_name in store:
        store[snapshot_name] = [t for t in store[snapshot_name] if t != tag]
        if not store[snapshot_name]:
            del store[snapshot_name]
        _save_tag_store(store, tag_file)


def get_tags(snapshot_name: str, tag_file: str = DEFAULT_TAG_FILE) -> List[str]:
    """Return the list of tags for a snapshot."""
    store = _load_tag_store(tag_file)
    return list(store.get(snapshot_name, []))


def find_by_tag(tag: str, tag_file: str = DEFAULT_TAG_FILE) -> List[str]:
    """Return all snapshot names that carry the given tag."""
    store = _load_tag_store(tag_file)
    return sorted(name for name, tags in store.items() if tag in tags)


def list_all_tags(tag_file: str = DEFAULT_TAG_FILE) -> Dict[str, List[str]]:
    """Return the full tag store as a dict."""
    return _load_tag_store(tag_file)
