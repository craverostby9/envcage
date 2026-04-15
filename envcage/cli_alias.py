"""CLI commands for managing snapshot aliases."""
from __future__ import annotations

import argparse
import sys

from envcage.env_alias import (
    set_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
    aliases_for_snapshot,
)

_DEFAULT_FILE = ".envcage_aliases.json"


def cmd_alias_set(args: argparse.Namespace) -> None:
    """envcage alias set <name> <snapshot_path>"""
    set_alias(args.name, args.snapshot, getattr(args, "alias_file", _DEFAULT_FILE))
    print(f"Alias '{args.name}' -> '{args.snapshot}' saved.")


def cmd_alias_remove(args: argparse.Namespace) -> None:
    """envcage alias remove <name>"""
    af = getattr(args, "alias_file", _DEFAULT_FILE)
    removed = remove_alias(args.name, af)
    if removed:
        print(f"Alias '{args.name}' removed.")
    else:
        print(f"Alias '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)


def cmd_alias_resolve(args: argparse.Namespace) -> None:
    """envcage alias resolve <name>"""
    af = getattr(args, "alias_file", _DEFAULT_FILE)
    path = resolve_alias(args.name, af)
    if path is None:
        print(f"Alias '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)
    print(path)


def cmd_alias_list(args: argparse.Namespace) -> None:
    """envcage alias list"""
    af = getattr(args, "alias_file", _DEFAULT_FILE)
    mapping = list_aliases(af)
    if not mapping:
        print("No aliases defined.")
        return
    for name, path in sorted(mapping.items()):
        print(f"  {name:<20} {path}")


def cmd_alias_find(args: argparse.Namespace) -> None:
    """envcage alias find <snapshot_path>"""
    af = getattr(args, "alias_file", _DEFAULT_FILE)
    names = aliases_for_snapshot(args.snapshot, af)
    if not names:
        print(f"No aliases point to '{args.snapshot}'.")
        return
    for name in names:
        print(f"  {name}")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("alias", help="Manage snapshot aliases")
    sub = p.add_subparsers(dest="alias_cmd", required=True)

    s = sub.add_parser("set", help="Set an alias")
    s.add_argument("name")
    s.add_argument("snapshot")
    s.set_defaults(func=cmd_alias_set)

    r = sub.add_parser("remove", help="Remove an alias")
    r.add_argument("name")
    r.set_defaults(func=cmd_alias_remove)

    rs = sub.add_parser("resolve", help="Resolve an alias to its path")
    rs.add_argument("name")
    rs.set_defaults(func=cmd_alias_resolve)

    ls = sub.add_parser("list", help="List all aliases")
    ls.set_defaults(func=cmd_alias_list)

    f = sub.add_parser("find", help="Find aliases for a snapshot path")
    f.add_argument("snapshot")
    f.set_defaults(func=cmd_alias_find)
