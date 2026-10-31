"""Render a :class:`~errorsum.summarizer.Summary` as text, JSON, or Markdown."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from errorsum.summarizer import ErrorGroup, Summary

__all__ = ["render", "render_text", "render_json", "render_markdown", "FORMATS"]

FORMATS = ("text", "json", "markdown")


def _fmt_dt(value: Optional[datetime]) -> str:
    return value.isoformat(sep=" ") if value is not None else "-"


def _levels(group: ErrorGroup) -> str:
    return ",".join(sorted(group.levels)) or "-"


def render_text(summary: Summary) -> str:
    """Render a human-readable plain-text report."""
    lines: List[str] = [
        "Error Summary",
        "=============",
        f"Records analyzed : {summary.total_records} ({summary.error_records} at error level)",
        f"Distinct errors  : {summary.distinct_signatures}",
        f"Window           : {_fmt_dt(summary.started_at)} .. {_fmt_dt(summary.ended_at)}",
    ]
    if summary.by_level:
        levels = ", ".join(f"{level}={count}" for level, count in sorted(summary.by_level.items()))
        lines.append(f"Levels           : {levels}")

    lines.append("")
    if not summary.groups:
        lines.append("No errors matched.")
        return "\n".join(lines) + "\n"

    lines.append("Top errors")
    lines.append("----------")
    for index, group in enumerate(summary.groups, start=1):
        lines.append(f"{index}. x{group.count} [{_levels(group)}] {group.signature}")
        lines.append(
            f"   id={group.signature_id} "
            f"first={_fmt_dt(group.first_seen)} last={_fmt_dt(group.last_seen)}"
        )
        for sample in group.samples:
            lines.append(f"   e.g. {sample}")
    return "\n".join(lines) + "\n"


def render_json(summary: Summary) -> str:
    """Render the summary as pretty-printed JSON."""
    return json.dumps(summary.to_dict(), indent=2, ensure_ascii=False) + "\n"


def render_markdown(summary: Summary) -> str:
    """Render a Markdown report with a summary table and per-error details."""
    lines: List[str] = [
        "# Error Summary",
        "",
        f"- **Records:** {summary.total_records} total ({summary.error_records} at error level)",
        f"- **Distinct signatures:** {summary.distinct_signatures}",
        f"- **Window:** {_fmt_dt(summary.started_at)} .. {_fmt_dt(summary.ended_at)}",
    ]
    if summary.by_level:
        levels = ", ".join(f"{level}: {count}" for level, count in sorted(summary.by_level.items()))
        lines.append(f"- **Levels:** {levels}")

    lines.append("")
    if not summary.groups:
        lines.append("_No errors matched._")
        return "\n".join(lines) + "\n"

    lines.append("## Top errors")
    lines.append("")
    lines.append("| # | Count | Level(s) | Signature |")
    lines.append("|---|-------|----------|-----------|")
    for index, group in enumerate(summary.groups, start=1):
        signature = group.signature.replace("|", "\\|")
        lines.append(f"| {index} | {group.count} | {_levels(group)} | `{signature}` |")

    lines.append("")
    lines.append("## Details")
    for index, group in enumerate(summary.groups, start=1):
        lines.append("")
        lines.append(f"### {index}. {group.signature}")
        lines.append(f"- **Count:** {group.count}")
        lines.append(f"- **Levels:** {_levels(group)}")
        lines.append(f"- **First seen:** {_fmt_dt(group.first_seen)}")
        lines.append(f"- **Last seen:** {_fmt_dt(group.last_seen)}")
        if group.sources:
            lines.append(f"- **Sources:** {', '.join(sorted(group.sources))}")
        for sample in group.samples:
            lines.append(f"- _e.g._ `{sample}`")
    return "\n".join(lines) + "\n"


_RENDERERS = {
    "text": render_text,
    "json": render_json,
    "markdown": render_markdown,
}


def render(summary: Summary, fmt: str = "text") -> str:
    """Render ``summary`` using the renderer named by ``fmt``."""
    try:
        renderer = _RENDERERS[fmt]
    except KeyError:
        raise ValueError(
            f"unknown format {fmt!r}; expected one of {', '.join(FORMATS)}"
        ) from None
    return renderer(summary)
