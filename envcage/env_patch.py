"""Apply a patch (set/delete operations) to a snapshot."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envcage.snapshot import load, save


@dataclass
class PatchOperation:
    op: str          # "set" | "delete"
    key: str
    value: Optional[str] = None


@dataclass
class PatchResult:
    original: Dict[str, str]
    patched: Dict[str, str]
    applied: List[PatchOperation] = field(default_factory=list)
    skipped: List[PatchOperation] = field(default_factory=list)


def apply_patch(env: Dict[str, str], ops: List[PatchOperation]) -> PatchResult:
    result = dict(env)
    applied: List[PatchOperation] = []
    skipped: List[PatchOperation] = []

    for op in ops:
        if op.op == "set":
            result[op.key] = op.value or ""
            applied.append(op)
        elif op.op == "delete":
            if op.key in result:
                del result[op.key]
                applied.append(op)
            else:
                skipped.append(op)
        else:
            skipped.append(op)

    return PatchResult(original=dict(env), patched=result, applied=applied, skipped=skipped)


def patch_from_dict(raw: List[Dict]) -> List[PatchOperation]:
    return [PatchOperation(op=r["op"], key=r["key"], value=r.get("value")) for r in raw]


def load_patch_file(path: str) -> List[PatchOperation]:
    data = json.loads(Path(path).read_text())
    return patch_from_dict(data)


def patch_snapshot_file(snap_path: str, patch_path: str, out_path: str) -> PatchResult:
    snap = load(snap_path)
    ops = load_patch_file(patch_path)
    result = apply_patch(snap["env"], ops)
    out_snap = dict(snap)
    out_snap["env"] = result.patched
    save(out_snap, out_path)
    return result
