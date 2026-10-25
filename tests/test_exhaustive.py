"""Exhaustive round-trip over every supported serial."""

from __future__ import annotations

import bisect

from nepdate import NepaliDate, _calendar

_OFFSET = _calendar.ORDINAL_OFFSET
_TOTAL_DAYS = _calendar.MONTH_START[-1]


def test_every_serial_round_trips() -> None:
    """Every serial 0 through 109211 round-trips through BS and back."""
    for serial in range(_TOTAL_DAYS):
        ordinal = _OFFSET + serial
        date = NepaliDate.from_ordinal(ordinal)
        assert date.to_ordinal() == ordinal
        assert NepaliDate.from_date(date.to_date()) == date


def test_bucket_matches_bisect() -> None:
    """The bucket lookup returns the same month index as bisect_right."""
    for serial in range(_TOTAL_DAYS):
        ordinal = _OFFSET + serial
        date = NepaliDate.from_ordinal(ordinal)
        actual = (date.year - _calendar.MIN_YEAR) * 12 + (date.month - 1)
        expected = bisect.bisect_right(_calendar.MONTH_START_ORD, ordinal) - 1
        assert actual == expected
