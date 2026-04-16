"""Rename keys across a snapshot, producing a new snapshot with updated key names."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envcage.snapshot import load, save


@dataclass
class RenameResult:
    renamed: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    skipped: List[str] = field(default_factory=list)         # requested but not found
    snapshot: Dict = field(default_factory=dict)


def rename_keys(
    snapshot: Dict,
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
) -> RenameResult:
    """Return a new snapshot with keys renamed according to *mapping*.

    Args:
        snapshot: source snapshot dict (must contain an ``env`` sub-dict).
        mapping: ``{old_key: new_key}`` pairs.
        overwrite: if *True*, silently replace an existing key that shares
                   the new name; otherwise the rename is skipped.
    """
    env: Dict[str, str] = dict(snapshot.get("env", {}))
    renamed: Dict[str, str] = {}
    skipped: List[str] = []

    for old, new in mapping.items():
        if old not in env:
            skipped.append(old)
            continue
        if new in env and not overwrite:
            skipped.append(old)
            continue
        env[new] = env.pop(old)
        renamed[old] = new

    new_snapshot = {**snapshot, "env": env}
    return RenameResult(renamed=renamed, skipped=skipped, snapshot=new_snapshot)


def rename_snapshot_file(
    src: str,
    dest: str,
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
) -> RenameResult:
    """Load *src*, rename keys, save result to *dest*."""
    snapshot = load(src)
    result = rename_keys(snapshot, mapping, overwrite=overwrite)
    save(result.snapshot, dest)
    return result
