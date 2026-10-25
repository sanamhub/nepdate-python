"""Acceptance checks for the generated calendar tables."""

from __future__ import annotations

from nepdate import _calendar

_MONTHS = 3588
_MONTH_BOUNDARIES = 3589
_YEARS = 300
_TOTAL_DAYS = 109212
_BUCKETS = 3413
_OFFSET = 673243
_MIN_YEAR = 1901
_MIN_MONTH_LENGTH = 29
_MAX_MONTH_LENGTH = 32


def test_table_lengths() -> None:
    """Every table has the size ADR-0002 §3 promises."""
    assert len(_calendar.MONTH_LENGTHS) == _MONTHS
    assert len(_calendar.MONTH_START) == _MONTH_BOUNDARIES
    assert len(_calendar.YEAR_START) == _YEARS
    assert len(_calendar.MONTH_START_ORD) == _MONTH_BOUNDARIES
    assert len(_calendar.MONTH_YEAR) == _MONTHS
    assert len(_calendar.MONTH_NUM) == _MONTHS
    assert len(_calendar.BUCKET) == _BUCKETS


def test_sentinels_agree() -> None:
    """The last serials line up and the ordinal offset is the epoch ordinal."""
    assert _calendar.YEAR_START[-1] == _calendar.MONTH_START[-1] == _TOTAL_DAYS
    assert _calendar.ORDINAL_OFFSET == _OFFSET
    assert _calendar.MONTH_START_ORD[0] == _OFFSET
    assert _calendar.MONTH_START_ORD[-1] == _OFFSET + _TOTAL_DAYS


def test_month_metadata_is_consistent() -> None:
    """MONTH_YEAR and MONTH_NUM name the month each index belongs to."""
    for index, year in enumerate(_calendar.MONTH_YEAR):
        assert year == _MIN_YEAR + index // 12
        assert _calendar.MONTH_NUM[index] == index % 12 + 1
    assert min(_calendar.MONTH_LENGTHS) == _MIN_MONTH_LENGTH
    assert max(_calendar.MONTH_LENGTHS) == _MAX_MONTH_LENGTH


def test_year_starts_are_month_starts() -> None:
    """YEAR_START is every 12th MONTH_START, the first day of each BS year."""
    assert list(_calendar.YEAR_START) == list(_calendar.MONTH_START[::12])
