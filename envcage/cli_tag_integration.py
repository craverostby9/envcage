"""Integration helpers: resolve snapshot paths by tag for use in other commands."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from envcage.tag import find_by_tag, DEFAULT_TAG_FILE
from envcage.snapshot import load


def resolve_snapshots_by_tag(
    tag: str,
    snapshot_dir: str = ".",
    tag_file: str = DEFAULT_TAG_FILE,
) -> List[dict]:
    """Load and return all snapshots whose name matches the given tag.

    Snapshot files are expected to follow the naming convention
    ``<snapshot_name>.json`` inside *snapshot_dir*.
    Snapshots whose file is missing are silently skipped.
    """
    names = find_by_tag(tag, tag_file=tag_file)
    results = []
    for name in names:
        candidate = Path(snapshot_dir) / f"{name}.json"
        if candidate.exists():
            results.append(load(str(candidate)))
    return results


def snapshot_has_tag(
    snapshot_name: str,
    tag: str,
    tag_file: str = DEFAULT_TAG_FILE,
) -> bool:
    """Return True if *snapshot_name* carries *tag*."""
    from envcage.tag import get_tags
    return tag in get_tags(snapshot_name, tag_file=tag_file)


def tag_summary(tag_file: str = DEFAULT_TAG_FILE) -> str:
    """Return a human-readable summary of all tags."""
    from envcage.tag import list_all_tags
    store = list_all_tags(tag_file=tag_file)
    if not store:
        return "No tags recorded."
    lines = []
    for name, tags in sorted(store.items()):
        lines.append(f"  {name}: {', '.join(tags)}")
    return "\n".join(lines)
