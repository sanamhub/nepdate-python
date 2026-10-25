"""Construction and accessor tests for NepaliDate."""

from __future__ import annotations

import pytest

from nepdate import NepaliDate
from nepdate._errors import ErrorKind, NepDateError


class _Indexable:
    """A small test type with ``__index__``, standing in for any int-like object."""

    def __init__(self, value: int) -> None:
        self._value = value

    def __index__(self) -> int:
        return self._value


_YEAR = 2081


def test_valid_date_works() -> None:
    """Shrawan 2081 has 32 days, so day 32 is valid."""
    date = NepaliDate(2081, 4, 32)
    assert (date.year, date.month, date.day) == (2081, 4, 32)


def test_invalid_day_raises() -> None:
    """Day 33 of a 32-day month raises with kind INVALID_DAY."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate(2081, 4, 33)
    assert caught.value.kind is ErrorKind.INVALID_DAY


def test_bool_rejected() -> None:
    """A ``bool`` argument is rejected, even though bool is an int subclass."""
    with pytest.raises(TypeError):
        NepaliDate(True, 1, 1)


def test_float_rejected() -> None:
    """A ``float`` argument is rejected, as it has no exact ``__index__``."""
    with pytest.raises(TypeError):
        NepaliDate(2081.0, 1, 1)  # type: ignore[arg-type]


def test_index_object_year_works() -> None:
    """An object with ``__index__`` is converted with operator.index."""
    date = NepaliDate(_Indexable(_YEAR), 1, 1)  # type: ignore[arg-type]
    assert date.year == _YEAR


def test_year_out_of_range_precedes_month() -> None:
    """A bad year wins over the bad month and day (ALGORITHM §3)."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate(1900, 13, 40)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_invalid_month_precedes_day() -> None:
    """A bad month wins over the bad day (ALGORITHM §3)."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate(2081, 13, 40)
    assert caught.value.kind is ErrorKind.INVALID_MONTH


def test_year_attribute_is_read_only() -> None:
    """Properties have no setters, so assignment raises AttributeError."""
    date = NepaliDate(2081, 1, 1)
    with pytest.raises(AttributeError):
        date.year = 2000  # type: ignore[misc]


def test_exactly_four_slots_and_no_dict() -> None:
    """The class has the four slots of ADR-0002 §2 and no ``__dict__``."""
    assert set(NepaliDate.__slots__) == {"_y", "_m", "_d", "_o"}
    assert not hasattr(NepaliDate(2081, 1, 1), "__dict__")
