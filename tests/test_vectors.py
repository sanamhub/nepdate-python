"""Golden vector tests: month boundaries and the C# dates table."""

from __future__ import annotations

from collections.abc import Callable

from nepdate import NepaliDate
from nepdate._names import Weekday

_MONTH_BOUNDARY_ROWS = 7176


def _parse_bs(value: str) -> tuple[int, int, int]:
    year, month, day = value.split("-")
    return int(year), int(month), int(day)


def test_month_boundaries(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every month boundary row matches: AD date, weekday and month length."""
    rows = vector_reader("month-boundaries.csv")
    assert len(rows) == _MONTH_BOUNDARY_ROWS
    for row in rows:
        date = NepaliDate(*_parse_bs(row["bs"]))
        assert date.to_date().isoformat() == row["ad"]
        assert date.weekday is Weekday[row["weekday"].upper()]
        assert date.month_length == int(row["month_length"])


def test_golden_dates(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """The C# golden dates table matches for ad, weekday, day_of_year and month_length."""
    rows = vector_reader("csharp-golden", "dates.tsv")
    for row in rows:
        date = NepaliDate(*_parse_bs(row["bs"]))
        assert date.to_date().isoformat() == row["ad"]
        assert date.weekday is Weekday[row["weekday"].upper()]
        assert date.day_of_year == int(row["day_of_year"])
        assert date.month_length == int(row["month_length"])
