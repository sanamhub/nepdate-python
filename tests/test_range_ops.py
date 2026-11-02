"""DateRange value and set operations beyond the vectors (NR16 to NR21, NR28 to NR30)."""

from __future__ import annotations

import pytest

from nepdate import MAX, MIN, DateRange, NepaliDate
from nepdate._errors import NepDateError

_TOTAL_DAYS = 109212


def _range(year: int, month: int, day: int, end_day: int) -> DateRange:
    return DateRange(NepaliDate(year, month, day), NepaliDate(year, month, end_day))


def test_equality_hash_and_repr() -> None:
    """Two ranges with the same bounds are equal, hash equal and print their constructor."""
    a = _range(2081, 4, 10, 20)
    b = _range(2081, 4, 10, 20)
    assert a == b
    assert hash(a) == hash(b)
    assert a != _range(2081, 4, 10, 21)
    assert a != "2081-04-10..2081-04-20"
    assert repr(a) == "DateRange(NepaliDate(2081, 4, 10), NepaliDate(2081, 4, 20))"


def test_contains_range_and_overlaps() -> None:
    """A range contains itself and its inner ranges; overlap is inclusive at the edges."""
    outer = _range(2081, 4, 10, 20)
    assert outer.contains_range(outer)
    assert outer.contains_range(_range(2081, 4, 12, 18))
    assert not outer.contains_range(_range(2081, 4, 9, 20))
    assert outer.overlaps(_range(2081, 4, 20, 25))
    assert not outer.overlaps(_range(2081, 4, 21, 25))


def test_adjacency_is_symmetric_and_false_at_the_edges() -> None:
    """Adjacency works in both directions and never leaves the range (D-16)."""
    first = _range(2081, 4, 10, 20)
    second = _range(2081, 4, 21, 25)
    assert first.is_adjacent_to(second)
    assert second.is_adjacent_to(first)
    assert not first.is_adjacent_to(first)
    assert not DateRange.single(MIN).is_adjacent_to(first)
    assert not DateRange.single(MAX).is_adjacent_to(first)


def test_intersect_returns_none_when_disjoint() -> None:
    """No overlap is None, including at the start of the data (D-16)."""
    assert _range(2081, 4, 10, 20).intersect(_range(2081, 4, 21, 25)) is None
    assert (
        DateRange(NepaliDate(1901, 1, 1), NepaliDate(1901, 1, 5)).intersect(_range(2081, 4, 10, 20))
        is None
    )
    inner = _range(2081, 4, 12, 18)
    assert _range(2081, 4, 10, 20).intersect(inner) == inner


def test_union_is_the_smallest_cover() -> None:
    """The union spans the gap and is order independent."""
    first = _range(2081, 4, 10, 20)
    second = _range(2081, 5, 1, 5)
    assert first.union(second) == DateRange(NepaliDate(2081, 4, 10), NepaliDate(2081, 5, 5))
    assert second.union(first) == first.union(second)


def test_difference_returns_zero_one_or_two_ranges() -> None:
    """Removing a range can leave nothing, one piece or two pieces."""
    full = _range(2081, 4, 1, 30)
    assert full.difference(_range(2081, 4, 1, 30)) == []
    assert full.difference(_range(2081, 4, 10, 20)) == [
        _range(2081, 4, 1, 9),
        _range(2081, 4, 21, 30),
    ]
    assert full.difference(_range(2081, 4, 1, 10)) == [_range(2081, 4, 11, 30)]
    assert full.difference(_range(2081, 4, 20, 30)) == [_range(2081, 4, 1, 19)]
    assert full.difference(_range(2081, 5, 1, 5)) == [full]


def test_difference_does_not_leave_the_range_at_the_edges() -> None:
    """Removing the first or last day of a range at the data edge stays inside it (D-16)."""
    first = DateRange(NepaliDate(1901, 1, 1), NepaliDate(1901, 1, 3))
    assert first.difference(DateRange.single(MIN)) == [
        DateRange(NepaliDate(1901, 1, 2), NepaliDate(1901, 1, 3))
    ]
    last = DateRange(NepaliDate(2199, 12, 28), NepaliDate(2199, 12, 30))
    assert last.difference(DateRange.single(MAX)) == [
        DateRange(NepaliDate(2199, 12, 28), NepaliDate(2199, 12, 29))
    ]


def test_to_string_defaults_match_str() -> None:
    """``to_string`` with no arguments is the default display of both dates."""
    rng = _range(2081, 4, 10, 20)
    assert rng.to_string() == str(rng) == "2081/04/10 - 2081/04/20"


def test_single_and_from_day_count_errors() -> None:
    """A day count below one and a failed shift past the range are refused (NR07, NR08)."""
    with pytest.raises(NepDateError):
        DateRange.from_day_count(NepaliDate(2081, 4, 15), 0)
    with pytest.raises(NepDateError):
        DateRange.from_day_count(MAX, 2)
    assert DateRange.single(NepaliDate(2081, 4, 15)).start == NepaliDate(2081, 4, 15)


def test_full_range_length() -> None:
    """The supported span has 109,212 days, both ends included."""
    assert len(DateRange(MIN, MAX)) == _TOTAL_DAYS
