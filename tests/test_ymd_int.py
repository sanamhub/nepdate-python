"""The ``YYYYMMDD`` integer form of a date: ymd-int.tsv (NC09, D-11)."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nepdate import MAX, MIN, NepaliDate
from nepdate._errors import ErrorKind, NepDateError

_ROWS = 14
_MIN_YMD = 19010101


def _date(value: str) -> NepaliDate:
    year, month, day = value.split("-")
    return NepaliDate(int(year), int(month), int(day))


def test_ymd_int_vectors(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of ymd-int.tsv matches, in both directions."""
    rows = vector_reader("csharp-golden", "ymd-int.tsv")
    assert len(rows) == _ROWS
    for row in rows:
        if row["kind"] == "date":
            date = _date(row["input"])
            assert date.to_ymd_int() == int(row["ymd"]), row
            assert NepaliDate.from_ymd_int(int(row["ymd"])) == date, row
            assert row["result"] == row["input"], row
        else:
            number = int(row["ymd"])
            if row["result"] == "ERR":
                with pytest.raises(NepDateError):
                    NepaliDate.from_ymd_int(number)
            else:
                assert NepaliDate.from_ymd_int(number).isoformat() == row["result"], row


def test_ymd_int_roundtrip_at_the_bounds() -> None:
    """MIN and MAX round-trip through the integer form."""
    assert MIN.to_ymd_int() == _MIN_YMD
    assert NepaliDate.from_ymd_int(_MIN_YMD) == MIN
    assert NepaliDate.from_ymd_int(MAX.to_ymd_int()) == MAX


def test_negative_integer_is_refused_by_validation() -> None:
    """A negative integer reaches validation rather than wrapping; the year is rejected first."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_ymd_int(-1)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


@given(st.integers(_MIN_YMD, 21991230))
def test_integer_splits_into_its_own_digits(number: int) -> None:
    """An integer in range either names a valid date or is refused; a valid one round-trips."""
    try:
        date = NepaliDate.from_ymd_int(number)
    except NepDateError:
        return
    assert date.to_ymd_int() == number
