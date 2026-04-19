"""Split a snapshot into multiple snapshots by prefix or key list."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envcage.snapshot import save, load


@dataclass
class SplitResult:
    parts: Dict[str, Dict[str, str]] = field(default_factory=dict)
    unmatched: Dict[str, str] = field(default_factory=dict)

    @property
    def total_parts(self) -> int:
        return len(self.parts)

    @property
    def total_keys(self) -> int:
        return sum(len(v) for v in self.parts.values()) + len(self.unmatched)


def split_by_prefix(
    env: Dict[str, str],
    prefixes: List[str],
    strip_prefix: bool = False,
) -> SplitResult:
    result = SplitResult(parts={p: {} for p in prefixes})
    for key, value in env.items():
        matched = False
        for prefix in prefixes:
            if key.startswith(prefix):
                out_key = key[len(prefix):] if strip_prefix else key
                result.parts[prefix][out_key] = value
                matched = True
                break
        if not matched:
            result.unmatched[key] = value
    return result


def split_by_keys(
    env: Dict[str, str],
    groups: Dict[str, List[str]],
) -> SplitResult:
    result = SplitResult(parts={name: {} for name in groups})
    assigned: set = set()
    for name, keys in groups.items():
        for key in keys:
            if key in env:
                result.parts[name][key] = env[key]
                assigned.add(key)
    result.unmatched = {k: v for k, v in env.items() if k not in assigned}
    return result


def split_snapshot_file(
    source: str,
    prefixes: Optional[List[str]] = None,
    groups: Optional[Dict[str, List[str]]] = None,
    output_dir: str = ".",
    strip_prefix: bool = False,
) -> SplitResult:
    snap = load(source)
    env = snap["env"]
    if prefixes is not None:
        result = split_by_prefix(env, prefixes, strip_prefix=strip_prefix)
    elif groups is not None:
        result = split_by_keys(env, groups)
    else:
        raise ValueError("Provide either prefixes or groups")
    import os
    for part_name, part_env in result.parts.items():
        safe_name = part_name.rstrip("_").replace("/", "_")
        out_path = os.path.join(output_dir, f"{safe_name}.json")
        save({"env": part_env, "required": []}, out_path)
    return result
