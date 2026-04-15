"""Integration helpers that connect lint results with hooks and audit."""

from __future__ import annotations

from typing import Dict, List

from envcage.lint import LintReport, lint_snapshot, lint_snapshot_file, summary
from envcage.hooks import _default_audit_path
from envcage import audit


def lint_and_audit(
    path: str,
    *,
    allow_empty: bool = False,
    max_length: int = 1024,
    require_screaming_snake: bool = True,
    audit_path: str | None = None,
) -> LintReport:
    """Lint a snapshot file and record the result in the audit log."""
    report = lint_snapshot_file(
        path,
        allow_empty=allow_empty,
        max_length=max_length,
        require_screaming_snake=require_screaming_snake,
    )
    _audit_path = audit_path or _default_audit_path()
    audit.record(
        action='lint',
        snapshot=path,
        detail={
            'passed': report.passed,
            'errors': len(report.errors),
            'warnings': len(report.warnings),
        },
        audit_path=_audit_path,
    )
    return report


def batch_lint_summary(paths: List[str], **lint_kwargs) -> Dict[str, str]:
    """Lint multiple snapshot files and return a path -> summary mapping."""
    results: Dict[str, str] = {}
    for path in paths:
        report = lint_snapshot_file(path, **lint_kwargs)
        results[path] = summary(report)
    return results


def any_lint_errors(paths: List[str], **lint_kwargs) -> bool:
    """Return True if any of the given snapshot files have lint errors."""
    for path in paths:
        report = lint_snapshot_file(path, **lint_kwargs)
        if not report.passed:
            return True
    return False
