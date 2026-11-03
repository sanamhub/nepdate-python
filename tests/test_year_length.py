"""Year length tests: the D-12 reference vector and the month-length sum."""

from __future__ import annotations

from collections.abc import Callable

from nepdate import MAX, MIN, NepaliDate, _calendar

_YEAR_ROWS = 299
_MIN_YEAR_LENGTH = 364
_MAX_YEAR_LENGTH = 367
_SAMPLE_MONTHS = ((1, 1), (4, 15), (11, 1), (12, 30))


def test_year_length_vector(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of year-length.tsv matches ``NepaliDate.year_length``."""
    rows = vector_reader("year-length.tsv")
    assert len(rows) == _YEAR_ROWS
    for row in rows:
        year = int(row["bs_year"])
        assert NepaliDate(year, 1, 1).year_length == int(row["year_length"]), row


def test_year_length_is_the_month_length_sum() -> None:
    """The year length is the sum of the twelve month lengths of that BS year."""
    for year in range(_calendar.MIN_YEAR, _calendar.MAX_YEAR + 1):
        index = (year - _calendar.MIN_YEAR) * 12
        expected = sum(_calendar.MONTH_LENGTHS[index : index + 12])
        assert NepaliDate(year, 1, 1).year_length == expected, year


def test_year_length_is_stable_within_a_year() -> None:
    """Every date of a year reports the same length, because it is a BS property (D-12)."""
    length = NepaliDate(2080, 1, 1).year_length
    for month, day in _SAMPLE_MONTHS:
        assert NepaliDate(2080, month, day).year_length == length


def test_year_length_range() -> None:
    """A BS year is 364 to 367 days, and the boundary dates report a supported length."""
    lengths = {NepaliDate(year, 1, 1).year_length for year in range(1901, 2200)}
    assert min(lengths) >= _MIN_YEAR_LENGTH
    assert max(lengths) <= _MAX_YEAR_LENGTH
    assert _MIN_YEAR_LENGTH <= MIN.year_length <= _MAX_YEAR_LENGTH
    assert MAX.year_length in lengths


def test_year_length_is_not_the_gregorian_leap_year() -> None:
    """One BS year can straddle two AD years; its length is still a single BS value (D-12)."""
    first = NepaliDate(2080, 1, 1)
    later = NepaliDate(2080, 11, 1)
    assert first.to_date().year != later.to_date().year
    assert first.year_length == later.year_length
