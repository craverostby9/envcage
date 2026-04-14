"""CLI commands for snapshot history management."""

from __future__ import annotations

import argparse
from typing import List

from envcage.history import load_history, find_by_tag, find_by_name, clear_history, HistoryEntry


def _format_entry(entry: HistoryEntry, index: int) -> str:
    tags_str = ", ".join(entry.tags) if entry.tags else "(none)"
    note_str = f"  note   : {entry.note}" if entry.note else ""
    lines = [
        f"[{index}] {entry.snapshot_name}",
        f"  path   : {entry.path}",
        f"  time   : {entry.timestamp}",
        f"  tags   : {tags_str}",
    ]
    if note_str:
        lines.append(note_str)
    return "\n".join(lines)


def cmd_history_list(args: argparse.Namespace) -> None:
    history_path = getattr(args, "history_file", ".envcage_history.json")
    entries = load_history(history_path)
    if not entries:
        print("No history recorded yet.")
        return
    for i, entry in enumerate(entries):
        print(_format_entry(entry, i))
        print()


def cmd_history_find(args: argparse.Namespace) -> None:
    history_path = getattr(args, "history_file", ".envcage_history.json")
    results: List[HistoryEntry] = []

    if args.tag:
        results = find_by_tag(args.tag, history_path=history_path)
    elif args.name:
        results = find_by_name(args.name, history_path=history_path)
    else:
        print("Provide --tag or --name to search.")
        return

    if not results:
        print("No matching history entries found.")
        return

    for i, entry in enumerate(results):
        print(_format_entry(entry, i))
        print()


def cmd_history_clear(args: argparse.Namespace) -> None:
    history_path = getattr(args, "history_file", ".envcage_history.json")
    clear_history(history_path)
    print("History cleared.")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    hist_parser = subparsers.add_parser("history", help="Manage snapshot history")
    hist_sub = hist_parser.add_subparsers(dest="history_cmd")

    list_p = hist_sub.add_parser("list", help="List all history entries")
    list_p.add_argument("--history-file", default=".envcage_history.json")
    list_p.set_defaults(func=cmd_history_list)

    find_p = hist_sub.add_parser("find", help="Search history by tag or name")
    find_p.add_argument("--tag", default=None, help="Filter by tag")
    find_p.add_argument("--name", default=None, help="Filter by snapshot name")
    find_p.add_argument("--history-file", default=".envcage_history.json")
    find_p.set_defaults(func=cmd_history_find)

    clear_p = hist_sub.add_parser("clear", help="Clear all history")
    clear_p.add_argument("--history-file", default=".envcage_history.json")
    clear_p.set_defaults(func=cmd_history_clear)
