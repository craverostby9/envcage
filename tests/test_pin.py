"""Tests for envcage.pin module."""

from __future__ import annotations

import json
import pytest

from envcage.pin import (
    pin_snapshot,
    unpin_snapshot,
    get_pin,
    list_pins,
    pin_labels,
)


@pytest.fixture
def pin_file(tmp_path):
    return str(tmp_path / "pins.json")


def test_pin_snapshot_creates_entry(pin_file):
    pin_snapshot("stable", "snapshots/stable.json", pin_file=pin_file)
    pins = list_pins(pin_file=pin_file)
    assert "stable" in pins
    assert pins["stable"] == "snapshots/stable.json"


def test_pin_snapshot_persists_to_file(pin_file):
    pin_snapshot("prod", "snapshots/prod.json", pin_file=pin_file)
    with open(pin_file) as fh:
        data = json.load(fh)
    assert data["prod"] == "snapshots/prod.json"


def test_pin_snapshot_overwrites_existing_label(pin_file):
    pin_snapshot("stable", "snapshots/v1.json", pin_file=pin_file)
    pin_snapshot("stable", "snapshots/v2.json", pin_file=pin_file)
    assert get_pin("stable", pin_file=pin_file) == "snapshots/v2.json"


def test_pin_multiple_labels(pin_file):
    pin_snapshot("alpha", "a.json", pin_file=pin_file)
    pin_snapshot("beta", "b.json", pin_file=pin_file)
    pins = list_pins(pin_file=pin_file)
    assert len(pins) == 2


def test_unpin_removes_label(pin_file):
    pin_snapshot("release", "r.json", pin_file=pin_file)
    result = unpin_snapshot("release", pin_file=pin_file)
    assert result is True
    assert get_pin("release", pin_file=pin_file) is None


def test_unpin_returns_false_when_not_found(pin_file):
    result = unpin_snapshot("nonexistent", pin_file=pin_file)
    assert result is False


def test_get_pin_returns_none_when_missing(pin_file):
    assert get_pin("missing", pin_file=pin_file) is None


def test_get_pin_returns_path(pin_file):
    pin_snapshot("v1", "snapshots/v1.json", pin_file=pin_file)
    assert get_pin("v1", pin_file=pin_file) == "snapshots/v1.json"


def test_list_pins_empty_when_no_file(pin_file):
    assert list_pins(pin_file=pin_file) == {}


def test_pin_labels_sorted(pin_file):
    pin_snapshot("zebra", "z.json", pin_file=pin_file)
    pin_snapshot("alpha", "a.json", pin_file=pin_file)
    pin_snapshot("mango", "m.json", pin_file=pin_file)
    assert pin_labels(pin_file=pin_file) == ["alpha", "mango", "zebra"]


def test_pin_labels_empty_when_no_pins(pin_file):
    assert pin_labels(pin_file=pin_file) == []
