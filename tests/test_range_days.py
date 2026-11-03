"""Range day helpers: range-days.tsv (NR24 to NR27, D-16)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from nepdate import DateRange, NepaliDate
from nepdate._errors import NepDateError

_ROWS = 18


def _date(value: str) -> NepaliDate:
    year, month, day = value.split("-")
    return NepaliDate(int(year), int(month), int(day))


def _text(values: list[NepaliDate]) -> str:
    return ";".join(value.isoformat() for value in values) or "none"


def test_range_day_vectors(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of range-days.tsv matches, including the D-16 rows at the data end."""
    rows = vector_reader("csharp-golden", "range-days.tsv")
    assert len(rows) == _ROWS
    for row in rows:
        rng = DateRange(_date(row["start"]), _date(row["end"]))
        operation = row["operation"]
        expected = row["result"]
        if operation == "dates_with_interval":
            if expected == "ERR":
                with pytest.raises(NepDateError):
                    rng.dates_with_interval(int(row["argument"]))
            else:
                actual = rng.dates_with_interval(int(row["argument"]))
                assert _text(actual) == expected, row
        elif operation == "working_days":
            actual = rng.working_days(row["argument"] == "true")
            assert _text(actual) == expected, row
        elif operation == "weekend_days":
            actual = rng.weekend_days(row["argument"] == "true")
            assert _text(actual) == expected, row
        elif operation == "enumerate":
            assert _text(list(rng)) == expected, row
        else:  # pragma: no cover - the vector only names the operations above
            raise AssertionError(f"unknown operation {operation}")


def test_interval_rejects_a_zero_or_negative_step() -> None:
    """An interval below one is refused rather than looping forever (NR24)."""
    rng = DateRange.month(2081, 4)
    for interval in (0, -1, -10):
        with pytest.raises(NepDateError):
            rng.dates_with_interval(interval)


def test_interval_larger_than_the_range_yields_the_start() -> None:
    """A step past the end still returns the start date once (NR24)."""
    rng = DateRange.from_day_count(NepaliDate(2081, 4, 15), 2)
    assert rng.dates_with_interval(11) == [NepaliDate(2081, 4, 15)]


def test_day_helpers_never_throw_at_the_data_end() -> None:
    """A one-day range on 2199-12-30 returns its date and does not advance past it (D-16)."""
    last = NepaliDate(2199, 12, 30)
    rng = DateRange.single(last)
    assert list(rng) == [last]
    assert rng.dates_with_interval(1) == [last]
    assert rng.working_days() == [last]
    assert rng.weekend_days() == []
    assert rng.split_by_month() == [rng]
    assert rng.split_by_fiscal_quarter() == [rng]
