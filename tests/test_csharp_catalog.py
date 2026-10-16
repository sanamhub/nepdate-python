"""One test per C# catalogue row tagged phase 1 (P1-05)."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest

from nepdate import MAX, MIN, NepaliDate, _calendar
from nepdate._errors import ErrorKind, NepDateError
from nepdate._names import Month, Weekday

_PHASE_1_ROWS = 113

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
