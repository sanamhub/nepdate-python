"""Smoke test for the patro package."""

from __future__ import annotations

import nepdate_patro


def test_nepdate_patro_imports() -> None:
    """Importing ``nepdate_patro`` succeeds and exposes a module docstring."""
    assert isinstance(nepdate_patro.__doc__, str)
