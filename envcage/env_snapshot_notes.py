"""Snapshot notes: attach and retrieve freeform notes for snapshots."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_NOTES_FILE = ".envcage_notes.json"


def _load_store(notes_file: str) -> Dict[str, List[str]]:
    p = Path(notes_file)
    if not p.exists():
        return {}
    with p.open() as fh:
        return json.load(fh)


def _save_store(store: Dict[str, List[str]], notes_file: str) -> None:
    Path(notes_file).write_text(json.dumps(store, indent=2))


def add_note(
    snapshot_name: str,
    note: str,
    notes_file: str = _DEFAULT_NOTES_FILE,
) -> None:
    """Append a note to the given snapshot."""
    store = _load_store(notes_file)
    store.setdefault(snapshot_name, [])
    store[snapshot_name].append(note)
    _save_store(store, notes_file)


def get_notes(
    snapshot_name: str,
    notes_file: str = _DEFAULT_NOTES_FILE,
) -> List[str]:
    """Return all notes for a snapshot (empty list if none)."""
    return _load_store(notes_file).get(snapshot_name, [])


def remove_notes(
    snapshot_name: str,
    notes_file: str = _DEFAULT_NOTES_FILE,
) -> int:
    """Remove all notes for a snapshot. Returns number of notes removed."""
    store = _load_store(notes_file)
    removed = store.pop(snapshot_name, [])
    _save_store(store, notes_file)
    return len(removed)


def list_noted_snapshots(
    notes_file: str = _DEFAULT_NOTES_FILE,
) -> List[str]:
    """Return sorted list of snapshot names that have at least one note."""
    return sorted(_load_store(notes_file).keys())


def all_notes(
    notes_file: str = _DEFAULT_NOTES_FILE,
) -> Dict[str, List[str]]:
    """Return the full notes store."""
    return dict(_load_store(notes_file))
