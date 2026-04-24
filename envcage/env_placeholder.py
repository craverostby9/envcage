"""env_placeholder.py – detect and report unresolved placeholder values in snapshots.

A placeholder is a value that looks like it was never substituted, e.g.
  - ${SOME_VAR}
  - {{SOME_VAR}}
  - <SOME_VAR>
  - __SOME_VAR__
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Patterns that indicate an unresolved placeholder
_PLACEHOLDER_PATTERNS: List[re.Pattern] = [
    re.compile(r"\$\{[^}]+\}"),       # ${VAR}
    re.compile(r"\{\{[^}]+\}\}"),     # {{VAR}}
    re.compile(r"<[A-Z_][A-Z0-9_]*>"),  # <VAR>
    re.compile(r"__[A-Z_][A-Z0-9_]*__"),  # __VAR__
]


@dataclass
class PlaceholderMatch:
    key: str
    value: str
    pattern: str

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "pattern": self.pattern}


@dataclass
class PlaceholderReport:
    matches: List[PlaceholderMatch] = field(default_factory=list)

    @property
    def any_found(self) -> bool:
        return len(self.matches) > 0

    @property
    def total(self) -> int:
        return len(self.matches)

    def affected_keys(self) -> List[str]:
        return [m.key for m in self.matches]

    def summary(self) -> str:
        if not self.any_found:
            return "No unresolved placeholders detected."
        lines = [f"Found {self.total} unresolved placeholder(s):"]
        for m in self.matches:
            lines.append(f"  {m.key}={m.value!r}  (matched: {m.pattern})")
        return "\n".join(lines)


def is_placeholder(value: str, patterns: Optional[List[re.Pattern]] = None) -> bool:
    """Return True if *value* looks like an unresolved placeholder."""
    for pat in (patterns or _PLACEHOLDER_PATTERNS):
        if pat.search(value):
            return True
    return False


def find_placeholders(
    env: Dict[str, str],
    patterns: Optional[List[re.Pattern]] = None,
) -> PlaceholderReport:
    """Scan *env* and return a PlaceholderReport with all unresolved entries."""
    pats = patterns or _PLACEHOLDER_PATTERNS
    matches: List[PlaceholderMatch] = []
    for key, value in env.items():
        for pat in pats:
            if pat.search(value):
                matches.append(PlaceholderMatch(key=key, value=value, pattern=pat.pattern))
                break  # one match per key is enough
    return PlaceholderReport(matches=matches)


def find_placeholders_in_file(
    path: str | Path,
    patterns: Optional[List[re.Pattern]] = None,
) -> PlaceholderReport:
    """Load a snapshot JSON file and scan it for unresolved placeholders."""
    data = json.loads(Path(path).read_text())
    env: Dict[str, str] = data.get("env", data)
    return find_placeholders(env, patterns=patterns)
