"""Day arithmetic tests: add_days, days_until, timedelta operators (P2-01)."""

from __future__ import annotations

import datetime
from collections.abc import Callable

import pytest

from nepdate import MAX, MIN, NepaliDate
from nepdate._errors import ErrorKind, NepDateError

_ADD_DAYS_ROWS = 9162
_DELTA = 5


def _bs_date(value: str) -> NepaliDate:
    year, month, day = value.split("-")
    return NepaliDate(int(year), int(month), int(day))


def test_add_days_golden(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every add-days.tsv row matches, including the ERR rows."""
    rows = vector_reader("csharp-golden", "add-days.tsv")
    assert len(rows) == _ADD_DAYS_ROWS
    for row in rows:
        date = _bs_date(row["bs"])
        result = row["result"]
        if result == "ERR":
            with pytest.raises(NepDateError) as caught:
                date.add_days(int(row["days"]))
            assert caught.value.kind is ErrorKind.OUT_OF_RANGE
        else:
            assert date.add_days(int(row["days"])) == _bs_date(result)


def test_add_days_zero_is_same_date() -> None:
    """Adding zero days returns an equal date."""
    date = NepaliDate(2081, 4, 15)
    assert date.add_days(0) == date


def test_add_days_boundaries() -> None:
    """The day after MAX and the day before MIN are out of range."""
    with pytest.raises(NepDateError) as caught:
        MAX.add_days(1)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE
    with pytest.raises(NepDateError) as caught:
        MIN.add_days(-1)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_days_until_is_signed() -> None:
    """days_until is other minus self, signed."""
    a = NepaliDate(2081, 4, 15)
    b = a.add_days(_DELTA)
    assert a.days_until(b) == _DELTA
    assert b.days_until(a) == -_DELTA
    assert a.days_until(a) == 0


def test_add_timedelta() -> None:
    """A whole-day timedelta adds its days."""
    date = NepaliDate(2081, 4, 15)
    assert date + datetime.timedelta(days=5) == NepaliDate(2081, 4, 20)
    assert date + datetime.timedelta(days=-5) == NepaliDate(2081, 4, 10)


def test_add_fractional_timedelta_raises() -> None:
    """A timedelta with a fractional day raises NepDateError (D-03)."""
    date = NepaliDate(2081, 4, 15)
    with pytest.raises(NepDateError):
        date + datetime.timedelta(days=1, hours=12)


def test_subtract_date_gives_timedelta() -> None:
    """Subtracting a date returns the signed timedelta."""
    a = NepaliDate(2081, 4, 20)
    b = NepaliDate(2081, 4, 15)
    assert a - b == datetime.timedelta(days=5)
    assert b - a == datetime.timedelta(days=-5)


def test_subtract_timedelta_gives_date() -> None:
    """Subtracting a timedelta returns a date."""
    date = NepaliDate(2081, 4, 20)
    assert date - datetime.timedelta(days=5) == NepaliDate(2081, 4, 15)


def test_subtract_fractional_timedelta_raises() -> None:
    """Subtracting a fractional timedelta raises NepDateError (D-03)."""
    date = NepaliDate(2081, 4, 15)
    with pytest.raises(NepDateError):
        date - datetime.timedelta(days=1, seconds=1)


def test_add_wrong_type_returns_not_implemented() -> None:
    """Adding a non-timedelta falls back to NotImplemented."""
    date = NepaliDate(2081, 4, 15)
    with pytest.raises(TypeError):
        date + 5  # type: ignore[operator]
