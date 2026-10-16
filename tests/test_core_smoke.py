"""Smoke test for the core package."""

from __future__ import annotations

import nepdate
from nepdate import _calendar

_MIN_YEAR = 1901
_MAX_YEAR = 2199


def test_nepdate_imports() -> None:
    """Importing ``nepdate`` succeeds and exposes a module docstring."""
    assert isinstance(nepdate.__doc__, str)


def test_generated_calendar_constants() -> None:
    """The generated calendar module exposes the supported year range."""
    assert _calendar.MIN_YEAR == _MIN_YEAR
    assert _calendar.MAX_YEAR == _MAX_YEAR
