"""CLI commands for scope management."""
from __future__ import annotations

import argparse
from pathlib import Path

from envcage.scope import (
    add_snapshot_to_scope,
    create_scope,
    delete_scope,
    list_scopes,
    load_scope,
    remove_snapshot_from_scope,
    save_scope,
)

_DEFAULT_SCOPE_FILE = Path(".envcage") / "scopes.json"


def cmd_scope_create(args: argparse.Namespace) -> None:
    sf = Path(getattr(args, "scope_file", _DEFAULT_SCOPE_FILE))
    scope = create_scope(args.name, description=getattr(args, "description", ""))
    save_scope(scope, sf)
    print(f"Scope '{args.name}' created.")


def cmd_scope_add(args: argparse.Namespace) -> None:
    sf = Path(getattr(args, "scope_file", _DEFAULT_SCOPE_FILE))
    scope = add_snapshot_to_scope(args.name, args.snapshot, sf)
    print(f"Snapshot '{args.snapshot}' added to scope '{args.name}'. ({len(scope.snapshots)} total)")


def cmd_scope_remove(args: argparse.Namespace) -> None:
    sf = Path(getattr(args, "scope_file", _DEFAULT_SCOPE_FILE))
    remove_snapshot_from_scope(args.name, args.snapshot, sf)
    print(f"Snapshot '{args.snapshot}' removed from scope '{args.name}'.")


def cmd_scope_show(args: argparse.Namespace) -> None:
    sf = Path(getattr(args, "scope_file", _DEFAULT_SCOPE_FILE))
    scope = load_scope(args.name, sf)
    if scope is None:
        print(f"Scope '{args.name}' not found.")
        return
    print(f"Scope: {scope.name}")
    if scope.description:
        print(f"  Description: {scope.description}")
    if scope.snapshots:
        print("  Snapshots:")
        for s in scope.snapshots:
            print(f"    - {s}")
    else:
        print("  No snapshots assigned.")


def cmd_scope_list(args: argparse.Namespace) -> None:
    sf = Path(getattr(args, "scope_file", _DEFAULT_SCOPE_FILE))
    names = list_scopes(sf)
    if not names:
        print("No scopes defined.")
        return
    for name in names:
        print(name)


def cmd_scope_delete(args: argparse.Namespace) -> None:
    sf = Path(getattr(args, "scope_file", _DEFAULT_SCOPE_FILE))
    removed = delete_scope(args.name, sf)
    if removed:
        print(f"Scope '{args.name}' deleted.")
    else:
        print(f"Scope '{args.name}' not found.")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("scope", help="Manage snapshot scopes")
    sub = p.add_subparsers(dest="scope_cmd", required=True)

    pc = sub.add_parser("create", help="Create a new scope")
    pc.add_argument("name")
    pc.add_argument("--description", default="")
    pc.set_defaults(func=cmd_scope_create)

    pa = sub.add_parser("add", help="Add snapshot to scope")
    pa.add_argument("name")
    pa.add_argument("snapshot")
    pa.set_defaults(func=cmd_scope_add)

    pr = sub.add_parser("remove", help="Remove snapshot from scope")
    pr.add_argument("name")
    pr.add_argument("snapshot")
    pr.set_defaults(func=cmd_scope_remove)

    ps = sub.add_parser("show", help="Show scope details")
    ps.add_argument("name")
    ps.set_defaults(func=cmd_scope_show)

    pl = sub.add_parser("list", help="List all scopes")
    pl.set_defaults(func=cmd_scope_list)

    pd = sub.add_parser("delete", help="Delete a scope")
    pd.add_argument("name")
    pd.set_defaults(func=cmd_scope_delete)
