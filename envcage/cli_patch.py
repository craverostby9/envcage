"""CLI commands for patching snapshots."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envcage.env_patch import load_patch_file, patch_snapshot_file, PatchOperation, apply_patch
from envcage.snapshot import load, save


def cmd_patch(args: argparse.Namespace) -> None:
    """Apply a patch file to a snapshot and write the result."""
    try:
        result = patch_snapshot_file(args.snapshot, args.patch, args.output)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Patched snapshot written to {args.output}")
    print(f"  Applied : {len(result.applied)} operation(s)")
    if result.skipped:
        print(f"  Skipped : {len(result.skipped)} operation(s)")
        for op in result.skipped:
            print(f"    - {op.op} {op.key} (skipped)")


def cmd_patch_show(args: argparse.Namespace) -> None:
    """Print the operations in a patch file."""
    try:
        ops = load_patch_file(args.patch)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not ops:
        print("(empty patch)")
        return
    for op in ops:
        if op.op == "set":
            print(f"  SET    {op.key} = {op.value}")
        elif op.op == "delete":
            print(f"  DELETE {op.key}")
        else:
            print(f"  UNKNOWN {op.op} {op.key}")


def register(subparsers) -> None:
    p = subparsers.add_parser("patch", help="Apply a patch to a snapshot")
    p.add_argument("snapshot", help="Source snapshot file")
    p.add_argument("patch", help="Patch JSON file")
    p.add_argument("output", help="Output snapshot file")
    p.set_defaults(func=cmd_patch)

    ps = subparsers.add_parser("patch-show", help="Show operations in a patch file")
    ps.add_argument("patch", help="Patch JSON file")
    ps.set_defaults(func=cmd_patch_show)
