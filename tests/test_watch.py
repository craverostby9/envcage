"""Tests for envcage.watch."""

from __future__ import annotations

import pytest

from envcage.watch import WatchEvent, WatchSession, watch_once, watch
from envcage.diff import DiffResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def before_env():
    return {"APP_HOST": "localhost", "APP_PORT": "8080", "APP_DEBUG": "false"}


@pytest.fixture
def after_env():
    return {"APP_HOST": "prod.example.com", "APP_PORT": "443", "APP_NEW": "1"}


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_has_changes_when_diff_non_empty():
    diff = DiffResult(added={"X": "1"}, removed={}, changed={})
    event = WatchEvent(timestamp=0.0, diff=diff)
    assert event.has_changes() is True


def test_watch_event_no_changes_when_diff_empty():
    diff = DiffResult(added={}, removed={}, changed={})
    event = WatchEvent(timestamp=0.0, diff=diff)
    assert event.has_changes() is False


# ---------------------------------------------------------------------------
# watch_once
# ---------------------------------------------------------------------------

def test_watch_once_detects_added_key(before_env, after_env):
    event = watch_once(before=before_env, after=after_env)
    assert "APP_NEW" in event.diff.added


def test_watch_once_detects_removed_key(before_env, after_env):
    event = watch_once(before=before_env, after=after_env)
    assert "APP_DEBUG" in event.diff.removed


def test_watch_once_detects_changed_key(before_env, after_env):
    event = watch_once(before=before_env, after=after_env)
    assert "APP_HOST" in event.diff.changed


def test_watch_once_no_changes_identical_envs(before_env):
    event = watch_once(before=before_env, after=before_env)
    assert not event.has_changes()


def test_watch_once_returns_watch_event(before_env, after_env):
    event = watch_once(before=before_env, after=after_env)
    assert isinstance(event, WatchEvent)
    assert event.timestamp > 0


def test_watch_once_with_required_keys(before_env, after_env):
    event = watch_once(
        required_keys=["APP_HOST", "APP_PORT"],
        before=before_env,
        after=after_env,
    )
    assert event.has_changes()


# ---------------------------------------------------------------------------
# WatchSession
# ---------------------------------------------------------------------------

def test_watch_session_defaults():
    session = WatchSession()
    assert session.interval == 2.0
    assert session.max_events == 0
    assert session.events() == []


def test_watch_session_event_count_starts_zero():
    session = WatchSession()
    assert session.event_count() == 0


# ---------------------------------------------------------------------------
# watch (polling loop with max_events)
# ---------------------------------------------------------------------------

def test_watch_stops_after_max_events(monkeypatch):
    call_count = 0
    envs = [
        {"KEY": "v1"},
        {"KEY": "v2"},
        {"KEY": "v3"},
    ]

    def fake_capture(required_keys, env=None):
        nonlocal call_count
        idx = min(call_count, len(envs) - 1)
        call_count += 1
        from envcage.snapshot import capture as real_capture
        return real_capture(required_keys=required_keys, env=envs[idx])

    monkeypatch.setattr("envcage.watch.capture", fake_capture)
    monkeypatch.setattr("envcage.watch.time.sleep", lambda _: None)

    collected = []
    session = WatchSession(interval=0.0, max_events=2)
    watch(session, callback=collected.append, env=envs[0])

    assert session.event_count() == 2
    assert len(collected) == 2
