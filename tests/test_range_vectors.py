"""Range vector tests: ranges.tsv, range-factories.tsv, range-splits.tsv and range-format.tsv."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from nepdate import DateOrder, DateRange, FiscalYear, Lang, NepaliDate, Separator
from nepdate._errors import NepDateError

_RANGE_ROWS = 54
_FACTORY_ROWS = 27
_SPLIT_ROWS = 9
_FORMAT_ROWS = 18


def _date(value: str) -> NepaliDate:
    year, month, day = value.split("-")
    return NepaliDate(int(year), int(month), int(day))


def _range(value: str) -> DateRange:
    start, end = value.split("..")
    return DateRange(_date(start), _date(end))


def _range_text(value: DateRange) -> str:
    return f"{value.start.isoformat()}..{value.end.isoformat()}"


def _joined(values: list[DateRange]) -> str:
    return ";".join(_range_text(value) for value in values) or "none"


def _date_text(values: list[NepaliDate]) -> str:
    return ";".join(value.isoformat() for value in values) or "none"


def test_ranges_vectors(  # noqa: PLR0912 - one branch per operation in the vector
    vector_reader: Callable[..., list[dict[str, str]]],
) -> None:
    """Every row of ranges.tsv matches, including the D-01 and D-16 rows."""
    rows = vector_reader("csharp-golden", "ranges.tsv")
    assert len(rows) == _RANGE_ROWS
    for row in rows:
        operation = row["operation"]
        expected = row["result"]
        if operation == "construct":
            if expected == "ERR":
                with pytest.raises(NepDateError):
                    DateRange(_date(row["start"]), _date(row["end"]))
            else:
                assert _range_text(DateRange(_date(row["start"]), _date(row["end"]))) == expected
            continue
        rng = DateRange(_date(row["start"]), _date(row["end"]))
        if operation == "length":
            assert len(rng) == int(expected), row
        elif operation == "contains_date":
            assert (_date(row["argument"]) in rng) is (expected == "true"), row
        elif operation == "contains_range":
            assert rng.contains_range(_range(row["argument"])) is (expected == "true"), row
        elif operation == "overlaps":
            assert rng.overlaps(_range(row["argument"])) is (expected == "true"), row
        elif operation == "is_adjacent_to":
            assert rng.is_adjacent_to(_range(row["argument"])) is (expected == "true"), row
        elif operation == "intersect":
            found = rng.intersect(_range(row["argument"]))
            assert ("none" if found is None else _range_text(found)) == expected, row
        elif operation == "union":
            assert _range_text(rng.union(_range(row["argument"]))) == expected, row
        elif operation == "except":
            assert _joined(rng.difference(_range(row["argument"]))) == expected, row
        elif operation == "equals":
            assert (rng == _range(row["argument"])) is (expected == "true"), row
        elif operation == "to_string":
            assert str(rng) == expected, row
        elif operation == "enumerate":
            assert _date_text(list(rng)) == expected, row
        else:  # pragma: no cover - the vector only names the operations above
            raise AssertionError(f"unknown operation {operation}")


def _factory(name: str, argument: str) -> DateRange:
    """Build the range one range-factories.tsv row names."""
    if name == "single_day":
        return DateRange.single(_date(argument))
    if name == "from_day_count":
        start, days = argument.split(",")
        return DateRange.from_day_count(_date(start), int(days))
    if name == "for_month":
        year, month = argument.split(",")
        return DateRange.month(int(year), int(month))
    if name == "for_calendar_year":
        return DateRange.year(int(argument))
    if name == "for_fiscal_year":
        return FiscalYear(int(argument)).range()
    if name == "construct":
        start, end = argument.split(",")
        return DateRange(_date(start), _date(end))
    raise AssertionError(f"unknown factory {name}")  # pragma: no cover


def test_range_factory_vectors(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of range-factories.tsv matches, including the refused arguments."""
    rows = vector_reader("csharp-golden", "range-factories.tsv")
    assert len(rows) == _FACTORY_ROWS
    for row in rows:
        if row["result"] == "ERR":
            with pytest.raises(NepDateError):
                _factory(row["factory"], row["argument"])
        else:
            actual = _factory(row["factory"], row["argument"])
            assert _range_text(actual) == row["result"], row


def test_range_split_vectors(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of range-splits.tsv matches, including the D-16 rows at the data end."""
    rows = vector_reader("csharp-golden", "range-splits.tsv")
    assert len(rows) == _SPLIT_ROWS
    for row in rows:
        rng = DateRange(_date(row["start"]), _date(row["end"]))
        if row["operation"] == "split_by_month":
            parts = rng.split_by_month()
        else:
            parts = rng.split_by_fiscal_quarter()
        assert _joined(parts) == row["result"], row


def test_range_format_vectors(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of range-format.tsv matches, including the D-15 rows and the refused range."""
    rows = vector_reader("csharp-golden", "range-format.tsv")
    assert len(rows) == _FORMAT_ROWS
    for row in rows:
        if row["result"] == "ERR":
            with pytest.raises(NepDateError):
                DateRange(_date(row["start"]), _date(row["end"]))
            continue
        rng = DateRange(_date(row["start"]), _date(row["end"]))
        if row["kind"] == "default":
            assert str(rng) == row["result"], row
        else:
            actual = rng.to_string(
                DateOrder[row["order"].upper()],
                Separator[row["separator"].upper()],
                Lang[row["lang"].upper()],
            )
            assert actual == row["result"], row
