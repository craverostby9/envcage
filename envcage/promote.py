"""Promote a snapshot from one environment stage to another.

A 'promotion' copies a snapshot file and records the transition
(e.g. staging -> production) in a promotion log.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from envcage.snapshot import load, save

_DEFAULT_PROMOTE_LOG = ".envcage_promotions.json"


@dataclass
class PromotionRecord:
    source_stage: str
    target_stage: str
    source_file: str
    target_file: str
    promoted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_stage": self.source_stage,
            "target_stage": self.target_stage,
            "source_file": self.source_file,
            "target_file": self.target_file,
            "promoted_at": self.promoted_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromotionRecord":
        return cls(**data)


def _load_log(log_path: str) -> list[PromotionRecord]:
    path = Path(log_path)
    if not path.exists():
        return []
    with open(path) as fh:
        return [PromotionRecord.from_dict(d) for d in json.load(fh)]


def _save_log(records: list[PromotionRecord], log_path: str) -> None:
    with open(log_path, "w") as fh:
        json.dump([r.to_dict() for r in records], fh, indent=2)


def promote(
    source_file: str,
    target_file: str,
    source_stage: str,
    target_stage: str,
    note: str = "",
    log_path: str = _DEFAULT_PROMOTE_LOG,
) -> PromotionRecord:
    """Copy *source_file* snapshot to *target_file* and record the promotion."""
    snapshot = load(source_file)
    save(snapshot, target_file)

    record = PromotionRecord(
        source_stage=source_stage,
        target_stage=target_stage,
        source_file=source_file,
        target_file=target_file,
        note=note,
    )
    records = _load_log(log_path)
    records.append(record)
    _save_log(records, log_path)
    return record


def load_log(log_path: str = _DEFAULT_PROMOTE_LOG) -> list[PromotionRecord]:
    """Return all promotion records from *log_path*."""
    return _load_log(log_path)
