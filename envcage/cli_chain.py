"""cli_chain.py — CLI commands for env-chain management."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envcage.env_chain import (
    create_chain,
    load_chain,
    resolve,
    resolve_key,
    save_chain,
    source_of,
)


# ---------- commands ----------

def cmd_chain_create(args: argparse.Namespace) -> None:
    """Create a new chain file."""
    snaps: List[str] = args.snapshots or []
    chain = create_chain(
        name=args.name,
        snapshots=snaps,
        description=args.description or "",
    )
    save_chain(chain, args.output)
    print(f"Chain '{args.name}' saved to {args.output} ({len(snaps)} snapshot(s)).")


def cmd_chain_show(args: argparse.Namespace) -> None:
    """Print the priority-ordered snapshot list for a chain."""
    chain = load_chain(args.chain_file)
    print(f"Chain: {chain.name}")
    if chain.description:
        print(f"  {chain.description}")
    if not chain.snapshots:
        print("  (no snapshots)")
        return
    for i, snap in enumerate(chain.snapshots, 1):
        print(f"  [{i}] {snap}")


def cmd_chain_resolve(args: argparse.Namespace) -> None:
    """Print the fully resolved env from a chain."""
    chain = load_chain(args.chain_file)
    merged = resolve(chain)
    if not merged:
        print("(empty)")
        return
    for key in sorted(merged):
        print(f"{key}={merged[key]}")


def cmd_chain_lookup(args: argparse.Namespace) -> None:
    """Look up a single key in a chain and show which snapshot provides it."""
    chain = load_chain(args.chain_file)
    value = resolve_key(chain, args.key)
    if value is None:
        print(f"Key '{args.key}' not found in chain '{chain.name}'.")
        sys.exit(1)
    src = source_of(chain, args.key)
    print(f"{args.key}={value}  (from {src})")


# ---------- registration ----------

def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # chain create
    p_create = subparsers.add_parser("chain-create", help="Create an env chain")
    p_create.add_argument("name", help="Chain name")
    p_create.add_argument("--output", required=True, help="Output chain file path")
    p_create.add_argument("--snapshots", nargs="*", metavar="SNAP", help="Ordered snapshot files (highest priority first)")
    p_create.add_argument("--description", default="", help="Optional description")
    p_create.set_defaults(func=cmd_chain_create)

    # chain show
    p_show = subparsers.add_parser("chain-show", help="Show chain contents")
    p_show.add_argument("chain_file", help="Chain file path")
    p_show.set_defaults(func=cmd_chain_show)

    # chain resolve
    p_resolve = subparsers.add_parser("chain-resolve", help="Print resolved env from chain")
    p_resolve.add_argument("chain_file", help="Chain file path")
    p_resolve.set_defaults(func=cmd_chain_resolve)

    # chain lookup
    p_lookup = subparsers.add_parser("chain-lookup", help="Look up a key in a chain")
    p_lookup.add_argument("chain_file", help="Chain file path")
    p_lookup.add_argument("key", help="Key to look up")
    p_lookup.set_defaults(func=cmd_chain_lookup)
