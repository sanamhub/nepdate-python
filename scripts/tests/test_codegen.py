"""Unit tests for ``scripts/codegen.py``."""

from __future__ import annotations

import json
from typing import Any, cast

import pytest


def _shipped_calendar(codegen: Any) -> dict[str, Any]:
    """Load a copy of the shipped calendar JSON.

    Args:
        codegen: The loaded codegen module.

    Returns:
        The parsed calendar data.
    """
    raw = json.loads(codegen.CALENDAR_JSON.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw)


def test_validate_accepts_shipped_data(codegen: Any) -> None:
    """The shipped calendar passes validation without raising."""
    codegen.validate_calendar(_shipped_calendar(codegen))


def test_validate_rejects_length_33(codegen: Any) -> None:
    """A month length of 33 is rejected."""
    data = _shipped_calendar(codegen)
    data["month_lengths"]["1901"][0] = 33
    with pytest.raises(ValueError):
        codegen.validate_calendar(data)


def test_generate_is_deterministic(codegen: Any) -> None:
    """The rendered module is byte for byte stable."""
    data = _shipped_calendar(codegen)
    assert codegen.generate_calendar_py(data) == codegen.generate_calendar_py(data)


def test_generated_calendar_matches_file(codegen: Any) -> None:
    """The on-disk ``_calendar.py`` matches what the generator would write."""
    data = _shipped_calendar(codegen)
    assert codegen.CALENDAR_PY.read_text(encoding="utf-8") == codegen.generate_calendar_py(data)
