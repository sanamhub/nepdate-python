"""The patro table builder and the ``CalendarInfo`` fields, checked value by value."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nepdate import NepaliDate
from nepdate_patro import _EMPTY, CalendarInfo, Event, Tithi, _build_day_info, coverage, info

_PATRO_JSON = Path(__file__).resolve().parents[3] / "shared" / "data" / "patro"


def test_build_day_info_matches_the_shared_data() -> None:
    """Rebuilding the table from the compact tables gives the JSON data of every covered day.

    The table is built once at import, before mutmut activates a mutant, so only a direct call
    exercises the builder. The JSON files are the independent oracle.
    """
    days: dict[str, dict[str, Any]] = {}
    for path in sorted(_PATRO_JSON.glob("*.json")):
        days.update(json.loads(path.read_text(encoding="utf-8"))["days"])
    start = coverage().start.to_ordinal()
    built = _build_day_info()
    assert len(built) == coverage().end.to_ordinal() - start + 1
    for offset, item in enumerate(built):
        date = NepaliDate.from_ordinal(start + offset)
        day = days.get(date.isoformat(), {})
        tithi = day.get("tithi")
        if not day.get("holiday") and not day.get("events") and tithi is None:
            assert item is _EMPTY, date
            continue
        assert item.tithi == (None if tithi is None else Tithi(tithi["np"], tithi["en"])), date
        assert item.is_public_holiday is bool(day.get("holiday")), date
        assert item.events == tuple(
            Event(event["np"], event["en"]) for event in day.get("events", [])
        ), date


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
