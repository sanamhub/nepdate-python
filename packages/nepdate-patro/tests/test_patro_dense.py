"""Dense ``DAY_INFO`` against a slow lookup over the compact tables."""

from __future__ import annotations

from bisect import bisect_left

from nepdate import MAX, MIN, NepaliDate
from nepdate_patro import _tables, info


def _slow_info(ordinal: int) -> tuple[tuple[str, str] | None, bool, tuple[tuple[str, str], ...]]:
    """Look a coverage day up in the compact tables, one table at a time.

    Args:
        ordinal: The proleptic Gregorian ordinal.

    Returns:
        The tithi pair or None, the holiday flag and the event pairs in file order.
    """
    tithi_first = _tables.TITHI_FIRST
    if tithi_first <= ordinal < tithi_first + len(_tables.TITHI_INDEX):
        tithi = _tables.TITHI_NAMES[_tables.TITHI_INDEX[ordinal - tithi_first]]
    else:
        tithi = None
    holiday_index = bisect_left(_tables.HOLIDAYS, ordinal)
    holiday = holiday_index < len(_tables.HOLIDAYS) and _tables.HOLIDAYS[holiday_index] == ordinal
    event_index = bisect_left(_tables.EVENT_DAYS, ordinal)
    if event_index < len(_tables.EVENT_DAYS) and _tables.EVENT_DAYS[event_index] == ordinal:
        start, end = _tables.EVENT_SPANS[event_index]
        events = tuple(_tables.NAMES[_tables.EVENT_IDS[i]] for i in range(start, end))
    else:
        events = ()
    return tithi, holiday, events


def test_every_coverage_day_matches_the_slow_lookup() -> None:
    """Every day of coverage agrees with the compact-table reference."""
    for ordinal in range(_tables.COVERAGE_FIRST, _tables.COVERAGE_LAST + 1):
        result = info(NepaliDate.from_ordinal(ordinal))
        tithi, holiday, events = _slow_info(ordinal)
        if tithi is None:
            assert result.tithi is None, ordinal
        else:
            assert result.tithi is not None
            assert (result.tithi.np, result.tithi.en) == tithi, ordinal
        assert result.is_public_holiday is holiday, ordinal
        assert tuple((event.np, event.en) for event in result.events) == events, ordinal


def test_outside_coverage_is_empty() -> None:
    """The day before coverage and the day after it return the empty object."""
    assert info(NepaliDate.from_ordinal(_tables.COVERAGE_FIRST - 1)).tithi is None
    assert info(NepaliDate.from_ordinal(_tables.COVERAGE_LAST + 1)).tithi is None
    assert info(MIN).tithi is None
    assert info(MAX).tithi is None
