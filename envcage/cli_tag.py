"""CLI commands for snapshot tagging."""

from __future__ import annotations

import argparse
import sys

from envcage.tag import (
    add_tag,
    remove_tag,
    get_tags,
    find_by_tag,
    list_all_tags,
    DEFAULT_TAG_FILE,
)


def cmd_tag_add(args: argparse.Namespace) -> None:
    """Add a tag to a snapshot."""
    add_tag(args.snapshot, args.tag, tag_file=args.tag_file)
    print(f"Tagged '{args.snapshot}' with '{args.tag}'.")


def cmd_tag_remove(args: argparse.Namespace) -> None:
    """Remove a tag from a snapshot."""
    remove_tag(args.snapshot, args.tag, tag_file=args.tag_file)
    print(f"Removed tag '{args.tag}' from '{args.snapshot}'.")


def cmd_tag_list(args: argparse.Namespace) -> None:
    """List tags for a snapshot, or all tags if no snapshot given."""
    if args.snapshot:
        tags = get_tags(args.snapshot, tag_file=args.tag_file)
        if tags:
            print(f"Tags for '{args.snapshot}': {', '.join(tags)}")
        else:
            print(f"No tags found for '{args.snapshot}'.")
    else:
        store = list_all_tags(tag_file=args.tag_file)
        if not store:
            print("No tags recorded.")
        else:
            for name, tags in sorted(store.items()):
                print(f"  {name}: {', '.join(tags)}")


def cmd_tag_find(args: argparse.Namespace) -> None:
    """Find all snapshots with a given tag."""
    results = find_by_tag(args.tag, tag_file=args.tag_file)
    if results:
        for name in results:
            print(name)
    else:
        print(f"No snapshots found with tag '{args.tag}'.")
        sys.exit(1)


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register tag sub-commands onto the provided subparsers."""
    tag_parser = subparsers.add_parser("tag", help="Manage snapshot tags")
    tag_sub = tag_parser.add_subparsers(dest="tag_cmd", required=True)
    tag_parser.add_argument("--tag-file", default=DEFAULT_TAG_FILE)

    p_add = tag_sub.add_parser("add", help="Add a tag to a snapshot")
    p_add.add_argument("snapshot")
    p_add.add_argument("tag")
    p_add.set_defaults(func=cmd_tag_add)

    p_remove = tag_sub.add_parser("remove", help="Remove a tag from a snapshot")
    p_remove.add_argument("snapshot")
    p_remove.add_argument("tag")
    p_remove.set_defaults(func=cmd_tag_remove)

    p_list = tag_sub.add_parser("list", help="List tags")
    p_list.add_argument("snapshot", nargs="?", default=None)
    p_list.set_defaults(func=cmd_tag_list)

    p_find = tag_sub.add_parser("find", help="Find snapshots by tag")
    p_find.add_argument("tag")
    p_find.set_defaults(func=cmd_tag_find)
