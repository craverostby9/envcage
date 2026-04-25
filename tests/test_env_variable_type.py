"""Tests for envcage.env_variable_type."""
import pytest
from envcage.env_variable_type import (
    infer_type,
    analyze_snapshot,
    TypeReport,
    TypeInference,
    INFERRED_TYPES,
)


# ---------------------------------------------------------------------------
# infer_type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    ("true", "bool"),
    ("True", "bool"),
    ("YES", "bool"),
    ("false", "bool"),
    ("0", "bool"),
    ("off", "bool"),
    ("1", "bool"),
    ("42", "int"),
    ("-7", "int"),
    ("3.14", "float"),
    ("-0.5", "float"),
    ("https://example.com", "url"),
    ("http://localhost:8080", "url"),
    ("user@example.com", "email"),
    ("/usr/local/bin", "path"),
    ("~/projects", "path"),
    ("C:\\Windows", "path"),
    ("", "empty"),
    ("hello world", "string"),
    ("some_value_123", "string"),
])
def test_infer_type(value, expected):
    assert infer_type(value) == expected


def test_infer_type_returns_known_type():
    for v in ["true", "1", "3.14", "https://x.com", "a@b.com", "/p", "", "abc"]:
        assert infer_type(v) in INFERRED_TYPES


# ---------------------------------------------------------------------------
# analyze_snapshot
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_env():
    return {
        "PORT": "8080",
        "DEBUG": "true",
        "API_URL": "https://api.example.com",
        "LABEL": "production",
        "RATIO": "0.75",
        "CONTACT": "ops@example.com",
        "LOG_DIR": "/var/log",
        "EMPTY_KEY": "",
    }


def test_analyze_returns_type_report(simple_env):
    report = analyze_snapshot(simple_env)
    assert isinstance(report, TypeReport)


def test_analyze_infers_int(simple_env):
    report = analyze_snapshot(simple_env)
    port = next(i for i in report.inferences if i.key == "PORT")
    assert port.inferred_type == "int"


def test_analyze_infers_bool(simple_env):
    report = analyze_snapshot(simple_env)
    debug = next(i for i in report.inferences if i.key == "DEBUG")
    assert debug.inferred_type == "bool"


def test_analyze_infers_url(simple_env):
    report = analyze_snapshot(simple_env)
    url = next(i for i in report.inferences if i.key == "API_URL")
    assert url.inferred_type == "url"


def test_analyze_infers_email(simple_env):
    report = analyze_snapshot(simple_env)
    entry = next(i for i in report.inferences if i.key == "CONTACT")
    assert entry.inferred_type == "email"


def test_analyze_infers_path(simple_env):
    report = analyze_snapshot(simple_env)
    entry = next(i for i in report.inferences if i.key == "LOG_DIR")
    assert entry.inferred_type == "path"


def test_analyze_infers_empty(simple_env):
    report = analyze_snapshot(simple_env)
    entry = next(i for i in report.inferences if i.key == "EMPTY_KEY")
    assert entry.inferred_type == "empty"


def test_analyze_no_mismatches_when_no_expected(simple_env):
    report = analyze_snapshot(simple_env)
    assert not report.any_mismatches


def test_analyze_detects_mismatch(simple_env):
    expected = {"PORT": "string"}  # PORT is actually int
    report = analyze_snapshot(simple_env, expected=expected)
    assert report.any_mismatches
    mismatch = report.mismatches[0]
    assert mismatch.key == "PORT"
    assert mismatch.inferred_type == "int"
    assert mismatch.expected_type == "string"


def test_analyze_no_mismatch_when_types_match(simple_env):
    expected = {"PORT": "int", "DEBUG": "bool"}
    report = analyze_snapshot(simple_env, expected=expected)
    assert not report.any_mismatches


def test_analyze_ignores_unknown_keys_in_expected(simple_env):
    expected = {"NONEXISTENT_KEY": "int"}
    report = analyze_snapshot(simple_env, expected=expected)
    assert not report.any_mismatches


def test_summary_no_mismatches(simple_env):
    report = analyze_snapshot(simple_env)
    assert "match" in report.summary()


def test_summary_with_mismatches(simple_env):
    expected = {"PORT": "string", "RATIO": "bool"}
    report = analyze_snapshot(simple_env, expected=expected)
    s = report.summary()
    assert "2" in s
    assert "PORT" in s
    assert "RATIO" in s


def test_to_dict_round_trips():
    ti = TypeInference(
        key="X", value="42", inferred_type="int", expected_type="string", mismatch=True
    )
    d = ti.to_dict()
    assert d["key"] == "X"
    assert d["inferred_type"] == "int"
    assert d["expected_type"] == "string"
    assert d["mismatch"] is True
