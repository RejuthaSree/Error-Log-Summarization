"""Tests for the log parser."""

from datetime import datetime

from errorsum.parser import LogRecord, parse_file, parse_line, parse_lines, parse_text


def test_parse_iso_line():
    record = parse_line("2024-03-01T08:15:30Z ERROR Failed to connect to db")
    assert record is not None
    assert record.level == "ERROR"
    assert record.message == "Failed to connect to db"
    assert record.timestamp == datetime(2024, 3, 1, 8, 15, 30, tzinfo=record.timestamp.tzinfo)
    assert record.is_error is True


def test_parse_log4j_style_with_millis_and_source():
    record = parse_line("2024-03-01 08:15:30,123 ERROR [com.example.Foo] boom")
    assert record.level == "ERROR"
    assert record.source == "com.example.Foo"
    assert record.message == "boom"
    assert record.timestamp.microsecond == 123000


def test_parse_bracketed_timestamp_and_warning_alias():
    record = parse_line("[2024-03-01 08:15:30] WARNING disk almost full")
    assert record.level == "WARN"
    assert record.message == "disk almost full"
    assert record.timestamp == datetime(2024, 3, 1, 8, 15, 30)


def test_line_without_timestamp_still_parsed():
    record = parse_line("INFO server started")
    assert record.timestamp is None
    assert record.level == "INFO"
    assert record.message == "server started"


def test_line_without_level_keeps_message():
    record = parse_line("just some free text")
    assert record.level is None
    assert record.message == "just some free text"
    assert record.is_error is False


def test_blank_line_returns_none():
    assert parse_line("   \n") is None


def test_non_error_levels_not_flagged():
    assert parse_line("2024-03-01 08:15:30 DEBUG warmup").is_error is False
    assert parse_line("2024-03-01 08:15:30 CRITICAL kernel panic").is_error is True


def test_parse_lines_joins_indented_continuation():
    text = (
        "2024-03-01 08:15:30 ERROR request failed\n"
        "    Traceback (most recent call last):\n"
        "      File \"a.py\", line 1\n"
        "2024-03-01 08:15:31 INFO recovered\n"
    )
    records = list(parse_lines(text.splitlines()))
    assert len(records) == 2
    assert "Traceback (most recent call last):" in records[0].message
    assert 'File "a.py", line 1' in records[0].message
    assert records[1].message == "recovered"


def test_parse_text_multiple_records():
    records = parse_text("2024-03-01 08:15:30 ERROR a\n\n2024-03-01 08:15:31 ERROR b\n")
    assert [r.message for r in records] == ["a", "b"]


def test_parse_file(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("2024-03-01 08:15:30 ERROR boom\n", encoding="utf-8")
    records = list(parse_file(log))
    assert len(records) == 1
    assert records[0].level == "ERROR"


def test_is_error_property_for_none_level():
    assert LogRecord(raw="x", message="x").is_error is False
