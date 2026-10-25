"""Month and year arithmetic tests: add_months, add_years."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from nepdate import MAX, MIN, NepaliDate, Overflow
from nepdate._errors import ErrorKind, NepDateError

_ADD_MONTHS_ROWS = 10180


def _bs_date(value: str) -> NepaliDate:
    year, month, day = value.split("-")
    return NepaliDate(int(year), int(month), int(day))


def _assert_out_of_range(fn: Callable[[], object]) -> None:
    with pytest.raises(NepDateError) as caught:
        fn()
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_add_months_golden(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every add-months.tsv row matches for clamp and spill."""
    rows = vector_reader("csharp-golden", "add-months.tsv")
    assert len(rows) == _ADD_MONTHS_ROWS
    for row in rows:
        date = _bs_date(row["bs"])
        n = int(row["months"])
        for column, overflow in (("clamp", Overflow.CLAMP), ("overflow", Overflow.SPILL)):
            result = row[column]
            if result == "ERR":
                with pytest.raises(NepDateError) as caught:
                    date.add_months(n, overflow)
                assert caught.value.kind is ErrorKind.OUT_OF_RANGE
            else:
                assert date.add_months(n, overflow) == _bs_date(result)


def test_add_months_clamp_examples() -> None:
    """The ALGORITHM §8 clamp examples."""
    date = NepaliDate(2081, 4, 32)
    assert date.add_months(2) == NepaliDate(2081, 6, 30)
    assert date.add_months(5) == NepaliDate(2081, 9, 29)


def test_add_months_spill_examples() -> None:
    """The ALGORITHM §8 spill examples."""
    date = NepaliDate(2081, 4, 32)
    assert date.add_months(2, Overflow.SPILL) == NepaliDate(2081, 7, 2)
    assert date.add_months(5, Overflow.SPILL) == NepaliDate(2081, 10, 3)


def test_add_months_negative() -> None:
    """Negative offsets preserve the day when it fits."""
    date = NepaliDate(2081, 4, 15)
    assert date.add_months(-1) == NepaliDate(2081, 3, 15)
    assert date.add_months(-16) == NepaliDate(2079, 12, 15)


def test_add_years() -> None:
    """add_years is add_months of 12 times the offset."""
    date = NepaliDate(2081, 4, 15)
    assert date.add_years(1) == NepaliDate(2082, 4, 15)
    assert date.add_years(-1) == NepaliDate(2080, 4, 15)


def test_add_years_clamps() -> None:
    """A day past the end clamps by default."""
    date = NepaliDate(2081, 4, 32)
    assert date.add_years(1) == NepaliDate(2082, 4, 31)


def test_add_months_out_of_range() -> None:
    """Boundary months raise OUT_OF_RANGE."""
    _assert_out_of_range(lambda: MAX.add_months(1))
    _assert_out_of_range(lambda: MIN.add_months(-1))
    _assert_out_of_range(lambda: MAX.add_years(1))
    _assert_out_of_range(lambda: MIN.add_years(-1))


def test_add_months_spill_out_of_range() -> None:
    """A spill past the last month raises OUT_OF_RANGE."""
    _assert_out_of_range(lambda: NepaliDate(2199, 12, 30).add_months(1, Overflow.SPILL))
