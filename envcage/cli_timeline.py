"""CLI commands for env timeline."""
from __future__ import annotations

import argparse
from typing import List, Optional

from envcage.env_timeline import build_timeline, save_timeline, load_timeline


def cmd_timeline_build(args: argparse.Namespace) -> None:
    """Build a timeline from an ordered list of snapshot files."""
    snapshots: List[str] = args.snapshots
    labels: Optional[List[str]] = (
        args.labels.split(",") if getattr(args, "labels", None) else None
    )
    if labels and len(labels) != len(snapshots):
        print("Error: number of labels must match number of snapshots.")
        raise SystemExit(1)

    tl = build_timeline(snapshots, labels=labels)

    if getattr(args, "output", None):
        save_timeline(tl, args.output)
        print(f"Timeline saved to {args.output} ({tl.total_steps()} steps).")
    else:
        for step in tl.steps:
            label_str = f" [{step.label}]" if step.label else ""
            print(f"Step {step.index}{label_str}: {step.snapshot_path}")
            if step.added:
                print(f"  + added:   {', '.join(step.added)}")
            if step.removed:
                print(f"  - removed: {', '.join(step.removed)}")
            if step.changed:
                print(f"  ~ changed: {', '.join(step.changed)}")
            if not (step.added or step.removed or step.changed):
                print("  (no changes)")


def cmd_timeline_show(args: argparse.Namespace) -> None:
    """Show a previously saved timeline file."""
    tl = load_timeline(args.timeline_file)
    print(f"Timeline: {tl.total_steps()} step(s), changes={'yes' if tl.any_changes() else 'no'}")
    for step in tl.steps:
        label_str = f" [{step.label}]" if step.label else ""
        added = len(step.added)
        removed = len(step.removed)
        changed = len(step.changed)
        print(
            f"  [{step.index}]{label_str} +{added} -{removed} ~{changed}  {step.snapshot_path}"
        )


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # timeline build
    p_build = subparsers.add_parser(
        "timeline-build", help="Build a timeline from ordered snapshots"
    )
    p_build.add_argument("snapshots", nargs="+", help="Snapshot files in chronological order")
    p_build.add_argument("--labels", default=None, help="Comma-separated labels for each step")
    p_build.add_argument("--output", default=None, help="Save timeline to this file")
    p_build.set_defaults(func=cmd_timeline_build)

    # timeline show
    p_show = subparsers.add_parser("timeline-show", help="Show a saved timeline file")
    p_show.add_argument("timeline_file", help="Path to saved timeline JSON")
    p_show.set_defaults(func=cmd_timeline_show)
