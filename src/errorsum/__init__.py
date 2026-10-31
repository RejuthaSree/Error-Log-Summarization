"""Error-Log Summarization toolkit.

Turns noisy error logs into a concise, grouped summary of error signatures.
"""

__version__ = "0.1.0"

from errorsum.parser import LogRecord, parse_file, parse_line, parse_lines, parse_text

__all__ = [
    "__version__",
    "LogRecord",
    "parse_line",
    "parse_lines",
    "parse_file",
    "parse_text",
]
