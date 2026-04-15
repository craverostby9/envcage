"""Notification hooks for envcage events."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class NotificationConfig:
    """Configuration for a notification channel."""
    channel: str          # 'stdout', 'file', 'webhook'
    target: str           # path or URL depending on channel
    events: List[str] = field(default_factory=list)  # empty = all events
    enabled: bool = True


@dataclass
class NotificationEvent:
    """A notification payload."""
    event_type: str
    message: str
    metadata: Dict = field(default_factory=dict)


_HANDLERS: Dict[str, Callable[[NotificationEvent, NotificationConfig], None]] = {}


def _register_handler(channel: str):
    def decorator(fn):
        _HANDLERS[channel] = fn
        return fn
    return decorator


@_register_handler("stdout")
def _handle_stdout(event: NotificationEvent, config: NotificationConfig) -> None:
    print(f"[envcage:{event.event_type}] {event.message}")


@_register_handler("file")
def _handle_file(event: NotificationEvent, config: NotificationConfig) -> None:
    path = Path(config.target)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps({"type": event.event_type, "message": event.message, **event.metadata}) + "\n")


@_register_handler("webhook")
def _handle_webhook(event: NotificationEvent, config: NotificationConfig) -> None:
    try:
        import urllib.request
        payload = json.dumps({"type": event.event_type, "message": event.message}).encode()
        req = urllib.request.Request(config.target, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:  # noqa: BLE001
        print(f"[envcage:notify] webhook failed: {exc}")


def notify(event: NotificationEvent, configs: List[NotificationConfig]) -> None:
    """Dispatch *event* to all matching enabled configs."""
    for cfg in configs:
        if not cfg.enabled:
            continue
        if cfg.events and event.event_type not in cfg.events:
            continue
        handler = _HANDLERS.get(cfg.channel)
        if handler:
            handler(event, cfg)


def load_notify_config(path: str) -> List[NotificationConfig]:
    """Load notification configs from a JSON file."""
    p = Path(path)
    if not p.exists():
        return []
    raw = json.loads(p.read_text())
    return [
        NotificationConfig(
            channel=item["channel"],
            target=item["target"],
            events=item.get("events", []),
            enabled=item.get("enabled", True),
        )
        for item in raw
    ]


def save_notify_config(configs: List[NotificationConfig], path: str) -> None:
    """Persist notification configs to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {"channel": c.channel, "target": c.target, "events": c.events, "enabled": c.enabled}
        for c in configs
    ]
    p.write_text(json.dumps(data, indent=2))
