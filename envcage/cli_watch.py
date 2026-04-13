"""CLI helpers for the `envcage watch` sub-command."""

from __future__ import annotations

import os
import sys
from typing import Optional

from envcage.watch import WatchSession, WatchEvent, watch
from envcage.redact import redact_snapshot


def _format_event(event: WatchEvent, redact: bool = False) -> str:
    """Return a human-readable string for a WatchEvent."""
    lines: list[str] = [f"[change detected at t={event.timestamp:.2f}]"]
    diff = event.diff

    added = diff.added
    removed = diff.removed
    changed = diff.changed

    if redact:
        added = redact_snapshot(added)
        removed = redact_snapshot(removed)
        changed = {k: (redact_snapshot({k: v[0]})[k], redact_snapshot({k: v[1]})[k])
                   for k, v in changed.items()}

    for key, val in sorted(added.items()):
        lines.append(f"  + {key}={val}")
    for key, val in sorted(removed.items()):
        lines.append(f"  - {key}={val}")
    for key, (old, new) in sorted(changed.items()):
        lines.append(f"  ~ {key}: {old!r} -> {new!r}")

    return "\n".join(lines)


def cmd_watch(
    required_keys: Optional[list[str]] = None,
    interval: float = 2.0,
    max_events: int = 0,
    redact: bool = True,
    output=None,
) -> int:
    """Entry point for the CLI watch command.

    Returns an exit code (0 = success, 1 = error).
    """
    if output is None:
        output = sys.stdout

    session = WatchSession(
        required_keys=required_keys or [],
        interval=interval,
        max_events=max_events,
    )

    def on_event(event: WatchEvent) -> None:
        print(_format_event(event, redact=redact), file=output, flush=True)

    print(
        f"Watching environment (interval={interval}s) — press Ctrl+C to stop.",
        file=output,
        flush=True,
    )

    try:
        watch(session, callback=on_event, env=None)
    except Exception as exc:  # pragma: no cover
        print(f"Error during watch: {exc}", file=sys.stderr)
        return 1

    print(
        f"Watch ended. {session.event_count()} change event(s) recorded.",
        file=output,
    )
    return 0
