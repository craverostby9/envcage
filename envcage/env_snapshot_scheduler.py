"""Snapshot scheduler: define recurring snapshot jobs with cron-like intervals."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_SCHEDULE_FILE = ".envcage_schedule.json"


@dataclass
class ScheduleEntry:
    name: str
    output_path: str
    interval_seconds: int
    last_run: Optional[float] = None
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "output_path": self.output_path,
            "interval_seconds": self.interval_seconds,
            "last_run": self.last_run,
            "enabled": self.enabled,
        }

    @staticmethod
    def from_dict(data: dict) -> "ScheduleEntry":
        return ScheduleEntry(
            name=data["name"],
            output_path=data["output_path"],
            interval_seconds=data["interval_seconds"],
            last_run=data.get("last_run"),
            enabled=data.get("enabled", True),
        )

    def is_due(self, now: Optional[float] = None) -> bool:
        if not self.enabled:
            return False
        now = now if now is not None else time.time()
        if self.last_run is None:
            return True
        return (now - self.last_run) >= self.interval_seconds


def _load_schedule(schedule_file: str) -> Dict[str, ScheduleEntry]:
    path = Path(schedule_file)
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {k: ScheduleEntry.from_dict(v) for k, v in data.items()}


def _save_schedule(entries: Dict[str, ScheduleEntry], schedule_file: str) -> None:
    path = Path(schedule_file)
    path.write_text(json.dumps({k: v.to_dict() for k, v in entries.items()}, indent=2))


def add_schedule(
    name: str,
    output_path: str,
    interval_seconds: int,
    schedule_file: str = _DEFAULT_SCHEDULE_FILE,
) -> ScheduleEntry:
    entries = _load_schedule(schedule_file)
    entry = ScheduleEntry(name=name, output_path=output_path, interval_seconds=interval_seconds)
    entries[name] = entry
    _save_schedule(entries, schedule_file)
    return entry


def remove_schedule(name: str, schedule_file: str = _DEFAULT_SCHEDULE_FILE) -> bool:
    entries = _load_schedule(schedule_file)
    if name not in entries:
        return False
    del entries[name]
    _save_schedule(entries, schedule_file)
    return True


def get_schedule(name: str, schedule_file: str = _DEFAULT_SCHEDULE_FILE) -> Optional[ScheduleEntry]:
    return _load_schedule(schedule_file).get(name)


def list_schedules(schedule_file: str = _DEFAULT_SCHEDULE_FILE) -> List[ScheduleEntry]:
    return list(_load_schedule(schedule_file).values())


def due_schedules(
    schedule_file: str = _DEFAULT_SCHEDULE_FILE,
    now: Optional[float] = None,
) -> List[ScheduleEntry]:
    now = now if now is not None else time.time()
    return [e for e in list_schedules(schedule_file) if e.is_due(now)]


def mark_ran(
    name: str,
    schedule_file: str = _DEFAULT_SCHEDULE_FILE,
    now: Optional[float] = None,
) -> Optional[ScheduleEntry]:
    entries = _load_schedule(schedule_file)
    if name not in entries:
        return None
    entries[name].last_run = now if now is not None else time.time()
    _save_schedule(entries, schedule_file)
    return entries[name]
