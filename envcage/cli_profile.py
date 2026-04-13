"""CLI commands for profile management."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envcage.profile import (
    create_profile,
    load_profile,
    missing_keys,
    save_profile,
)
from envcage.snapshot import load as load_snapshot


def cmd_profile_create(args: argparse.Namespace) -> None:
    """Create a new profile JSON file."""
    keys: List[str] = args.keys or []
    defaults: dict = {}
    for item in args.default or []:
        if "=" not in item:
            print(f"[error] default must be KEY=VALUE, got: {item}", file=sys.stderr)
            sys.exit(1)
        k, v = item.split("=", 1)
        defaults[k] = v

    profile = create_profile(
        name=args.name,
        required_keys=keys,
        defaults=defaults,
        description=args.description or "",
    )
    save_profile(profile, args.output)
    print(f"[ok] profile '{args.name}' saved to {args.output}")


def cmd_profile_show(args: argparse.Namespace) -> None:
    """Display a profile's contents as JSON."""
    profile = load_profile(args.profile)
    data = {
        "name": profile.name,
        "description": profile.description,
        "required_keys": profile.required_keys,
        "defaults": profile.defaults,
    }
    print(json.dumps(data, indent=2))


def cmd_profile_check(args: argparse.Namespace) -> None:
    """Check a snapshot against a profile's required keys."""
    profile = load_profile(args.profile)
    snapshot = load_snapshot(args.snapshot)
    env = snapshot.get("env", {})
    absent = missing_keys(profile, env)
    if absent:
        print("[fail] missing required keys:")
        for k in absent:
            print(f"  - {k}")
        sys.exit(1)
    else:
        print(f"[ok] all {len(profile.required_keys)} required keys present")


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register profile sub-commands onto the provided subparsers."""
    # create
    p_create = subparsers.add_parser("profile-create", help="Create a profile")
    p_create.add_argument("name", help="Profile name")
    p_create.add_argument("--output", required=True, help="Output JSON file")
    p_create.add_argument("--keys", nargs="*", help="Required keys")
    p_create.add_argument("--default", nargs="*", help="Default values KEY=VALUE")
    p_create.add_argument("--description", help="Profile description")
    p_create.set_defaults(func=cmd_profile_create)

    # show
    p_show = subparsers.add_parser("profile-show", help="Show a profile")
    p_show.add_argument("profile", help="Profile JSON file")
    p_show.set_defaults(func=cmd_profile_show)

    # check
    p_check = subparsers.add_parser("profile-check", help="Check snapshot against profile")
    p_check.add_argument("profile", help="Profile JSON file")
    p_check.add_argument("snapshot", help="Snapshot JSON file")
    p_check.set_defaults(func=cmd_profile_check)
