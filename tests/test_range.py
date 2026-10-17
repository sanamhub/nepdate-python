"""DateRange tests (P2-05)."""

from __future__ import annotations

import pytest

from nepdate import DateRange, NepaliDate, _calendar
from nepdate._errors import ErrorKind, NepDateError


def test_month_contains() -> None:
    """The P2-05 acceptance example."""
    assert NepaliDate(2081, 4, 15) in DateRange.month(2081, 4)


def test_month_boundaries() -> None:
    """A month range starts on day 1 and ends on the month's last day."""
    for year in (_calendar.MIN_YEAR, 2081, _calendar.MAX_YEAR):
        for month in range(1, 13):
            rng = DateRange.month(year, month)
            assert rng.start == NepaliDate(year, month, 1)
            assert rng.end == NepaliDate(year, month, 1).last_of_month()


def test_year_lengths() -> None:
    """len(DateRange.year(y)) equals the sum of the year's month lengths."""
    for year in range(_calendar.MIN_YEAR, _calendar.MAX_YEAR + 1):
        index = (year - _calendar.MIN_YEAR) * 12
        expected = sum(_calendar.MONTH_LENGTHS[index : index + 12])
        assert len(DateRange.year(year)) == expected


def test_year_boundaries() -> None:
    """A year range spans Baishakh 1 to Chaitra's end."""
    rng = DateRange.year(2081)
    assert rng.start == NepaliDate(2081, 1, 1)
    assert rng.end == NepaliDate(2081, 12, 1).last_of_month()


def test_len_and_iter_agree() -> None:
    """Iterating a range yields exactly len(d) dates."""
    rng = DateRange(NepaliDate(2081, 4, 1), NepaliDate(2081, 4, 10))
    dates = list(rng)
    assert len(dates) == len(rng)
    assert dates[0] == rng.start
    assert dates[-1] == rng.end


def test_reversed_iteration() -> None:
    """Reversed iteration goes from end to start."""
    rng = DateRange(NepaliDate(2081, 4, 1), NepaliDate(2081, 4, 3))
    assert list(reversed(rng)) == [
        NepaliDate(2081, 4, 3),
        NepaliDate(2081, 4, 2),
        NepaliDate(2081, 4, 1),
    ]


def test_contains_non_date_is_false() -> None:
    """A non-date is never in the range."""
    rng = DateRange.month(2081, 4)
    assert "2081/04/15" not in rng
    assert object() not in rng


def test_start_after_end_raises() -> None:
    """A reversed range raises OUT_OF_RANGE (D-09: no empty range)."""
    with pytest.raises(NepDateError) as caught:
        DateRange(NepaliDate(2081, 4, 10), NepaliDate(2081, 4, 1))
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_single_day_range() -> None:
    """A range of one day has length 1 and yields that day."""
    day = NepaliDate(2081, 4, 15)
    rng = DateRange(day, day)
    assert len(rng) == 1
    assert list(rng) == [day]
