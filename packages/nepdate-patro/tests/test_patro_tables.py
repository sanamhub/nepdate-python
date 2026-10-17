"""Compact table checks for ``nepdate_patro`` (P4-01 and P4-02)."""

from __future__ import annotations

from nepdate import NepaliDate
from nepdate_patro import _tables

_TITHI_DAYS = 2190
_TITHI_NAMES = 32
_HOLIDAYS = 294
_EVENT_DAYS = 1671
_EVENT_IDS = 3032
_EVENT_NAMES = 721
_ALL_NAMES = 753


def test_table_counts() -> None:
    """The generated tables have the sizes PATRO §3 and P4-01 promise."""
    assert len(_tables.TITHI_INDEX) == _TITHI_DAYS
    assert len(_tables.TITHI_NAMES) == _TITHI_NAMES
    assert len(_tables.HOLIDAYS) == _HOLIDAYS
    assert len(_tables.EVENT_DAYS) == _EVENT_DAYS
    assert len(_tables.EVENT_IDS) == _EVENT_IDS
    assert len(_tables.EVENT_SPANS) == _EVENT_DAYS
    assert len(_tables.NAMES) == _EVENT_NAMES
    assert len(set(_tables.TITHI_NAMES) | set(_tables.NAMES)) == _ALL_NAMES


def test_tithi_index_covers_the_whole_range() -> None:
    """The tithi index is one entry per day from 2078-01-02 through 2083-12-30."""
    assert NepaliDate(2078, 1, 2).to_ordinal() == _tables.TITHI_FIRST
    assert (
        _tables.TITHI_FIRST + len(_tables.TITHI_INDEX) - 1 == NepaliDate(2083, 12, 30).to_ordinal()
    )
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


def test_coverage_ordinals() -> None:
    """Coverage is 2077-01-01 through 2084-08-20 (PATRO §2)."""
    assert NepaliDate(2077, 1, 1).to_ordinal() == _tables.COVERAGE_FIRST
    assert NepaliDate(2084, 8, 20).to_ordinal() == _tables.COVERAGE_LAST
    assert _tables.HOLIDAYS[0] >= _tables.COVERAGE_FIRST
    assert _tables.HOLIDAYS[-1] <= _tables.COVERAGE_LAST
    assert _tables.EVENT_DAYS[0] >= _tables.COVERAGE_FIRST
    assert _tables.EVENT_DAYS[-1] <= _tables.COVERAGE_LAST
