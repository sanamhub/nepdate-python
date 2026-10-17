"""Public API checks for ``nepdate_patro`` (P4-02)."""

from __future__ import annotations

import pytest

import nepdate_patro
from nepdate import MAX, MIN, DateRange, Lang, NepaliDate
from nepdate_patro import (
    _EMPTY,
    CalendarInfo,
    Event,
    Tithi,
    coverage,
    info,
    public_holidays,
)

_HOLIDAYS = 294


def test_public_surface() -> None:
    """``__all__`` is exactly the six names of docs/API.md."""
    assert set(nepdate_patro.__all__) == {
        "CalendarInfo",
        "Event",
        "Tithi",
        "coverage",
        "info",
        "public_holidays",
    }


_ANCHORS = (
    (
        "2081-01-01",
        "Panchami",
        True,
        ("New Year", "Mesh Sankranti", "Bisket Jatra"),
    ),
    ("2081-01-02", "Shashthi", False, ()),
    ("2081-02-15", "Panchami", True, ("Republic Day",)),
    (
        "2080-11-01",
        "Chaturthi",
        False,
        (
            "Mangala Chauthi Brata",
            "People's War Day",
            "Tilakund Chauthi",
            "Kumbha Sankranti",
            "World Radio Day",
        ),
    ),
    (
        "2081-04-15",
        "Dashami",
        False,
        (
            "Kheer Khane Din",
            "World Day Against Human Trafficking",
            "International Friendship Day",
        ),
    ),
)


def _parse_bs(text: str) -> tuple[int, int, int]:
    year, month, day = text.split("-")
    return int(year), int(month), int(day)


def test_patro_anchors() -> None:
    """Every PATRO §4 anchor row matches."""
    for text, tithi_en, holiday, event_ens in _ANCHORS:
        result = info(NepaliDate(*_parse_bs(text)))
        assert result.tithi is not None
        assert result.tithi.en == tithi_en, text
        assert result.is_public_holiday is holiday, text
        assert tuple(event.en for event in result.events) == event_ens, text


def test_empty_dates() -> None:
    """The two empty anchor dates return the shared empty object."""
    assert info(NepaliDate(2070, 6, 15)) is _EMPTY
    assert info(NepaliDate(2090, 1, 1)) is _EMPTY
    assert info(NepaliDate(2070, 6, 15)) == CalendarInfo(None, False, ())


def test_info_before_and_after_range() -> None:
    """MIN and MAX are outside coverage and return the empty object without raising."""
    assert info(MIN) is _EMPTY
    assert info(MAX) is _EMPTY


def test_info_returns_the_same_object() -> None:
    """Two calls for the same day return the same prebuilt object."""
    date = NepaliDate(2081, 1, 1)
    assert info(date) is info(date)
    assert info(date) is info(NepaliDate(2081, 1, 1))
    tithi_only = NepaliDate(2081, 1, 2)
    assert info(tithi_only) is info(tithi_only)


def test_coverage() -> None:
    """Coverage is the DateRange 2077-01-01 through 2084-08-20."""
    result = coverage()
    assert isinstance(result, DateRange)
    assert (result.start, result.end) == (
        NepaliDate(2077, 1, 1),
        NepaliDate(2084, 8, 20),
    )


def test_public_holidays() -> None:
    """The iterator yields 294 holidays in ascending order."""
    holidays = list(public_holidays())
    assert len(holidays) == _HOLIDAYS
    assert holidays == sorted(holidays)
    assert holidays[0] == NepaliDate(2077, 1, 1)
    assert holidays[-1] == NepaliDate(2084, 8, 18)
    assert len(set(holidays)) == len(holidays)


def test_labels() -> None:
    """``label`` returns the Nepali or English string for the language."""
    tithi = Tithi("पञ्चमी", "Panchami")
    assert tithi.label(Lang.NE) == "पञ्चमी"
    assert tithi.label(Lang.EN) == "Panchami"
    event = Event("नयाँ वर्ष", "New Year")
    assert event.label(Lang.NE) == "नयाँ वर्ष"
    assert event.label(Lang.EN) == "New Year"


def test_value_equality_and_hash() -> None:
    """Value types compare and hash by their fields."""
    assert Tithi("a", "b") == Tithi("a", "b")
    assert Tithi("a", "b") != Tithi("a", "c")
    assert hash(Tithi("a", "b")) == hash(Tithi("a", "b"))
    assert Event("a", "b") == Event("a", "b")
    assert hash(Event("a", "b")) == hash(Event("a", "b"))
    first = CalendarInfo(Tithi("a", "b"), True, (Event("c", "d"),))
    second = CalendarInfo(Tithi("a", "b"), True, (Event("c", "d"),))
    assert first == second
    assert hash(first) == hash(second)
    assert first != CalendarInfo(None, False, ())


def test_values_are_immutable() -> None:
    """Setting or deleting a field raises ``AttributeError``."""
    tithi = Tithi("a", "b")
    event = Event("c", "d")
    calendar_info = CalendarInfo(tithi, True, (event,))
    for item, name in ((tithi, "np"), (event, "en"), (calendar_info, "is_public_holiday")):
        with pytest.raises(AttributeError):
            setattr(item, name, "changed")
        with pytest.raises(AttributeError):
            delattr(item, name)


def test_events_are_a_tuple() -> None:
    """``CalendarInfo.events`` is always a tuple, never None or a list."""
    assert isinstance(_EMPTY.events, tuple)
    assert isinstance(info(NepaliDate(2081, 1, 1)).events, tuple)
