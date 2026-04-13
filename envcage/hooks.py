"""Post-action hooks that record audit entries and apply redaction before output."""

from __future__ import annotations

import os
from typing import Dict, Optional

from envcage import audit
from envcage.redact import redact_snapshot


def _default_audit_path() -> str:
    return os.environ.get("ENVCAGE_AUDIT_FILE", ".envcage_audit.jsonl")


def after_snapshot(
    name: str,
    snapshot: Dict[str, str],
    audit_path: Optional[str] = None,
) -> Dict[str, str]:
    """Record a snapshot audit entry and return a redacted copy of the snapshot."""
    path = audit_path or _default_audit_path()
    audit.record(action="snapshot", details={"name": name}, audit_file=path)
    return redact_snapshot(snapshot)


def after_diff(
    snapshot_a: str,
    snapshot_b: str,
    changed_count: int,
    audit_path: Optional[str] = None,
) -> None:
    """Record a diff audit entry."""
    path = audit_path or _default_audit_path()
    audit.record(
        action="diff",
        details={"from": snapshot_a, "to": snapshot_b, "changed": changed_count},
        audit_file=path,
    )


def after_validate(
    snapshot_name: str,
    passed: bool,
    missing: int,
    audit_path: Optional[str] = None,
) -> None:
    """Record a validate audit entry."""
    path = audit_path or _default_audit_path()
    audit.record(
        action="validate",
        details={"snapshot": snapshot_name, "passed": passed, "missing": missing},
        audit_file=path,
    )


def after_merge(
    sources: list,
    conflicts: int,
    audit_path: Optional[str] = None,
) -> None:
    """Record a merge audit entry."""
    path = audit_path or _default_audit_path()
    audit.record(
        action="merge",
        details={"sources": sources, "conflicts": conflicts},
        audit_file=path,
    )


def after_export(
    snapshot_name: str,
    fmt: str,
    audit_path: Optional[str] = None,
) -> None:
    """Record an export audit entry."""
    path = audit_path or _default_audit_path()
    audit.record(
        action="export",
        details={"snapshot": snapshot_name, "format": fmt},
        audit_file=path,
    )
