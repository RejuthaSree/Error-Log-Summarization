"""Tests for the aggregation / summarization engine."""

from datetime import datetime

from errorsum.parser import LogRecord
from errorsum.summarizer import summarize

SAMPLE = "\n".join(
    [
        "2024-03-01 08:00:00 INFO server started",
        "2024-03-01 08:00:01 ERROR timeout after 30 seconds on 10.0.0.1",
        "2024-03-01 08:00:02 ERROR timeout after 45 seconds on 10.0.0.2",
        "2024-03-01 08:00:03 WARN disk almost full",
        "2024-03-01 08:00:04 ERROR timeout after 12 seconds on 10.0.0.3",
        "2024-03-01 08:00:05 DEBUG cache warm",
    ]
)


def _records():
    from errorsum.parser import parse_text

    return parse_text(SAMPLE)


def test_counts_and_distinct_signatures():
    summary = summarize(_records())
    assert summary.total_records == 6
    assert summary.error_records == 4  # 3 ERROR + 1 WARN
    assert summary.distinct_signatures == 2  # timeout group + disk group
    assert len(summary.groups) == 2


def test_volatile_values_are_grouped():
    summary = summarize(_records())
    top = summary.groups[0]
    assert top.count == 3
    assert top.signature == "timeout after <NUM> seconds on <IP>"
    assert top.samples[0] == "timeout after 30 seconds on 10.0.0.1"


def test_groups_sorted_by_count_desc():
    summary = summarize(_records())
    assert [g.count for g in summary.groups] == [3, 1]


def test_errors_only_excludes_info_and_debug():
    summary = summarize(_records(), errors_only=False)
    assert summary.distinct_signatures == 4  # adds INFO and DEBUG groups


def test_min_count_filters_rare_groups():
    summary = summarize(_records(), min_count=2)
    assert len(summary.groups) == 1
    assert summary.groups[0].count == 3


def test_top_limits_groups():
    summary = summarize(_records(), top=1)
    assert len(summary.groups) == 1
    assert summary.groups[0].count == 3


def test_max_samples_caps_distinct_examples():
    summary = summarize(_records(), max_samples=2)
    top = summary.groups[0]
    assert len(top.samples) == 2


def test_first_and_last_seen():
    summary = summarize(_records())
    top = summary.groups[0]
    assert top.first_seen == datetime(2024, 3, 1, 8, 0, 1)
    assert top.last_seen == datetime(2024, 3, 1, 8, 0, 4)
    assert summary.started_at == datetime(2024, 3, 1, 8, 0, 1)
    assert summary.ended_at == datetime(2024, 3, 1, 8, 0, 4)


def test_by_level_counts():
    summary = summarize(_records())
    assert summary.by_level == {"ERROR": 3, "WARN": 1}


def test_sources_tracked():
    records = [
        LogRecord(raw="", message="boom", level="ERROR", source="svc.a"),
        LogRecord(raw="", message="boom", level="ERROR", source="svc.b"),
    ]
    summary = summarize(records)
    assert summary.groups[0].sources == {"svc.a": 1, "svc.b": 1}


def test_to_dict_round_trip_keys():
    summary = summarize(_records())
    payload = summary.to_dict()
    assert set(payload) >= {
        "total_records",
        "error_records",
        "distinct_signatures",
        "groups",
        "by_level",
    }
    assert payload["groups"][0]["count"] == 3
