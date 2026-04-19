"""Masking: partially obscure env var values for safe display."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envcage.redact import is_sensitive

_DEFAULT_VISIBLE = 4
_MASK_CHAR = "*"


@dataclass
class MaskResult:
    original_keys: List[str]
    masked_keys: List[str]
    env: Dict[str, str]


def mask_value(value: str, visible: int = _DEFAULT_VISIBLE, char: str = _MASK_CHAR) -> str:
    """Return value with all but the last *visible* characters replaced."""
    if len(value) <= visible:
        return char * len(value)
    return char * (len(value) - visible) + value[-visible:]


def mask_snapshot(
    snapshot: Dict[str, str],
    patterns: Optional[List[str]] = None,
    visible: int = _DEFAULT_VISIBLE,
    char: str = _MASK_CHAR,
) -> MaskResult:
    """Return a copy of *snapshot* with sensitive values masked."""
    masked_keys: List[str] = []
    result: Dict[str, str] = {}
    for key, value in snapshot.items():
        if is_sensitive(key, patterns):
            result[key] = mask_value(value, visible=visible, char=char)
            masked_keys.append(key)
        else:
            result[key] = value
    return MaskResult(
        original_keys=list(snapshot.keys()),
        masked_keys=sorted(masked_keys),
        env=result,
    )


def mask_snapshot_file(
    path: str,
    patterns: Optional[List[str]] = None,
    visible: int = _DEFAULT_VISIBLE,
) -> MaskResult:
    from envcage.snapshot import load
    snap = load(path)
    return mask_snapshot(snap["env"], patterns=patterns, visible=visible)
