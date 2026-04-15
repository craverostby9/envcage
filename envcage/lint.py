"""Lint environment variable snapshots for style and convention issues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envcage.snapshot import load

SCREAMING_SNAKE = re.compile(r'^[A-Z][A-Z0-9_]*$')
EMPTY_VALUE_WARN = True
MAX_VALUE_LENGTH = 1024


@dataclass
class LintIssue:
    key: str
    severity: str  # 'error' | 'warning' | 'info'
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintReport:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'error']

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'warning']

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def lint_snapshot(
    env: Dict[str, str],
    *,
    allow_empty: bool = False,
    max_length: int = MAX_VALUE_LENGTH,
    require_screaming_snake: bool = True,
) -> LintReport:
    """Run lint checks on an env dict and return a LintReport."""
    report = LintReport()

    for key, value in env.items():
        if require_screaming_snake and not SCREAMING_SNAKE.match(key):
            report.issues.append(LintIssue(
                key=key,
                severity='warning',
                message=f"Key '{key}' does not follow SCREAMING_SNAKE_CASE convention.",
            ))

        if not allow_empty and value.strip() == '':
            report.issues.append(LintIssue(
                key=key,
                severity='warning',
                message=f"Key '{key}' has an empty or blank value.",
            ))

        if len(value) > max_length:
            report.issues.append(LintIssue(
                key=key,
                severity='error',
                message=(
                    f"Key '{key}' value exceeds max length "
                    f"({len(value)} > {max_length})."
                ),
            ))

    return report


def lint_snapshot_file(
    path: str,
    *,
    allow_empty: bool = False,
    max_length: int = MAX_VALUE_LENGTH,
    require_screaming_snake: bool = True,
) -> LintReport:
    """Load a snapshot file and lint it."""
    snap = load(path)
    env: Dict[str, str] = snap.get('env', {})
    return lint_snapshot(
        env,
        allow_empty=allow_empty,
        max_length=max_length,
        require_screaming_snake=require_screaming_snake,
    )


def summary(report: LintReport) -> str:
    """Return a human-readable summary of a LintReport."""
    if not report.issues:
        return 'No lint issues found.'
    lines = [str(issue) for issue in report.issues]
    lines.append(
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)."
    )
    return '\n'.join(lines)
