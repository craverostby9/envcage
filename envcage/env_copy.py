"""env_copy.py — copy/clone a snapshot with optional key filtering."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from envcage.snapshot import load, save


@dataclass
class CopyResult:
    source: str
    destination: str
    keys_copied: list[str] = field(default_factory=list)
    keys_skipped: list[str] = field(default_factory=list)

    @property
    def total_copied(self) -> int:
        return len(self.keys_copied)


def copy_snapshot(
    source_env: dict,
    *,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> tuple[dict, CopyResult]:
    """Return a filtered copy of *source_env* and a CopyResult."""
    include_set = set(include) if include is not None else None
    exclude_set = set(exclude) if exclude is not None else set()

    copied: dict = {}
    skipped: list[str] = []

    for key, value in source_env.items():
        if include_set is not None and key not in include_set:
            skipped.append(key)
            continue
        if key in exclude_set:
            skipped.append(key)
            continue
        copied[key] = value

    result = CopyResult(
        source="<dict>",
        destination="<dict>",
        keys_copied=sorted(copied),
        keys_skipped=sorted(skipped),
    )
    return copy.deepcopy(copied), result


def copy_snapshot_file(
    source_path: str | Path,
    dest_path: str | Path,
    *,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> CopyResult:
    """Load *source_path*, filter, and write to *dest_path*."""
    source_snap = load(str(source_path))
    source_env: dict = source_snap.get("env", {})

    new_env, result = copy_snapshot(
        source_env, include=include, exclude=exclude
    )

    dest_snap = copy.deepcopy(source_snap)
    dest_snap["env"] = new_env
    save(dest_snap, str(dest_path))

    result.source = str(source_path)
    result.destination = str(dest_path)
    return result
