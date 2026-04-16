"""Transform snapshot keys/values: rename prefixes, uppercase keys, strip values."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from envcage.snapshot import load, save


@dataclass
class TransformResult:
    original: Dict[str, str]
    transformed: Dict[str, str]
    changes: List[str] = field(default_factory=list)


def uppercase_keys(env: Dict[str, str]) -> TransformResult:
    changes = [k for k in env if k != k.upper()]
    transformed = {k.upper(): v for k, v in env.items()}
    return TransformResult(original=env, transformed=transformed, changes=changes)


def strip_values(env: Dict[str, str]) -> TransformResult:
    changes = [k for k, v in env.items() if v != v.strip()]
    transformed = {k: v.strip() for k, v in env.items()}
    return TransformResult(original=env, transformed=transformed, changes=changes)


def replace_prefix(env: Dict[str, str], old_prefix: str, new_prefix: str) -> TransformResult:
    changes = []
    transformed = {}
    for k, v in env.items():
        if k.startswith(old_prefix):
            new_key = new_prefix + k[len(old_prefix):]
            transformed[new_key] = v
            changes.append(k)
        else:
            transformed[k] = v
    return TransformResult(original=env, transformed=transformed, changes=changes)


def apply_transforms(env: Dict[str, str], *, uppercase: bool = False,
                     strip: bool = False,
                     replace_prefix_pair: tuple[str, str] | None = None) -> TransformResult:
    result = TransformResult(original=env, transformed=dict(env))
    if uppercase:
        r = uppercase_keys(result.transformed)
        result.transformed = r.transformed
        result.changes.extend(r.changes)
    if strip:
        r = strip_values(result.transformed)
        result.transformed = r.transformed
        result.changes.extend(r.changes)
    if replace_prefix_pair:
        old, new = replace_prefix_pair
        r = replace_prefix(result.transformed, old, new)
        result.transformed = r.transformed
        result.changes.extend(r.changes)
    return result


def transform_snapshot_file(src: str, dest: str, **kwargs) -> TransformResult:
    snap = load(src)
    env = snap.get("env", {})
    result = apply_transforms(env, **kwargs)
    snap["env"] = result.transformed
    save(snap, dest)
    return result
