"""Command-line interface for ``errorsum``."""

from __future__ import annotations

import argparse
import sys
from typing import Iterator, List, Optional, Sequence, TextIO

from errorsum import __version__
from errorsum.parser import LogRecord, parse_file, parse_lines
from errorsum.report import FORMATS, render
from errorsum.summarizer import summarize

__all__ = ["build_parser", "main"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="errorsum",
        description="Summarize error logs by grouping similar errors.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        metavar="LOG",
        help="Log files to read. Use '-' for stdin. Reads stdin when omitted.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=FORMATS,
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=None,
        help="Show only the N most frequent errors.",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        help="Drop errors occurring fewer than N times (default: 1).",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=3,
        help="Maximum example messages kept per error (default: 3).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include non-error records (INFO/DEBUG) in the summary.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"errorsum {__version__}",
    )
    return parser


def _iter_records(paths: Sequence[str], stdin: TextIO) -> Iterator[LogRecord]:
    if not paths:
        yield from parse_lines(stdin)
        return
    for path in paths:
        if path == "-":
            yield from parse_lines(stdin)
        else:
            yield from parse_file(path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)

    try:
        records: List[LogRecord] = list(_iter_records(args.paths, sys.stdin))
    except OSError as exc:
        print(f"errorsum: {exc}", file=sys.stderr)
        return 1

    summary = summarize(
        records,
        errors_only=not args.all,
        max_samples=args.max_samples,
        min_count=args.min_count,
        top=args.top,
    )
    sys.stdout.write(render(summary, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
