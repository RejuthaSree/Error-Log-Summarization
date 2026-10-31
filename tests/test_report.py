"""Tests for report rendering."""

import json

import pytest

from errorsum.parser import parse_text
from errorsum.report import render, render_json, render_markdown, render_text
from errorsum.summarizer import summarize

SAMPLE = "\n".join(
    [
        "2024-03-01 08:00:01 ERROR timeout after 30 seconds on 10.0.0.1",
        "2024-03-01 08:00:02 ERROR timeout after 45 seconds on 10.0.0.2",
        "2024-03-01 08:00:03 WARN disk almost full",
    ]
)


def _summary():
    return summarize(parse_text(SAMPLE))


def test_render_text_contains_key_sections():
    out = render_text(_summary())
    assert "Error Summary" in out
    assert "Records analyzed : 3 (3 at error level)" in out
    assert "Top errors" in out
    assert "timeout after <NUM> seconds on <IP>" in out
    assert "e.g. timeout after 30 seconds on 10.0.0.1" in out


def test_render_json_is_valid_and_complete():
    out = render_json(_summary())
    payload = json.loads(out)
    assert payload["distinct_signatures"] == 2
    assert payload["groups"][0]["count"] == 2
    assert payload["groups"][0]["signature_id"]


def test_render_markdown_has_table_and_details():
    out = render_markdown(_summary())
    assert out.startswith("# Error Summary")
    assert "| # | Count | Level(s) | Signature |" in out
    assert "## Details" in out


def test_render_dispatch():
    summary = _summary()
    assert render(summary, "text") == render_text(summary)
    assert render(summary, "json") == render_json(summary)
    assert render(summary, "markdown") == render_markdown(summary)


def test_render_unknown_format_raises():
    with pytest.raises(ValueError):
        render(_summary(), "yaml")


def test_empty_summary_messages():
    empty = summarize(parse_text("2024-03-01 08:00:01 INFO all good"))
    assert "No errors matched." in render_text(empty)
    assert "_No errors matched._" in render_markdown(empty)
    assert json.loads(render_json(empty))["groups"] == []
