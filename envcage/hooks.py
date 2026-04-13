"""Lifecycle hooks that fire after major envcage operations.

Each hook persists an audit entry and can be extended by users via
environment variables or direct call.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from envcage import audit

_AUDIT_DIR_ENV = "ENVCAGE_AUDIT_DIR"
_DEFAULT_AUDIT_DIR = ".envcage"


def _default_audit_path() -> str:
    base = os.environ.get(_AUDIT_DIR_ENV, _DEFAULT_AUDIT_DIR)
    return str(Path(base) / "audit.jsonl")


def after_snapshot(path: str, env_keys: list[str]) -> None:
    """Hook called after a snapshot is saved."""
    audit.record(
        operation="snapshot",
        details={"path": path, "key_count": len(env_keys)},
        audit_path=_default_audit_path(),
    )


def after_diff(path_a: str, path_b: str, has_changes: bool) -> None:
    """Hook called after a diff is computed."""
    audit.record(
        operation="diff",
        details={"path_a": path_a, "path_b": path_b, "has_changes": has_changes},
        audit_path=_default_audit_path(),
    )


def after_validate(path: str, is_valid: bool, missing: list[str]) -> None:
    """Hook called after a snapshot is validated."""
    audit.record(
        operation="validate",
        details={"path": path, "is_valid": is_valid, "missing": missing},
        audit_path=_default_audit_path(),
    )


def after_merge(paths: list[str], conflict_count: int) -> None:
    """Hook called after snapshots are merged."""
    audit.record(
        operation="merge",
        details={"paths": paths, "conflict_count": conflict_count},
        audit_path=_default_audit_path(),
    )


def after_template(operation: str, template_path: str, details: dict[str, Any] | None = None) -> None:
    """Hook called after any template operation."""
    audit.record(
        operation=f"template:{operation}",
        details={"template_path": template_path, **(details or {})},
        audit_path=_default_audit_path(),
    )
