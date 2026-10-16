"""Tests for the calendar enums and the one exception type (P1-02)."""

from __future__ import annotations

import pytest

from nepdate._errors import ErrorKind, NepDateError
from nepdate._names import Lang, Month, Weekday

_MONTH_COUNT = 12
_WEEKDAY_COUNT = 7
_ERROR_KIND_COUNT = 9


def test_month_members() -> None:
    """Month is an IntEnum from Baishakh (1) to Chaitra (12)."""
    assert [member.value for member in Month] == list(range(1, _MONTH_COUNT + 1))
    assert Month(1) is Month.BAISHAKH
    assert Month(_MONTH_COUNT) is Month.CHAITRA


def test_weekday_members() -> None:
    """Weekday is an IntEnum from Sunday (0) to Saturday (6)."""
    assert [member.value for member in Weekday] == list(range(_WEEKDAY_COUNT))
    assert Weekday(0) is Weekday.SUNDAY
    assert Weekday(_WEEKDAY_COUNT - 1) is Weekday.SATURDAY


def test_lang_members() -> None:
    """Lang has exactly the two members of docs/API.md."""
    assert Lang.EN.value == "en"
    assert Lang.NE.value == "ne"
    assert list(Lang) == [Lang.EN, Lang.NE]


def test_error_kind_members() -> None:
    """ErrorKind has the nine members of docs/API.md."""
    assert len(ErrorKind) == _ERROR_KIND_COUNT
    assert ErrorKind.OUT_OF_RANGE is ErrorKind.OUT_OF_RANGE
    assert ErrorKind.UNRECOGNIZED is ErrorKind.UNRECOGNIZED


def test_nep_date_error_is_value_error() -> None:
    """NepDateError subclasses ValueError and carries its kind."""
    error = NepDateError(ErrorKind.INVALID_DAY, "day 33 is out of range")
    with pytest.raises(ValueError) as caught:
        raise error
    assert caught.value is error
    assert error.kind is ErrorKind.INVALID_DAY


def test_nep_date_error_kind_is_read_only() -> None:
    """The kind attribute has no setter."""
    error = NepDateError(ErrorKind.OUT_OF_RANGE, "out of range")
    with pytest.raises(AttributeError):
        error.kind = ErrorKind.INVALID_DAY  # type: ignore[misc]
