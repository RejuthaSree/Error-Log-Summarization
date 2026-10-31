"""Error-Log Summarization toolkit.

Turns noisy error logs into a concise, grouped summary of error signatures.
"""

__version__ = "0.1.0"

from errorsum.parser import LogRecord, parse_file, parse_line, parse_lines, parse_text
from errorsum.signature import compute_signature, normalize_message, signature_id
from errorsum.summarizer import ErrorGroup, Summary, summarize
from errorsum.report import render, render_json, render_markdown, render_text

__all__ = [
    "__version__",
    "LogRecord",
    "parse_line",
    "parse_lines",
    "parse_file",
    "parse_text",
    "normalize_message",
    "signature_id",
    "compute_signature",
    "ErrorGroup",
    "Summary",
    "summarize",
    "render",
    "render_text",
    "render_json",
    "render_markdown",
]
