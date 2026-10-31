# Error-Log Summarization

A small, dependency-free Python toolkit that turns noisy error logs into a
concise summary: it parses log lines, normalizes each message into a stable
*error signature*, clusters identical signatures together, and reports the most
frequent errors with their first/last occurrence and sample messages.

The core is fully offline and deterministic (rule-based / statistical), so it is
easy to test and safe to run on sensitive logs.

## Status

Under active development. Planned features are added one at a time, each with
its own tests and commit.

## Development

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"   # Windows
pytest
```

## Roadmap

1. Package scaffolding
2. Log parsing into structured records
3. Error signature extraction
4. Aggregation / summarization engine
5. Report rendering (text / JSON / Markdown)
6. Command-line interface
