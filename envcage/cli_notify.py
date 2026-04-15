"""CLI commands for managing envcage notification configs."""
from __future__ import annotations

import argparse
from pathlib import Path

from envcage.notify import (
    NotificationConfig,
    load_notify_config,
    save_notify_config,
)

_DEFAULT_CONFIG = ".envcage_notify.json"


def cmd_notify_add(args: argparse.Namespace) -> None:
    """Add a notification channel to the config."""
    cfg_path = getattr(args, "config", _DEFAULT_CONFIG)
    configs = load_notify_config(cfg_path)
    events = args.events.split(",") if args.events else []
    new_cfg = NotificationConfig(
        channel=args.channel,
        target=args.target,
        events=events,
        enabled=True,
    )
    configs.append(new_cfg)
    save_notify_config(configs, cfg_path)
    print(f"Added {args.channel} notification → {args.target}")


def cmd_notify_list(args: argparse.Namespace) -> None:
    """List all configured notification channels."""
    cfg_path = getattr(args, "config", _DEFAULT_CONFIG)
    configs = load_notify_config(cfg_path)
    if not configs:
        print("No notification channels configured.")
        return
    for i, cfg in enumerate(configs, 1):
        status = "enabled" if cfg.enabled else "disabled"
        events = ", ".join(cfg.events) if cfg.events else "all"
        print(f"{i}. [{status}] {cfg.channel} → {cfg.target} (events: {events})")


def cmd_notify_remove(args: argparse.Namespace) -> None:
    """Remove a notification channel by 1-based index."""
    cfg_path = getattr(args, "config", _DEFAULT_CONFIG)
    configs = load_notify_config(cfg_path)
    idx = args.index - 1
    if idx < 0 or idx >= len(configs):
        print(f"Error: index {args.index} out of range (have {len(configs)} entries).")
        raise SystemExit(1)
    removed = configs.pop(idx)
    save_notify_config(configs, cfg_path)
    print(f"Removed {removed.channel} → {removed.target}")


def register(subparsers) -> None:
    """Register notify sub-commands."""
    p_notify = subparsers.add_parser("notify", help="Manage notification channels")
    sub = p_notify.add_subparsers(dest="notify_cmd")

    p_add = sub.add_parser("add", help="Add a notification channel")
    p_add.add_argument("channel", choices=["stdout", "file", "webhook"])
    p_add.add_argument("target", help="File path or webhook URL")
    p_add.add_argument("--events", default="", help="Comma-separated event types to subscribe to")
    p_add.add_argument("--config", default=_DEFAULT_CONFIG)
    p_add.set_defaults(func=cmd_notify_add)

    p_list = sub.add_parser("list", help="List notification channels")
    p_list.add_argument("--config", default=_DEFAULT_CONFIG)
    p_list.set_defaults(func=cmd_notify_list)

    p_rm = sub.add_parser("remove", help="Remove a notification channel")
    p_rm.add_argument("index", type=int, help="1-based index from 'notify list'")
    p_rm.add_argument("--config", default=_DEFAULT_CONFIG)
    p_rm.set_defaults(func=cmd_notify_remove)
