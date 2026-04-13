"""Redaction utilities for masking sensitive environment variable values."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

# Default patterns that indicate a key holds sensitive data
DEFAULT_SENSITIVE_PATTERNS: List[str] = [
    r"(?i).*secret.*",
    r"(?i).*password.*",
    r"(?i).*passwd.*",
    r"(?i).*token.*",
    r"(?i).*api_key.*",
    r"(?i).*apikey.*",
    r"(?i).*private_key.*",
    r"(?i).*auth.*",
    r"(?i).*credential.*",
]

REDACT_PLACEHOLDER = "***REDACTED***"


def is_sensitive(key: str, patterns: Optional[List[str]] = None) -> bool:
    """Return True if the key name matches any sensitive pattern."""
    patterns = patterns if patterns is not None else DEFAULT_SENSITIVE_PATTERNS
    return any(re.fullmatch(pattern, key) for pattern in patterns)


def redact_snapshot(
    snapshot: Dict[str, str],
    patterns: Optional[List[str]] = None,
    placeholder: str = REDACT_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of snapshot with sensitive values replaced by placeholder."""
    return {
        key: (placeholder if is_sensitive(key, patterns) else value)
        for key, value in snapshot.items()
    }


def redacted_keys(
    snapshot: Dict[str, str],
    patterns: Optional[List[str]] = None,
) -> List[str]:
    """Return a sorted list of keys that would be redacted in the given snapshot."""
    return sorted(key for key in snapshot if is_sensitive(key, patterns))
