"""Tests for envcage.export module."""

from __future__ import annotations

import json
import pytest

from envcage.export import to_dotenv, to_shell, to_json, export_snapshot, export_snapshot_to_file


@pytest.fixture
def simple_env():
    return {"APP_ENV": "production", "PORT": "8080", "DEBUG": "false"}


@pytest.fixture
def complex_env():
    return {
        "GREETING": "hello world",
        "PATH_VAR": "/usr/local/bin",
        "QUOTED": 'say "hi"',
    }


def test_to_dotenv_simple(simple_env):
    result = to_dotenv(simple_env)
    assert "APP_ENV=production" in result
    assert "PORT=8080" in result
    assert "DEBUG=false" in result


def test_to_dotenv_quotes_values_with_spaces(complex_env):
    result = to_dotenv(complex_env)
    assert 'GREETING="hello world"' in result


def test_to_dotenv_quotes_values_with_double_quotes(complex_env):
    result = to_dotenv(complex_env)
    assert 'QUOTED=' in result
    line = [l for l in result.splitlines() if l.startswith("QUOTED=")][0]
    assert line.startswith('QUOTED="')


def test_to_dotenv_ends_with_newline(simple_env):
    assert to_dotenv(simple_env).endswith("\n")


def test_to_dotenv_empty_env():
    assert to_dotenv({}) == ""


def test_to_shell_uses_export(simple_env):
    result = to_shell(simple_env)
    for line in result.strip().splitlines():
        assert line.startswith("export ")


def test_to_shell_quotes_values_with_spaces(complex_env):
    result = to_shell(complex_env)
    assert "export GREETING='hello world'" in result


def test_to_shell_ends_with_newline(simple_env):
    assert to_shell(simple_env).endswith("\n")


def test_to_json_is_valid_json(simple_env):
    result = to_json(simple_env)
    parsed = json.loads(result)
    assert parsed == simple_env


def test_to_json_is_sorted(simple_env):
    result = to_json(simple_env)
    parsed = json.loads(result)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_export_snapshot_dotenv(tmp_path, simple_env):
    import json as _json
    snap_file = tmp_path / "snap.json"
    snap_file.write_text(_json.dumps({"env": simple_env}), encoding="utf-8")
    result = export_snapshot(str(snap_file), fmt="dotenv")
    assert "APP_ENV=production" in result


def test_export_snapshot_shell(tmp_path, simple_env):
    import json as _json
    snap_file = tmp_path / "snap.json"
    snap_file.write_text(_json.dumps({"env": simple_env}), encoding="utf-8")
    result = export_snapshot(str(snap_file), fmt="shell")
    assert "export PORT='8080'" in result or "export PORT=8080" in result


def test_export_snapshot_invalid_format(tmp_path, simple_env):
    import json as _json
    snap_file = tmp_path / "snap.json"
    snap_file.write_text(_json.dumps({"env": simple_env}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_snapshot(str(snap_file), fmt="xml")  # type: ignore


def test_export_snapshot_to_file(tmp_path, simple_env):
    import json as _json
    snap_file = tmp_path / "snap.json"
    out_file = tmp_path / "output.env"
    snap_file.write_text(_json.dumps({"env": simple_env}), encoding="utf-8")
    export_snapshot_to_file(str(snap_file), str(out_file), fmt="dotenv")
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "APP_ENV=production" in content
