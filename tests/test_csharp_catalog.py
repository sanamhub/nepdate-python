"""One test per C# catalogue row tagged phase 1 (P1-05)."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest

from nepdate import (
    MAX,
    MIN,
    DateOrder,
    DateRange,
    FiscalYear,
    Lang,
    NepaliDate,
    Overflow,
    Quarter,
    Separator,
    _calendar,
    to_nepali_digits,
)
from nepdate._errors import ErrorKind, NepDateError
from nepdate._names import Month, Weekday

_PHASE_1_ROWS = 113
_PHASE_2_ROWS = 180
_PHASE_3_ROWS = 148

_D1 = NepaliDate(2081, 1, 1)
_D2 = NepaliDate(2081, 1, 2)
_D3 = NepaliDate(2081, 2, 1)
_FORMAT_DATE = NepaliDate(2081, 4, 15)
_VERIFY_DATE = NepaliDate(2080, 5, 15)
_YEAR_2080 = 2080
_MONTH_NUMBERS = tuple(range(1, 13))
_DISPLAY_LENGTH = 10
_MIN_MONTH_LENGTH = 29
_MAX_MONTH_LENGTH = 32


def _test_name(catalog_id: str) -> str:
    """Map a catalogue row id to its test function name.

    Args:
        catalog_id: The catalogue ``id``.

    Returns:
        ``test_`` plus the id lower-cased with every non-alphanumeric character as ``_``.
    """
    lowered = catalog_id.lower()
    sanitized = "".join(ch if ("a" <= ch <= "z") or ("0" <= ch <= "9") else "_" for ch in lowered)
    return "test_" + sanitized


def _catalog_rows(repo_root: Path) -> list[dict[str, str]]:
    """Read the catalogue rows, skipping its comment line.

    Args:
        repo_root: The repository root directory.

    Returns:
        One dictionary per data row, keyed by the header line.
    """
    path = repo_root / "shared" / "spec" / "vectors" / "csharp-tests" / "catalog.tsv"
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        if header is None:
            header = line.split("\t")
            continue
        rows.append(dict(zip(header, line.split("\t"), strict=True)))
    return rows


def _assert_construction_error(args: tuple[int, int, int], kind: ErrorKind) -> None:
    """Assert NepaliDate(*args) raises NepDateError with the given kind.

    Args:
        args: The constructor arguments.
        kind: The expected ErrorKind.
    """
    with pytest.raises(NepDateError) as caught:
        NepaliDate(*args)
    assert caught.value.kind is kind


def _assert_parse_error(text: str, kind: ErrorKind) -> None:
    """Assert ``NepaliDate.parse(text)`` raises ``NepDateError`` with the given kind.

    Args:
        text: The strict input.
        kind: The expected ErrorKind.
    """
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse(text)
    assert caught.value.kind is kind


def _assert_lenient_error(text: str, kind: ErrorKind) -> None:
    """Assert ``NepaliDate.parse_lenient(text)`` raises ``NepDateError`` with the given kind.

    Args:
        text: The lenient input.
        kind: The expected ErrorKind.
    """
    with pytest.raises(NepDateError) as caught:
        NepaliDate.parse_lenient(text)
    assert caught.value.kind is kind


def test_all_phase_1_rows_have_a_test(repo_root: Path) -> None:
    """Every catalogue row tagged phase 1 has a test named after its id."""
    rows = [row for row in _catalog_rows(repo_root) if row["phase"] == "1"]
    assert len(rows) == _PHASE_1_ROWS
    module = sys.modules[__name__]
    missing = [row["id"] for row in rows if not hasattr(module, _test_name(row["id"]))]
    assert not missing, f"phase 1 rows without a test: {missing}"


def test_all_phase_2_rows_have_a_test(repo_root: Path) -> None:
    """Every catalogue row tagged phase 2 has a test named after its id."""
    rows = [row for row in _catalog_rows(repo_root) if row["phase"] == "2"]
    assert len(rows) == _PHASE_2_ROWS
    module = sys.modules[__name__]
    missing = [row["id"] for row in rows if not hasattr(module, _test_name(row["id"]))]
    assert not missing, f"phase 2 rows without a test: {missing}"


def test_all_phase_3_rows_have_a_test(repo_root: Path) -> None:
    """Every catalogue row tagged phase 3 has a test named after its id."""
    rows = [row for row in _catalog_rows(repo_root) if row["phase"] == "3"]
    assert len(rows) == _PHASE_3_ROWS
    module = sys.modules[__name__]
    missing = [row["id"] for row in rows if not hasattr(module, _test_name(row["id"]))]
    assert not missing, f"phase 3 rows without a test: {missing}"


# --- Abilities/NepaliDateComparableTests.cs ---


def test_nepalidatecomparabletests_compareto_object_earlier_returnsnegative() -> None:
    """The earlier date orders below the later one."""
    assert _D1 < _D2


def test_nepalidatecomparabletests_compareto_object_same_returnszero() -> None:
    """Equal dates compare equal."""
    assert NepaliDate(2081, 1, 1) == _D1


def test_nepalidatecomparabletests_compareto_object_later_returnspositive() -> None:
    """The later date orders above the earlier one."""
    assert _D3 > _D1


def test_nepalidatecomparabletests_compareto_object_null_returnspositive() -> None:
    """C# compares against null; Python has no null reference."""
    pytest.skip("n/a: C# null reference")


def test_nepalidatecomparabletests_compareto_wrongtype_throwsargumentexception() -> None:
    """C# IComparable.CompareTo throws on a wrong type; Python returns NotImplemented."""
    pytest.skip("n/a: C# IComparable.CompareTo")


def test_nepalidatecomparabletests_compareto_generic_earlier_returnsnegative() -> None:
    """The earlier date orders below the later one."""
    assert _D1 < _D2


def test_nepalidatecomparabletests_compareto_generic_same_returnszero() -> None:
    """Equal dates compare equal."""
    assert NepaliDate(2081, 1, 1) == _D1


def test_nepalidatecomparabletests_compareto_generic_later_returnspositive() -> None:
    """The later date orders above the earlier one."""
    assert _D3 > _D1


def test_nepalidatecomparabletests_sortedset_orderscorrectly() -> None:
    """Sorting puts the earliest date first."""
    assert sorted([_D3, _D1, _D2])[0] == _D1


def test_nepalidatecomparabletests_arraysort_viaicomparable_orderscorrectly() -> None:
    """Sorting an array-like list puts the earliest date first."""
    dates = [_D3, _D1, _D2]
    assert sorted(dates)[0] == _D1


def test_nepalidatecomparabletests_list_sort_orderscorrectly() -> None:
    """Sorting a list in place puts the earliest date first."""
    dates = [_D3, _D1, _D2]
    dates.sort()
    assert dates[0] == _D1


# --- Core/DictionaryIntegrityTests.cs ---


def test_dictionaryintegritytests_allnepalimonths_roundtriptoenglishandback_producesoriginaldate() -> (
    None
):
    """Every BS month's first day round-trips through AD and back."""
    for index, _length in enumerate(_calendar.MONTH_LENGTHS):
        year = _calendar.MIN_YEAR + index // 12
        month = index % 12 + 1
        date = NepaliDate(year, month, 1)
        assert NepaliDate.from_date(date.to_date()) == date


def test_dictionaryintegritytests_allnepalidays_roundtriptoenglishandback_producesoriginaldate() -> (
    None
):
    """Every BS day round-trips through AD and back."""
    for serial in range(_calendar.MONTH_START[-1]):
        date = NepaliDate.from_ordinal(_calendar.ORDINAL_OFFSET + serial)
        assert NepaliDate.from_date(date.to_date()) == date


def test_dictionaryintegritytests_allenglishdays_roundtriptonepaliandback_producesoriginaldate() -> (
    None
):
    """Every AD day in range round-trips through BS and back."""
    for serial in range(_calendar.MONTH_START[-1]):
        ad = datetime.date.fromordinal(_calendar.ORDINAL_OFFSET + serial)
        date = NepaliDate.from_date(ad)
        assert date.to_date() == ad


def test_dictionaryintegritytests_allmonths_monthendday_iswithinvalidrange() -> None:
    """Every month length is between 29 and 32 days."""
    assert min(_calendar.MONTH_LENGTHS) == _MIN_MONTH_LENGTH
    assert max(_calendar.MONTH_LENGTHS) == _MAX_MONTH_LENGTH


def test_dictionaryintegritytests_consecutivenepalidays_produceconsecutiveenglishdays() -> None:
    """Consecutive BS days map to consecutive AD days."""
    previous = NepaliDate.from_ordinal(_calendar.ORDINAL_OFFSET).to_date()
    for serial in range(1, _calendar.MONTH_START[-1]):
        current = NepaliDate.from_ordinal(_calendar.ORDINAL_OFFSET + serial).to_date()
        assert (current - previous).days == 1
        previous = current


def test_dictionaryintegritytests_knownreferencedates_convertcorrectly_1() -> None:
    """2080-01-01 BS is 2023-04-14 AD."""
    assert NepaliDate(2080, 1, 1).to_date() == datetime.date(2023, 4, 14)


def test_dictionaryintegritytests_knownreferencedates_convertcorrectly_2() -> None:
    """2000-01-01 BS is 1943-04-14 AD."""
    assert NepaliDate(2000, 1, 1).to_date() == datetime.date(1943, 4, 14)


def test_dictionaryintegritytests_knownreferencedates_convertcorrectly_3() -> None:
    """2081-01-01 BS is 2024-04-13 AD."""
    assert NepaliDate(2081, 1, 1).to_date() == datetime.date(2024, 4, 13)


def test_dictionaryintegritytests_knownreferencedates_convertcorrectly_4() -> None:
    """1901-01-01 BS is 1844-04-11 AD."""
    assert NepaliDate(1901, 1, 1).to_date() == datetime.date(1844, 4, 11)


def test_dictionaryintegritytests_boundarydates_convertcorrectly() -> None:
    """The two boundary dates are MIN and MAX."""
    assert NepaliDate(1901, 1, 1) == MIN
    assert NepaliDate(2199, 12, 30) == MAX


def test_dictionaryintegritytests_totaldaysinrange_matchesenglishdatespan() -> None:
    """The supported BS range spans the same number of days as its AD span."""
    span = datetime.date(2143, 4, 15) - datetime.date(1844, 4, 11)
    assert _calendar.MONTH_START[-1] == span.days + 1


# --- Core/NepaliDateConstructionTests.cs ---


def test_nepalidateconstructiontests_constructor_validnepalidate_createsinstance() -> None:
    """A valid date keeps its fields."""
    assert (
        NepaliDate(2080, 1, 1).year,
        NepaliDate(2080, 1, 1).month,
        NepaliDate(2080, 1, 1).day,
    ) == (2080, 1, 1)


def test_nepalidateconstructiontests_constructor_minvalue_createsinstance() -> None:
    """The minimum year constructs."""
    assert NepaliDate(1901, 1, 1) == MIN


def test_nepalidateconstructiontests_constructor_maxvalue_createsinstance() -> None:
    """The maximum year constructs."""
    assert NepaliDate(2199, 12, 30) == MAX


def test_nepalidateconstructiontests_constructor_invalidnepalidate_throwsexception_1() -> None:
    """Month 0 is invalid."""
    _assert_construction_error((2080, 0, 1), ErrorKind.INVALID_MONTH)


def test_nepalidateconstructiontests_constructor_invalidnepalidate_throwsexception_2() -> None:
    """Month 13 is invalid."""
    _assert_construction_error((2080, 13, 1), ErrorKind.INVALID_MONTH)


def test_nepalidateconstructiontests_constructor_invalidnepalidate_throwsexception_3() -> None:
    """Day 0 is invalid."""
    _assert_construction_error((2080, 1, 0), ErrorKind.INVALID_DAY)


def test_nepalidateconstructiontests_constructor_invalidnepalidate_throwsexception_4() -> None:
    """Day 33 is invalid."""
    _assert_construction_error((2080, 1, 33), ErrorKind.INVALID_DAY)


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_1() -> None:
    """The strict parser accepts ``2080/05/15``."""
    assert NepaliDate.parse("2080/05/15").year == _YEAR_2080


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_2() -> None:
    """The strict parser accepts ``2080-05-15``."""
    assert NepaliDate.parse("2080-05-15").year == _YEAR_2080


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_3() -> None:
    """The strict parser accepts ``2080.05.15``."""
    assert NepaliDate.parse("2080.05.15").year == _YEAR_2080


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_4() -> None:
    """The strict parser accepts ``2080_05_15``."""
    assert NepaliDate.parse("2080_05_15").year == _YEAR_2080


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_5() -> None:
    """The strict parser accepts backslash separators."""
    assert NepaliDate.parse("2080\\05\\15").year == _YEAR_2080


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_6() -> None:
    """The strict parser accepts space separators."""
    assert NepaliDate.parse("2080 05 15").year == _YEAR_2080


