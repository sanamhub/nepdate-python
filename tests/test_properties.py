"""Hypothesis property tests (P1-05)."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from nepdate import NepaliDate, _calendar

_OFFSET = _calendar.ORDINAL_OFFSET
_MAX_SERIAL = _calendar.MONTH_START[-1] - 1


@given(st.integers(0, _MAX_SERIAL))
def test_round_trip(serial: int) -> None:
    """from_date(to_date(d)) == d and to_ordinal round-trips, for any serial."""
    date = NepaliDate.from_ordinal(_OFFSET + serial)
    assert NepaliDate.from_date(date.to_date()) == date
    assert date.to_ordinal() == _OFFSET + serial
