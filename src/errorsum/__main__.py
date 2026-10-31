"""Allow ``python -m errorsum`` to invoke the CLI."""

from errorsum.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
