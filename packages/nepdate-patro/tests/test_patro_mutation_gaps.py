"""Regression tests for patro mutation-testing survivors (P8-03)."""

from __future__ import annotations

import pytest

from nepdate import NepaliDate
from nepdate_patro import CalendarInfo, Event, Tithi, info


def test_empty_days_inside_coverage_share_the_empty_info() -> None:
    """A covered day with no tithi, holiday or event is the same object as a day outside."""
    empty_inside = info(NepaliDate(2077, 1, 2))
    assert empty_inside.tithi is None
    assert not empty_inside.is_public_holiday
    assert empty_inside.events == ()
    assert empty_inside is info(NepaliDate(2000, 1, 1))


def test_calendar_info_keeps_its_three_fields() -> None:
    """CalendarInfo stores the tithi, the holiday flag and the events it was given."""
    tithi = Tithi("शुक्ल", "Shukla")
    day = CalendarInfo(tithi, True, ())
    assert day.tithi is tithi
    assert day.is_public_holiday is True
    assert day.events == ()


@pytest.mark.parametrize(
    ("value", "name"),
    [
        (Tithi("शुक्ल", "Shukla"), "np"),
        (Event("नयाँ वर्ष", "New Year"), "np"),
        (CalendarInfo(None, False, ()), "tithi"),
    ],
)
def test_deleting_a_field_names_the_type(value: object, name: str) -> None:
    """The immutability error is an AttributeError with a message, not a blank one."""
    with pytest.raises(AttributeError) as caught:
        delattr(value, name)
    assert type(value).__name__ in str(caught.value)
