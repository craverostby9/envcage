"""env_flatten.py — flatten nested dict structures into dot-notation env keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from envcage.snapshot import load, save


@dataclass
class FlattenResult:
    flattened: dict[str, str]
    original_keys: list[str] = field(default_factory=list)
    produced_keys: list[str] = field(default_factory=list)

    @property
    def total_produced(self) -> int:
        return len(self.produced_keys)

    def summary(self) -> str:
        return (
            f"Flattened {len(self.original_keys)} key(s) "
            f"into {self.total_produced} env key(s)."
        )


def _flatten_dict(
    obj: Any,
    prefix: str = "",
    sep: str = "_",
) -> dict[str, str]:
    """Recursively flatten a nested dict into dot/sep-separated string keys."""
    items: dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}{sep}{k}".upper() if prefix else k.upper()
            items.update(_flatten_dict(v, new_key, sep))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            new_key = f"{prefix}{sep}{i}" if prefix else str(i)
            items.update(_flatten_dict(v, new_key, sep))
    else:
        items[prefix] = str(obj) if obj is not None else ""
    return items


def flatten_env(
    env: dict[str, Any],
    sep: str = "_",
) -> FlattenResult:
    """Flatten an env dict that may contain nested dicts/lists into a flat str->str map."""
    flat: dict[str, str] = {}
    original_keys = list(env.keys())
    for key, value in env.items():
        if isinstance(value, (dict, list, tuple)):
            nested = _flatten_dict(value, prefix=key.upper(), sep=sep)
            flat.update(nested)
        else:
            flat[key.upper()] = str(value) if value is not None else ""
    return FlattenResult(
        flattened=flat,
        original_keys=original_keys,
        produced_keys=list(flat.keys()),
    )


def flatten_snapshot_file(
    src: str,
    dest: str,
    sep: str = "_",
) -> FlattenResult:
    """Load a snapshot from *src*, flatten it, and save to *dest*."""
    snap = load(src)
    env = snap.get("env", {})
    result = flatten_env(env, sep=sep)
    out_snap = {k: v for k, v in snap.items() if k != "env"}
    out_snap["env"] = result.flattened
    save(out_snap, dest)
    return result
