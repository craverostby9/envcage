"""Annotation support — attach notes/metadata to snapshot keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

# Store structure: {snapshot_path: {key: annotation}}
AnnotationStore = Dict[str, Dict[str, str]]


def _load_store(annotation_file: str) -> AnnotationStore:
    p = Path(annotation_file)
    if not p.exists():
        return {}
    with p.open() as f:
        return json.load(f)


def _save_store(store: AnnotationStore, annotation_file: str) -> None:
    with open(annotation_file, "w") as f:
        json.dump(store, f, indent=2)


def set_annotation(snapshot_path: str, key: str, note: str, annotation_file: str) -> None:
    """Attach a note to a key within a snapshot."""
    store = _load_store(annotation_file)
    store.setdefault(snapshot_path, {})[key] = note
    _save_store(store, annotation_file)


def get_annotation(snapshot_path: str, key: str, annotation_file: str) -> Optional[str]:
    """Return the note for a key, or None."""
    store = _load_store(annotation_file)
    return store.get(snapshot_path, {}).get(key)


def remove_annotation(snapshot_path: str, key: str, annotation_file: str) -> bool:
    """Remove a note. Returns True if something was removed."""
    store = _load_store(annotation_file)
    removed = store.get(snapshot_path, {}).pop(key, None)
    if removed is not None:
        _save_store(store, annotation_file)
        return True
    return False


def list_annotations(snapshot_path: str, annotation_file: str) -> Dict[str, str]:
    """Return all key->note pairs for a snapshot."""
    store = _load_store(annotation_file)
    return dict(store.get(snapshot_path, {}))


def all_annotations(annotation_file: str) -> AnnotationStore:
    """Return the full annotation store."""
    return _load_store(annotation_file)
