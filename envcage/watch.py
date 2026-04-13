"""Watch for environment variable changes between two points in time."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from envcage.snapshot import capture
from envcage.diff import diff_snapshots, DiffResult


@dataclass
class WatchEvent:
    """Emitted when a change is detected during a watch session."""

    timestamp: float
    diff: DiffResult

    def has_changes(self) -> bool:
        return bool(self.diff.added or self.diff.removed or self.diff.changed)


@dataclass
class WatchSession:
    """Tracks state across a watch loop."""

    required_keys: list[str] = field(default_factory=list)
    interval: float = 2.0
    max_events: int = 0  # 0 = unlimited
    _events: list[WatchEvent] = field(default_factory=list, init=False)

    def events(self) -> list[WatchEvent]:
        return list(self._events)

    def event_count(self) -> int:
        return len(self._events)


def watch(
    session: WatchSession,
    callback: Callable[[WatchEvent], None],
    env: Optional[dict] = None,
) -> WatchSession:
    """Poll the environment at a fixed interval and invoke callback on changes.

    Runs until max_events is reached (if set) or KeyboardInterrupt.
    Returns the completed WatchSession.
    """
    baseline = capture(required_keys=session.required_keys, env=env)

    try:
        while True:
            time.sleep(session.interval)
            current = capture(required_keys=session.required_keys, env=env)
            result = diff_snapshots(baseline, current)

            event = WatchEvent(timestamp=time.time(), diff=result)
            if event.has_changes():
                session._events.append(event)
                callback(event)
                baseline = current

            if session.max_events and session.event_count() >= session.max_events:
                break
    except KeyboardInterrupt:
        pass

    return session


def watch_once(
    required_keys: list[str] | None = None,
    before: dict | None = None,
    after: dict | None = None,
) -> WatchEvent:
    """Compare two explicit snapshots and return a WatchEvent."""
    before_snap = capture(required_keys=required_keys or [], env=before)
    after_snap = capture(required_keys=required_keys or [], env=after)
    result = diff_snapshots(before_snap, after_snap)
    return WatchEvent(timestamp=time.time(), diff=result)
