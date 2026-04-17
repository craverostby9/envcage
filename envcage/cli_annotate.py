"""CLI commands for key annotations."""
from __future__ import annotations

import argparse

from envcage.env_annotate import (
    set_annotation,
    get_annotation,
    remove_annotation,
    list_annotations,
)

DEFAULT_ANNOTATION_FILE = ".envcage_annotations.json"


def cmd_annotate_set(args: argparse.Namespace) -> None:
    set_annotation(args.snapshot, args.key, args.note, args.annotation_file)
    print(f"Annotation set: [{args.snapshot}] {args.key} = {args.note!r}")


def cmd_annotate_get(args: argparse.Namespace) -> None:
    note = get_annotation(args.snapshot, args.key, args.annotation_file)
    if note is None:
        print(f"No annotation for {args.key!r} in {args.snapshot}")
    else:
        print(f"{args.key}: {note}")


def cmd_annotate_remove(args: argparse.Namespace) -> None:
    removed = remove_annotation(args.snapshot, args.key, args.annotation_file)
    if removed:
        print(f"Removed annotation for {args.key!r} in {args.snapshot}")
    else:
        print(f"No annotation found for {args.key!r} in {args.snapshot}")


def cmd_annotate_list(args: argparse.Namespace) -> None:
    notes = list_annotations(args.snapshot, args.annotation_file)
    if not notes:
        print(f"No annotations for {args.snapshot}")
        return
    for key, note in sorted(notes.items()):
        print(f"  {key}: {note}")


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("annotate", help="Manage key annotations")
    p.add_argument("--annotation-file", default=DEFAULT_ANNOTATION_FILE)
    sub = p.add_subparsers(dest="annotate_cmd", required=True)

    ps = sub.add_parser("set", help="Set annotation for a key")
    ps.add_argument("snapshot")
    ps.add_argument("key")
    ps.add_argument("note")
    ps.set_defaults(func=cmd_annotate_set)

    pg = sub.add_parser("get", help="Get annotation for a key")
    pg.add_argument("snapshot")
    pg.add_argument("key")
    pg.set_defaults(func=cmd_annotate_get)

    pr = sub.add_parser("remove", help="Remove annotation for a key")
    pr.add_argument("snapshot")
    pr.add_argument("key")
    pr.set_defaults(func=cmd_annotate_remove)

    pl = sub.add_parser("list", help="List all annotations for a snapshot")
    pl.add_argument("snapshot")
    pl.set_defaults(func=cmd_annotate_list)
