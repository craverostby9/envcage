"""Integration helpers that fire notifications from envcage lifecycle events."""
from __future__ import annotations

from typing import List, Optional

from envcage.notify import (
    NotificationConfig,
    NotificationEvent,
    load_notify_config,
    notify,
)

_DEFAULT_CONFIG = ".envcage_notify.json"


def _load(config_path: Optional[str]) -> List[NotificationConfig]:
    return load_notify_config(config_path or _DEFAULT_CONFIG)


def notify_snapshot(snapshot_file: str, config_path: Optional[str] = None) -> None:
    """Fire a 'snapshot' notification after a snapshot is saved."""
    event = NotificationEvent(
        event_type="snapshot",
        message=f"Snapshot saved: {snapshot_file}",
        metadata={"file": snapshot_file},
    )
    notify(event, _load(config_path))


def notify_diff(source: str, target: str, has_changes: bool, config_path: Optional[str] = None) -> None:
    """Fire a 'diff' notification after a diff is computed."""
    change_str = "changes detected" if has_changes else "no changes"
    event = NotificationEvent(
        event_type="diff",
        message=f"Diff {source} → {target}: {change_str}",
        metadata={"source": source, "target": target, "has_changes": has_changes},
    )
    notify(event, _load(config_path))


def notify_validate(snapshot_file: str, passed: bool, config_path: Optional[str] = None) -> None:
    """Fire a 'validate' notification after validation."""
    result = "passed" if passed else "failed"
    event = NotificationEvent(
        event_type="validate",
        message=f"Validation {result} for {snapshot_file}",
        metadata={"file": snapshot_file, "passed": passed},
    )
    notify(event, _load(config_path))


def notify_promote(source: str, target: str, config_path: Optional[str] = None) -> None:
    """Fire a 'promote' notification after a snapshot is promoted."""
    event = NotificationEvent(
        event_type="promote",
        message=f"Promoted {source} → {target}",
        metadata={"source": source, "target": target},
    )
    notify(event, _load(config_path))
