"""Batch conversion tests: bulk.tsv, ordered in both directions (NC04 to NC08)."""

from __future__ import annotations

import datetime
from collections.abc import Callable, Iterable

import pytest

from nepdate import NepaliDate, to_english_dates, to_nepali_dates
from nepdate._errors import NepDateError

_ROWS = 6


def _date(value: str) -> NepaliDate:
    year, month, day = value.split("-")
    return NepaliDate(int(year), int(month), int(day))


def _dates(value: str) -> list[NepaliDate]:
    return [_date(part) for part in value.split(";")]


def _ad_dates(value: str) -> list[datetime.date]:
    return [datetime.date.fromisoformat(part) for part in value.split(";")]


def _english(items: Iterable[str]) -> list[str]:
    return [d.isoformat() for d in to_english_dates(items)]


def _nepali(dates: Iterable[datetime.date]) -> list[str]:
    return [d.isoformat() for d in to_nepali_dates(dates)]


def test_bulk_vectors(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every row of bulk.tsv matches, including the one error row."""
    rows = vector_reader("csharp-golden", "bulk.tsv")
    assert len(rows) == _ROWS
    for row in rows:
        operation = row["operation"]
        if operation in {"to_nepali_dates", "batch_to_nepali_dates"}:
            assert _nepali(_ad_dates(row["input"])) == row["output"].split(";"), row
        elif operation == "to_english_dates_from_strings":
            if row["output"] == "ERR":
                with pytest.raises(NepDateError):
                    _english(row["input"].split(";"))
            else:
                assert _english(row["input"].split(";")) == row["output"].split(";"), row
        elif operation in {"to_english_dates_from_dates", "batch_to_english_dates"}:
            assert _english(_dates(row["input"])) == row["output"].split(";"), row
        else:  # pragma: no cover - the vector only names the five operations above
            raise AssertionError(f"unknown operation {operation}")


def test_batch_keeps_input_order_and_accepts_iterators() -> None:
    """The output is in input order, and each function takes any iterable, not only a list."""
    gregorian = (datetime.date(2025, 4, 14), datetime.date(1844, 4, 11), datetime.date(2000, 1, 1))
    assert [d.isoformat() for d in to_nepali_dates(iter(gregorian))] == [
        "2082-01-01",
        "1901-01-01",
        "2056-09-17",
    ]
    assert _english(iter(["2081-04-15", "1901-01-01"])) == ["2024-07-30", "1844-04-11"]


def test_batch_output_is_a_new_list() -> None:
    """The result is a list the caller can change without touching the input."""
    dates = [datetime.date(2024, 7, 31)]
    result = to_nepali_dates(dates)
    assert isinstance(result, list)
    result.clear()
    assert dates == [datetime.date(2024, 7, 31)]


def test_batch_rejects_a_foreign_item() -> None:
    """A string is a date in one direction only; a foreign value raises TypeError."""
    with pytest.raises(TypeError):
        to_english_dates([2081])
    with pytest.raises(NepDateError):
        to_english_dates(["not a date"])
