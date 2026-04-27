"""Snapshot versioning: attach semantic version labels to snapshots."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_STORE = ".envcage_versions.json"


@dataclass
class VersionEntry:
    snapshot: str
    version: str
    label: str = ""
    note: str = ""

    def to_dict(self) -> Dict:
        return {
            "snapshot": self.snapshot,
            "version": self.version,
            "label": self.label,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "VersionEntry":
        return cls(
            snapshot=d["snapshot"],
            version=d["version"],
            label=d.get("label", ""),
            note=d.get("note", ""),
        )


def _load_store(store_path: str) -> Dict[str, VersionEntry]:
    p = Path(store_path)
    if not p.exists():
        return {}
    raw = json.loads(p.read_text())
    return {k: VersionEntry.from_dict(v) for k, v in raw.items()}


def _save_store(store: Dict[str, VersionEntry], store_path: str) -> None:
    Path(store_path).write_text(json.dumps({k: v.to_dict() for k, v in store.items()}, indent=2))


def set_version(
    snapshot: str,
    version: str,
    label: str = "",
    note: str = "",
    store_path: str = _DEFAULT_STORE,
) -> VersionEntry:
    store = _load_store(store_path)
    entry = VersionEntry(snapshot=snapshot, version=version, label=label, note=note)
    store[snapshot] = entry
    _save_store(store, store_path)
    return entry


def get_version(snapshot: str, store_path: str = _DEFAULT_STORE) -> Optional[VersionEntry]:
    return _load_store(store_path).get(snapshot)


def remove_version(snapshot: str, store_path: str = _DEFAULT_STORE) -> bool:
    store = _load_store(store_path)
    if snapshot not in store:
        return False
    del store[snapshot]
    _save_store(store, store_path)
    return True


def list_versions(store_path: str = _DEFAULT_STORE) -> List[VersionEntry]:
    return list(_load_store(store_path).values())


def find_by_version(version: str, store_path: str = _DEFAULT_STORE) -> List[VersionEntry]:
    return [e for e in list_versions(store_path) if e.version == version]
