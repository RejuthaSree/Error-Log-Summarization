# Error-Log Summarization

A small, dependency-free Python toolkit that turns noisy error logs into a
concise summary: it parses log lines, normalizes each message into a stable
*error signature*, clusters identical signatures together, and reports the most
frequent errors with their first/last occurrence and sample messages.

The core is fully offline and deterministic (rule-based / statistical), so it is
easy to test and safe to run on sensitive logs.

## Install

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"   # Windows
# source .venv/bin/activate && pip install -e ".[dev]"   # macOS / Linux
```

## Usage

Summarize one or more log files:

```bash
errorsum path/to/app.log
errorsum logs/*.log --format markdown --top 10 --min-count 2
errorsum - --format json < app.log
```

Options:

| Option | Description |
| --- | --- |
| `-f, --format {text,json,markdown}` | Output format (default: `text`). |
| `-n, --top N` | Show only the N most frequent errors. |
| `--min-count N` | Drop errors occurring fewer than N times. |
| `--max-samples N` | Example messages kept per error (default: 3). |
| `--all` | Include non-error records (INFO/DEBUG). |

Library usage:

```python
from errorsum import parse_file, summarize, render

summary = summarize(parse_file("examples/sample.log"))
print(render(summary, "markdown"))
```

## Tests

```bash
pytest
```
