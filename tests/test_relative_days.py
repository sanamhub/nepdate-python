"""Relative date predicates and the current range factories, with an injected clock."""

from __future__ import annotations

import datetime

import pytest

import nepdate._date as core_date
from nepdate import MAX, MIN, DateRange, FiscalYear, NepaliDate
from nepdate._errors import ErrorKind, NepDateError

# 2024-07-30 18:30 UTC is 2081-04-16 in Nepal (UTC+5:45) and 2081-04-15 in UTC.
_FIXED = datetime.datetime(2024, 7, 30, 18, 30, tzinfo=datetime.UTC)
_NEPAL_TODAY = NepaliDate(2081, 4, 16)
_UTC_TODAY = NepaliDate(2081, 4, 15)


@pytest.fixture
def fixed_clock(monkeypatch: pytest.MonkeyPatch) -> NepaliDate:
    """Replace the clock with a fixed instant and return the Nepal date it names."""
    monkeypatch.setattr(core_date, "_now", lambda: _FIXED)
    return _NEPAL_TODAY


def test_is_today(fixed_clock: NepaliDate) -> None:
    """``is_today`` compares against ``today(tz)``, Nepal by default."""
    assert _NEPAL_TODAY.is_today() is True
    assert _UTC_TODAY.is_today() is False
    assert _UTC_TODAY.is_today(datetime.UTC) is True
    assert _NEPAL_TODAY.is_today(datetime.UTC) is False
    assert fixed_clock.is_today() is True


def test_is_yesterday(fixed_clock: NepaliDate) -> None:
    """``is_yesterday`` is exactly one day before today in the given zone."""
    assert NepaliDate(2081, 4, 15).is_yesterday() is True
    assert NepaliDate(2081, 4, 14).is_yesterday() is False
    assert _NEPAL_TODAY.is_yesterday() is False
    assert NepaliDate(2081, 4, 14).is_yesterday(datetime.UTC) is True


def test_is_tomorrow(fixed_clock: NepaliDate) -> None:
    """``is_tomorrow`` is exactly one day after today in the given zone."""
    assert NepaliDate(2081, 4, 17).is_tomorrow() is True
    assert NepaliDate(2081, 4, 18).is_tomorrow() is False
    assert _NEPAL_TODAY.is_tomorrow() is False
    assert NepaliDate(2081, 4, 16).is_tomorrow(datetime.UTC) is True


def test_relative_predicates_at_the_data_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    """The edges answer false instead of building a date outside the range (D-16)."""
    monkeypatch.setattr(
        core_date,
        "_now",
        lambda: datetime.datetime(1844, 4, 10, 20, 0, tzinfo=datetime.UTC),
    )
    assert MIN.is_today() is True
    assert MIN.is_yesterday() is False
    assert NepaliDate(1901, 1, 2).is_tomorrow() is True

    monkeypatch.setattr(
        core_date,
        "_now",
        lambda: datetime.datetime(2143, 4, 14, 20, 0, tzinfo=datetime.UTC),
    )
    assert MAX.is_today() is True
    assert MAX.is_tomorrow() is False
    assert NepaliDate(2199, 12, 29).is_yesterday() is True


def test_relative_predicates_reject_an_out_of_range_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """A clock outside the supported range raises, as ``today`` does."""
    monkeypatch.setattr(
        core_date,
        "_now",
        lambda: datetime.datetime(1700, 1, 1, tzinfo=datetime.UTC),
    )
    for call in (_NEPAL_TODAY.is_today, _NEPAL_TODAY.is_yesterday, _NEPAL_TODAY.is_tomorrow):
        with pytest.raises(NepDateError) as caught:
            call()
        assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_current_ranges(fixed_clock: NepaliDate) -> None:
    """The three current factories wrap today's month, fiscal year and calendar year."""
    assert DateRange.current_month() == DateRange.month(2081, 4)
    assert DateRange.current_calendar_year() == DateRange.year(2081)
    assert DateRange.current_fiscal_year() == FiscalYear(2081).range()
    assert fixed_clock in DateRange.current_month()
    assert fixed_clock in DateRange.current_calendar_year()
    assert fixed_clock in DateRange.current_fiscal_year()


def test_current_ranges_use_the_requested_zone(monkeypatch: pytest.MonkeyPatch) -> None:
    """The zone moves the day, so a range built in UTC can be the previous month."""
    first = NepaliDate(2081, 4, 1).to_date()
    previous = first - datetime.timedelta(days=1)
    # 18:15 UTC is midnight in Nepal, so Nepal is on 2081-04-01 while UTC is still on 2081-03-31.
    monkeypatch.setattr(
        core_date,
        "_now",
        lambda: datetime.datetime(
            previous.year, previous.month, previous.day, 18, 15, tzinfo=datetime.UTC
        ),
    )
    assert NepaliDate.today() == NepaliDate(2081, 4, 1)
    assert DateRange.current_month() == DateRange.month(2081, 4)
    assert DateRange.current_month(datetime.UTC) == DateRange.month(2081, 3)
    assert DateRange.current_calendar_year(datetime.UTC) == DateRange.year(2081)


def test_current_ranges_agree_with_today(fixed_clock: NepaliDate) -> None:
    """Every current range contains today, which is the contract of NR12 to NR14."""
    today = NepaliDate.today()
    assert today in DateRange.current_month()
    assert today in DateRange.current_calendar_year()
    assert today in DateRange.current_fiscal_year()
