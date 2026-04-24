"""CLI commands for the snapshot index feature."""
from __future__ import annotations

import argparse
import sys

from envcage.env_snapshot_index import (
    index_snapshot,
    remove_from_index,
    get_index_entry,
    list_index,
    search_index,
)

_DEFAULT_INDEX = ".envcage_index.json"


def cmd_index_add(args: argparse.Namespace) -> None:
    tags = args.tags.split(",") if args.tags else []
    entry = index_snapshot(
        name=args.name,
        path=args.path,
        key_count=args.key_count,
        tags=tags,
        description=args.description or "",
        index_file=args.index_file,
    )
    print(f"Indexed '{entry.name}' ({entry.key_count} keys) → {entry.path}")


def cmd_index_remove(args: argparse.Namespace) -> None:
    removed = remove_from_index(args.name, index_file=args.index_file)
    if removed:
        print(f"Removed '{args.name}' from index.")
    else:
        print(f"'{args.name}' not found in index.", file=sys.stderr)
        sys.exit(1)


def cmd_index_show(args: argparse.Namespace) -> None:
    entry = get_index_entry(args.name, index_file=args.index_file)
    if entry is None:
        print(f"No index entry for '{args.name}'.", file=sys.stderr)
        sys.exit(1)
    print(f"Name       : {entry.name}")
    print(f"Path       : {entry.path}")
    print(f"Keys       : {entry.key_count}")
    print(f"Tags       : {', '.join(entry.tags) if entry.tags else '(none)'}")
    print(f"Description: {entry.description or '(none)'}")


def cmd_index_list(args: argparse.Namespace) -> None:
    entries = list_index(index_file=args.index_file)
    if not entries:
        print("Index is empty.")
        return
    for e in entries:
        tag_str = f" [{', '.join(e.tags)}]" if e.tags else ""
        print(f"{e.name}{tag_str} — {e.key_count} keys — {e.path}")


def cmd_index_search(args: argparse.Namespace) -> None:
    results = search_index(
        args.pattern,
        index_file=args.index_file,
        case_sensitive=args.case_sensitive,
    )
    if not results:
        print(f"No entries matching '{args.pattern}'.")
        return
    for e in results:
        print(f"{e.name} — {e.path}")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--index-file", default=_DEFAULT_INDEX)

    p_add = subparsers.add_parser("index-add", parents=[common], help="Add/update a snapshot in the index")
    p_add.add_argument("name")
    p_add.add_argument("path")
    p_add.add_argument("--key-count", type=int, default=0)
    p_add.add_argument("--tags", default="")
    p_add.add_argument("--description", default="")
    p_add.set_defaults(func=cmd_index_add)

    p_rm = subparsers.add_parser("index-remove", parents=[common], help="Remove a snapshot from the index")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_index_remove)

    p_show = subparsers.add_parser("index-show", parents=[common], help="Show details of an index entry")
    p_show.add_argument("name")
    p_show.set_defaults(func=cmd_index_show)

    p_list = subparsers.add_parser("index-list", parents=[common], help="List all indexed snapshots")
    p_list.set_defaults(func=cmd_index_list)

    p_search = subparsers.add_parser("index-search", parents=[common], help="Search the snapshot index")
    p_search.add_argument("pattern")
    p_search.add_argument("--case-sensitive", action="store_true")
    p_search.set_defaults(func=cmd_index_search)
