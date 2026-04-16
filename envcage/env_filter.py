"""Filter snapshot keys by pattern, prefix, or sensitivity."""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from envcage.redact import is_sensitive


def filter_by_pattern(
    env: Dict[str, str],
    pattern: str,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = re.compile(pattern, flags)
    return {k: v for k, v in env.items() if compiled.search(k)}


def filter_by_prefix(
    env: Dict[str, str],
    prefixes: List[str],
    case_sensitive: bool = False,
) -> Dict[str, str]:
    def matches(key: str) -> bool:
        for p in prefixes:
            a, b = (key, p) if case_sensitive else (key.upper(), p.upper())
            if a.startswith(b):
                return True
        return False

    return {k: v for k, v in env.items() if matches(k)}


def filter_sensitive(env: Dict[str, str]) -> Dict[str, str]:
    return {k: v for k, v in env.items() if is_sensitive(k)}


def filter_non_sensitive(env: Dict[str, str]) -> Dict[str, str]:
    return {k: v for k, v in env.items() if not is_sensitive(k)}


def filter_empty_values(env: Dict[str, str]) -> Dict[str, str]:
    return {k: v for k, v in env.items() if not v}


def filter_snapshot(
    env: Dict[str, str],
    pattern: Optional[str] = None,
    prefixes: Optional[List[str]] = None,
    sensitive_only: bool = False,
    non_sensitive_only: bool = False,
    empty_only: bool = False,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    result = dict(env)
    if pattern:
        result = filter_by_pattern(result, pattern, case_sensitive)
    if prefixes:
        result = filter_by_prefix(result, prefixes, case_sensitive)
    if sensitive_only:
        result = filter_sensitive(result)
    elif non_sensitive_only:
        result = filter_non_sensitive(result)
    if empty_only:
        result = filter_empty_values(result)
    return result
