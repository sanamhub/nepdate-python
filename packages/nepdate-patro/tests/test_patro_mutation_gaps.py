"""Regression tests for patro mutation-testing survivors (P8-03)."""

from __future__ import annotations

from nepdate import NepaliDate
from nepdate_patro import CalendarInfo, Tithi, _build_day_info, coverage, info


def test_build_day_info_matches_the_prebuilt_day_info() -> None:
    """Rebuilding the table reproduces every field of the prebuilt infos."""
    start = coverage().start.to_ordinal()
    end = coverage().end.to_ordinal()
    built = _build_day_info()
    assert len(built) == end - start + 1
    for offset, item in enumerate(built):
        current = info(NepaliDate.from_ordinal(start + offset))
        assert item.tithi == current.tithi
        assert item.is_public_holiday == current.is_public_holiday
        assert item.events == current.events


def test_calendar_info_keeps_its_three_fields() -> None:
    """CalendarInfo stores the tithi, the holiday flag and the events it was given."""
    tithi = Tithi("शुक्ल", "Shukla")
    day = CalendarInfo(tithi, True, ())
    assert day.tithi is tithi
    assert day.is_public_holiday is True
    assert day.events == ()
