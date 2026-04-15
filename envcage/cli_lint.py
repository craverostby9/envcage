"""CLI commands for the lint feature."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envcage.lint import lint_snapshot_file, summary


def cmd_lint(args: argparse.Namespace) -> None:
    """Lint one or more snapshot files and report issues."""
    any_failed = False

    for path in args.snapshots:
        report = lint_snapshot_file(
            path,
            allow_empty=args.allow_empty,
            max_length=args.max_length,
            require_screaming_snake=not args.no_screaming_snake,
        )
        print(f"--- {path} ---")
        print(summary(report))
        print()
        if not report.passed:
            any_failed = True

    if any_failed:
        sys.exit(1)


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the lint subcommand."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'lint',
        help='Lint snapshot files for style and convention issues.',
    )
    parser.add_argument(
        'snapshots',
        nargs='+',
        metavar='SNAPSHOT',
        help='Path(s) to snapshot JSON file(s) to lint.',
    )
    parser.add_argument(
        '--allow-empty',
        action='store_true',
        default=False,
        help='Do not warn on empty values.',
    )
    parser.add_argument(
        '--max-length',
        type=int,
        default=1024,
        metavar='N',
        help='Maximum allowed value length (default: 1024).',
    )
    parser.add_argument(
        '--no-screaming-snake',
        action='store_true',
        default=False,
        help='Disable SCREAMING_SNAKE_CASE convention check.',
    )
    parser.set_defaults(func=cmd_lint)
