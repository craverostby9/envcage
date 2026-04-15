"""Tests for envcage.baseline."""

from __future__ import annotations

import json
import pytest

from envcage.baseline import (
    set_baseline,
    get_baseline,
    remove_baseline,
    list_baselines,
    drift_from_baseline,
)
from envcage.snapshot import save


@pytest.fixture()
def bf(tmp_path):
    return str(tmp_path / "baselines.json")


@pytest.fixture()
def snap_file(tmp_path):
    path = str(tmp_path / "snap.json")
    save({"env": {"APP": "1", "DB": "postgres"}, "required": []}, path)
    return path


def test_set_baseline_creates_entry(bf, snap_file):
    set_baseline("prod", snap_file, bf)
    assert get_baseline("prod", bf) == snap_file


def test_get_baseline_returns_none_when_missing(bf):
    assert get_baseline("nonexistent", bf) is None


def test_set_baseline_persists_to_file(bf, snap_file):
    set_baseline("staging", snap_file, bf)
    raw = json.loads(open(bf).read())
    assert "staging" in raw


def test_set_baseline_overwrites_existing(bf, snap_file, tmp_path):
    other = str(tmp_path / "other.json")
    save({"env": {}, "required": []}, other)
    set_baseline("prod", snap_file, bf)
    set_baseline("prod", other, bf)
    assert get_baseline("prod", bf) == other


def test_remove_baseline_returns_true_when_existed(bf, snap_file):
    set_baseline("prod", snap_file, bf)
    assert remove_baseline("prod", bf) is True


def test_remove_baseline_returns_false_when_missing(bf):
    assert remove_baseline("ghost", bf) is False


def test_remove_baseline_deletes_entry(bf, snap_file):
    set_baseline("prod", snap_file, bf)
    remove_baseline("prod", bf)
    assert get_baseline("prod", bf) is None


def test_list_baselines_empty(bf):
    assert list_baselines(bf) == {}


def test_list_baselines_multiple(bf, snap_file):
    set_baseline("a", snap_file, bf)
    set_baseline("b", snap_file, bf)
    result = list_baselines(bf)
    assert set(result.keys()) == {"a", "b"}


def test_drift_from_baseline_detects_added_key(bf, snap_file):
    set_baseline("prod", snap_file, bf)
    current = {"env": {"APP": "1", "DB": "postgres", "NEW": "x"}, "required": []}
    result = drift_from_baseline("prod", current, bf)
    assert "NEW" in result.added


def test_drift_from_baseline_detects_removed_key(bf, snap_file):
    set_baseline("prod", snap_file, bf)
    current = {"env": {"APP": "1"}, "required": []}
    result = drift_from_baseline("prod", current, bf)
    assert "DB" in result.removed


def test_drift_from_baseline_raises_for_unknown_label(bf):
    with pytest.raises(KeyError, match="no_label"):
        drift_from_baseline("no_label", {"env": {}, "required": []}, bf)
