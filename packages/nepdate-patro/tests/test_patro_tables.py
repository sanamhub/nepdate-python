"""Compact table checks for ``nepdate_patro``."""

from __future__ import annotations

from typing import Any

from nepdate import NepaliDate
from nepdate_patro import _tables


def _ordinal(text: str) -> int:
    """Convert a canonical BS date to its proleptic Gregorian ordinal.

    Args:
        text: The date text.

    Returns:
        The ordinal.
    """
    year, month, day = (int(part) for part in text.split("-"))
    return NepaliDate(year, month, day).to_ordinal()


def test_table_counts(patro_summary: dict[str, Any]) -> None:
    """The generated tables have the counts of the shared summary."""
    assert len(_tables.TITHI_INDEX) == patro_summary["tithi_days"]
    assert len(_tables.TITHI_NAMES) == patro_summary["tithi_names"]
    assert len(_tables.HOLIDAYS) == patro_summary["holidays"]
    assert len(_tables.EVENT_DAYS) == patro_summary["event_days"]
    assert len(_tables.EVENT_IDS) == patro_summary["events"]
    assert len(_tables.EVENT_SPANS) == patro_summary["event_days"]
    assert len(_tables.NAMES) == patro_summary["event_names"]
    assert len(set(_tables.TITHI_NAMES) | set(_tables.NAMES)) == patro_summary["names"]


def test_name_bytes(patro_summary: dict[str, Any]) -> None:
    """The distinct name pool has the UTF-8 size the summary records."""
    names = set(_tables.TITHI_NAMES) | set(_tables.NAMES)
    name_bytes = sum(len(np.encode("utf-8")) + len(en.encode("utf-8")) for np, en in names)
    assert name_bytes == patro_summary["name_bytes"]


def test_tithi_index_covers_the_whole_range(patro_summary: dict[str, Any]) -> None:
    """The tithi index is one entry per day of the summary's tithi range."""
    assert _ordinal(patro_summary["tithi_first_day"]) == _tables.TITHI_FIRST
    assert _tables.TITHI_FIRST + len(_tables.TITHI_INDEX) - 1 == _ordinal(
        patro_summary["tithi_last_day"]
    )
    assert len(_tables.TITHI_INDEX) == patro_summary["tithi_days"]
    assert max(_tables.TITHI_INDEX) < len(_tables.TITHI_NAMES)


def test_sorting() -> None:
    """Holidays and event days are strictly increasing, with no duplicates."""
    assert list(_tables.HOLIDAYS) == sorted(set(_tables.HOLIDAYS))
    assert list(_tables.EVENT_DAYS) == sorted(set(_tables.EVENT_DAYS))


def test_event_spans_are_contiguous() -> None:
    """Each event span starts where the previous one ended."""
    previous = 0
    for start, end in _tables.EVENT_SPANS:
        assert start == previous
        assert start < end
        previous = end
    assert previous == len(_tables.EVENT_IDS)
    assert all(index < len(_tables.NAMES) for index in _tables.EVENT_IDS)


def test_names_are_non_empty() -> None:
    """Every tithi and event name has both languages."""
    for names in (_tables.TITHI_NAMES, _tables.NAMES):
        for np, en in names:
            assert np
            assert en


def test_coverage_ordinals(patro_summary: dict[str, Any]) -> None:
    """Coverage is the range and day span of the summary (PATRO §2)."""
    assert _ordinal(patro_summary["first_day"]) == _tables.COVERAGE_FIRST
    assert _ordinal(patro_summary["last_day"]) == _tables.COVERAGE_LAST
    assert patro_summary["days"] == _tables.COVERAGE_LAST - _tables.COVERAGE_FIRST + 1
    assert _tables.HOLIDAYS[0] >= _tables.COVERAGE_FIRST
    assert _tables.HOLIDAYS[-1] <= _tables.COVERAGE_LAST
    assert _tables.EVENT_DAYS[0] >= _tables.COVERAGE_FIRST
    assert _tables.EVENT_DAYS[-1] <= _tables.COVERAGE_LAST