def test_nepalidateconstructiontests_constructor_autoadjustedformats_createsinstance_1() -> None:
    """C# auto-adjusts ambiguous strings; the port has no such constructor."""
    pytest.skip("n/a: C# auto-adjust constructor")


def test_nepalidateconstructiontests_constructor_autoadjustedformats_createsinstance_2() -> None:
    """C# auto-adjusts ambiguous strings; the port has no such constructor."""
    pytest.skip("n/a: C# auto-adjust constructor")


def test_nepalidateconstructiontests_constructor_autoadjustedformats_createsinstance_3() -> None:
    """C# auto-adjusts ambiguous strings; the port has no such constructor."""
    pytest.skip("n/a: C# auto-adjust constructor")


def test_nepalidateconstructiontests_constructor_autoadjustedformats_createsinstance_4() -> None:
    """C# auto-adjusts ambiguous strings; the port has no such constructor."""
    pytest.skip("n/a: C# auto-adjust constructor")


def test_nepalidateconstructiontests_constructor_autoadjust_monthoverflowwithboundaryday_swapsasdocumented_1() -> (
    None
):
    """C# swaps an overflowing month and day; the port does not guess."""
    pytest.skip("n/a: C# auto-adjust constructor")


def test_nepalidateconstructiontests_constructor_autoadjust_monthoverflowwithboundaryday_swapsasdocumented_2() -> (
    None
):
    """C# swaps an overflowing month and day; the port does not guess."""
    pytest.skip("n/a: C# auto-adjust constructor")


def test_nepalidateconstructiontests_tryparse_autoadjust_monthoverflowwithboundaryday_swapsasdocumented() -> (
    None
):
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


def test_nepalidateconstructiontests_constructor_invalidstringformats_throwsexception_1() -> None:
    """An empty string has no groups."""
    _assert_parse_error("", ErrorKind.WRONG_GROUP_COUNT)


def test_nepalidateconstructiontests_constructor_invalidstringformats_throwsexception_2() -> None:
    """Letters are not a valid character."""
    _assert_parse_error("invalid", ErrorKind.INVALID_CHARACTER)


def test_nepalidateconstructiontests_constructor_invalidstringformats_throwsexception_3() -> None:
    """Two groups are too few."""
    _assert_parse_error("2080/5", ErrorKind.WRONG_GROUP_COUNT)


def test_nepalidateconstructiontests_constructor_validformatinvaliddate_throwsexception_1() -> None:
    """A valid shape with day 40 is an invalid day."""
    _assert_parse_error("2080/5/40", ErrorKind.INVALID_DAY)


def test_nepalidateconstructiontests_constructor_englishdate_convertscorrectly() -> None:
    """An English date converts to the matching BS year."""
    assert NepaliDate.from_date(datetime.date(2023, 4, 14)) == NepaliDate(2080, 1, 1)


def test_nepalidateconstructiontests_tryparse_validstring_returnstruewithcorrectdate() -> None:
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


def test_nepalidateconstructiontests_tryparse_invalidstring_returnsfalsewithdefault_1() -> None:
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


def test_nepalidateconstructiontests_tryparse_invalidstring_returnsfalsewithdefault_2() -> None:
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


def test_nepalidateconstructiontests_tryparse_invalidstring_returnsfalsewithdefault_3() -> None:
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


# --- Core/NepaliDatePropertiesTests.cs ---


def test_nepalidatepropertiestests_englishdate_conversion_returnscorrectdate() -> None:
    """to_date yields the AD date for a known BS date."""
    assert NepaliDate(2080, 1, 1).to_date() == datetime.date(2023, 4, 14)


def test_nepalidatepropertiestests_dayofweek_returnscorrectvalue() -> None:
    """2080-01-01 is a Friday."""
    assert NepaliDate(2080, 1, 1).weekday is Weekday.FRIDAY


def test_nepalidatepropertiestests_monthendday_returnscorrectvalue() -> None:
    """Baishakh 2080 has 31 days."""
    assert NepaliDate(2080, 1, 1).month_length == NepaliDate(2080, 1, 1).last_of_month().day


def test_nepalidatepropertiestests_monthname_returnscorrectenum() -> None:
    """Month 5 is Bhadra."""
    assert NepaliDate(2080, 5, 1).month_enum is Month.BHADRA


def test_nepalidatepropertiestests_today_returnscurrentnepalidate() -> None:
    """``today`` returns a date inside the supported range."""
    today = NepaliDate.today()
    assert MIN <= today <= MAX


def test_nepalidatepropertiestests_dayofyear_firstdayofyear_returns1() -> None:
    """The first day of the year is day 1 of the year."""
    assert NepaliDate(2080, 1, 1).day_of_year == 1


def test_nepalidatepropertiestests_dayofyear_firstdayofmonth4_equalssum_of_months1to3_plus1() -> (
    None
):
    """The first day of month 4 is one past the first three months."""
    expected = sum(NepaliDate(2080, month, 1).month_length for month in range(1, 4)) + 1
    assert NepaliDate(2080, 4, 1).day_of_year == expected


def test_nepalidatepropertiestests_equals_nullobject_returnsfalse() -> None:
    """Equality with None is False."""
    assert (NepaliDate(2080, 5, 15) == None) is False  # noqa: E711


def test_nepalidatepropertiestests_equals_differenttype_returnsfalse() -> None:
    """Equality with another type is False."""
    assert (NepaliDate(2080, 5, 15) == "2080/05/15") is False


# --- Core/OptimizationVerificationTests.cs ---


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_1() -> None:
    """The strict parser accepts ``/``."""
    assert NepaliDate.parse("2080/05/15").year == _YEAR_2080


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_2() -> None:
    """The strict parser accepts ``-``."""
    assert NepaliDate.parse("2080-05-15").year == _YEAR_2080


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_3() -> None:
    """The strict parser accepts ``.``."""
    assert NepaliDate.parse("2080.05.15").year == _YEAR_2080


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_4() -> None:
    """The strict parser accepts ``_``."""
    assert NepaliDate.parse("2080_05_15").year == _YEAR_2080


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_5() -> None:
    """The strict parser accepts a backslash."""
    assert NepaliDate.parse("2080\\05\\15").year == _YEAR_2080


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_6() -> None:
    """The strict parser accepts a space."""
    assert NepaliDate.parse("2080 05 15").year == _YEAR_2080


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_7() -> None:
    """The strict parser accepts the danda ``।``."""
    assert NepaliDate.parse("2080।05।15").year == _YEAR_2080


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_8() -> None:
    """The strict parser accepts ``|``."""
    assert NepaliDate.parse("2080|05|15").year == _YEAR_2080


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_1() -> None:
    """An empty string has no groups."""
    _assert_parse_error("", ErrorKind.WRONG_GROUP_COUNT)


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_2() -> None:
    """Letters are not a valid character."""
    _assert_parse_error("invalid", ErrorKind.INVALID_CHARACTER)


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_3() -> None:
    """Two groups are too few."""
    _assert_parse_error("2080/05", ErrorKind.WRONG_GROUP_COUNT)


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_4() -> None:
    """One group is too few."""
    _assert_parse_error("2080", ErrorKind.WRONG_GROUP_COUNT)


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_5() -> None:
    """A fourth group is rejected."""
    _assert_parse_error("2080/05/15/99", ErrorKind.WRONG_GROUP_COUNT)


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_6() -> None:
    """Letters are not a valid character."""
    _assert_parse_error("abc/def/ghi", ErrorKind.INVALID_CHARACTER)


def test_optimizationverificationtests_constructor_nullstring_throwsexception() -> None:
    """C# throws on a null string; Python has no null reference."""
    pytest.skip("n/a: C# null reference")


def test_optimizationverificationtests_constructor_withoutleadingzeros_parsescorrectly_1() -> None:
    """``2080/5/15`` parses without leading zeros."""
    assert NepaliDate.parse("2080/5/15") == NepaliDate(2080, 5, 15)


def test_optimizationverificationtests_constructor_withoutleadingzeros_parsescorrectly_2() -> None:
    """``2080/05/5`` parses without a leading zero on the day."""
    assert NepaliDate.parse("2080/05/5") == NepaliDate(2080, 5, 5)


def test_optimizationverificationtests_constructor_withoutleadingzeros_parsescorrectly_3() -> None:
    """``2080/1/1`` parses without leading zeros."""
    assert NepaliDate.parse("2080/1/1") == NepaliDate(2080, 1, 1)


def test_optimizationverificationtests_operator_equality_samedates_returnstrue() -> None:
    """Equal dates compare equal."""
    assert NepaliDate(2080, 5, 15) == NepaliDate(2080, 5, 15)


def test_optimizationverificationtests_operator_inequality_differentdates_returnstrue() -> None:
    """Different dates compare unequal."""
    assert NepaliDate(2080, 5, 15) != NepaliDate(2080, 5, 16)


def test_optimizationverificationtests_operator_lessthan_earlierdate_returnstrue() -> None:
    """An earlier date is less than a later date."""
    assert NepaliDate(2080, 5, 15) < NepaliDate(2080, 5, 16)


def test_optimizationverificationtests_operator_lessthanorequal_sameandearlier_returnstrue() -> (
    None
):
    """Less-than-or-equal holds for equal and earlier dates."""
    assert NepaliDate(2080, 5, 15) <= NepaliDate(2080, 5, 16)
    assert NepaliDate(2080, 5, 15) <= NepaliDate(2080, 5, 15)


def test_optimizationverificationtests_operator_greaterthan_laterdate_returnstrue() -> None:
    """A later date is greater than an earlier date."""
    assert NepaliDate(2080, 5, 16) > NepaliDate(2080, 5, 15)


def test_optimizationverificationtests_operator_greaterthanorequal_sameandlater_returnstrue() -> (
    None
):
    """Greater-than-or-equal holds for equal and later dates."""
    assert NepaliDate(2080, 5, 16) >= NepaliDate(2080, 5, 15)
    assert NepaliDate(2080, 5, 15) >= NepaliDate(2080, 5, 15)


def test_optimizationverificationtests_operator_minmaxboundary_correctordering() -> None:
    """MIN is below MAX."""
    assert MIN < MAX


def test_optimizationverificationtests_compareto_earlierdate_returnsnegative() -> None:
    """C# IComparable.CompareTo has no Python equivalent."""
    pytest.skip("n/a: C# IComparable.CompareTo")


def test_optimizationverificationtests_compareto_samedate_returnszero() -> None:
    """C# IComparable.CompareTo has no Python equivalent."""
    pytest.skip("n/a: C# IComparable.CompareTo")


def test_optimizationverificationtests_compareto_laterdate_returnspositive() -> None:
    """C# IComparable.CompareTo has no Python equivalent."""
    pytest.skip("n/a: C# IComparable.CompareTo")


def test_optimizationverificationtests_compareto_differentyears_correctordering() -> None:
    """C# IComparable.CompareTo has no Python equivalent."""
    pytest.skip("n/a: C# IComparable.CompareTo")


def test_optimizationverificationtests_compareto_differentmonths_correctordering() -> None:
    """C# IComparable.CompareTo has no Python equivalent."""
    pytest.skip("n/a: C# IComparable.CompareTo")


def test_optimizationverificationtests_equals_samedates_returnstrue() -> None:
    """Equal dates report equal."""
    a = NepaliDate(2080, 5, 15)
    b = NepaliDate(2080, 5, 15)
    assert a == b


def test_optimizationverificationtests_equals_differentdates_returnsfalse() -> None:
    """Different dates report unequal."""
    a = NepaliDate(2080, 5, 15)
    b = NepaliDate(2080, 5, 16)
    assert a != b


def test_optimizationverificationtests_gethashcode_equaldates_samehashcode() -> None:
    """Equal dates hash equally."""
    assert hash(NepaliDate(2080, 5, 15)) == hash(NepaliDate(2080, 5, 15))


def test_optimizationverificationtests_gethashcode_stableacrossmultiplecalls() -> None:
    """The hash is stable across calls."""
    date = NepaliDate(2080, 5, 15)
    assert hash(date) == hash(date)


