"""CLI commands for schema validation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envcage.schema import (
    SchemaRule,
    load_schema,
    save_schema,
    validate_schema_file,
)


def cmd_schema_create(args: argparse.Namespace) -> None:
    """Create a schema file from a list of key specs."""
    rules = []
    for spec in args.keys:
        key = spec
        rule = SchemaRule(key=key, required=not args.optional)
        if args.pattern:
            rule.pattern = args.pattern
        if args.min_length is not None:
            rule.min_length = args.min_length
        if args.max_length is not None:
            rule.max_length = args.max_length
        if args.allowed:
            rule.allowed_values = args.allowed
        rules.append(rule)
    save_schema(rules, args.output)
    print(f"Schema written to {args.output} ({len(rules)} rule(s)).")


def cmd_schema_show(args: argparse.Namespace) -> None:
    """Display the rules in a schema file."""
    rules = load_schema(args.schema)
    if not rules:
        print("Schema is empty.")
        return
    for rule in rules:
        parts = [f"{rule.key}"]
        parts.append("required" if rule.required else "optional")
        if rule.pattern:
            parts.append(f"pattern={rule.pattern}")
        if rule.min_length is not None:
            parts.append(f"min={rule.min_length}")
        if rule.max_length is not None:
            parts.append(f"max={rule.max_length}")
        if rule.allowed_values:
            parts.append(f"allowed={rule.allowed_values}")
        print("  " + " | ".join(parts))


def cmd_schema_check(args: argparse.Namespace) -> None:
    """Validate a snapshot file against a schema."""
    report = validate_schema_file(args.snapshot, args.schema)
    print(report.summary())
    if not report.is_valid:
        sys.exit(1)


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # schema create
    p_create = subparsers.add_parser("schema-create", help="Create a schema file")
    p_create.add_argument("keys", nargs="+", help="Keys to include in schema")
    p_create.add_argument("--output", required=True, help="Output schema file path")
    p_create.add_argument("--optional", action="store_true", help="Mark keys as optional")
    p_create.add_argument("--pattern", default=None, help="Regex pattern for all keys")
    p_create.add_argument("--min-length", type=int, default=None, dest="min_length")
    p_create.add_argument("--max-length", type=int, default=None, dest="max_length")
    p_create.add_argument("--allowed", nargs="*", default=[], help="Allowed values")
    p_create.set_defaults(func=cmd_schema_create)

    # schema show
    p_show = subparsers.add_parser("schema-show", help="Display schema rules")
    p_show.add_argument("schema", help="Path to schema file")
    p_show.set_defaults(func=cmd_schema_show)

    # schema check
    p_check = subparsers.add_parser("schema-check", help="Validate snapshot against schema")
    p_check.add_argument("snapshot", help="Path to snapshot file")
    p_check.add_argument("schema", help="Path to schema file")
    p_check.set_defaults(func=cmd_schema_check)
