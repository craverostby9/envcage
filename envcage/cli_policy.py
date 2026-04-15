"""CLI commands for policy management."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envcage.policy import (
    create_policy,
    save_policy,
    load_policy,
    enforce_policy_file,
)


def cmd_policy_create(args: argparse.Namespace) -> None:
    """Create and save a policy file."""
    required = args.require or []
    forbidden = args.forbid or []
    prefixes = args.prefix or []
    max_empty = args.max_empty if args.max_empty is not None else -1

    policy = create_policy(
        required_keys=required,
        forbidden_keys=forbidden,
        required_prefixes=prefixes,
        max_empty_values=max_empty,
        description=args.description or "",
    )
    save_policy(policy, args.output)
    print(f"Policy saved to {args.output}")


def cmd_policy_show(args: argparse.Namespace) -> None:
    """Display the contents of a policy file."""
    policy = load_policy(args.policy)
    print(f"Description : {policy.description or '(none)'}")
    print(f"Required    : {', '.join(policy.required_keys) or '(none)'}")
    print(f"Forbidden   : {', '.join(policy.forbidden_keys) or '(none)'}")
    print(f"Prefixes    : {', '.join(policy.required_prefixes) or '(none)'}")
    max_e = policy.max_empty_values
    print(f"Max empty   : {'unlimited' if max_e < 0 else max_e}")


def cmd_policy_check(args: argparse.Namespace) -> None:
    """Check a snapshot against a policy file."""
    result = enforce_policy_file(args.policy, args.snapshot)
    print(result.summary())
    if not result.passed:
        sys.exit(1)


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # policy create
    p_create = subparsers.add_parser("policy-create", help="Create a policy file")
    p_create.add_argument("output", help="Output path for policy JSON")
    p_create.add_argument("--require", nargs="*", metavar="KEY", help="Required keys")
    p_create.add_argument("--forbid", nargs="*", metavar="KEY", help="Forbidden keys")
    p_create.add_argument("--prefix", nargs="*", metavar="PREFIX", help="Required key prefixes")
    p_create.add_argument("--max-empty", type=int, default=None, metavar="N", help="Max empty values allowed")
    p_create.add_argument("--description", default="", help="Human-readable policy description")
    p_create.set_defaults(func=cmd_policy_create)

    # policy show
    p_show = subparsers.add_parser("policy-show", help="Show a policy file")
    p_show.add_argument("policy", help="Path to policy JSON")
    p_show.set_defaults(func=cmd_policy_show)

    # policy check
    p_check = subparsers.add_parser("policy-check", help="Check snapshot against a policy")
    p_check.add_argument("policy", help="Path to policy JSON")
    p_check.add_argument("snapshot", help="Path to snapshot JSON")
    p_check.set_defaults(func=cmd_policy_check)
