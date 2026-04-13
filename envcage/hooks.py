"""Lifecycle hooks — automatically record audit entries for snapshot, diff, and validate operations."""

from __future__ import annotations

from typing import Callable, Any

from envcage import audit


def _default_audit_path() -> str:
    return audit.DEFAULT_AUDIT_FILE


def after_snapshot(name: str, path: str, audit_path: str = audit.DEFAULT_AUDIT_FILE) -> None:
    """Record an audit entry after a snapshot is saved."""
    audit.record("snapshot", {"name": name, "path": path}, audit_path=audit_path)


def after_diff(snapshot_a: str, snapshot_b: str, has_changes: bool, audit_path: str = audit.DEFAULT_AUDIT_FILE) -> None:
    """Record an audit entry after a diff is performed."""
    audit.record(
        "diff",
        {"snapshot_a": snapshot_a, "snapshot_b": snapshot_b, "has_changes": has_changes},
        audit_path=audit_path,
    )


def after_validate(
    name: str, passed: bool, missing: list, unexpected: list, audit_path: str = audit.DEFAULT_AUDIT_FILE
) -> None:
    """Record an audit entry after a validation is run."""
    audit.record(
        "validate",
        {
            "name": name,
            "passed": passed,
            "missing_count": len(missing),
            "unexpected_count": len(unexpected),
        },
        audit_path=audit_path,
    )


def after_merge(sources: list, output: str, conflict_count: int, audit_path: str = audit.DEFAULT_AUDIT_FILE) -> None:
    """Record an audit entry after snapshots are merged."""
    audit.record(
        "merge",
        {"sources": sources, "output": output, "conflict_count": conflict_count},
        audit_path=audit_path,
    )


def after_export(name: str, format: str, destination: str, audit_path: str = audit.DEFAULT_AUDIT_FILE) -> None:
    """Record an audit entry after a snapshot is exported."""
    audit.record(
        "export",
        {"name": name, "format": format, "destination": destination},
        audit_path=audit_path,
    )
