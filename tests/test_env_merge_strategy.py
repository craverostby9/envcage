import pytest
from envcage.env_merge_strategy import (
    apply_strategy,
    STRATEGY_LAST_WINS,
    STRATEGY_FIRST_WINS,
    STRATEGY_STRICT,
    StrategyResult,
)


snap_a = {"A": "1", "B": "2", "C": "shared"}
snap_b = {"B": "99", "C": "shared", "D": "4"}
snap_c = {"A": "1", "B": "77", "E": "5"}


def test_empty_list_returns_empty():
    result = apply_strategy([])
    assert result.env == {}
    assert not result.has_conflicts


def test_single_snapshot_returns_copy():
    result = apply_strategy([snap_a])
    assert result.env == snap_a


def test_last_wins_takes_last_value():
    result = apply_strategy([snap_a, snap_b], STRATEGY_LAST_WINS)
    assert result.env["B"] == "99"


def test_last_wins_records_conflict():
    result = apply_strategy([snap_a, snap_b], STRATEGY_LAST_WINS)
    assert "B" in result.conflicts


def test_last_wins_no_conflict_on_same_value():
    result = apply_strategy([snap_a, snap_b], STRATEGY_LAST_WINS)
    assert "C" not in result.conflicts


def test_last_wins_collects_all_keys():
    result = apply_strategy([snap_a, snap_b], STRATEGY_LAST_WINS)
    assert set(result.env.keys()) == {"A", "B", "C", "D"}


def test_first_wins_keeps_first_value():
    result = apply_strategy([snap_a, snap_b], STRATEGY_FIRST_WINS)
    assert result.env["B"] == "2"


def test_first_wins_records_conflict():
    result = apply_strategy([snap_a, snap_b], STRATEGY_FIRST_WINS)
    assert "B" in result.conflicts


def test_first_wins_includes_new_keys_from_later_snaps():
    result = apply_strategy([snap_a, snap_b], STRATEGY_FIRST_WINS)
    assert "D" in result.env


def test_strict_detects_conflict():
    result = apply_strategy([snap_a, snap_b], STRATEGY_STRICT)
    assert result.has_conflicts
    assert "B" in result.conflicts


def test_strict_no_conflict_when_identical():
    result = apply_strategy([snap_a, snap_a], STRATEGY_STRICT)
    assert not result.has_conflicts


def test_strategy_result_summary_contains_strategy():
    result = apply_strategy([snap_a, snap_b], STRATEGY_LAST_WINS)
    s = result.summary()
    assert STRATEGY_LAST_WINS in s


def test_strategy_result_summary_lists_conflicts():
    result = apply_strategy([snap_a, snap_b], STRATEGY_LAST_WINS)
    s = result.summary()
    assert "B" in s


def test_three_snapshots_last_wins():
    result = apply_strategy([snap_a, snap_b, snap_c], STRATEGY_LAST_WINS)
    assert result.env["B"] == "77"
