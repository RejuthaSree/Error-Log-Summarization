"""Parse raw log lines into structured :class:`LogRecord` objects.

The parser is deliberately permissive: it recognises the most common timestamp
and log-level layouts, and falls back to treating the whole line as the message
when no known structure is found.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Union

__all__ = [
    "LogRecord",
    "parse_line",
    "parse_lines",
    "parse_file",
    "parse_text",
    "LEVEL_ALIASES",
]

#: Canonical set of levels we recognise (case-insensitive on input).
LEVEL_ALIASES = {
    "WARNING": "WARN",
    "FATAL": "CRITICAL",
    "ERR": "ERROR",
    "CRIT": "CRITICAL",
}

_LEVEL_TOKEN = r"CRITICAL|FATAL|CRIT|ERROR|ERR|WARN|WARNING|NOTICE|INFO|DEBUG|TRACE"
_LEVEL_RE = re.compile(rf"\b({_LEVEL_TOKEN})\b", re.IGNORECASE)

# Leading timestamp, optionally wrapped in square brackets.
_TIMESTAMP_RE = re.compile(
    r"^\s*\[?"
    r"(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d{1,6})?(?:Z|[+-]\d{2}:?\d{2})?)"
    r"\]?\s*"
)

# A bracketed logger/source token, e.g. "[com.example.Foo]".
_SOURCE_RE = re.compile(r"^\[(?P<source>[^\]\s]+)\]\s*")

_TIMESTAMP_FORMATS = (
    "%Y-%m-%d %H:%M:%S.%f%z",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
)


@dataclass
class LogRecord:
    """A single parsed log line."""

    raw: str
    message: str
    level: Optional[str] = None
    timestamp: Optional[datetime] = None
    source: Optional[str] = None

    @property
    def is_error(self) -> bool:
        """Whether this record is at error severity or above."""
        return self.level in {"CRITICAL", "ERROR", "WARN"}


def _normalize_level(token: str) -> str:
    upper = token.upper()
    return LEVEL_ALIASES.get(upper, upper)


def _parse_timestamp(value: str) -> Optional[datetime]:
    """Best-effort parse of a captured timestamp token."""
    raw = value.replace(",", ".")
    if raw.endswith("Z") or raw.endswith("z"):
        raw = raw[:-1] + "+00:00"
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def parse_line(line: str) -> Optional[LogRecord]:
    """Parse a single line into a :class:`LogRecord`.

    Returns ``None`` for blank lines. Lines without a recognised level are still
    returned, with :attr:`LogRecord.level` set to ``None``.
    """
    text = line.rstrip("\r\n")
    if not text.strip():
        return None

    rest = text
    timestamp: Optional[datetime] = None

    match = _TIMESTAMP_RE.match(text)
    if match:
        timestamp = _parse_timestamp(match.group("ts"))
        rest = text[match.end():]

    level: Optional[str] = None
    level_match = _LEVEL_RE.search(rest)
    if level_match:
        level = _normalize_level(level_match.group(1))
        rest = rest[level_match.end():]

    source: Optional[str] = None
    source_match = _SOURCE_RE.match(rest.lstrip())
    if source_match:
        source = source_match.group("source")
        rest = rest.lstrip()[source_match.end():]

    return LogRecord(
        raw=text,
        message=rest.strip(),
        level=level,
        timestamp=timestamp,
        source=source,
    )


def parse_lines(lines: Iterable[str]) -> Iterator[LogRecord]:
    """Parse an iterable of lines, joining indented continuation lines.

    Stack traces and other multi-line messages are appended to the record that
    started them, so a traceback stays attached to its error record.
    """
    previous: Optional[LogRecord] = None
    for line in lines:
        text = line.rstrip("\r\n")
        if not text.strip():
            continue

        is_indented = text[:1].isspace()
        starts_record = bool(_TIMESTAMP_RE.match(text)) or _LEVEL_RE.search(text) is not None

        if is_indented and not starts_record and previous is not None:
            previous.message = f"{previous.message}\n{text.strip()}"
            previous.raw = f"{previous.raw}\n{text}"
            continue

        record = parse_line(text)
        if record is None:
            continue
        if previous is not None:
            yield previous
        previous = record

    if previous is not None:
        yield previous


def parse_file(
    path: Union[str, Path],
    *,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> Iterator[LogRecord]:
    """Parse a log file from disk."""
    with Path(path).open("r", encoding=encoding, errors=errors) as handle:
        yield from parse_lines(handle)


def parse_text(text: str) -> List[LogRecord]:
    """Parse a log blob held in memory."""
    return list(parse_lines(text.splitlines()))
