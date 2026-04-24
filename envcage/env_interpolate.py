"""Interpolate environment variable references within snapshot values.

Supports ${VAR} and $VAR style references.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envcage.snapshot import load, save

_REF_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolateResult:
    env: Dict[str, str]
    resolved: List[str] = field(default_factory=list)
    unresolved: List[str] = field(default_factory=list)

    @property
    def any_unresolved(self) -> bool:
        return bool(self.unresolved)


def _refs_in(value: str) -> List[str]:
    """Return all variable names referenced in *value*."""
    return [
        m.group(1) or m.group(2)
        for m in _REF_PATTERN.finditer(value)
    ]


def interpolate_snapshot(
    env: Dict[str, str],
    context: Optional[Dict[str, str]] = None,
    *,
    strict: bool = False,
) -> InterpolateResult:
    """Resolve variable references in *env* values.

    Parameters
    ----------
    env:
        The snapshot whose values may contain ``${VAR}`` references.
    context:
        Additional variables to resolve against.  Defaults to *env* itself.
    strict:
        If *True*, raise ``KeyError`` when a reference cannot be resolved.
    """
    lookup = dict(env)
    if context:
        lookup.update(context)

    result_env: Dict[str, str] = {}
    resolved_keys: List[str] = []
    unresolved_keys: List[str] = []

    for key, value in env.items():
        refs = _refs_in(value)
        if not refs:
            result_env[key] = value
            continue

        missing = [r for r in refs if r not in lookup]
        if missing:
            if strict:
                raise KeyError(f"Unresolved reference(s) in '{key}': {missing}")
            unresolved_keys.append(key)
            result_env[key] = value
        else:
            def _replace(m: re.Match) -> str:  # noqa: E306
                name = m.group(1) or m.group(2)
                return lookup.get(name, m.group(0))

            result_env[key] = _REF_PATTERN.sub(_replace, value)
            resolved_keys.append(key)

    return InterpolateResult(env=result_env, resolved=resolved_keys, unresolved=unresolved_keys)


def interpolate_snapshot_file(
    src: str | Path,
    dest: str | Path,
    context: Optional[Dict[str, str]] = None,
    *,
    strict: bool = False,
) -> InterpolateResult:
    """Load *src*, interpolate, and save to *dest*."""
    snap = load(str(src))
    result = interpolate_snapshot(snap["env"], context=context, strict=strict)
    snap["env"] = result.env
    save(snap, str(dest))
    return result
