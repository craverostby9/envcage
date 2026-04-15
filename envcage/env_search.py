"""Search and filter environment variable keys/values across snapshots."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envcage.snapshot import load


@dataclass
class SearchMatch:
    snapshot_path: str
    key: str
    value: str

    def to_dict(self) -> dict:
        return {
            "snapshot": self.snapshot_path,
            "key": self.key,
            "value": self.value,
        }


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.matches)

    def snapshots_matched(self) -> List[str]:
        seen = []
        for m in self.matches:
            if m.snapshot_path not in seen:
                seen.append(m.snapshot_path)
        return seen


def search_snapshot(
    snapshot: Dict[str, str],
    pattern: str,
    *,
    search_values: bool = False,
    case_sensitive: bool = False,
    snapshot_path: str = "",
) -> List[SearchMatch]:
    """Search a single snapshot dict for keys (and optionally values) matching pattern."""
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        raise ValueError(f"Invalid search pattern: {pattern!r}") from exc

    matches = []
    env = snapshot.get("env", snapshot)
    for key, value in env.items():
        key_hit = compiled.search(key) is not None
        value_hit = search_values and compiled.search(str(value)) is not None
        if key_hit or value_hit:
            matches.append(SearchMatch(snapshot_path=snapshot_path, key=key, value=value))
    return matches


def search_snapshot_files(
    paths: List[str],
    pattern: str,
    *,
    search_values: bool = False,
    case_sensitive: bool = False,
) -> SearchResult:
    """Search across multiple snapshot files."""
    result = SearchResult()
    for path in paths:
        snapshot = load(path)
        matches = search_snapshot(
            snapshot,
            pattern,
            search_values=search_values,
            case_sensitive=case_sensitive,
            snapshot_path=path,
        )
        result.matches.extend(matches)
    return result


def summary(result: SearchResult) -> str:
    if result.total == 0:
        return "No matches found."
    lines = [f"Found {result.total} match(es) across {len(result.snapshots_matched())} snapshot(s):"]
    for m in result.matches:
        lines.append(f"  [{m.snapshot_path}] {m.key}={m.value}")
    return "\n".join(lines)
