"""CLI commands for template management."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from envcage import template as tmpl_mod
from envcage.snapshot import load as load_snapshot


def cmd_template_create(args) -> int:
    """Create a new template from a list of keys."""
    keys = args.keys  # list[str]
    description = args.description or ""
    tmpl = tmpl_mod.create_template(keys, description)
    tmpl_mod.save_template(tmpl, args.output)
    print(f"Template saved to {args.output} ({len(tmpl['keys'])} keys)")
    return 0


def cmd_template_from_snapshot(args) -> int:
    """Derive a template from an existing snapshot file."""
    snap = load_snapshot(args.snapshot)
    description = args.description or ""
    tmpl = tmpl_mod.template_from_snapshot(snap, description)
    tmpl_mod.save_template(tmpl, args.output)
    print(f"Template saved to {args.output} ({len(tmpl['keys'])} keys)")
    return 0


def cmd_template_check(args) -> int:
    """Check a snapshot against a template and report missing keys."""
    tmpl = tmpl_mod.load_template(args.template)
    snap = load_snapshot(args.snapshot)
    missing = tmpl_mod.missing_keys(tmpl, snap)
    if missing:
        print(f"Missing {len(missing)} required key(s):")
        for key in sorted(missing):
            print(f"  - {key}")
        return 1
    print("All required keys are present.")
    return 0


def cmd_template_show(args) -> int:
    """Print a template's keys to stdout."""
    tmpl = tmpl_mod.load_template(args.template)
    desc = tmpl.get("description", "")
    if desc:
        print(f"Description: {desc}")
    print(f"{len(tmpl['keys'])} key(s):")
    for key in tmpl["keys"]:
        print(f"  {key}")
    return 0


def cmd_template_scaffold(args) -> int:
    """Scaffold a .env file skeleton from a template."""
    tmpl = tmpl_mod.load_template(args.template)
    lines = [f"{key}=" for key in tmpl["keys"]]
    output = "\n".join(lines) + "\n"
    if args.output and args.output != "-":
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Scaffold written to {args.output}")
    else:
        sys.stdout.write(output)
    return 0
