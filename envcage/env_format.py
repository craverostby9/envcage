"""env_format.py — Detect and report formatting issues in environment variable snapshots."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envcage.snapshot import load

# Patterns considered well-formed
_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*$')
_LEADING_TRAILING_SPACE = re.compile(r'^\s|\s$')
_CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f]')


@dataclass
class FormatIssue:
    key: str
    kind: str  # 'key_case', 'key_chars', 'value_whitespace', 'value_control'
    message: str

    def to_dict(self) -> dict:
        return {"key": self.key, "kind": self.kind, "message": self.message}


@dataclass
class FormatReport:
    issues: List[FormatIssue] = field(default_factory=list)

    @property
    def any_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    def by_kind(self, kind: str) -> List[FormatIssue]:
        return [i for i in self.issues if i.kind == kind]

    def summary(self) -> str:
        if not self.any_issues:
            return "No formatting issues found."
        lines = [f"{self.issue_count} formatting issue(s) found:"]
        for issue in self.issues:
            lines.append(f"  [{issue.kind}] {issue.key}: {issue.message}")
        return "\n".join(lines)


def check_snapshot(env: Dict[str, str]) -> FormatReport:
    """Check a snapshot dict for formatting issues and return a FormatReport."""
    issues: List[FormatIssue] = []

    for key, value in env.items():
        # Key must be uppercase with underscores/digits only
        if not _KEY_PATTERN.match(key):
            if key != key.upper():
                issues.append(FormatIssue(
                    key=key,
                    kind="key_case",
                    message=f"Key '{key}' contains lowercase letters; expected UPPER_SNAKE_CASE.",
                ))
            else:
                issues.append(FormatIssue(
                    key=key,
                    kind="key_chars",
                    message=f"Key '{key}' contains invalid characters (only A-Z, 0-9, _ allowed, must start with a letter).",
                ))

        # Value must not have leading/trailing whitespace
        if _LEADING_TRAILING_SPACE.search(value):
            issues.append(FormatIssue(
                key=key,
                kind="value_whitespace",
                message=f"Value for '{key}' has leading or trailing whitespace.",
            ))

        # Value must not contain control characters
        if _CONTROL_CHARS.search(value):
            issues.append(FormatIssue(
                key=key,
                kind="value_control",
                message=f"Value for '{key}' contains control characters.",
            ))

    return FormatReport(issues=issues)


def check_snapshot_file(path: str) -> FormatReport:
    """Load a snapshot from *path* and return its FormatReport."""
    snap = load(path)
    env: Dict[str, str] = snap.get("env", {})
    return check_snapshot(env)