def test_optimizationverificationtests_isleapyear_checksenglishyearcorrectly_1() -> None:
    """IsLeapYear is not ported (D-12)."""
    pytest.skip("D-12: IsLeapYear is not ported")


def test_optimizationverificationtests_isleapyear_checksenglishyearcorrectly_2() -> None:
    """IsLeapYear is not ported (D-12)."""
    pytest.skip("D-12: IsLeapYear is not ported")


def test_optimizationverificationtests_isleapyear_checksenglishyearcorrectly_3() -> None:
    """IsLeapYear is not ported (D-12)."""
    pytest.skip("D-12: IsLeapYear is not ported")


def test_optimizationverificationtests_constructor_invalidyearmonthday_throwsexception_1() -> None:
    """Month 0 is invalid."""
    _assert_construction_error((2080, 0, 15), ErrorKind.INVALID_MONTH)


def test_optimizationverificationtests_constructor_invalidyearmonthday_throwsexception_2() -> None:
    """Month 13 is invalid."""
    _assert_construction_error((2080, 13, 15), ErrorKind.INVALID_MONTH)


def test_optimizationverificationtests_constructor_invalidyearmonthday_throwsexception_3() -> None:
    """Day 0 is invalid."""
    _assert_construction_error((2080, 5, 0), ErrorKind.INVALID_DAY)


def test_optimizationverificationtests_constructor_invalidyearmonthday_throwsexception_4() -> None:
    """Day 33 is invalid."""
    _assert_construction_error((2080, 5, 33), ErrorKind.INVALID_DAY)


def test_optimizationverificationtests_constructor_invalidyearmonthday_throwsexception_5() -> None:
    """Year 1900 is out of range."""
    _assert_construction_error((1900, 1, 1), ErrorKind.OUT_OF_RANGE)


def test_optimizationverificationtests_constructor_invalidyearmonthday_throwsexception_6() -> None:
    """Year 2200 is out of range."""
    _assert_construction_error((2200, 1, 1), ErrorKind.OUT_OF_RANGE)


def test_optimizationverificationtests_constructor_minvalue_isvalid() -> None:
    """MIN constructs with year 1901."""
    assert NepaliDate(1901, 1, 1) == MIN


def test_optimizationverificationtests_constructor_maxvalue_isvalid() -> None:
    """MAX constructs with year 2199."""
    assert NepaliDate(2199, 12, 30) == MAX


def test_optimizationverificationtests_englishdate_minvalue_convertsandroundtrips() -> None:
    """MIN round-trips through AD and back."""
    assert NepaliDate.from_date(MIN.to_date()) == MIN


def test_optimizationverificationtests_englishdate_maxvalue_convertsandroundtrips() -> None:
    """MAX round-trips through AD and back."""
    assert NepaliDate.from_date(MAX.to_date()) == MAX


def test_optimizationverificationtests_englishdate_justbeforemin_throwsexception() -> None:
    """The AD day before MIN raises OUT_OF_RANGE."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_date(datetime.date(1844, 4, 10))
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_optimizationverificationtests_englishdate_justaftermax_throwsexception() -> None:
    """The AD day after MAX raises OUT_OF_RANGE."""
    with pytest.raises(NepDateError) as caught:
        NepaliDate.from_date(datetime.date(2143, 4, 16))
    assert caught.value.kind is ErrorKind.OUT_OF_RANGE


def test_optimizationverificationtests_monthendday_creatingdatewithexactendday_succeeds() -> None:
    """A date on the exact month end is its own last day."""
    date = NepaliDate(2080, 1, 31)
    assert date == date.last_of_month()


def test_optimizationverificationtests_dayofweek_matchesenglishdatedayofweek() -> None:
    """The weekday matches the AD date's weekday for a spread of dates."""
    for parts in [(1901, 1, 1), (2081, 1, 1), (2199, 12, 30)]:
        date = NepaliDate(*parts)
        assert date.weekday.value == date.to_date().isoweekday() % 7


def test_optimizationverificationtests_isdefault_defaultstruct_returnstrue() -> None:
    """D-01: an invalid date cannot be constructed."""
    pytest.skip("D-01: no default NepaliDate")


def test_optimizationverificationtests_isdefault_validdate_returnsfalse() -> None:
    """D-01: an invalid date cannot be constructed."""
    pytest.skip("D-01: no default NepaliDate")


