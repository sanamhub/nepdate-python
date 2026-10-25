"""diff tests."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nepdate import DateDiff, NepaliDate, _calendar

_OFFSET = _calendar.ORDINAL_OFFSET
_MAX_SERIAL = _calendar.MONTH_START[-1] - 1


def test_diff_table() -> None:
    """Worked examples, computed from shared/data on 2026-10-07."""
    rows = [
        (
            NepaliDate(2081, 4, 15),
            NepaliDate(2082, 1, 1),
            DateDiff(negative=False, years=0, months=8, days=17, total_days=258),
        ),
        (
            NepaliDate(2082, 1, 1),
            NepaliDate(2081, 4, 15),
            DateDiff(negative=True, years=0, months=8, days=17, total_days=-258),
        ),
        (
            NepaliDate(2081, 4, 32),
            NepaliDate(2081, 6, 30),
            DateDiff(negative=False, years=0, months=2, days=0, total_days=61),
        ),
        (
            NepaliDate(2081, 1, 1),
            NepaliDate(2081, 1, 1),
            DateDiff(negative=False, years=0, months=0, days=0, total_days=0),
        ),
        (
            NepaliDate(2000, 1, 1),
            NepaliDate(2081, 4, 15),
            DateDiff(negative=False, years=81, months=3, days=14, total_days=29693),
        ),
    ]
    for a, b, expected in rows:
        assert a.diff(b) == expected


@given(
    a_serial=st.integers(0, _MAX_SERIAL),
    b_serial=st.integers(0, _MAX_SERIAL),
)
def test_diff_properties(a_serial: int, b_serial: int) -> None:
    """Diff agrees with days_until on the total and with comparison on the sign."""
    a = NepaliDate.from_ordinal(_OFFSET + a_serial)
    b = NepaliDate.from_ordinal(_OFFSET + b_serial)
    result = a.diff(b)
    assert result.total_days == a.days_until(b)
    assert result.negative == (b < a)


def test_date_diff_is_an_immutable_value() -> None:
    """Equal breakdowns compare and hash equal, print their fields and refuse changes."""
    a = DateDiff(negative=False, years=1, months=2, days=3, total_days=430)
    b = DateDiff(False, 1, 2, 3, 430)
    assert a == b
    assert hash(a) == hash(b)
    assert a != DateDiff(negative=True, years=1, months=2, days=3, total_days=-430)
    assert a != (False, 1, 2, 3, 430)
    assert repr(a) == "DateDiff(negative=False, years=1, months=2, days=3, total_days=430)"
    with pytest.raises(AttributeError):
        a.years = 5  # type: ignore[misc]
    with pytest.raises(AttributeError):
        del a.days
    with pytest.raises(AttributeError):
        a.extra = 1  # type: ignore[attr-defined]
