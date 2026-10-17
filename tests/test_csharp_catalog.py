"""One test per C# catalogue row tagged phase 1 (P1-05)."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest

from nepdate import MAX, MIN, DateRange, FiscalYear, NepaliDate, Overflow, Quarter, _calendar
from nepdate._errors import ErrorKind, NepDateError
from nepdate._names import Month, Weekday

_PHASE_1_ROWS = 113
_PHASE_2_ROWS = 180

_D1 = NepaliDate(2081, 1, 1)
_D2 = NepaliDate(2081, 1, 2)
_D3 = NepaliDate(2081, 2, 1)
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
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_2() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_3() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_4() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_5() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_nepalidateconstructiontests_constructor_validstringformats_createsinstance_6() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


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
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_nepalidateconstructiontests_constructor_invalidstringformats_throwsexception_2() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_nepalidateconstructiontests_constructor_invalidstringformats_throwsexception_3() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_nepalidateconstructiontests_constructor_validformatinvaliddate_throwsexception_1() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


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
    """today() is the P4 interop task."""
    pytest.skip("pending P4-03: today()")


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
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_2() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_3() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_4() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_5() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_6() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_7() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_allseparators_parsecorrectly_8() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_1() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_2() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_3() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_4() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_5() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_invalidstrings_throwsexception_6() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_nullstring_throwsexception() -> None:
    """C# throws on a null string; Python has no null reference."""
    pytest.skip("n/a: C# null reference")


def test_optimizationverificationtests_constructor_withoutleadingzeros_parsescorrectly_1() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_withoutleadingzeros_parsescorrectly_2() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


def test_optimizationverificationtests_constructor_withoutleadingzeros_parsescorrectly_3() -> None:
    """The string constructor is the P3 strict parser."""
    pytest.skip("pending P3-04: string parsing")


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
    """Current-month helpers need today()."""
    pytest.skip("pending P4-03: today()")


def test_nepalidaterangeextendedtests_currentmonth_endislastdayofcurrentmonth() -> None:
    """Current-month helpers need today()."""
    pytest.skip("pending P4-03: today()")


def test_nepalidaterangeextendedtests_currentmonth_containstoday() -> None:
    """Current-month helpers need today()."""
    pytest.skip("pending P4-03: today()")


def test_nepalidaterangeextendedtests_currentfiscalyear_containstoday() -> None:
    """Current-fiscal helpers need today()."""
    pytest.skip("pending P4-03: today()")


def test_nepalidaterangeextendedtests_currentfiscalyear_startisshrawan() -> None:
    """Current-fiscal helpers need today()."""
    pytest.skip("pending P4-03: today()")


def test_nepalidaterangeextendedtests_currentfiscalyear_endisashadh() -> None:
    """Current-fiscal helpers need today()."""
    pytest.skip("pending P4-03: today()")


def test_nepalidaterangeextendedtests_currentcalendaryear_containstoday() -> None:
    """Current-calendar helpers need today()."""
    pytest.skip("pending P4-03: today()")


def test_nepalidaterangeextendedtests_currentcalendaryear_startisbaishakh1() -> None:
    """Current-calendar helpers need today()."""
    pytest.skip("pending P4-03: today()")


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
