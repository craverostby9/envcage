"""CLI commands for managing snapshot bookmarks."""
from __future__ import annotations

import argparse
from pathlib import Path

from envcage.env_bookmark import (
    get_bookmark,
    list_bookmarks,
    remove_bookmark,
    set_bookmark,
)

_DEFAULT_STORE = Path(".envcage") / "bookmarks.json"


def cmd_bookmark_set(args: argparse.Namespace) -> None:
    """Create or update a named bookmark pointing to a snapshot file."""
    store = Path(args.store) if hasattr(args, "store") and args.store else _DEFAULT_STORE
    bm = set_bookmark(
        name=args.name,
        snapshot_path=args.snapshot,
        description=getattr(args, "description", "") or "",
        store_path=store,
    )
    print(f"Bookmark '{bm.name}' -> {bm.snapshot_path}")


def cmd_bookmark_get(args: argparse.Namespace) -> None:
    """Show the snapshot path for a named bookmark."""
    store = Path(args.store) if hasattr(args, "store") and args.store else _DEFAULT_STORE
    bm = get_bookmark(args.name, store_path=store)
    if bm is None:
        print(f"No bookmark named '{args.name}'.")
        raise SystemExit(1)
    print(bm.snapshot_path)
    if bm.description:
        print(f"  # {bm.description}")


def cmd_bookmark_remove(args: argparse.Namespace) -> None:
    """Remove a named bookmark."""
    store = Path(args.store) if hasattr(args, "store") and args.store else _DEFAULT_STORE
    removed = remove_bookmark(args.name, store_path=store)
    if removed:
        print(f"Removed bookmark '{args.name}'.")
    else:
        print(f"Bookmark '{args.name}' not found.")
        raise SystemExit(1)


def cmd_bookmark_list(args: argparse.Namespace) -> None:
    """List all bookmarks."""
    store = Path(args.store) if hasattr(args, "store") and args.store else _DEFAULT_STORE
    bookmarks = list_bookmarks(store_path=store)
    if not bookmarks:
        print("No bookmarks defined.")
        return
    for bm in bookmarks:
        desc = f"  # {bm.description}" if bm.description else ""
        print(f"{bm.name:<20} {bm.snapshot_path}{desc}")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("bookmark", help="Manage snapshot bookmarks")
    sub = p.add_subparsers(dest="bookmark_cmd", required=True)

    ps = sub.add_parser("set", help="Create or update a bookmark")
    ps.add_argument("name", help="Bookmark name")
    ps.add_argument("snapshot", help="Path to snapshot file")
    ps.add_argument("--description", default="", help="Optional description")
    ps.add_argument("--store", default="", help="Custom bookmark store path")
    ps.set_defaults(func=cmd_bookmark_set)

    pg = sub.add_parser("get", help="Resolve a bookmark to its snapshot path")
    pg.add_argument("name", help="Bookmark name")
    pg.add_argument("--store", default="", help="Custom bookmark store path")
    pg.set_defaults(func=cmd_bookmark_get)

    pr = sub.add_parser("remove", help="Remove a bookmark")
    pr.add_argument("name", help="Bookmark name")
    pr.add_argument("--store", default="", help="Custom bookmark store path")
    pr.set_defaults(func=cmd_bookmark_remove)

    pl = sub.add_parser("list", help="List all bookmarks")
    pl.add_argument("--store", default="", help="Custom bookmark store path")
    pl.set_defaults(func=cmd_bookmark_list)
