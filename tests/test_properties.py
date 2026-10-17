"""Hypothesis property tests (P1-05)."""

from __future__ import annotations

from hypothesis import assume, given
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


@given(
    serial=st.integers(0, _MAX_SERIAL),
    n=st.integers(-_MAX_SERIAL, _MAX_SERIAL),
)
def test_add_days_inverse(serial: int, n: int) -> None:
    """add_days(n).days_until(d) == -n, for any in-range shift (ADR-0004)."""
    assume(0 <= serial + n <= _MAX_SERIAL)
    date = NepaliDate.from_ordinal(_OFFSET + serial)
    assert date.add_days(n).days_until(date) == -n