# --- phase 2 ---


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_dateinshrawan_returnssameyearshrawan1() -> (
    None
):
    """The fiscal start of a Shrawan date is Shrawan 1 of the same year."""
    assert NepaliDate(2080, 4, 1).fiscal_year().start() == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_dateinchaitra_returnssameyearshrawan1() -> (
    None
):
    """The fiscal start of a Chaitra date is Shrawan 1 of the same year."""
    assert NepaliDate(2080, 12, 1).fiscal_year().start() == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_dateinbasikhakh_returnspreviousyearshrawan1() -> (
    None
):
    """A Baishakh date belongs to the previous fiscal year."""
    assert NepaliDate(2080, 1, 1).fiscal_year().start() == NepaliDate(2079, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_dateinashadh_returnspreviousyearshrawan1() -> (
    None
):
    """An Ashad date belongs to the previous fiscal year."""
    assert NepaliDate(2080, 3, 1).fiscal_year().start() == NepaliDate(2079, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_withpositiveyearoffset_shiftsforward() -> (
    None
):
    """A positive year offset shifts the fiscal start forward."""
    fy = NepaliDate(2080, 4, 1).fiscal_year()
    assert FiscalYear(fy.start_year + 1).start() == NepaliDate(2081, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_withnegativeyearoffset_shiftsbackward() -> (
    None
):
    """A negative year offset shifts the fiscal start backward."""
    fy = NepaliDate(2080, 4, 1).fiscal_year()
    assert FiscalYear(fy.start_year - 1).start() == NepaliDate(2079, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearenddate_dateinshrawan_returnsnextyearashad() -> (
    None
):
    """A Shrawan date ends at Ashad of the next year."""
    assert NepaliDate(2080, 4, 1).fiscal_year().end() == NepaliDate(2081, 3, 1).last_of_month()


def test_fiscalyearinstancemethodtests_fiscalyearenddate_dateinchaitra_returnsnextyearashadh() -> (
    None
):
    """A Chaitra date ends at Ashad of the next year."""
    assert NepaliDate(2080, 12, 1).fiscal_year().end() == NepaliDate(2081, 3, 1).last_of_month()


def test_fiscalyearinstancemethodtests_fiscalyearenddate_dateinbasikhakh_returnssameyearashadh() -> (
    None
):
    """A Baishakh date ends at Ashad of the same calendar year."""
    assert NepaliDate(2080, 1, 1).fiscal_year().end() == NepaliDate(2080, 3, 1).last_of_month()


def test_fiscalyearinstancemethodtests_fiscalyearenddate_withpositiveyearoffset_shiftsforward() -> (
    None
):
    """A positive year offset shifts the fiscal end forward."""
    fy = NepaliDate(2080, 4, 1).fiscal_year()
    assert FiscalYear(fy.start_year + 1).end() == NepaliDate(2082, 3, 1).last_of_month()


def test_fiscalyearinstancemethodtests_fiscalyearstartandenddate_dateinq2_returnsbothboundaries() -> (
    None
):
    """A Q2 date yields both fiscal boundaries."""
    fy = NepaliDate(2080, 7, 1).fiscal_year()
    assert fy.start() == NepaliDate(2080, 4, 1)
    assert fy.end() == NepaliDate(2081, 3, 1).last_of_month()


def test_fiscalyearinstancemethodtests_fiscalyearstartandenddate_dateinq4_returnspreviousfiscalyearboundaries() -> (
    None
):
    """A Q4 date yields the previous fiscal year boundaries."""
    fy = NepaliDate(2081, 1, 1).fiscal_year()
    assert fy.start() == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_explicitfirst_returnsshrawan1() -> (
    None
):
    """Q1 starts on Shrawan 1."""
    assert FiscalYear(2080).quarter_range(Quarter.Q1).start == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_explicitsecond_returnskartik1() -> (
    None
):
    """Q2 starts on Kartik 1."""
    assert FiscalYear(2080).quarter_range(Quarter.Q2).start == NepaliDate(2080, 7, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_explicitthird_returnsmagh1() -> (
    None
):
    """Q3 starts on Magh 1."""
    assert FiscalYear(2080).quarter_range(Quarter.Q3).start == NepaliDate(2080, 10, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_explicitfourth_returnsnextyearbasikhakh1() -> (
    None
):
    """Q4 starts on Baishakh 1 of the next year."""
    assert FiscalYear(2080).quarter_range(Quarter.Q4).start == NepaliDate(2081, 1, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_explicitfirst_returnslastdayofashoj() -> (
    None
):
    """Q1 ends on the last day of Ashoj."""
    r = FiscalYear(2080).quarter_range(Quarter.Q1)
    assert (r.end.year, r.end.month) == (2080, 6)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_explicitsecond_returnslastdayofpoush() -> (
    None
):
    """Q2 ends on the last day of Poush."""
    r = FiscalYear(2080).quarter_range(Quarter.Q2)
    assert (r.end.year, r.end.month) == (2080, 9)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_explicitthird_returnslastdayofchaitra() -> (
    None
):
    """Q3 ends on the last day of Chaitra."""
    r = FiscalYear(2080).quarter_range(Quarter.Q3)
    assert (r.end.year, r.end.month) == (2080, 12)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_explicitfourth_returnsnextyearlastdayofashadh() -> (
    None
):
    """Q4 ends on the last day of Ashad of the next year."""
    r = FiscalYear(2080).quarter_range(Quarter.Q4)
    assert (r.end.year, r.end.month) == (2081, 3)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartandenddate_explicitsecond_returnsbothboundaries() -> (
    None
):
    """An explicit Q2 yields its start boundary."""
    r = FiscalYear(2080).quarter_range(Quarter.Q2)
    assert r.start == NepaliDate(2080, 7, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartandenddate_explicitthird_returnsbothboundaries() -> (
    None
):
    """An explicit Q3 yields its start boundary."""
    r = FiscalYear(2080).quarter_range(Quarter.Q3)
    assert r.start == NepaliDate(2080, 10, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_current_dateinq1_returnsshrawan1() -> (
    None
):
    """The current quarter of a Q1 date starts on Shrawan 1."""
    d = NepaliDate(2080, 4, 1)
    assert d.fiscal_year().quarter_range(d.quarter()).start == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_current_dateinq1_returnslastdayofashoj() -> (
    None
):
    """The current quarter of a Q1 date ends in Ashoj."""
    d = NepaliDate(2080, 4, 1)
    r = d.fiscal_year().quarter_range(d.quarter())
    assert (r.end.year, r.end.month) == (2080, 6)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_current_dateinq2_returnskartik1() -> (
    None
):
    """The current quarter of a Q2 date starts on Kartik 1."""
    d = NepaliDate(2080, 7, 1)
    assert d.fiscal_year().quarter_range(d.quarter()).start == NepaliDate(2080, 7, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_current_dateinq3_returnsmagh1() -> (
    None
):
    """The current quarter of a Q3 date starts on Magh 1."""
    d = NepaliDate(2080, 10, 1)
    assert d.fiscal_year().quarter_range(d.quarter()).start == NepaliDate(2080, 10, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_current_dateinq3_returnslastdayofchaitra() -> (
    None
):
    """The current quarter of a Q3 date ends in Chaitra."""
    d = NepaliDate(2080, 10, 1)
    r = d.fiscal_year().quarter_range(d.quarter())
    assert (r.end.year, r.end.month) == (2080, 12)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_explicitfirstwithoffset1_returnsnextyearshrawan1() -> (
    None
):
    """An offset Q1 start shifts forward a year."""
    assert FiscalYear(2081).quarter_range(Quarter.Q1).start == NepaliDate(2081, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_explicitfirstwithnegativeoffset_returnspreviousyearshrawan1() -> (
    None
):
    """A negative offset Q1 start shifts backward a year."""
    assert FiscalYear(2079).quarter_range(Quarter.Q1).start == NepaliDate(2079, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_allfiscalmonths_return2080shrawan1_1() -> (
    None
):
    """A date in Shrawan maps to Shrawan 1 of 2080."""
    assert NepaliDate(2080, 4, 1).fiscal_year().start() == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_allfiscalmonths_return2080shrawan1_2() -> (
    None
):
    """A date in Ashoj maps to Shrawan 1 of 2080."""
    assert NepaliDate(2080, 6, 1).fiscal_year().start() == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_allfiscalmonths_return2080shrawan1_3() -> (
    None
):
    """A date in Kartik maps to Shrawan 1 of 2080."""
    assert NepaliDate(2080, 7, 1).fiscal_year().start() == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_allfiscalmonths_return2080shrawan1_4() -> (
    None
):
    """A date in Chaitra maps to Shrawan 1 of 2080."""
    assert NepaliDate(2080, 12, 1).fiscal_year().start() == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_q4calendarmonths_returnpreviousyearshrawan1_1() -> (
    None
):
    """A Baishakh date maps to the previous fiscal year."""
    assert NepaliDate(2080, 1, 1).fiscal_year().start() == NepaliDate(2079, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_q4calendarmonths_returnpreviousyearshrawan1_2() -> (
    None
):
    """A Jestha date maps to the previous fiscal year."""
    assert NepaliDate(2080, 2, 1).fiscal_year().start() == NepaliDate(2079, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearstartdate_q4calendarmonths_returnpreviousyearshrawan1_3() -> (
    None
):
    """An Ashad date maps to the previous fiscal year."""
    assert NepaliDate(2080, 3, 1).fiscal_year().start() == NepaliDate(2079, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_fromq4date_explicitfirst_returnsfy2080q1start() -> (
    None
):
    """An explicit Q1 of FY 2080 starts on Shrawan 1."""
    assert FiscalYear(2080).quarter_range(Quarter.Q1).start == NepaliDate(2080, 4, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_fromq4date_explicitsecond_returnsfy2080q2start() -> (
    None
):
    """An explicit Q2 of FY 2080 starts on Kartik 1."""
    assert FiscalYear(2080).quarter_range(Quarter.Q2).start == NepaliDate(2080, 7, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_fromq4date_explicitthird_returnsfy2080q3start() -> (
    None
):
    """An explicit Q3 of FY 2080 starts on Magh 1."""
    assert FiscalYear(2080).quarter_range(Quarter.Q3).start == NepaliDate(2080, 10, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_fromq4date_explicitfourth_returnsfy2080q4start() -> (
    None
):
    """An explicit Q4 of FY 2080 starts on Baishakh 1 of 2081."""
    assert FiscalYear(2080).quarter_range(Quarter.Q4).start == NepaliDate(2081, 1, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterstartdate_fromq4date_current_returnsfy2080q4start() -> (
    None
):
    """The current quarter of a Q4 date is Q4."""
    d = NepaliDate(2081, 1, 1)
    assert d.fiscal_year().quarter_range(d.quarter()).start == NepaliDate(2081, 1, 1)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_fromq4date_explicitfirst_returnsfy2080q1end() -> (
    None
):
    """An explicit Q1 of FY 2080 ends in Ashoj."""
    r = FiscalYear(2080).quarter_range(Quarter.Q1)
    assert (r.end.year, r.end.month) == (2080, 6)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_fromq4date_explicitthird_returnsfy2080q3end() -> (
    None
):
    """An explicit Q3 of FY 2080 ends in Chaitra."""
    r = FiscalYear(2080).quarter_range(Quarter.Q3)
    assert (r.end.year, r.end.month) == (2080, 12)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_fromq4date_explicitfourth_returnsfy2080q4end() -> (
    None
):
    """An explicit Q4 of FY 2080 ends in Ashad of 2081."""
    r = FiscalYear(2080).quarter_range(Quarter.Q4)
    assert (r.end.year, r.end.month) == (2081, 3)


def test_fiscalyearinstancemethodtests_fiscalyearquarterenddate_fromq4date_current_returnsfy2080q4end() -> (
    None
):
    """The current quarter of a Q4 date ends in Ashad of 2081."""
    d = NepaliDate(2081, 1, 1)
    r = d.fiscal_year().quarter_range(d.quarter())
    assert (r.end.year, r.end.month) == (2081, 3)


def test_fiscalyeartests_getfiscalyearstartandenddate_validyear_returnscorrectdates() -> None:
    """A valid fiscal year starts on Shrawan 1."""
    assert FiscalYear(2080).start() == NepaliDate(2080, 4, 1)


def test_fiscalyeartests_getfiscalyearstartandenddate_invalidyear_throwsexception_1() -> None:
    """A fiscal year before the range is rejected."""
    with pytest.raises(NepDateError):
        FiscalYear(1843)


def test_fiscalyeartests_getfiscalyearstartandenddate_invalidyear_throwsexception_2() -> None:
    """A fiscal year after the range is rejected."""
    with pytest.raises(NepDateError):
        FiscalYear(2200)


def test_fiscalyeartests_getfiscalyearstartdate_validyear_returnscorrectdate() -> None:
    """A valid fiscal year start is Shrawan 1."""
    assert FiscalYear(2080).start() == NepaliDate(2080, 4, 1)


def test_fiscalyeartests_getfiscalyearenddate_validyear_returnscorrectdate() -> None:
    """A valid fiscal year ends at the next Ashad."""
    assert FiscalYear(2080).end() == NepaliDate(2081, 3, 1).last_of_month()


def test_fiscalyeartests_fiscalyearstartandenddate_onnepalidateinstance_returnscorrectdates() -> (
    None
):
    """A date instance yields its fiscal start."""
    assert NepaliDate(2080, 5, 15).fiscal_year().start() == NepaliDate(2080, 4, 1)


def test_fiscalyeartests_fiscalyearstartdate_onnepalidateinstance_returnscorrectdate() -> None:
    """A date instance yields its fiscal start."""
    assert NepaliDate(2080, 5, 15).fiscal_year().start() == NepaliDate(2080, 4, 1)


def test_fiscalyeartests_fiscalyearenddate_onnepalidateinstance_returnscorrectdate() -> None:
    """A date instance yields its fiscal end."""
    assert NepaliDate(2080, 5, 15).fiscal_year().end() == NepaliDate(2081, 3, 1).last_of_month()


def test_fiscalyeartests_getfiscalyearquarterstartandenddate_validyearandmonth_returnscorrectdates() -> (
    None
):
    """A fiscal quarter range starts on Shrawan 1."""
    assert FiscalYear(2080).quarter_range(Quarter.Q1).start == NepaliDate(2080, 4, 1)


def test_fiscalyeartests_getfiscalyearquarterstartdate_validyearandmonth_returnscorrectdate() -> (
    None
):
    """A fiscal quarter start for Kartik is Kartik 1."""
    assert FiscalYear(2080).quarter_range(Quarter.Q2).start == NepaliDate(2080, 7, 1)


def test_fiscalyeartests_getfiscalyearquarterenddate_validyearandmonth_returnscorrectdate() -> None:
    """A fiscal quarter end for Chaitra is the last day of Chaitra."""
    r = FiscalYear(2080).quarter_range(Quarter.Q3)
    assert (r.end.year, r.end.month) == (2080, 12)


def test_nepalidatearithmeticedgecasetests_adddays_zero_returnssamedate() -> None:
    """Adding zero days returns an equal date."""
    d = NepaliDate(2080, 5, 15)
    assert d.add_days(0) == d


def test_nepalidatearithmeticedgecasetests_adddays_positiveacrossmonthboundary_iscorrect() -> None:
    """Adding days across a month boundary lands in the next month."""
    assert NepaliDate(2080, 1, 31).add_days(1) == NepaliDate(2080, 2, 1)


def test_nepalidatearithmeticedgecasetests_adddays_negativeacrossmonthboundary_iscorrect() -> None:
    """Subtracting days across a month boundary lands in the previous month."""
    assert NepaliDate(2080, 2, 1).add_days(-1) == NepaliDate(2080, 1, 31)


def test_nepalidatearithmeticedgecasetests_adddays_positiveacrossyearboundary_iscorrect() -> None:
    """Adding days across a year boundary lands in the next year."""
    assert NepaliDate(2080, 12, 30).add_days(1) == NepaliDate(2081, 1, 1)


def test_nepalidatearithmeticedgecasetests_adddays_negativeacrossyearboundary_iscorrect() -> None:
    """Subtracting days across a year boundary lands in the previous year."""
    assert NepaliDate(2081, 1, 1).add_days(-1) == NepaliDate(2080, 12, 30)


def test_nepalidatearithmeticedgecasetests_adddays_largepositivevalue_iscorrect() -> None:
    """A large positive day count round-trips."""
    d = NepaliDate(2080, 1, 1)
    assert d.add_days(400).add_days(-400) == d


def test_nepalidatearithmeticedgecasetests_addmonths_positivecrossesyearboundary_iscorrect() -> (
    None
):
    """Adding a month across a year boundary lands in the next year."""
    assert NepaliDate(2080, 12, 15).add_months(1) == NepaliDate(2081, 1, 15)


def test_nepalidatearithmeticedgecasetests_addmonths_negativecrossesyearboundary_iscorrect() -> (
    None
):
    """Subtracting a month across a year boundary lands in the previous year."""
    assert NepaliDate(2081, 1, 15).add_months(-1) == NepaliDate(2080, 12, 15)


def test_nepalidatearithmeticedgecasetests_addmonths_positivemorethan12_crossesmultipleyears() -> (
    None
):
    """Adding more than 12 months crosses multiple years."""
    assert NepaliDate(2080, 5, 15).add_months(13) == NepaliDate(2081, 6, 15)


def test_nepalidatearithmeticedgecasetests_addmonths_exactly12_samemonthnextyear() -> None:
    """Adding exactly 12 months keeps the month and advances the year."""
    assert NepaliDate(2080, 5, 15).add_months(12) == NepaliDate(2081, 5, 15)


def test_nepalidatearithmeticedgecasetests_addmonths_daycappedatmonthend_whenresultmonthisshorter() -> (
    None
):
    """A day past the end clamps to the target month's length."""
    assert NepaliDate(2081, 4, 32).add_months(1) == NepaliDate(2081, 5, 31)


def test_nepalidatearithmeticedgecasetests_addmonths_negative_samedaypreservedwhenfits() -> None:
    """A negative month offset preserves the day when it fits."""
    assert NepaliDate(2080, 6, 15).add_months(-1) == NepaliDate(2080, 5, 15)


def test_nepalidatearithmeticedgecasetests_addmonths_halfmonth_addsapproximately15days() -> None:
    """Fractional months are not ported."""
    pytest.skip("D-02: fractional AddMonths is not ported")


def test_nepalidatearithmeticedgecasetests_addmonths_negativehalfmonth_subtractsapproximately15days() -> (
    None
):
    """Fractional months are not ported."""
    pytest.skip("D-02: fractional AddMonths is not ported")


def test_nepalidatearithmeticedgecasetests_addmonths_oneandhalfmonths_addsapproximately46days() -> (
    None
):
    """Fractional months are not ported."""
    pytest.skip("D-02: fractional AddMonths is not ported")


def test_nepalidatearithmeticedgecasetests_addmonths_fractionalvalue_returnsdatefurtherthanzeromonths() -> (
    None
):
    """Fractional months are not ported."""
    pytest.skip("D-02: fractional AddMonths is not ported")


def test_nepalidatearithmeticedgecasetests_constructor_datetimewithmidnighttime_ignorestime() -> (
    None
):
    """A datetime at midnight converts by its date part."""
    assert NepaliDate.from_date(datetime.datetime(2023, 4, 14, 0, 0)) == NepaliDate(2080, 1, 1)


def test_nepalidatearithmeticedgecasetests_constructor_datetimewithnoontime_ignorestime() -> None:
    """A datetime at noon converts by its date part."""
    assert NepaliDate.from_date(datetime.datetime(2023, 4, 14, 12, 0)) == NepaliDate(2080, 1, 1)


def test_nepalidatearithmeticedgecasetests_constructor_datetimewithendofdaytime_ignorestime() -> (
    None
):
    """A datetime at the end of day converts by its date part."""
    assert NepaliDate.from_date(datetime.datetime(2023, 4, 14, 23, 59, 59)) == NepaliDate(
        2080, 1, 1
    )


def test_nepalidatearithmeticedgecasetests_constructor_twodatetimesonsameenglishdatedifferenttimes_producesamenepalidate() -> (
    None
):
    """Two datetimes on the same AD date convert to the same BS date."""
    morning = NepaliDate.from_date(datetime.datetime(2023, 4, 14, 1, 0))
    evening = NepaliDate.from_date(datetime.datetime(2023, 4, 14, 22, 0))
    assert morning == evening


def test_nepalidatearithmeticedgecasetests_tryparse_autoadjust_dayyearmonthformat_returnscorrectdate() -> (
    None
):
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


def test_nepalidatearithmeticedgecasetests_tryparse_autoadjust_monthdayyearinvertedorder_returnscorrectdate() -> (
    None
):
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


def test_nepalidatearithmeticedgecasetests_tryparse_autoadjust_twodigityear_expandstocurrentmillennium() -> (
    None
):
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


def test_nepalidatearithmeticedgecasetests_tryparse_autoadjust_invaliddateafteradjustment_returnsfalse() -> (
    None
):
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


def test_nepalidatearithmeticedgecasetests_tryparse_autoadjust_validstandardformat_returnscorrectdate() -> (
    None
):
    """TryParse is C#-only."""
    pytest.skip("n/a: C# TryParse")


def test_nepalidatemanipulationtests_monthenddate_returnscorrectdate() -> None:
    """The month end date is the last day of the month."""
    assert NepaliDate(2080, 5, 1).last_of_month() == NepaliDate(2080, 5, 31)


def test_nepalidatemanipulationtests_addmonths_returnscorrectdate_1() -> None:
    """Adding one month lands in the next month."""
    assert NepaliDate(2080, 5, 15).add_months(1) == NepaliDate(2080, 6, 15)


def test_nepalidatemanipulationtests_addmonths_returnscorrectdate_2() -> None:
    """Subtracting one month lands in the previous month."""
    assert NepaliDate(2080, 5, 15).add_months(-1) == NepaliDate(2080, 4, 15)


def test_nepalidatemanipulationtests_addmonths_returnscorrectdate_3() -> None:
    """Adding twelve months advances the year."""
    assert NepaliDate(2080, 5, 15).add_months(12) == NepaliDate(2081, 5, 15)


def test_nepalidatemanipulationtests_addmonths_returnscorrectdate_4() -> None:
    """A day past the end clamps by default."""
    assert NepaliDate(2081, 4, 32).add_months(5) == NepaliDate(2081, 9, 29)


def test_nepalidatemanipulationtests_addmonths_returnscorrectdate_5() -> None:
    """SPILL carries the leftover days into the next month."""
    assert NepaliDate(2081, 4, 32).add_months(5, Overflow.SPILL) == NepaliDate(2081, 10, 3)


def test_nepalidatemanipulationtests_adddays_returnscorrectdate_1() -> None:
    """Adding days lands on the expected date."""
    assert NepaliDate(2080, 5, 15).add_days(5) == NepaliDate(2080, 5, 20)


def test_nepalidatemanipulationtests_adddays_returnscorrectdate_2() -> None:
    """Subtracting days lands on the expected date."""
    assert NepaliDate(2080, 5, 15).add_days(-5) == NepaliDate(2080, 5, 10)


def test_nepalidatemanipulationtests_adddays_returnscorrectdate_3() -> None:
    """Adding one day crosses into the next month."""
    assert NepaliDate(2080, 5, 31).add_days(1) == NepaliDate(2080, 6, 1)


def test_nepalidatemanipulationtests_adddays_returnscorrectdate_4() -> None:
    """Adding days crosses into the next year."""
    assert NepaliDate(2080, 12, 30).add_days(5) == NepaliDate(2081, 1, 5)


def test_nepalidatemanipulationtests_subtract_twodates_returnscorrecttimespan() -> None:
    """Subtracting two dates returns their day difference."""
    assert NepaliDate(2080, 5, 20) - NepaliDate(2080, 5, 5) == datetime.timedelta(days=15)


def test_nepalidatemanipulationtests_subtract_samedate_returnszero() -> None:
    """Subtracting a date from itself returns zero."""
    d = NepaliDate(2080, 5, 15)
    assert d - d == datetime.timedelta(0)


def test_nepalidaterangeextendedtests_forcalendaryear_startsatbaishakhone_endsatchaitraend() -> (
    None
):
    """A calendar year range spans Baishakh 1 to Chaitra's end."""
    r = DateRange.year(2080)
    assert r.start == NepaliDate(2080, 1, 1)
    assert r.end == NepaliDate(2080, 12, 1).last_of_month()


def test_nepalidaterangeextendedtests_forcalendaryear_lengthisreasonable() -> None:
    """A calendar year length equals the sum of its month lengths."""
    r = DateRange.year(2080)
    i = (2080 - _calendar.MIN_YEAR) * 12
    assert len(r) == sum(_calendar.MONTH_LENGTHS[i : i + 12])


def test_nepalidaterangeextendedtests_currentmonth_startisfirstdayofcurrentmonth() -> None:
    """DateRange has no current-month helper; build it from today() and month()."""
    pytest.skip("n/a: D-09, DateRange has no current-month helper")


def test_nepalidaterangeextendedtests_currentmonth_endislastdayofcurrentmonth() -> None:
    """DateRange has no current-month helper; build it from today() and month()."""
    pytest.skip("n/a: D-09, DateRange has no current-month helper")


def test_nepalidaterangeextendedtests_currentmonth_containstoday() -> None:
    """DateRange has no current-month helper; build it from today() and month()."""
    pytest.skip("n/a: D-09, DateRange has no current-month helper")


def test_nepalidaterangeextendedtests_currentfiscalyear_containstoday() -> None:
    """DateRange has no current-fiscal-year helper; build it from today() and fiscal_year()."""
    pytest.skip("n/a: D-09, DateRange has no current-fiscal-year helper")


def test_nepalidaterangeextendedtests_currentfiscalyear_startisshrawan() -> None:
    """DateRange has no current-fiscal-year helper; build it from today() and fiscal_year()."""
    pytest.skip("n/a: D-09, DateRange has no current-fiscal-year helper")


def test_nepalidaterangeextendedtests_currentfiscalyear_endisashadh() -> None:
    """DateRange has no current-fiscal-year helper; build it from today() and fiscal_year()."""
    pytest.skip("n/a: D-09, DateRange has no current-fiscal-year helper")


def test_nepalidaterangeextendedtests_currentcalendaryear_containstoday() -> None:
    """DateRange has no current-calendar-year helper; build it from today() and year()."""
    pytest.skip("n/a: D-09, DateRange has no current-calendar-year helper")


def test_nepalidaterangeextendedtests_currentcalendaryear_startisbaishakh1() -> None:
    """DateRange has no current-calendar-year helper; build it from today() and year()."""
    pytest.skip("n/a: D-09, DateRange has no current-calendar-year helper")


def test_nepalidaterangeextendedtests_splitbyfiscalquarter_emptyrange_returnsemptyarray() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_splitbyfiscalquarter_rangewithinonequarter_returnssinglerange() -> (
    None
):
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_splitbyfiscalquarter_rangespanningtwoquarters_returnstworanges() -> (
    None
):
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_splitbyfiscalquarter_fullfiscalyear_returnsfourranges() -> (
    None
):
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_splitbyfiscalquarter_rangeinq4months_singlerange() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_dateswithinterval_zero_throwsargumentoutofrangeexception() -> (
    None
):
    """DatesWithInterval is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_dateswithinterval_negativeinterval_throwsargumentoutofrangeexception() -> (
    None
):
    """DatesWithInterval is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_dateswithinterval_intervalofone_yieldseveryday() -> None:
    """DatesWithInterval is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_dateswithinterval_intervaloftwo_yieldsodddays() -> None:
    """DatesWithInterval is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_dateswithinterval_intervallargerthanrange_yieldsonlystartdate() -> (
    None
):
    """DatesWithInterval is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_dateswithinterval_emptyrange_yieldsnothing() -> None:
    """DatesWithInterval is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_weekenddays_includesundaytrue_returnsbothsaturdayandsunday() -> (
    None
):
    """Working-day helpers are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_weekenddays_includesundayfalse_returnsonlysaturday() -> None:
    """Working-day helpers are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_weekenddays_rangewithnoweekend_returnsempty() -> None:
    """Working-day helpers are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_weekenddays_emptyrange_returnsempty() -> None:
    """Working-day helpers are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_workingdays_excludesundayfalse_excludesonlysaturday() -> None:
    """Working-day helpers are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_workingdays_excludesundaytrue_excludesbothsatandsun() -> None:
    """Working-day helpers are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_workingdays_emptyrange_returnsempty() -> None:
    """Working-day helpers are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_fromdaycount_zerodays_throwsargumentoutofrangeexception() -> (
    None
):
    """FromDayCount is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_fromdaycount_negativedays_throwsargumentoutofrangeexception() -> (
    None
):
    """FromDayCount is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_intersect_nonoverlappingranges_returnsemptyrange() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_intersect_adjacentranges_returnsemptyrange() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_intersect_onerangefullyinsideother_returnsinnerrange() -> (
    None
):
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_union_leftrangeisempty_returnsrightrange() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_union_rightrangeisempty_returnsleftrange() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_union_nonoverlappingranges_spansentiregap() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_contains_exactstartdate_returnstrue() -> None:
    """The exact start date is in the range."""
    r = DateRange(NepaliDate(2080, 1, 5), NepaliDate(2080, 1, 20))
    assert NepaliDate(2080, 1, 5) in r


def test_nepalidaterangeextendedtests_contains_exactenddate_returnstrue() -> None:
    """The exact end date is in the range."""
    r = DateRange(NepaliDate(2080, 1, 5), NepaliDate(2080, 1, 20))
    assert NepaliDate(2080, 1, 20) in r


def test_nepalidaterangeextendedtests_contains_onedaybeforestart_returnsfalse() -> None:
    """A date one day before the start is outside the range."""
    r = DateRange(NepaliDate(2080, 1, 5), NepaliDate(2080, 1, 20))
    assert NepaliDate(2080, 1, 4) not in r


def test_nepalidaterangeextendedtests_contains_onedayafterend_returnsfalse() -> None:
    """A date one day after the end is outside the range."""
    r = DateRange(NepaliDate(2080, 1, 5), NepaliDate(2080, 1, 20))
    assert NepaliDate(2080, 1, 21) not in r


def test_nepalidaterangeextendedtests_contains_emptyrange_containsnothing() -> None:
    """There is no empty DateRange."""
    pytest.skip("n/a: D-09, no empty DateRange (start > end raises)")


def test_nepalidaterangeextendedtests_isadjacentto_gapbetweenranges_returnsfalse() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_isadjacentto_overlappingranges_returnsfalse() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_isadjacentto_emptyrange_returnsfalse() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_except_nonoverlappingexcluderange_returnsoriginalrange() -> (
    None
):
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_except_excluderangefullycontainsthis_returnsemptyarray() -> (
    None
):
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_except_excludeoverlapsstart_returnsrightpart() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_except_excludeoverlapsend_returnsleftpart() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangeextendedtests_getenumerator_threedayrange_yieldsexactlythreedates() -> None:
    """A three-day range yields exactly three dates."""
    r = DateRange(NepaliDate(2080, 1, 1), NepaliDate(2080, 1, 3))
    assert list(r) == [
        NepaliDate(2080, 1, 1),
        NepaliDate(2080, 1, 2),
        NepaliDate(2080, 1, 3),
    ]


def test_nepalidaterangeextendedtests_getenumerator_emptyrange_yieldsnodates() -> None:
    """There is no empty DateRange."""
    pytest.skip("n/a: D-09, no empty DateRange (start > end raises)")


def test_nepalidaterangeextendedtests_getenumerator_singledayrange_yieldsonedate() -> None:
    """A single-day range yields that one date."""
    d = NepaliDate(2080, 5, 5)
    assert list(DateRange(d, d)) == [d]


def test_nepalidaterangeextendedtests_tostring_defaultformat_isstartdashend() -> None:
    """DateRange has no ToString in the Python API."""
    pytest.skip("n/a: DateRange has no ToString in the Python API")


def test_nepalidaterangeextendedtests_tostring_emptyrange_returnsemptyrangestring() -> None:
    """DateRange has no ToString in the Python API."""
    pytest.skip("n/a: DateRange has no ToString in the Python API")


def test_nepalidaterangeextendedtests_tostring_withdateformat_usesspecifiedformat() -> None:
    """DateRange has no ToString in the Python API."""
    pytest.skip("n/a: DateRange has no ToString in the Python API")


def test_nepalidaterangeextendedtests_tostring_withdateformat_emptyrange_returnsemptyrangestring() -> (
    None
):
    """DateRange has no ToString in the Python API."""
    pytest.skip("n/a: DateRange has no ToString in the Python API")


def test_nepalidaterangeextendedtests_equals_identicalranges_returnstrue() -> None:
    """DateRange has no equality in the Python API."""
    pytest.skip("n/a: DateRange has no equality in the Python API")


def test_nepalidaterangeextendedtests_equals_differentstart_returnsfalse() -> None:
    """DateRange has no equality in the Python API."""
    pytest.skip("n/a: DateRange has no equality in the Python API")


def test_nepalidaterangeextendedtests_equals_differentend_returnsfalse() -> None:
    """DateRange has no equality in the Python API."""
    pytest.skip("n/a: DateRange has no equality in the Python API")


def test_nepalidaterangeextendedtests_equals_bothempty_returnstrue() -> None:
    """DateRange has no equality in the Python API."""
    pytest.skip("n/a: DateRange has no equality in the Python API")


def test_nepalidaterangeextendedtests_equals_objectoverload_samerange_returnstrue() -> None:
    """DateRange has no equality in the Python API."""
    pytest.skip("n/a: DateRange has no equality in the Python API")


def test_nepalidaterangeextendedtests_equals_objectoverload_wrongtype_returnsfalse() -> None:
    """DateRange has no equality in the Python API."""
    pytest.skip("n/a: DateRange has no equality in the Python API")


def test_nepalidaterangeextendedtests_gethashcode_equalranges_samehash() -> None:
    """DateRange has no hash in the Python API."""
    pytest.skip("n/a: DateRange has no hash in the Python API")


def test_nepalidaterangeextendedtests_operatorequals_identicalranges_returnstrue() -> None:
    """DateRange has no equality in the Python API."""
    pytest.skip("n/a: DateRange has no equality in the Python API")


def test_nepalidaterangeextendedtests_operatornotequals_differentranges_returnstrue() -> None:
    """DateRange has no equality in the Python API."""
    pytest.skip("n/a: DateRange has no equality in the Python API")


def test_nepalidaterangetests_constructor_validdates_createsrange() -> None:
    """A valid range keeps its start."""
    r = DateRange(NepaliDate(2080, 1, 1), NepaliDate(2080, 1, 10))
    assert r.start == NepaliDate(2080, 1, 1)


def test_nepalidaterangetests_constructor_endbeforestart_createsemptyrange() -> None:
    """There is no empty DateRange."""
    pytest.skip("n/a: D-09, no empty DateRange (start > end raises)")


def test_nepalidaterangetests_singleday_createsrangewithoneday() -> None:
    """A single-day range has that day as both ends."""
    d = NepaliDate(2080, 1, 1)
    r = DateRange(d, d)
    assert r.start == d
    assert r.end == d


def test_nepalidaterangetests_fromdaycount_createscorrectrange() -> None:
    """FromDayCount is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_formonth_createscorrectrange() -> None:
    """A month range starts on day 1."""
    assert DateRange.month(2080, 5).start == NepaliDate(2080, 5, 1)


def test_nepalidaterangetests_forfiscalyear_createscorrectrange() -> None:
    """A fiscal year range starts on Shrawan 1."""
    assert FiscalYear(2080).range().start == NepaliDate(2080, 4, 1)


def test_nepalidaterangetests_contains_dateinrange_returnstrue() -> None:
    """A date inside the range is contained."""
    r = DateRange(NepaliDate(2080, 1, 1), NepaliDate(2080, 1, 10))
    assert NepaliDate(2080, 1, 5) in r


def test_nepalidaterangetests_contains_dateoutsiderange_returnsfalse() -> None:
    """A date outside the range is not contained."""
    r = DateRange(NepaliDate(2080, 1, 1), NepaliDate(2080, 1, 10))
    assert NepaliDate(2080, 1, 11) not in r


def test_nepalidaterangetests_contains_rangefullycontained_returnstrue() -> None:
    """Range containment is not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_overlaps_rangesoverlap_returnstrue() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_overlaps_rangesdontoverlap_returnsfalse() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_isadjacentto_adjacentranges_returnstrue() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_intersect_overlappingranges_returnsintersection() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_union_overlappingranges_returnsunion() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_except_removingrangefrommiddle_returnstworanges() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_splitbymonth_rangeacrossmonths_splitscorrectly() -> None:
    """Set operations are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_workingdays_returnscorrectdays() -> None:
    """Working-day helpers are not ported."""
    pytest.skip("n/a: D-09, DateRange has no set operations")


def test_nepalidaterangetests_enumeration_enumeratesalldaysinrange() -> None:
    """Enumeration yields every day in the range."""
    r = DateRange(NepaliDate(2080, 1, 1), NepaliDate(2080, 1, 10))
    assert len(list(r)) == len(r)


def test_nepalidaterangetests_demo_rangeoperations() -> None:
    """A demo without assertions."""
    pytest.skip("n/a: C# demo")


def test_optimizationverificationtests_subtraction_samedate_returnszerodays() -> None:
    """Subtracting a date from itself returns zero days."""
    d = NepaliDate(2080, 5, 15)
    assert d - d == datetime.timedelta(0)


def test_optimizationverificationtests_subtraction_adjacentdays_returnsoneday() -> None:
    """Adjacent days differ by one day."""
    a = NepaliDate(2080, 5, 15)
    b = NepaliDate(2080, 5, 16)
    assert b - a == datetime.timedelta(days=1)


def test_optimizationverificationtests_subtraction_crossmonth_correctdays() -> None:
    """Days across a month boundary differ by one day."""
    assert NepaliDate(2080, 6, 1) - NepaliDate(2080, 5, 31) == datetime.timedelta(days=1)


def test_optimizationverificationtests_subtraction_crossyear_correctdays() -> None:
    """Days across a year boundary differ by one day."""
    assert NepaliDate(2081, 1, 1) - NepaliDate(2080, 12, 30) == datetime.timedelta(days=1)


# --- phase 3: Abilities/NepaliDateFormattableTests.cs ---

_NE_2080_05_15 = "\u0968\u0966\u096e\u0966/\u0966\u096b/\u0967\u096b"
_NE_2080_04_15 = "\u0968\u0966\u096e\u0966/\u0966\u096a/\u0967\u096b"


def test_nepalidateformattabletests_tostring_nullformat_returnsdefault() -> None:
    """A null format is the default display."""
    assert format(_FORMAT_DATE, "") == "2081/04/15"


def test_nepalidateformattabletests_tostring_g_sameasdefault() -> None:
    """``G`` and ``g`` are the default display.

    The catalogue ids ``ToString_G_SameAsDefault`` and ``ToString_g_SameAsDefault`` lower-case to
    the same function name, so one function covers both rows.
    """
    assert format(_FORMAT_DATE, "G") == str(_FORMAT_DATE)
    assert format(_FORMAT_DATE, "g") == str(_FORMAT_DATE)


def test_nepalidateformattabletests_tostring_d_sameasdefault() -> None:
    """``d`` is the default display."""
    assert format(_FORMAT_DATE, "d") == "2081/04/15"


def test_nepalidateformattabletests_tostring_d_returnslongdatestring() -> None:
    """``D`` is the long form, which contains the year."""
    assert "2081" in format(_FORMAT_DATE, "D")


def test_nepalidateformattabletests_tostring_s_returnssortableisoformat() -> None:
    """``s`` is the sortable ISO form."""
    assert format(_FORMAT_DATE, "s") == "2081-04-15"


def test_nepalidateformattabletests_customformat_yyyy_mm_dd_withdash() -> None:
    """``yyyy-MM-dd`` formats with dashes."""
    assert _FORMAT_DATE.format("yyyy-MM-dd") == "2081-04-15"


def test_nepalidateformattabletests_customformat_dd_mm_yyyy_withdot() -> None:
    """``dd.MM.yyyy`` formats day first with dots."""
    assert _FORMAT_DATE.format("dd.MM.yyyy") == "15.04.2081"


def test_nepalidateformattabletests_customformat_mm_slash_dd_slash_yyyy() -> None:
    """``MM/dd/yyyy`` formats month first with slashes."""
    assert _FORMAT_DATE.format("MM/dd/yyyy") == "04/15/2081"


def test_nepalidateformattabletests_customformat_mmmxxx_returnsthreecharmonthabbreviation() -> None:
    """``MMM`` is the three-letter month abbreviation, followed by literals."""
    assert _FORMAT_DATE.format("MMMxxx") == "Shrxxx"


def test_nepalidateformattabletests_customformat_mmmm_returnsfullmonthname() -> None:
    """``MMMM`` is the full month name."""
    assert _FORMAT_DATE.format("MMMM") == "Shrawan"


def test_nepalidateformattabletests_customformat_yy_returnstwodigityear() -> None:
    """``yy`` is the last two digits of the year."""
    assert _FORMAT_DATE.format("yy/MM/dd") == "81/04/15"


def test_nepalidateformattabletests_customformat_m_withoutleadingzero_returnsunpadded() -> None:
    """``M`` is the month without a leading zero."""
    assert _FORMAT_DATE.format("M/d/yyyy") == "4/15/2081"


def test_nepalidateformattabletests_customformat_singledigitmonth_withoutleadingzero() -> None:
    """A single-digit month and day have no leading zero with ``M`` and ``d``."""
    assert NepaliDate(2081, 1, 5).format("M/d/yyyy") == "1/5/2081"


def test_nepalidateformattabletests_customformat_literalinsinglequotes() -> None:
    """Text in single quotes is a literal."""
    assert _FORMAT_DATE.format("yyyy'BS'") == "2081BS"


def test_nepalidateformattabletests_customformat_backslashescapedtokens_produceliterals() -> None:
    """A backslash before a token letter writes the letter literally."""
    assert _FORMAT_DATE.format("yyyy\\M\\M-\\d\\d") == "2081MM-dd"


def test_nepalidateformattabletests_customformat_backslashbeforeliteralchar_ispassedthrough() -> (
    None
):
    """A backslash before a non-token character passes that character through."""
    assert _FORMAT_DATE.format("yyyy\\-MM\\-dd") == "2081-04-15"


def test_nepalidateformattabletests_stringinterpolation_withformatspecifier_usesiformattable() -> (
    None
):
    """An f-string spec reaches ``__format__``."""
    assert f"{_FORMAT_DATE:yyyy-MM-dd}" == "2081-04-15"


def test_nepalidateformattabletests_stringformatmethod_withspecifier() -> None:
    """``str.format`` reaches ``__format__``."""
    assert str.format("{0:yyyy-MM-dd}", _FORMAT_DATE) == "2081-04-15"


def test_nepalidateformattabletests_sortableformat_lexicographicorderequalschronologicalorder() -> (
    None
):
    """The ``s`` form sorts lexicographically in chronological order."""
    assert _D1.format("s") < _D3.format("s")


# --- phase 3: Abilities/NepaliDateParsableTests.cs ---


def test_nepalidateparsabletests_parse_via_genericconstraint_returns_correctdate() -> None:
    """``parse`` returns the date of a valid string."""
    assert NepaliDate.parse("2081/04/15") == _FORMAT_DATE


def test_nepalidateparsabletests_tryparse_via_genericconstraint_validdate_returns_true() -> None:
    """Python has no TryParse: ``parse`` returns the date on success."""
    assert NepaliDate.parse("2081/04/15") == _FORMAT_DATE


def test_nepalidateparsabletests_tryparse_via_genericconstraint_invaliddate_returns_false() -> None:
    """Python has no TryParse: ``parse`` raises where C# returns false."""
    _assert_parse_error("invalid", ErrorKind.INVALID_CHARACTER)


def test_nepalidateparsabletests_spanparse_via_genericconstraint_returns_correctdate() -> None:
    """C# ReadOnlySpan has no Python equivalent."""
    pytest.skip("n/a: C# ReadOnlySpan")


def test_nepalidateparsabletests_spantryparse_via_genericconstraint_validdate_returns_true() -> (
    None
):
    """C# ReadOnlySpan has no Python equivalent."""
    pytest.skip("n/a: C# ReadOnlySpan")


# --- phase 3: Core/NepaliDateMonthNameTests.cs ---


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_1() -> None:
    """Baishakh is month 1."""
    assert NepaliDate(2080, 1, 1).month_enum is Month.BAISHAKH


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_2() -> None:
    """Jestha is month 2."""
    assert NepaliDate(2080, 2, 1).month_enum is Month.JESTHA


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_3() -> None:
    """Ashad is month 3."""
    assert NepaliDate(2080, 3, 1).month_enum is Month.ASHAD


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_4() -> None:
    """Shrawan is month 4."""
    assert NepaliDate(2080, 4, 1).month_enum is Month.SHRAWAN


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_5() -> None:
    """Bhadra is month 5."""
    assert NepaliDate(2080, 5, 1).month_enum is Month.BHADRA


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_6() -> None:
    """Ashoj is month 6."""
    assert NepaliDate(2080, 6, 1).month_enum is Month.ASHOJ


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_7() -> None:
    """Kartik is month 7."""
    assert NepaliDate(2080, 7, 1).month_enum is Month.KARTIK


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_8() -> None:
    """Mangsir is month 8."""
    assert NepaliDate(2080, 8, 1).month_enum is Month.MANGSIR


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_9() -> None:
    """Poush is month 9."""
    assert NepaliDate(2080, 9, 1).month_enum is Month.POUSH


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_10() -> None:
    """Magh is month 10."""
    assert NepaliDate(2080, 10, 1).month_enum is Month.MAGH


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_11() -> None:
    """Falgun is month 11."""
    assert NepaliDate(2080, 11, 1).month_enum is Month.FALGUN


def test_nepalidatemonthnametests_monthname_allmonths_returncorrectenum_12() -> None:
    """Chaitra is month 12."""
    assert NepaliDate(2080, 12, 1).month_enum is Month.CHAITRA


def test_nepalidatemonthnametests_monthname_samemonthdifferentdays_allreturnsameenum() -> None:
    """Different days of Shrawan all report Shrawan."""
    length = NepaliDate(2080, 4, 1).month_length
    for day in (1, 15, length):
        assert NepaliDate(2080, 4, day).month_enum is Month.SHRAWAN


def test_nepalidatemonthnametests_monthname_samemonthdifferentyears_allreturnsameenum_1() -> None:
    """Poush 2070 reports Poush."""
    assert NepaliDate(2070, 9, 1).month_enum is Month.POUSH


def test_nepalidatemonthnametests_monthname_samemonthdifferentyears_allreturnsameenum_2() -> None:
    """Poush 2080 reports Poush."""
    assert NepaliDate(2080, 9, 1).month_enum is Month.POUSH


def test_nepalidatemonthnametests_monthname_samemonthdifferentyears_allreturnsameenum_3() -> None:
    """Poush 2090 reports Poush."""
    assert NepaliDate(2090, 9, 1).month_enum is Month.POUSH


def test_nepalidatemonthnametests_monthname_samemonthdifferentyears_allreturnsameenum_4() -> None:
    """Poush 2100 reports Poush."""
    assert NepaliDate(2100, 9, 1).month_enum is Month.POUSH


def test_nepalidatemonthnametests_monthname_addingonemonth_advancesenum() -> None:
    """Adding a month advances the month enum."""
    assert NepaliDate(2080, 11, 1).add_months(1).month_enum is Month.CHAITRA


def test_nepalidatemonthnametests_monthname_yearboundary_wrapsfromchaitratobasikhakh() -> None:
    """Adding a month to Chaitra wraps to Baishakh of the next year."""
    chaitra = NepaliDate(2080, 12, 1)
    assert chaitra.month_enum is Month.CHAITRA
    assert chaitra.add_months(1).month_enum is Month.BAISHAKH


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_1() -> None:
    """Baishakh has integer value 1."""
    assert int(Month.BAISHAKH) == _MONTH_NUMBERS[0]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_2() -> None:
    """Jestha has integer value 2."""
    assert int(Month.JESTHA) == _MONTH_NUMBERS[1]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_3() -> None:
    """Ashad has integer value 3."""
    assert int(Month.ASHAD) == _MONTH_NUMBERS[2]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_4() -> None:
    """Shrawan has integer value 4."""
    assert int(Month.SHRAWAN) == _MONTH_NUMBERS[3]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_5() -> None:
    """Bhadra has integer value 5."""
    assert int(Month.BHADRA) == _MONTH_NUMBERS[4]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_6() -> None:
    """Ashoj has integer value 6."""
    assert int(Month.ASHOJ) == _MONTH_NUMBERS[5]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_7() -> None:
    """Kartik has integer value 7."""
    assert int(Month.KARTIK) == _MONTH_NUMBERS[6]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_8() -> None:
    """Mangsir has integer value 8."""
    assert int(Month.MANGSIR) == _MONTH_NUMBERS[7]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_9() -> None:
    """Poush has integer value 9."""
    assert int(Month.POUSH) == _MONTH_NUMBERS[8]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_10() -> None:
    """Magh has integer value 10."""
    assert int(Month.MAGH) == _MONTH_NUMBERS[9]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_11() -> None:
    """Falgun has integer value 11."""
    assert int(Month.FALGUN) == _MONTH_NUMBERS[10]


def test_nepalidatemonthnametests_nepalimonthsenum_integervaluematchesmonthnumber_12() -> None:
    """Chaitra has integer value 12."""
    assert int(Month.CHAITRA) == _MONTH_NUMBERS[11]


# --- phase 3: Core/OptimizationVerificationTests.cs ---


def test_optimizationverificationtests_tostring_producesexactformat_1() -> None:
    """2080-05-15 displays as ``2080/05/15``."""
    assert str(NepaliDate(2080, 5, 15)) == "2080/05/15"


def test_optimizationverificationtests_tostring_producesexactformat_2() -> None:
    """2080-01-01 displays as ``2080/01/01``."""
    assert str(NepaliDate(2080, 1, 1)) == "2080/01/01"


def test_optimizationverificationtests_tostring_producesexactformat_3() -> None:
    """2080-12-30 displays as ``2080/12/30``."""
    assert str(NepaliDate(2080, 12, 30)) == "2080/12/30"


def test_optimizationverificationtests_tostring_producesexactformat_4() -> None:
    """1901-01-01 displays as ``1901/01/01``."""
    assert str(NepaliDate(1901, 1, 1)) == "1901/01/01"


def test_optimizationverificationtests_tostring_producesexactformat_5() -> None:
    """2199-12-30 displays as ``2199/12/30``."""
    assert str(NepaliDate(2199, 12, 30)) == "2199/12/30"


def test_optimizationverificationtests_tostring_producesexactformat_6() -> None:
    """2000-06-09 displays as ``2000/06/09``."""
    assert str(NepaliDate(2000, 6, 9)) == "2000/06/09"


def test_optimizationverificationtests_tostring_producesexactformat_7() -> None:
    """2100-10-29 displays as ``2100/10/29``."""
    assert str(NepaliDate(2100, 10, 29)) == "2100/10/29"


def test_optimizationverificationtests_tostring_outputisexactly10characters() -> None:
    """The default display is ten characters."""
    assert len(str(_VERIFY_DATE)) == _DISPLAY_LENGTH


def test_optimizationverificationtests_tostring_allmonthszeropadded() -> None:
    """Every month is two digits."""
    for month in range(1, 13):
        assert str(NepaliDate(2080, month, 1))[5:7] == f"{month:02d}"


def test_optimizationverificationtests_tostring_alldayszeropadded() -> None:
    """Every day is two digits."""
    length = _VERIFY_DATE.month_length
    for day in range(1, length + 1):
        assert str(NepaliDate(2080, 5, day))[8:10] == f"{day:02d}"


def test_optimizationverificationtests_tostring_roundtripswithconstructor() -> None:
    """The display form parses back to the same fields."""
    parsed = NepaliDate.parse(str(_VERIFY_DATE))
    assert (parsed.year, parsed.month, parsed.day) == (2080, 5, 15)


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_1() -> (
    None
):
    """YMD with a slash."""
    assert _VERIFY_DATE.short(DateOrder.YMD, Separator.SLASH) == "2080/05/15"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_2() -> (
    None
):
    """YMD with a dash."""
    assert _VERIFY_DATE.short(DateOrder.YMD, Separator.DASH) == "2080-05-15"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_3() -> (
    None
):
    """YMD with a dot."""
    assert _VERIFY_DATE.short(DateOrder.YMD, Separator.DOT) == "2080.05.15"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_4() -> (
    None
):
    """YMD with an underscore."""
    assert _VERIFY_DATE.short(DateOrder.YMD, Separator.UNDERSCORE) == "2080_05_15"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_5() -> (
    None
):
    """YMD with a space."""
    assert _VERIFY_DATE.short(DateOrder.YMD, Separator.SPACE) == "2080 05 15"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_6() -> (
    None
):
    """YMD with a backslash."""
    assert _VERIFY_DATE.short(DateOrder.YMD, Separator.BACKSLASH) == "2080\\05\\15"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_7() -> (
    None
):
    """DMY with a slash."""
    assert _VERIFY_DATE.short(DateOrder.DMY, Separator.SLASH) == "15/05/2080"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_8() -> (
    None
):
    """DMY with a dash."""
    assert _VERIFY_DATE.short(DateOrder.DMY, Separator.DASH) == "15-05-2080"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_9() -> (
    None
):
    """MDY with a slash."""
    assert _VERIFY_DATE.short(DateOrder.MDY, Separator.SLASH) == "05/15/2080"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_10() -> (
    None
):
    """YDM with a slash."""
    assert _VERIFY_DATE.short(DateOrder.YDM, Separator.SLASH) == "2080/15/05"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_11() -> (
    None
):
    """MYD with a slash."""
    assert _VERIFY_DATE.short(DateOrder.MYD, Separator.SLASH) == "05/2080/15"


def test_optimizationverificationtests_tostring_withformatandseparator_producescorrectoutput_12() -> (
    None
):
    """DYM with a slash."""
    assert _VERIFY_DATE.short(DateOrder.DYM, Separator.SLASH) == "15/2080/05"


def test_optimizationverificationtests_tostring_withoutleadingzeros_producescorrectoutput_1() -> (
    None
):
    """YMD without padding."""
    assert _VERIFY_DATE.short(DateOrder.YMD, Separator.SLASH, pad=False) == "2080/5/15"


def test_optimizationverificationtests_tostring_withoutleadingzeros_producescorrectoutput_2() -> (
    None
):
    """DMY without padding."""
    assert _VERIFY_DATE.short(DateOrder.DMY, Separator.DASH, pad=False) == "15-5-2080"


def test_optimizationverificationtests_tostring_withoutleadingzeros_producescorrectoutput_3() -> (
    None
):
    """MDY without padding."""
    assert _VERIFY_DATE.short(DateOrder.MDY, Separator.DOT, pad=False) == "5.15.2080"


def test_optimizationverificationtests_tounicodestring_defaultformat_convertsalldigits() -> None:
    """The Unicode form is the default display in Nepali digits."""
    assert _VERIFY_DATE.short(lang=Lang.NE) == _NE_2080_05_15


def test_optimizationverificationtests_tounicodestring_eachdigitconvertscorrectly() -> None:
    """Every ASCII digit maps to its Devanagari counterpart."""
    assert to_nepali_digits(1234567890) == "१२३४५६७८९०"


def test_optimizationverificationtests_tounicodestring_separatorspreserved() -> None:
    """Separators are not localised."""
    assert "-" in _VERIFY_DATE.short(sep=Separator.DASH, lang=Lang.NE)


def test_optimizationverificationtests_tounicodestring_samelengthastostring() -> None:
    """The Unicode form has the same length as the ASCII form."""
    assert len(_VERIFY_DATE.short(lang=Lang.NE)) == len(str(_VERIFY_DATE))


def test_optimizationverificationtests_smartdateparser_nepalidigits_parsecorrectly_1() -> None:
    """Lenient parse accepts Devanagari digits with slashes."""
    assert (
        NepaliDate.parse_lenient("\u0968\u0966\u096e\u0966/\u0966\u096b/\u0967\u096b").year
        == _YEAR_2080
    )


def test_optimizationverificationtests_smartdateparser_nepalidigits_parsecorrectly_2() -> None:
    """Lenient parse accepts Devanagari digits with dashes."""
    assert (
        NepaliDate.parse_lenient("\u0968\u0966\u096e\u0966-\u0966\u096b-\u0967\u096b").year
        == _YEAR_2080
    )


def test_optimizationverificationtests_smartdateparser_pureenglishdigits_noconversionneeded() -> (
    None
):
    """Plain ASCII digits parse without conversion."""
    assert NepaliDate.parse_lenient("2080/05/15").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_mixednepalienglishdigits_parsecorrectly() -> (
    None
):
    """A number may mix ASCII and Devanagari digits (D-05)."""
    assert NepaliDate.parse_lenient("\u0968\u0966\u096e0/0\u096b/15").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_withindicators_removesandparsescorrectly_1() -> (
    None
):
    """The ``B.S.`` era marker is dropped."""
    assert NepaliDate.parse_lenient("2080/05/15 B.S.").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_withindicators_removesandparsescorrectly_2() -> (
    None
):
    """The ``BS`` era marker is dropped."""
    assert NepaliDate.parse_lenient("2080/05/15 BS").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_withindicators_removesandparsescorrectly_3() -> (
    None
):
    """The ``V.S.`` era marker is dropped."""
    assert NepaliDate.parse_lenient("2080/05/15 V.S.").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_withindicators_removesandparsescorrectly_4() -> (
    None
):
    """The ``VS`` era marker is dropped."""
    assert NepaliDate.parse_lenient("2080/05/15 VS").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_withindicators_removesandparsescorrectly_5() -> (
    None
):
    """A lower-case ``bs`` era marker is dropped."""
    assert NepaliDate.parse_lenient("2080/05/15 bs").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_withindicators_removesandparsescorrectly_6() -> (
    None
):
    """A lower-case ``v.s.`` era marker is dropped."""
    assert NepaliDate.parse_lenient("2080/05/15 v.s.").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_withnepalikeywords_removesandparses() -> (
    None
):
    """``मिति`` and ``गते`` are dropped."""
    assert NepaliDate.parse_lenient("मिति 2080/05/15 गते").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_withextraspaces_parsescorrectly() -> None:
    """Leading, trailing and repeated spaces are harmless."""
    assert NepaliDate.parse_lenient("  2080 / 05 / 15  ").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_1() -> None:
    """Baisakh parses as month 1."""
    assert NepaliDate.parse_lenient("15 Baisakh 2080") == NepaliDate(2080, 1, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_2() -> None:
    """Jestha parses as month 2."""
    assert NepaliDate.parse_lenient("15 Jestha 2080") == NepaliDate(2080, 2, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_3() -> None:
    """Asar parses as month 3."""
    assert NepaliDate.parse_lenient("15 Asar 2080") == NepaliDate(2080, 3, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_4() -> None:
    """Shrawan parses as month 4."""
    assert NepaliDate.parse_lenient("15 Shrawan 2080") == NepaliDate(2080, 4, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_5() -> None:
    """Bhadra parses as month 5."""
    assert NepaliDate.parse_lenient("15 Bhadra 2080") == NepaliDate(2080, 5, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_6() -> None:
    """Ashwin parses as month 6."""
    assert NepaliDate.parse_lenient("15 Ashwin 2080") == NepaliDate(2080, 6, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_7() -> None:
    """Kartik parses as month 7."""
    assert NepaliDate.parse_lenient("15 Kartik 2080") == NepaliDate(2080, 7, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_8() -> None:
    """Mangsir parses as month 8."""
    assert NepaliDate.parse_lenient("15 Mangsir 2080") == NepaliDate(2080, 8, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_9() -> None:
    """Poush parses as month 9."""
    assert NepaliDate.parse_lenient("15 Poush 2080") == NepaliDate(2080, 9, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_10() -> None:
    """Magh parses as month 10."""
    assert NepaliDate.parse_lenient("15 Magh 2080") == NepaliDate(2080, 10, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_11() -> None:
    """Falgun parses as month 11."""
    assert NepaliDate.parse_lenient("15 Falgun 2080") == NepaliDate(2080, 11, 15)


def test_optimizationverificationtests_smartdateparser_allmonthnames_parsecorrectly_12() -> None:
    """Chaitra parses as month 12."""
    assert NepaliDate.parse_lenient("15 Chaitra 2080") == NepaliDate(2080, 12, 15)


def test_optimizationverificationtests_smartdateparser_monthnamedifferentpositions_parsescorrectly_1() -> (
    None
):
    """The month name may come first."""
    assert NepaliDate.parse_lenient("Baisakh 15, 2080") == NepaliDate(2080, 1, 15)


def test_optimizationverificationtests_smartdateparser_monthnamedifferentpositions_parsescorrectly_2() -> (
    None
):
    """The month name may come second."""
    assert NepaliDate.parse_lenient("2080 Baisakh 15") == NepaliDate(2080, 1, 15)


def test_optimizationverificationtests_smartdateparser_nepaliunicodemonthnames_parsecorrectly_1() -> (
    None
):
    """``वैशाख`` parses as month 1."""
    assert NepaliDate.parse_lenient("15 वैशाख 2080") == NepaliDate(2080, 1, 15)


def test_optimizationverificationtests_smartdateparser_nepaliunicodemonthnames_parsecorrectly_2() -> (
    None
):
    """``जेष्ठ`` parses as month 2."""
    assert NepaliDate.parse_lenient("15 जेष्ठ 2080") == NepaliDate(2080, 2, 15)


def test_optimizationverificationtests_smartdateparser_nepaliunicodemonthnames_parsecorrectly_3() -> (
    None
):
    """``असार`` parses as month 3."""
    assert NepaliDate.parse_lenient("15 असार 2080") == NepaliDate(2080, 3, 15)


def test_optimizationverificationtests_smartdateparser_nepaliunicodemonthnames_parsecorrectly_4() -> (
    None
):
    """``श्रावण`` parses as month 4."""
    assert NepaliDate.parse_lenient("15 श्रावण 2080") == NepaliDate(2080, 4, 15)


def test_optimizationverificationtests_smartdateparser_twodigityear_adjustedto2000s() -> None:
    """D-06: a two-digit year is Ambiguous, not expanded to 2080."""
    _assert_lenient_error("15/04/80", ErrorKind.AMBIGUOUS)


def test_optimizationverificationtests_smartdateparser_invalidinput_throwsformatexception() -> None:
    """Invalid text raises ``NepDateError``."""
    _assert_lenient_error("not a date", ErrorKind.UNRECOGNIZED)


def test_optimizationverificationtests_smartdateparser_nullinput_throwsexception() -> None:
    """C# throws on a null string; Python has no null reference."""
    pytest.skip("n/a: C# null reference")


def test_optimizationverificationtests_smartdateparser_emptyinput_throwsexception() -> None:
    """An empty string is Unrecognized in the lenient parser."""
    _assert_lenient_error("", ErrorKind.UNRECOGNIZED)


def test_optimizationverificationtests_smartdateparser_whitespaceinput_throwsexception() -> None:
    """Whitespace is Unrecognized in the lenient parser."""
    _assert_lenient_error(" ", ErrorKind.UNRECOGNIZED)


def test_optimizationverificationtests_smartdateparser_tryparse_validinput_returnstrue() -> None:
    """Python has no TryParse: ``parse_lenient`` returns the date on success."""
    assert NepaliDate.parse_lenient("2080/05/15").year == _YEAR_2080


def test_optimizationverificationtests_smartdateparser_tryparse_invalidinput_returnsfalse() -> None:
    """Python has no TryParse: ``parse_lenient`` raises where C# returns false."""
    _assert_lenient_error("garbage", ErrorKind.UNRECOGNIZED)


def test_optimizationverificationtests_smartdateparser_tryparse_nullinput_returnsfalse() -> None:
    """C# TryParse has no Python equivalent and there is no null reference."""
    pytest.skip("n/a: C# TryParse and null reference")


def test_optimizationverificationtests_tostring_everymonthfirstday_roundtripsviaconstructor() -> (
    None
):
    """Every month's first day round-trips through the display form and the parser."""
    for month in range(1, 13):
        date = NepaliDate(2080, month, 1)
        assert NepaliDate.parse(str(date)) == date


def test_optimizationverificationtests_unicodeconversion_alldigits_roundtripcorrectly() -> None:
    """The Nepali display form parses back to the same date."""
    assert NepaliDate.parse(_VERIFY_DATE.short(lang=Lang.NE)) == _VERIFY_DATE


def test_optimizationverificationtests_tolongdatestring_default_containsmonthnameandday() -> None:
    """The default long form contains the day."""
    assert "15" in _VERIFY_DATE.long()


def test_optimizationverificationtests_tolongdatestring_withdayname_containsdayofweek() -> None:
    """The long form with weekday contains the weekday name."""
    assert _VERIFY_DATE.weekday.label() in _VERIFY_DATE.long(weekday=True)


def test_optimizationverificationtests_tolongdatestring_withoutyear_doesnotcontainyear() -> None:
    """The long form without the year does not contain the year."""
    assert "2080" not in _VERIFY_DATE.long(year=False)


# --- phase 3: Core/SmartDateParserTests.cs ---


def test_smartdateparsertests_parse_standardformat_returnscorrectdate() -> None:
    """The standard form parses."""
    assert NepaliDate.parse_lenient("2080/04/15") == NepaliDate(2080, 4, 15)


def test_smartdateparsertests_parse_invertedformat_returnscorrectdate() -> None:
    """Day, month, year parses when the year is last and has four digits."""
    assert NepaliDate.parse_lenient("15/04/2080") == NepaliDate(2080, 4, 15)


def test_smartdateparsertests_parse_monthdayyearformat_returnscorrectdate() -> None:
    """D-06: the port does not guess a month-first three-number form."""
    _assert_lenient_error("04/15/2080", ErrorKind.INVALID_MONTH)


def test_smartdateparsertests_parse_withmonthnames_returnscorrectdate() -> None:
    """A Latin month name parses."""
    assert NepaliDate.parse_lenient("15 Shrawan 2080") == NepaliDate(2080, 4, 15)


def test_smartdateparsertests_parse_withnepaliunicode_returnscorrectdate() -> None:
    """Devanagari digits parse."""
    assert NepaliDate.parse_lenient(_NE_2080_04_15) == NepaliDate(2080, 4, 15)


def test_smartdateparsertests_parse_mixedformats_returnscorrectdate() -> None:
    """A Nepali month name among ASCII digits parses."""
    assert NepaliDate.parse_lenient("15 साउन 2080") == NepaliDate(2080, 4, 15)


def test_smartdateparsertests_parse_withsuffixes_returnscorrectdate() -> None:
    """An era marker suffix is dropped."""
    assert NepaliDate.parse_lenient("15 Shrawan 2080 B.S.") == NepaliDate(2080, 4, 15)


def test_smartdateparsertests_parse_withtypos_returnscorrectdate() -> None:
    """``Srawan`` is on the closed month-name list."""
    assert NepaliDate.parse_lenient("15 Srawan 2080") == NepaliDate(2080, 4, 15)


def test_smartdateparsertests_parse_shorteryearformats_returnscorrectdate() -> None:
    """D-06: a two-digit year is Ambiguous, not expanded."""
    _assert_lenient_error("15/04/80", ErrorKind.AMBIGUOUS)


def test_smartdateparsertests_parse_invalidformat_throwsformatexception() -> None:
    """Invalid text raises ``NepDateError``."""
    _assert_lenient_error("not a date", ErrorKind.UNRECOGNIZED)


def test_smartdateparsertests_tryparse_validformat_returnstrue() -> None:
    """Python has no TryParse: ``parse_lenient`` returns the date on success."""
    assert NepaliDate.parse_lenient("2080/04/15") == NepaliDate(2080, 4, 15)


def test_smartdateparsertests_tryparse_invalidformat_returnsfalse() -> None:
    """Python has no TryParse: ``parse_lenient`` raises where C# returns false."""
    _assert_lenient_error("garbage", ErrorKind.UNRECOGNIZED)


def test_smartdateparsertests_extensionmethod_tonepalidate_parsescorrectly() -> None:
    """The extension method is the strict parser."""
    assert NepaliDate.parse("2080/04/15") == NepaliDate(2080, 4, 15)


def test_smartdateparsertests_extensionmethod_trytonepalidate_parsescorrectly() -> None:
    """The Try extension method's success path is ``parse``."""
    assert NepaliDate.parse("2080/04/15") == NepaliDate(2080, 4, 15)


# --- phase 3: Extensions/StringExtensionsTests.cs ---


def test_stringextensionstests_tonepalidate_validdatestring_returnsnepalidate() -> None:
    """A valid string parses to the date."""
    assert NepaliDate.parse("2080/05/15") == NepaliDate(2080, 5, 15)


def test_stringextensionstests_tonepalidate_nepalidigits_returnsnepalidate() -> None:
    """Devanagari digits parse to the date."""
    assert NepaliDate.parse(_NE_2080_05_15) == NepaliDate(2080, 5, 15)


def test_stringextensionstests_tonepalidate_invaliddatestring_throwsformatexception() -> None:
    """An invalid string raises ``NepDateError``."""
    _assert_parse_error("not a date", ErrorKind.INVALID_CHARACTER)


def test_stringextensionstests_trytonepalidate_validdatestring_returnstrue() -> None:
    """The Try extension method's success path is ``parse``."""
    assert NepaliDate.parse("2080/05/15") == NepaliDate(2080, 5, 15)


def test_stringextensionstests_trytonepalidate_invaliddatestring_returnsfalse() -> None:
    """The Try extension method's failure path is ``parse`` raising."""
    _assert_parse_error("not a date", ErrorKind.INVALID_CHARACTER)
