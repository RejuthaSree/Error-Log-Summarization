"""Smoke tests for the package scaffold."""

import errorsum


def test_version_is_exposed():
    assert isinstance(errorsum.__version__, str)
    assert errorsum.__version__
