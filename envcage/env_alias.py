"""env_alias.py — map logical alias names to snapshot file paths."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_ALIAS_FILE = ".envcage_aliases.json"


@dataclass
class AliasStore:
    aliases: Dict[str, str] = field(default_factory=dict)


def _load_store(alias_file: str = _DEFAULT_ALIAS_FILE) -> AliasStore:
    p = Path(alias_file)
    if not p.exists():
        return AliasStore()
    data = json.loads(p.read_text())
    return AliasStore(aliases=data.get("aliases", {}))


def _save_store(store: AliasStore, alias_file: str = _DEFAULT_ALIAS_FILE) -> None:
    Path(alias_file).write_text(json.dumps({"aliases": store.aliases}, indent=2))


def set_alias(name: str, snapshot_path: str, alias_file: str = _DEFAULT_ALIAS_FILE) -> None:
    """Create or overwrite an alias pointing to *snapshot_path*."""
    store = _load_store(alias_file)
    store.aliases[name] = snapshot_path
    _save_store(store, alias_file)


def remove_alias(name: str, alias_file: str = _DEFAULT_ALIAS_FILE) -> bool:
    """Remove an alias.  Returns True if it existed, False otherwise."""
    store = _load_store(alias_file)
    if name not in store.aliases:
        return False
    del store.aliases[name]
    _save_store(store, alias_file)
    return True


def resolve_alias(name: str, alias_file: str = _DEFAULT_ALIAS_FILE) -> Optional[str]:
    """Return the snapshot path for *name*, or None if unknown."""
    return _load_store(alias_file).aliases.get(name)


def list_aliases(alias_file: str = _DEFAULT_ALIAS_FILE) -> Dict[str, str]:
    """Return all alias → path mappings."""
    return dict(_load_store(alias_file).aliases)


def aliases_for_snapshot(snapshot_path: str, alias_file: str = _DEFAULT_ALIAS_FILE) -> List[str]:
    """Return every alias that points to *snapshot_path*."""
    store = _load_store(alias_file)
    return sorted(k for k, v in store.aliases.items() if v == snapshot_path)
