"""Tests for envcage.env_snapshot_scheduler."""
import json
import time

import pytest

from envcage.env_snapshot_scheduler import (
    ScheduleEntry,
    add_schedule,
    due_schedules,
    get_schedule,
    list_schedules,
    mark_ran,
    remove_schedule,
)


@pytest.fixture()
def sf(tmp_path):
    return str(tmp_path / "schedule.json")


# --- ScheduleEntry unit tests ---

def test_entry_is_due_when_never_run():
    e = ScheduleEntry(name="job", output_path="snap.json", interval_seconds=60)
    assert e.is_due()


def test_entry_is_due_after_interval_elapsed():
    past = time.time() - 120
    e = ScheduleEntry(name="job", output_path="snap.json", interval_seconds=60, last_run=past)
    assert e.is_due()


def test_entry_not_due_before_interval():
    recent = time.time() - 10
    e = ScheduleEntry(name="job", output_path="snap.json", interval_seconds=60, last_run=recent)
    assert not e.is_due()


def test_entry_disabled_never_due():
    e = ScheduleEntry(name="job", output_path="snap.json", interval_seconds=1, enabled=False)
    assert not e.is_due()


def test_to_dict_round_trips():
    e = ScheduleEntry(name="x", output_path="out.json", interval_seconds=300, last_run=1234.5)
    restored = ScheduleEntry.from_dict(e.to_dict())
    assert restored.name == e.name
    assert restored.output_path == e.output_path
    assert restored.interval_seconds == e.interval_seconds
    assert restored.last_run == e.last_run
    assert restored.enabled == e.enabled


# --- Persistence tests ---

def test_add_schedule_creates_file(sf):
    add_schedule("nightly", "snap.json", 86400, schedule_file=sf)
    import pathlib
    assert pathlib.Path(sf).exists()


def test_add_schedule_file_is_valid_json(sf):
    add_schedule("nightly", "snap.json", 86400, schedule_file=sf)
    data = json.loads(open(sf).read())
    assert "nightly" in data


def test_get_schedule_returns_entry(sf):
    add_schedule("daily", "daily.json", 86400, schedule_file=sf)
    entry = get_schedule("daily", schedule_file=sf)
    assert entry is not None
    assert entry.name == "daily"
    assert entry.output_path == "daily.json"
    assert entry.interval_seconds == 86400


def test_get_schedule_returns_none_when_missing(sf):
    assert get_schedule("ghost", schedule_file=sf) is None


def test_list_schedules_empty_when_no_file(sf):
    assert list_schedules(schedule_file=sf) == []


def test_list_schedules_returns_all(sf):
    add_schedule("a", "a.json", 60, schedule_file=sf)
    add_schedule("b", "b.json", 120, schedule_file=sf)
    names = [e.name for e in list_schedules(schedule_file=sf)]
    assert "a" in names and "b" in names


def test_remove_schedule_deletes_entry(sf):
    add_schedule("temp", "t.json", 60, schedule_file=sf)
    result = remove_schedule("temp", schedule_file=sf)
    assert result is True
    assert get_schedule("temp", schedule_file=sf) is None


def test_remove_schedule_missing_returns_false(sf):
    assert remove_schedule("nope", schedule_file=sf) is False


def test_due_schedules_returns_overdue(sf):
    past = time.time() - 9999
    add_schedule("old", "old.json", 60, schedule_file=sf)
    # force last_run to past by marking ran with past timestamp then re-check
    mark_ran("old", schedule_file=sf, now=past)
    due = due_schedules(schedule_file=sf)
    assert any(e.name == "old" for e in due)


def test_mark_ran_updates_last_run(sf):
    add_schedule("j", "j.json", 60, schedule_file=sf)
    now = time.time()
    entry = mark_ran("j", schedule_file=sf, now=now)
    assert entry is not None
    assert entry.last_run == now


def test_mark_ran_persists(sf):
    add_schedule("k", "k.json", 60, schedule_file=sf)
    ts = 99999.0
    mark_ran("k", schedule_file=sf, now=ts)
    loaded = get_schedule("k", schedule_file=sf)
    assert loaded.last_run == ts


def test_mark_ran_missing_returns_none(sf):
    assert mark_ran("ghost", schedule_file=sf) is None
