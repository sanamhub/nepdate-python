"""Fiscal year and quarter tests (P2-04)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from nepdate import FiscalYear, Lang, NepaliDate, Quarter
from nepdate._errors import ErrorKind, NepDateError
from nepdate._names import Month


def _bs_date(value: str) -> NepaliDate:
    year, month, day = value.split("-")
    return NepaliDate(int(year), int(month), int(day))


def test_fiscal_year_golden(vector_reader: Callable[..., list[dict[str, str]]]) -> None:
    """Every dates.tsv fy_start, fy_end, quarter_start and quarter_end row matches."""
    rows = vector_reader("csharp-golden", "dates.tsv")
    for row in rows:
        date = _bs_date(row["bs"])
        fy = date.fiscal_year()
        for column, method in (("fy_start", fy.start), ("fy_end", fy.end)):
            if row[column] == "ERR":
                with pytest.raises(NepDateError) as caught:
                    method()
                assert caught.value.kind is ErrorKind.OUT_OF_RANGE
            else:
                assert method() == _bs_date(row[column])
        quarter = fy.quarter_range(date.quarter())
        assert quarter.start == _bs_date(row["quarter_start"])
        assert quarter.end == _bs_date(row["quarter_end"])


def test_fiscal_year_label() -> None:
    """The P2-04 acceptance example."""
    assert FiscalYear(2082).label() == "2082/83"
    assert FiscalYear(2082).label(Lang.NE) == "२०८२/८३"


def test_fiscal_year_containing() -> None:
    """Dates before Shrawan belong to the previous fiscal year."""
    assert NepaliDate(2081, 4, 15).fiscal_year() == FiscalYear(2081)
    assert NepaliDate(2081, 3, 15).fiscal_year() == FiscalYear(2080)
    assert NepaliDate(2081, 1, 1).fiscal_year() == FiscalYear(2080)


def test_fiscal_year_boundaries() -> None:
    """The boundary fiscal years have one out-of-range end each."""
    fy = FiscalYear(1900)
    with pytest.raises(NepDateError):
        fy.start()
    assert fy.end() == NepaliDate(1901, 3, 32)
    fy = FiscalYear(2199)
    assert fy.start() == NepaliDate(2199, 4, 1)
    with pytest.raises(NepDateError):
        fy.end()


def test_fiscal_year_invalid_year() -> None:
    """A fiscal year with neither end in range is rejected."""
    for year in (1843, 2200):
        with pytest.raises(NepDateError) as caught:
            FiscalYear(year)
        assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_quarter_months() -> None:
    """Quarter.months returns the three calendar months in order."""
    assert Quarter.Q1.months() == (Month.SHRAWAN, Month.BHADRA, Month.ASHOJ)
    assert Quarter.Q2.months() == (Month.KARTIK, Month.MANGSIR, Month.POUSH)
    assert Quarter.Q3.months() == (Month.MAGH, Month.FALGUN, Month.CHAITRA)
    assert Quarter.Q4.months() == (Month.BAISHAKH, Month.JESTHA, Month.ASHAD)


def test_date_quarter() -> None:
    """The quarter follows ALGORITHM §8b month ranges."""
    assert NepaliDate(2081, 4, 15).quarter() is Quarter.Q1
    assert NepaliDate(2081, 8, 15).quarter() is Quarter.Q2
    assert NepaliDate(2081, 11, 15).quarter() is Quarter.Q3
    assert NepaliDate(2081, 2, 15).quarter() is Quarter.Q4
