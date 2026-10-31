"""Tests for the command-line interface."""

import io
import json
import subprocess
import sys

from errorsum.cli import main

SAMPLE = (
    "2024-03-01 08:00:01 ERROR boom 1\n"
    "2024-03-01 08:00:02 ERROR boom 2\n"
    "2024-03-01 08:00:03 INFO everything ok\n"
)


def _write(tmp_path, text=SAMPLE):
    path = tmp_path / "app.log"
    path.write_text(text, encoding="utf-8")
    return path


def test_text_output(tmp_path, capsys):
    code = main([str(_write(tmp_path))])
    out = capsys.readouterr().out
    assert code == 0
    assert "Error Summary" in out
    assert "boom <NUM>" in out


def test_json_output(tmp_path, capsys):
    code = main([str(_write(tmp_path)), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["groups"][0]["count"] == 2


def test_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(SAMPLE))
    code = main(["-"])
    assert code == 0
    assert "boom <NUM>" in capsys.readouterr().out


def test_top_option(tmp_path, capsys):
    text = SAMPLE + "2024-03-01 08:00:04 WARN disk full\n"
    main([str(_write(tmp_path, text)), "--top", "1", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["groups"]) == 1
    assert payload["groups"][0]["count"] == 2


def test_all_flag_includes_info(tmp_path, capsys):
    main([str(_write(tmp_path)), "--all", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["distinct_signatures"] == 2


def test_missing_file_returns_error(capsys):
    code = main(["does-not-exist.log"])
    assert code == 1
    assert "errorsum:" in capsys.readouterr().err


def test_module_invocation_end_to_end(tmp_path):
    path = _write(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "errorsum", str(path), "--format", "markdown"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.startswith("# Error Summary")
