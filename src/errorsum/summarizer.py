"""Aggregate parsed records into a grouped error summary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from errorsum.parser import LogRecord
from errorsum.signature import compute_signature

__all__ = ["ErrorGroup", "Summary", "summarize"]


@dataclass
class ErrorGroup:
    """All occurrences that share one normalized error signature."""

    signature: str
    signature_id: str
    count: int = 0
    levels: Dict[str, int] = field(default_factory=dict)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    sources: Dict[str, int] = field(default_factory=dict)
    samples: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "signature": self.signature,
            "signature_id": self.signature_id,
            "count": self.count,
            "levels": dict(self.levels),
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "sources": dict(self.sources),
            "samples": list(self.samples),
        }


@dataclass
class Summary:
    """Result of summarizing a set of log records."""

    total_records: int
    error_records: int
    distinct_signatures: int
    groups: List[ErrorGroup]
    by_level: Dict[str, int] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "total_records": self.total_records,
            "error_records": self.error_records,
            "distinct_signatures": self.distinct_signatures,
            "by_level": dict(self.by_level),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "groups": [group.to_dict() for group in self.groups],
        }


def summarize(
    records: Iterable[LogRecord],
    *,
    errors_only: bool = True,
    max_samples: int = 3,
    min_count: int = 1,
    top: Optional[int] = None,
) -> Summary:
    """Group records by signature and return an aggregated :class:`Summary`.

    Args:
        records: Parsed log records.
        errors_only: When ``True`` (default), only ERROR/CRITICAL/WARN records
            are summarized; otherwise every record is included.
        max_samples: Maximum number of distinct example messages kept per group.
        min_count: Drop groups occurring fewer than this many times.
        top: Keep only the ``top`` most frequent groups (after sorting).
    """
    all_records = list(records)
    considered = [r for r in all_records if r.is_error or not errors_only]

    groups: Dict[str, ErrorGroup] = {}
    by_level: Dict[str, int] = {}
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    for record in considered:
        signature, sig_id = compute_signature(record.message)
        group = groups.get(sig_id)
        if group is None:
            group = ErrorGroup(signature=signature, signature_id=sig_id)
            groups[sig_id] = group

        group.count += 1

        if record.level:
            group.levels[record.level] = group.levels.get(record.level, 0) + 1
            by_level[record.level] = by_level.get(record.level, 0) + 1

        if record.source:
            group.sources[record.source] = group.sources.get(record.source, 0) + 1

        if record.message not in group.samples and len(group.samples) < max_samples:
            group.samples.append(record.message)

        if record.timestamp is not None:
            if group.first_seen is None or record.timestamp < group.first_seen:
                group.first_seen = record.timestamp
            if group.last_seen is None or record.timestamp > group.last_seen:
                group.last_seen = record.timestamp
            if started_at is None or record.timestamp < started_at:
                started_at = record.timestamp
            if ended_at is None or record.timestamp > ended_at:
                ended_at = record.timestamp

    ordered = sorted(groups.values(), key=lambda g: (-g.count, g.signature))
    ordered = [g for g in ordered if g.count >= min_count]
    filtered = ordered[:top] if top is not None else ordered

    return Summary(
        total_records=len(all_records),
        error_records=sum(1 for r in all_records if r.is_error),
        distinct_signatures=len(groups),
        groups=filtered,
        by_level=by_level,
        started_at=started_at,
        ended_at=ended_at,
    )
