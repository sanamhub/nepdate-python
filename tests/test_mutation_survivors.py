"""Survivors of the 0.2 mutation run: behaviour the suite did not pin (ADR-0013)."""

from __future__ import annotations

import itertools

import pytest

from nepdate import DateRange, NepaliDate, to_english_dates
from nepdate._errors import ErrorKind, NepDateError

_QUARTERS = 2
_WEEKEND_DAYS = 2
_SATURDAY_ONLY = 1


def test_from_json_rejects_a_one_character_quote() -> None:
    """A lone quote is a quoting error, not a parse error."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_json('"')
    assert caught.value.kind is ErrorKind.INVALID_CHARACTER


def test_from_json_of_an_empty_quoted_string_is_a_parse_error() -> None:
    """Two quotes pass the quoting rule, so the parser reports the missing groups."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_json('""')
    assert caught.value.kind is ErrorKind.WRONG_GROUP_COUNT


def test_from_json_accepts_a_valid_quoted_date() -> None:
    """The ordinary path reads the quoted date, not only the rejection paths."""
    assert NepaliDate.from_json('"2081-04-15"') == NepaliDate(2081, 4, 15)


def test_dates_with_interval_rejects_zero_as_out_of_range() -> None:
    """A step below one is an out of range error, with that kind."""
    with pytest.raises(NepDateError) as caught:
        DateRange.month(2080, 1).dates_with_interval(0)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_from_day_count_rejects_zero_as_out_of_range() -> None:
    """A day count below one is an out of range error, with that kind."""
    with pytest.raises(NepDateError) as caught:
        DateRange.from_day_count(NepaliDate(2080, 1, 1), 0)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_from_ymd_int_negative_number_is_out_of_range() -> None:
    """C# truncating division sends a negative integer to the year check, not to a month."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_ymd_int(-20810415)
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_intersect_uses_the_later_start() -> None:
    """The result starts at the later of the two starts."""
    later = DateRange(NepaliDate(2080, 1, 6), NepaliDate(2080, 1, 20))
    wider = DateRange(NepaliDate(2080, 1, 1), NepaliDate(2080, 1, 25))
    assert later.intersect(wider) == DateRange(NepaliDate(2080, 1, 6), NepaliDate(2080, 1, 20))


def test_intersect_of_ranges_that_touch_on_one_day_is_that_day() -> None:
    """A single shared day is a range, not None."""
    left = DateRange(NepaliDate(2080, 1, 1), NepaliDate(2080, 1, 10))
    right = DateRange(NepaliDate(2080, 1, 10), NepaliDate(2080, 1, 20))
    assert left.intersect(right) == DateRange.single(NepaliDate(2080, 1, 10))


def test_split_by_month_crosses_the_new_year_without_a_gap() -> None:
    """The month after Chaitra is Baishakh of the next year."""
    whole = DateRange(NepaliDate(2080, 12, 20), NepaliDate(2081, 1, 5))
    pieces = whole.split_by_month()
    assert [piece.start for piece in pieces] == [whole.start, NepaliDate(2081, 1, 1)]
    assert [piece.end for piece in pieces] == [
        NepaliDate(2080, 12, 1).last_of_month(),
        whole.end,
    ]


def test_split_by_fiscal_quarter_pieces_are_contiguous() -> None:
    """Consecutive quarters meet on the next day, with no day skipped."""
    whole = DateRange(NepaliDate(2081, 1, 1), NepaliDate(2081, 5, 1))
    pieces = whole.split_by_fiscal_quarter()
    assert len(pieces) == _QUARTERS
    assert pieces[0].start == whole.start
    assert pieces[-1].end == whole.end
    for previous, following in itertools.pairwise(pieces):
        assert following.start.to_ordinal() == previous.end.to_ordinal() + 1


def test_weekend_days_includes_sunday_by_default() -> None:
    """Saturday and Sunday are the default weekend; Sunday is optional."""
    week = DateRange(NepaliDate(2081, 1, 1), NepaliDate(2081, 1, 7))
    assert len(week.weekend_days()) == _WEEKEND_DAYS
    assert len(week.weekend_days(include_sunday=False)) == _SATURDAY_ONLY


def test_to_english_dates_rejects_an_unknown_item() -> None:
    """A non-date, non-string item is a TypeError with a message."""
    with pytest.raises(TypeError) as caught:
        to_english_dates([1])  # type: ignore[list-item]
    assert str(caught.value)
    assert str(caught.value) != "None"
