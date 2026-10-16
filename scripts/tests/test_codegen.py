"""Unit tests for ``scripts/codegen.py``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

_MONTHS = 3588
_MONTH_BOUNDARIES = 3589
_YEARS = 300
_TOTAL_DAYS = 109212
_BUCKETS = 3413
_OFFSET = 673243


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


def test_generate_tables_match_acceptance_counts(codegen: Any) -> None:
    """The generated tables have the sizes P1-01 promises."""
    data = _shipped_calendar(codegen)
    lengths = codegen.build_month_lengths(data)
    starts = codegen.build_month_starts(lengths)
    years = codegen.build_year_starts(starts)
    bucket = codegen.build_bucket(starts)
    assert len(lengths) == _MONTHS
    assert len(starts) == _MONTH_BOUNDARIES
    assert len(years) == _YEARS
    assert years[-1] == starts[-1] == _TOTAL_DAYS
    assert len(bucket) == _BUCKETS
    assert codegen.build_ordinal_offset(data) == _OFFSET


def test_bucket_two_step_bound_holds(codegen: Any) -> None:
    """The shipped data satisfies the two-step bucket bound without raising."""
    data = _shipped_calendar(codegen)
    lengths = codegen.build_month_lengths(data)
    bucket = codegen.build_bucket(codegen.build_month_starts(lengths))
    assert len(bucket) == _BUCKETS


def test_bucket_rejects_bad_month_starts(codegen: Any) -> None:
    """A serial more than two months past its block start raises ValueError.

    Negative control: ``build_bucket`` must reject a table that would need more than two
    steps, so the bound check can fail when the generator is wrong.
    """
    with pytest.raises(ValueError):
        codegen.build_bucket(list(range(40)))


def test_main_returns_nonzero_on_bad_table(codegen: Any, tmp_path: Path, monkeypatch: Any) -> None:
    """A calendar whose generation fails makes ``main`` exit non-zero."""
    data = _shipped_calendar(codegen)
    data["month_lengths"]["1901"][0] = 1
    bad = tmp_path / "bs-calendar.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(codegen, "CALENDAR_JSON", bad)
    assert codegen.main([]) == 1
