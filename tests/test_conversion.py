"""Conversion tests for NepaliDate (P1-04)."""

from __future__ import annotations

import datetime

import pytest

from nepdate import MAX, MIN, NepaliDate
from nepdate._errors import ErrorKind, NepDateError
from nepdate._names import Weekday

_OFFSET = 673243
_TOTAL_DAYS = 109212


def test_min_to_date() -> None:
    """1901-01-01 BS is 1844-04-11 AD."""
    assert NepaliDate(1901, 1, 1).to_date() == datetime.date(1844, 4, 11)


def test_max_to_date() -> None:
    """2199-12-30 BS is 2143-04-15 AD."""
    assert NepaliDate(2199, 12, 30).to_date() == datetime.date(2143, 4, 15)


def test_reference_rows() -> None:
    """ALGORITHM §9 reference values match, weekday included."""
    rows = [
        (1901, 1, 1, datetime.date(1844, 4, 11), Weekday.THURSDAY),
        (2081, 1, 1, datetime.date(2024, 4, 13), Weekday.SATURDAY),
        (2082, 1, 1, datetime.date(2025, 4, 14), Weekday.MONDAY),
        (2083, 1, 1, datetime.date(2026, 4, 14), Weekday.TUESDAY),
    ]
    for year, month, day, ad, weekday in rows:
        date = NepaliDate(year, month, day)
        assert date.to_date() == ad
        assert date.weekday is weekday


def test_from_date_before_min_raises() -> None:
    """1844-04-10 is one day before the supported range."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_date(datetime.date(1844, 4, 10))
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_from_date_after_max_raises() -> None:
    """2143-04-16 is one day after the supported range."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_date(datetime.date(2143, 4, 16))
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_from_ordinal_boundaries_raise() -> None:
    """The ordinal one before and one after the range are both out of range."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_ordinal(_OFFSET - 1)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_ordinal(_OFFSET + _TOTAL_DAYS)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_from_date_datetime_uses_its_date() -> None:
    """A datetime.datetime converts by its own date part."""
    moment = datetime.datetime(2024, 4, 13, 10, 30)
    assert NepaliDate.from_date(moment) == NepaliDate(2081, 1, 1)


def test_round_trip_through_date() -> None:
    """BS to AD to BS is the identity for a spread of dates."""
    for parts in [(1901, 1, 1), (2081, 4, 32), (2081, 12, 31), (2199, 12, 30)]:
        date = NepaliDate(*parts)
        assert NepaliDate.from_date(date.to_date()) == date


def test_ordinal_round_trip() -> None:
    """to_ordinal and from_ordinal agree with datetime.date ordinals."""
    date = NepaliDate(2081, 4, 15)
    assert date.to_ordinal() == date.to_date().toordinal()
    assert NepaliDate.from_ordinal(date.to_ordinal()) == date


def test_min_max_constants() -> None:
    """MIN and MAX are the two boundary dates."""
    assert NepaliDate(1901, 1, 1) == MIN
    assert NepaliDate(2199, 12, 30) == MAX
    assert MIN.to_ordinal() == _OFFSET
    assert MAX.to_ordinal() == _OFFSET + _TOTAL_DAYS - 1


def test_derived_properties() -> None:
    """weekday, day_of_year, month_length and month_enum derive from the tables."""
    date = NepaliDate(2081, 1, 1)
    assert date.weekday is Weekday.SATURDAY
    assert date.day_of_year == 1
    assert date.month_length == date.last_of_month().day
    assert date.month_enum.value == 1


def test_first_and_last_of_month() -> None:
    """first_of_month and last_of_month bound the month."""
    date = NepaliDate(2081, 4, 15)
    assert date.first_of_month() == NepaliDate(2081, 4, 1)
    assert date.last_of_month() == NepaliDate(2081, 4, 32)
    assert (
        date.last_of_month().to_ordinal() - date.first_of_month().to_ordinal()
        == date.month_length - 1
    )
