"""Tests for ``NepaliDate.today`` and its injectable clock (P4-03)."""

from __future__ import annotations

import datetime

import pytest

import nepdate._date as core_date
from nepdate import MIN, NepaliDate
from nepdate._date import _today_from
from nepdate._errors import ErrorKind, NepDateError

_FIXED = datetime.datetime(2024, 7, 30, 18, 30, tzinfo=datetime.UTC)


def test_fixed_clock_in_nepal() -> None:
    """The default zone is Asia/Kathmandu, so UTC 18:30 is the next BS day."""
    assert _today_from(_FIXED, None, NepaliDate) == NepaliDate(2081, 4, 16)


def test_fixed_clock_in_utc() -> None:
    """An explicit UTC zone keeps the UTC date."""
    assert _today_from(_FIXED, datetime.UTC, NepaliDate) == NepaliDate(2081, 4, 15)


def test_today_uses_the_injected_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """``today`` reads ``_now`` and converts it through the requested zone."""
    monkeypatch.setattr(core_date, "_now", lambda: _FIXED)
    assert NepaliDate.today() == NepaliDate(2081, 4, 16)
    assert NepaliDate.today(datetime.UTC) == NepaliDate(2081, 4, 15)


def test_today_is_inside_the_supported_range() -> None:
    """The real clock produces a supported date with the default zone."""
    today = NepaliDate.today()
    assert MIN <= today <= NepaliDate(2199, 12, 30)


def test_today_out_of_range_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A clock outside the supported range raises ``OUT_OF_RANGE``, not a made-up date."""
    ancient = datetime.datetime(1700, 1, 1, tzinfo=datetime.UTC)
    monkeypatch.setattr(core_date, "_now", lambda: ancient)
    with pytest.raises(NepDateError) as caught:
        NepaliDate.today()
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE
